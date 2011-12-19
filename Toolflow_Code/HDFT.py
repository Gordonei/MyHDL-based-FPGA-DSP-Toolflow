#Hybrid DFT-FFT class
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *
import Actor,DFT,Mux,Unscrambler,DivideAndConquer,DFT_Model,numpy,math

class HDFT(Actor.Actor):
  name = "HDFT"
  
  twiddle_bitsize = 0 #Input parameters
  multiplier_bitsize = 0
  dft_size = 0
  
  num_dac_stages = 0
  dac_output_bitsize = 0
  
  dacs = [] #Internal divide and conquer stages
  dacs_tf_real = ()
  dacs_tf_imag = ()
  dac_signals_line_real = []
  dac_signals_line_imag = []
  dac_signals_trigger = []
  dac_signals_enable = []
  
  dac_mux_real = [] #lists of signals for connecting the divide and conquer modules to the mux
  dac_mux_imag = []
  dac_mux_trigger = []
  dac_mux_enable = []
  
  mux = None 
  mux_dft_line_real = Signal(intbv(0)) #Signal connecting the mux to the DFT module
  mux_dft_line_imag = Signal(intbv(0))
  mux_dft_trigger = Signal(bool(0))
  mux_dft_enable = Signal(bool(0))
  
  dft = None
  dft_output_bitsize = 0
  dft_tf_real = (())
  dft_tf_imag = (())
  dft_unscrambler_line_real = Signal(intbv(0)) #Signals connecting the DFT to the unscrambler module
  dft_unscrambler_line_imag = Signal(intbv(0))
  dft_unscrambler_trigger = Signal(bool(0))
  dft_unscrambler_enable = Signal(bool(0))
  
  unscrambler = None
  index_mapping  = ()
  
  def __init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize,twiddle_bitsize,multiplier_bitsize,dft_size):
    """
    HDFT Constructor
    Parameters:
      *Control Signals*
	clk -> clock signal, used to synchronise behaviour across the module
	reset -> asynchronous reset line, used to restart the behaviour of the module
    
      *Data Signals*
	**Input**
	  input_line_real -> input data line for the real part of the input signal
	  input_line_imag -> input data line for the imaginary part of the input signal
	  input_trigger -> input signal (1 bit) line used to indicate that data may be read into the actor
	  input_enable -> actually an output signal line used to indicate that the actor is ready to read new data
      
	**Output**
	  output_line_real -> output data line for the real part of the output signal
	  output_line_imag -> output data line for the imaginary part of the output signal
	  output_trigger -> output signal (1 bit) line used to indicate that data is ready to be read from the actor
	  output_enable -> actually an input signal line used to indicate to the module that the following actor is ready to read from it
      
      *Normal Parameters*
	no_inputs -> integer value specifying how many samples need to be read into the actor before it processes that data
	no_outputs -> integer value specifying how many samples will be produced  upon the completion of its processing activity
	input_bitsize -> the bit size of each of the input data lines
	output_bitsize -> the bit size of each of the output data line
	twiddle_bitsize -> the bit size of the twiddle factors used in the DFT calculation
	multiplier_bitsize -> the bit size of the result of the DFT operation
	dft_size ->  the size of the direct DFT performed as part of the HDFT algorithm
      
    """
    Actor.Actor.__init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize)
    
    self.twiddle_bitsize = twiddle_bitsize
    self.multiplier_bitsize = multiplier_bitsize
    self.dft_size = dft_size
    
    self.num_dac_stages = int(numpy.ceil(numpy.log(self.no_inputs/self.dft_size)/numpy.log(2)))
    self.dac_output_bitsize = self.input_bitsize + self.twiddle_bitsize*(self.num_dac_stages)
    
    for j in range(1,2**(self.num_dac_stages)): #there are 2^(dac stages)-1 dac units
      self.dac_signals_line_real.append(Signal(intbv(0,min=-2**(self.dac_output_bitsize-1),max=2**(self.dac_output_bitsize-1))))
      self.dac_signals_line_imag.append(Signal(intbv(0,min=-2**(self.dac_output_bitsize-1),max=2**(self.dac_output_bitsize-1))))
      self.dac_signals_trigger.append(Signal(bool(0)))
      self.dac_signals_enable.append(Signal(bool(1)))
    
    #The first DAC
    temp_tf = self.twiddle_factors(self.no_inputs,self.no_inputs/2,self.twiddle_bitsize)
    temp_tf_real = temp_tf[0]
    temp_tf_imag = temp_tf[1]
    self.dacs.append(DivideAndConquer.DivideAndConquer(self.input_line_real,self.input_line_imag,self.input_trigger,self.input_enable,self.no_inputs,self.dac_signals_line_real[0],self.dac_signals_line_imag[0],self.dac_signals_trigger[0],self.dac_signals_enable[0],self.no_inputs/2,self.dac_signals_line_real[1],self.dac_signals_line_imag[1],self.dac_signals_trigger[1],self.dac_signals_enable[1],self.no_inputs/2,self.reset,self.clk,self.twiddle_bitsize,temp_tf_real,temp_tf_imag,self.input_bitsize,self.dac_output_bitsize,self.dac_output_bitsize))
    
    #The rest of the DAC's, except for the last stage
    input_offset = 0
    output_offset = 2
    for i in range(1,self.num_dac_stages-1):
      temp_tf = self.twiddle_factors(self.no_inputs,self.no_inputs/(2**(i+1)),self.twiddle_bitsize)
      temp_tf_real = temp_tf[0]
      temp_tf_imag = temp_tf[1]
      for j in range(2**i): #each stage requires 2^(stage no)
	self.dacs.append(DivideAndConquer.DivideAndConquer(self.dac_signals_line_real[input_offset],self.dac_signals_line_imag[input_offset],self.dac_signals_trigger[input_offset],self.dac_signals_enable[input_offset],self.no_inputs/(2**i),self.dac_signals_line_real[output_offset],self.dac_signals_line_imag[output_offset],self.dac_signals_trigger[output_offset],self.dac_signals_enable[output_offset],self.no_inputs/(2**(i+1)),self.dac_signals_line_real[output_offset+1],self.dac_signals_line_imag[output_offset+1],self.dac_signals_trigger[output_offset+1],self.dac_signals_enable[output_offset+1],self.no_inputs/(2**(i+1)),self.reset,self.clk,self.twiddle_bitsize,temp_tf_real,temp_tf_imag,self.dac_output_bitsize,self.dac_output_bitsize,self.dac_output_bitsize))
	input_offset += 1
	output_offset += 2
	
    #The last stage of DACs, which feed into the mux, so they have their own array of output signals
    for i in range(2**(self.num_dac_stages-1)):
      for j in range(2): #2 signals for each DAC
	self.dac_mux_real.append(Signal(intbv(0,min=-2**(self.dac_output_bitsize-1),max=2**(self.dac_output_bitsize-1))))
	self.dac_mux_imag.append(Signal(intbv(0,min=-2**(self.dac_output_bitsize-1),max=2**(self.dac_output_bitsize-1))))
	self.dac_mux_trigger.append(Signal(bool(0)))
	self.dac_mux_enable.append(Signal(bool(0)))
      
      temp_tf = self.twiddle_factors(self.no_inputs,self.no_inputs/(2**(self.num_dac_stages)),self.twiddle_bitsize)
      temp_tf_real = temp_tf[0]
      temp_tf_imag = temp_tf[1]
      self.dacs.append(DivideAndConquer.DivideAndConquer(self.dac_signals_line_real[input_offset],self.dac_signals_line_imag[input_offset],self.dac_signals_trigger[input_offset],self.dac_signals_enable[input_offset],self.no_inputs/(2**(self.num_dac_stages-1)),self.dac_mux_real[-2],self.dac_mux_imag[-2],self.dac_mux_trigger[-2],self.dac_mux_enable[-2],self.no_inputs/(2**self.num_dac_stages),self.dac_mux_real[-1],self.dac_mux_imag[-1],self.dac_mux_trigger[-1],self.dac_mux_enable[-1],self.no_inputs/(2**self.num_dac_stages),self.reset,self.clk,self.twiddle_bitsize,temp_tf_real,temp_tf_imag,self.dac_output_bitsize,self.dac_output_bitsize,self.dac_output_bitsize))
      input_offset += 1
    
    #mux output signals and mux declaration itself. The input bitsize is truncated for input into the DFT
    self.mux_dft_line_real = Signal(intbv(0,min=-2**(self.multiplier_bitsize-1),max=2**(self.multiplier_bitsize-1)))
    self.mux_dft_line_imag = Signal(intbv(0,min=-2**(self.multiplier_bitsize-1),max=2**(self.multiplier_bitsize-1)))
    self.mux_dft_trigger = Signal(bool(0))
    self.mux_dft_enable = Signal(bool(1))
    self.mux = Mux.Mux(self.dac_mux_real,self.dac_mux_imag,self.dac_mux_trigger,self.dac_mux_enable,self.dft_size,len(self.dac_mux_real),self.mux_dft_line_real,self.mux_dft_line_imag,self.mux_dft_trigger,self.mux_dft_enable,self.dft_size,self.reset,self.clk,self.dac_output_bitsize,self.multiplier_bitsize)
    
    #dft twiddle factor generation
    dft_tf = self.twiddle_factors_power(self.dft_size,self.multiplier_bitsize)
    self.dft_tf_real = dft_tf[0]
    self.dft_tf_imag = dft_tf[1]
    
    #dft signal and unit declation.
    self.dft_output_bitsize = 2*self.multiplier_bitsize+int(self.dft_size/8.0)#self.dft_size-1
    self.dft_unscrambler_line_real = Signal(intbv(0,min=-2**(self.dft_output_bitsize),max=2**(self.dft_output_bitsize)))
    self.dft_unscrambler_line_imag = Signal(intbv(0,min=-2**(self.dft_output_bitsize),max=2**(self.dft_output_bitsize)))
    self.dft_unscrambler_trigger = Signal(bool(0))
    self.dft_unscrambler_enable = Signal(bool(1))
    self.dft = DFT.DFT(self.mux_dft_line_real,self.mux_dft_line_imag,self.mux_dft_trigger,self.mux_dft_enable,self.dft_size,self.dft_unscrambler_line_real,self.dft_unscrambler_line_imag,self.dft_unscrambler_trigger,self.dft_unscrambler_enable,self.dft_size,self.reset,self.clk,self.dft_tf_real,self.dft_tf_imag,self.multiplier_bitsize,self.dft_output_bitsize,self.multiplier_bitsize,self.multiplier_bitsize)
    
    #index remapping generated, and unscrambler unit declared, with the output being the output of the DFT. The output bitsize from the DFT is truncated to the output bitsize
    self.index_mapping = self.index_map(self.no_inputs,self.dft_size)
    self.unscrambler = Unscrambler.Unscrambler(self.dft_unscrambler_line_real,self.dft_unscrambler_line_imag,self.dft_unscrambler_trigger,self.dft_unscrambler_enable,self.dft_size,self.output_line_real,self.output_line_imag,self.output_trigger,self.output_enable,self.no_inputs,self.reset,self.clk,self.index_mapping,self.dft_output_bitsize,self.output_bitsize)
    
  def receiving(self): pass
  def processing(self): pass
  def transmiting(self): pass
  
  def logic(self,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,clk,reset):
    """
    HDFT logic method
    calls all of the modules used in the algorithm for conversion purposes
    """
    baseclass_logic = Actor.Actor.logic(self)
    
    #DAC Logic
    dac_receive_logic = [d.receiving() for d in self.dacs]
    dac_processing_logic = [d.processing() for d in self.dacs]
    dac_transmiting_logic = [d.transmiting() for d in self.dacs]
    dac_twiddle_rom_real_logic = [d.rom(d.twiddle_rom_line_real,d.twiddle_rom_addr_real,d.tf_real) for d in self.dacs]
    dac_twiddle_rom_imag_logic = [d.rom(d.twiddle_rom_line_imag,d.twiddle_rom_addr_imag,d.tf_imag) for d in self.dacs]
  
    #mux_logic = self.mux.logic() #method called to elaborate logic structure
    
    #Mux Logic
    self.mux.muxes = [] #this list will hold the mux 2 instances that make up the mux
    self.mux.muxes_signal_real = [] #these lists represent the internal signals that the mux 2 instances use to make up the N part mux
    self.mux.muxes_signal_imag = []
    self.mux.muxes_signal_trigger = []
    self.mux.muxes_signal_enable = []
    
    self.mux.muxes_signal_real.append(Signal(intbv(0,min=-2**(self.mux.input_bitsize-1),max=2**(self.mux.input_bitsize-1)))) #these lists represent the internal signals that the mux 2 instances use to make up the N part mux
    self.mux.muxes_signal_imag.append(Signal(intbv(0,min=-2**(self.mux.input_bitsize-1),max=2**(self.mux.input_bitsize-1))))
    self.mux.muxes_signal_trigger.append(Signal(bool(0)))
    self.mux.muxes_signal_enable.append(Signal(bool(1)))
    
    #assign output of the mux "tree" as input to the next class
    self.mux.input_line_real = self.mux.muxes_signal_real[-1]
    self.mux.input_line_imag = self.mux.muxes_signal_imag[-1]
    self.mux.input_trigger = self.mux.muxes_signal_trigger[-1]
    self.mux.input_enable = self.mux.muxes_signal_enable[-1]
    
    output_offset = 0 #Variable for tracking where the output lines from the muxes will be in the list
    index_slice = int(math.log(self.mux.no_input_lines)/math.log(2))-1 #Variable for tracking the bit which will be the select for a particular mux
    for i in range(int(math.log(self.mux.no_input_lines)/math.log(2))-1):
      print 2**i
      for j in range(2**i): #Each stage has 2^(stage no) muxes
	for k in range(2): #Each mux has 2 input signals
	  self.mux.muxes_signal_real.append(Signal(intbv(0,min=-2**(self.mux.input_bitsize-1),max=2**(self.mux.input_bitsize-1))))
	  self.mux.muxes_signal_imag.append(Signal(intbv(0,min=-2**(self.mux.input_bitsize-1),max=2**(self.mux.input_bitsize-1))))
	  self.mux.muxes_signal_trigger.append(Signal(bool(0)))
	  self.mux.muxes_signal_enable.append(Signal(bool(0)))
	
	#Mux construction, using two input signals just generated and a signal previous added to the list
	self.mux.muxes.append(self.mux.mux2(self.mux.muxes_signal_real[-2],self.mux.muxes_signal_imag[-2],self.mux.muxes_signal_trigger[-2],self.mux.muxes_signal_enable[-2],self.mux.muxes_signal_real[-1],self.mux.muxes_signal_imag[-1],self.mux.muxes_signal_trigger[-1],self.mux.muxes_signal_enable[-1],self.mux.muxes_signal_real[output_offset+j],self.mux.muxes_signal_imag[output_offset+j],self.mux.muxes_signal_trigger[output_offset+j],self.mux.muxes_signal_enable[output_offset+j],self.mux.input_line_no(index_slice),self.mux.clk))
      
      output_offset += 2**i #offset is basically the sum of the muxes up to the end of the previous stage
      index_slice -= 1 #index slice moves from left to right, as output grows by factor 2
      
    #for loop for connecting lists of input signals to the inputs to the outermost stages of the mux
    index = self.mux.no_input_lines/2
    for i in range(index):
      self.mux.muxes.append(self.mux.mux2(self.mux.input_line_real_array[i*2],self.mux.input_line_imag_array[i*2],self.mux.input_trigger_array[i*2],self.mux.input_enable_array[i*2],self.mux.input_line_real_array[i*2+1],self.mux.input_line_imag_array[i*2+1],self.mux.input_trigger_array[i*2+1],self.mux.input_enable_array[i*2+1],self.mux.muxes_signal_real[output_offset+i],self.mux.muxes_signal_imag[output_offset+i],self.mux.muxes_signal_trigger[output_offset+i],self.mux.muxes_signal_enable[output_offset+i],self.mux.input_line_no(index_slice),self.mux.clk))
    
    mux_receive_logic = self.mux.receiving()
    mux_processing_logic = self.mux.processing()
    mux_transmiting_logic = self.mux.transmiting()
    mux_muxes_tree_logic = self.mux.muxes
  
    #self.dft.logic() #method called to elaborate logic structure
    #DFT Logic
    self.dft.twiddle_factor_units = [] #twiddle roms used to store twiddle values
    self.dft.twiddle_factor_units_output_real = [] #output signals from twiddle roms
    self.dft.twiddle_factor_units_output_imag = []
  
    self.dft.multipliers = [] #normal multiplers used in the complex multiplication task
    self.dft.multiplier_signals = [] #signals used to communicate within the complex multipliers
  
    self.dft.complex_multiplier_loaders = [] #units that do the pre-multiplication addition for the complex multiplication operation
    self.dft.complex_multiplier_adders = [] #units that do the post-multiplcation addition for the complex multiplication operation
    self.dft.multipliers_output_real = [] #output signals from the complex multipliers
    self.dft.multipliers_output_imag = []
  
    self.dft.complex_adders = [] #complex adder units used to sum outputs input value multiplication with twiddle factors
    self.dft.complex_adders_output_real = [] #output signals from the adders
    self.dft.complex_adders_output_imag = []
    self.dft.complex_adders_output_trigger = [] #output triggers for adder units, used to trigger the next adder in the set, and reset the previous set
    
    adder_stages = int(math.log(self.dft.no_inputs)/math.log(2)) #calculating the required size of the adder tree
    #creating output triggers for the adders in the tree
    for i in range(int(self.dft.no_inputs)-1): self.dft.complex_adders_output_trigger.append(Signal(bool(0)))#,delay=1))
    
    #logic to create complex multiplications and twiddle factor units, and wire them up
    self.dft.twiddle_factor_units_output_real.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize-1),max=2**(self.dft.multiplier_bitsize-1))))
    
    adder_trigger_index = 0
    for i in range(self.dft.no_inputs):
      self.dft.twiddle_factor_units_output_real.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize-1),max=2**(self.dft.multiplier_bitsize-1))))
      self.dft.twiddle_factor_units.append(self.dft.rom(self.dft.twiddle_factor_units_output_real[-1],self.dft.iteration_count,tuple(map(int,self.dft.tf_real[i*self.dft.no_inputs:i*self.dft.no_inputs+self.dft.no_inputs]))))
      
      self.dft.twiddle_factor_units_output_imag.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize-1),max=2**(self.dft.multiplier_bitsize-1))))
      self.dft.twiddle_factor_units.append(self.dft.rom(self.dft.twiddle_factor_units_output_imag[-1],self.dft.iteration_count,tuple(map(int,self.dft.tf_imag[i*self.dft.no_inputs:i*self.dft.no_inputs+self.dft.no_inputs]))))
      
      for j in range(3): #three multipliers needed per complex multiplication
	self.dft.multiplier_signals.append(Signal(intbv(0,min=-2**(2*self.dft.multiplier_bitsize-1),max=2**(2*self.dft.multiplier_bitsize-1))))
	for k in range(2): #three signals needed per multipler -> output, input_a, input_b
	  self.dft.multiplier_signals.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize),max=2**(self.dft.multiplier_bitsize))))
	
	multi_name = "multi_%d_%d_%d" % (i,j,k)
	self.dft.multipliers.append(self.dft.multi(self.dft.multiplier_signals[-3],self.dft.multiplier_signals[-2],self.dft.multiplier_signals[-1],self.dft.clk,self.dft.reset,multi_name,self.dft.pull_up))
	
      self.dft.complex_multiplier_loaders.append(self.dft.complex_multiplier_loader(self.dft.input_buffer_real[i],self.dft.input_buffer_imag[i],self.dft.twiddle_factor_units_output_real[-1],self.dft.twiddle_factor_units_output_imag[-1],self.dft.multiplier_signals[-8],self.dft.multiplier_signals[-7],self.dft.multiplier_signals[-5],self.dft.multiplier_signals[-4],self.dft.multiplier_signals[-2],self.dft.multiplier_signals[-1]))
      
      self.dft.multipliers_output_real.append(Signal(intbv(0,min=-2**(2*self.dft.multiplier_bitsize-1),max=2**(2*self.dft.multiplier_bitsize-1))))
      self.dft.multipliers_output_imag.append(Signal(intbv(0,min=-2**(2*self.dft.multiplier_bitsize-1),max=2**(2*self.dft.multiplier_bitsize-1))))
      self.dft.complex_multiplier_adders.append(self.dft.complex_multiplier_adder(self.dft.multipliers_output_real[-1],self.dft.multipliers_output_imag[-1],self.dft.multiplier_signals[-9],self.dft.multiplier_signals[-6],self.dft.multiplier_signals[-3]))
      
      #creating the first row of the adder tree, i.e. the stage straight after the complex multiplication
      if(i%2): #every 2nd value
	self.dft.complex_adders_output_real.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize*2+adder_stages),max=2**(self.dft.multiplier_bitsize*2+adder_stages))))
	self.dft.complex_adders_output_imag.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize*2+adder_stages),max=2**(self.dft.multiplier_bitsize*2+adder_stages))))
    
	self.dft.complex_adders.append(self.dft.complex_adder(self.dft.complex_adders_output_real[-1],self.dft.complex_adders_output_imag[-1],self.dft.complex_adders_output_trigger[adder_trigger_index],self.dft.multipliers_output_real[-2],self.dft.multipliers_output_imag[-2],self.dft.processing_iteration,self.dft.multipliers_output_real[-1],self.dft.multipliers_output_imag[-1],self.dft.processing_iteration))
	adder_trigger_index += 1
	
      
    #logic to create adder tree, beyond 1st row
    output_offset = 0
    adders = self.dft.no_inputs/4
    
    for j in range(adder_stages-2):
      for i in range(adders): 
	
	self.dft.complex_adders_output_real.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize*2+adder_stages),max=2**(self.dft.multiplier_bitsize*2+adder_stages))))
	self.dft.complex_adders_output_imag.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize*2+adder_stages),max=2**(self.dft.multiplier_bitsize*2+adder_stages))))

	self.dft.complex_adders.append(self.dft.complex_adder(self.dft.complex_adders_output_real[-1],self.dft.complex_adders_output_imag[-1],self.dft.complex_adders_output_trigger[adder_trigger_index],self.dft.complex_adders_output_real[output_offset],self.dft.complex_adders_output_imag[output_offset],self.dft.complex_adders_output_trigger[output_offset],self.dft.complex_adders_output_real[output_offset+1],self.dft.complex_adders_output_imag[output_offset+1],self.dft.complex_adders_output_trigger[output_offset+1]))
	adder_trigger_index += 1
	output_offset += 2
	 
      adders = adders/2
      
    #last stage of output signals
    self.dft.complex_adders_output_real.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize*2+adder_stages),max=2**(self.dft.multiplier_bitsize*2+adder_stages))))
    self.dft.complex_adders_output_imag.append(Signal(intbv(0,min=-2**(self.dft.multiplier_bitsize*2+adder_stages),max=2**(self.dft.multiplier_bitsize*2+adder_stages))))
	
    self.dft.complex_adders.append(self.dft.complex_adder(self.dft.complex_adders_output_real[-1],self.dft.complex_adders_output_imag[-1],self.dft.complex_adders_output_trigger[adder_trigger_index],self.dft.complex_adders_output_real[output_offset],self.dft.complex_adders_output_imag[output_offset],self.dft.complex_adders_output_trigger[output_offset],self.dft.complex_adders_output_real[output_offset+1],self.dft.complex_adders_output_imag[output_offset+1],self.dft.complex_adders_output_trigger[output_offset+1]))
    
    #various logic instances created  
    tf_unit_insts = self.dft.twiddle_factor_units
    multi_insts = self.dft.multipliers
    complex_multi_loader_insts = self.dft.complex_multiplier_loaders
    complex_multi_adder_insts = self.dft.complex_multiplier_adders
    complex_adder_insts = self.dft.complex_adders
    
    dft_receiving_logic = self.dft.receiving()
    dft_processing_logic = self.dft.processing()
    dft_transmiting_logic = self.dft.transmiting()
    #End of DFT Logic
  
    index_rom_logic = self.unscrambler.rom(self.unscrambler.index_output,self.unscrambler.index_addr,self.unscrambler.index_mapping)
    unscrambler_receiving_logic = self.unscrambler.receiving()
    unscrambler_processing_logic = self.unscrambler.processing()
    unscrambler_transmiting_logic = self.unscrambler.transmiting()
    
    
    return instances()
    
  def twiddle_factors(self,N,stage_length,bits):
    """
    HDFT twiddle_factors method
    used to generate the twiddle factors required for the divide and conquer stages needed in the HDFT algorithm
    """
    segments = 2*numpy.pi/N
    stage = numpy.log(N/stage_length)/numpy.log(2) #Calculating which stage of the divide and conquer operation this is
    
    Wn_real = numpy.cos(segments)
    Wn_imag = -1*numpy.sin(segments)

    tf_real = []
    tf_imag = []
    for i in range(stage_length): #For the length of the stage, each twiddle factor is calculated
      value = (Wn_real+1.0j*Wn_imag)**(i*2**(stage-1))
      if(bits): #scaling the twiddle factors
	value_real = int(value.real*(2**(bits-1)))
	value_imag = int(value.imag*(2**(bits-1)))
	
	if((value_real>=2**(bits-1)) and (value_imag>=2**(bits-1))):
	  tf_real.append(intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1)))
	
	elif(value_real>=2**(bits-1)):
	  tf_real.append(intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag,min=-2**(bits-1),max=2**(bits-1)))
	  
	elif(value_imag>=2**(bits-1)):
	  tf_real.append(intbv(value_real,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1)))
	
	else:
	  tf_real.append(intbv(value_real,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag,min=-2**(bits-1),max=2**(bits-1)))
	  
      else:
	value_real = value.real
	value_imag = value.imag
	
	tf_real.append(value_real)
	tf_imag.append(value_imag)

    return [tuple(tf_real),tuple(tf_imag)] #list of twiddle factors is returned
    
  def twiddle_factors_power(self,size,bits):
    """
    HDFT twiddle_factors_power method
    used to generate the twiddle factors required for the DFT stage in the HDFT algorithm
    """
    segment_size = 2*numpy.pi/size
    base = numpy.cos(segment_size)-1.0j*(numpy.sin(segment_size))
    
    tf_power_real = []
    tf_power_imag = []
    for i in range(size):
      
      for n in range(size):
	value = base**(i*n)
	value_real = value.real
	value_imag = value.imag
	
	if(bits): #scaling the twiddle factors
	  value_real = int(value_real*2**(bits-1))
	  value_imag = int(value_imag*2**(bits-1))
	  
	  if((value_real>=2**(bits-1)) and (value_imag>=2**(bits-1))):
	    value_real = intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1))
	
	  elif(value_real>=2**(bits-1)):
	    value_real = intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag,min=-2**(bits-1),max=2**(bits-1))
	  
	  elif(value_imag>=2**(bits-1)):
	    value_real = intbv(value_real,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1))
	
	  else:
	    value_real = intbv(value_real,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag,min=-2**(bits-1),max=2**(bits-1))
	
	tf_power_real.extend(value_real)
	tf_power_imag.extend(value_imag)
    
    tf_power_real = tuple(tf_power_real)
    tf_power_imag = tuple(tf_power_imag)
    
    return (tf_power_real,tf_power_imag)
    
  def index_map(self,length,dft_size):
    """
    HDFT index_map method
    method for generating the index mapping required in the unscrambler module
    """
    im = range(length)
    
    N_D = length/dft_size #Number of DFTs performed for a particular stage, starting with the final stage
    D_S = dft_size #The size of a DFT performed for a particular stage

    no_stages = int(numpy.ceil(numpy.log(length/dft_size)/numpy.log(2)))
    for k in range(no_stages): #For each stage of decimation
      temp = [0.0]*length
      
      for i in range(N_D/2): #Iterating over the data in this stage of decimation
	start = i*D_S*2 #start and finish values are not rearranged, and so are copied straight across
	finish = i*D_S*2 + D_S*2-1
	
	temp[start] = im[start]
	temp[finish] = im[finish]

	upper = start+1 #starting point for the upper and lower branches of the rearrangement operation are calculated
	lower = start+D_S
      
	index = start+1
	for j in range(D_S-1): #Iterating over the remaining data in this stage of decimation, and assigning values to the correct part of the dataset
	  temp[index] = im[lower] #lower values are first, then the upper value
	  temp[index+1] = im[upper]
      
	  index += 2 #indices are iterated
	  lower += 1
	  upper += 1

      im = temp #copy the unscrambled data to the output array
      
      D_S = D_S*2 #Increase the size of the "DFT" for the next stage of decimation reversal
      N_D = N_D/2 #Half the number of DFTs performed
      
    return_im = im
    return tuple(return_im)
  
  def model(self,input_values_real,input_values_imag):
    """
    HDFT model method
    performs the same operation as the processing method of the HDFT module, but does it upon a Python list
    
    Parameters:
      input_values_real -> input list of the real values
      input_values_imag -> input list of the imaginary values
      
    Output:
      [output real values list, output imaginary values list]
    """
    
    hfd = DFT_Model.HybridFFTDFT("","",self.input_bitsize,self.twiddle_bitsize,self.dft_size,self.multiplier_bitsize,self.output_bitsize) #Uses the DFT_model class to recreate the behaviour of the HDFT algorithm
    
    hfd.num_stages = int(numpy.ceil(numpy.log(len(hfd.input_values_real)/hfd.dft_size)/numpy.log(2)))+1 #Calculating number of stages required
    
    hfd.input_values_real = input_values_real
    hfd.input_values_imag = input_values_imag
    
    hfd.divide_and_conquer()
    hfd.DFT()
    hfd.unscramble()
    
    return [hfd.output_values_real,hfd.output_values_imag]