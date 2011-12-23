#DFT class
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *
import Actor,math,numpy

class DFT(Actor.Actor):
  name = "DFT"
  
  multiplier_bitsize = 0 #parameters
  twiddle_factor_bitsize = 0
  
  iteration_count = Signal(intbv(0))
  iteration_start = Signal(bool(0))
  iteration_finished = Signal(bool(0))
  processing_iteration = Signal(bool(0))#,delay=1)
  clear_output = Signal(bool(0))
  pull_up = Signal(bool(1))
  #processing_iteration_done = Signal(bool(0))
  
  twiddle_factor_units = [] #twiddle roms used to store twiddle values
  twiddle_factor_units_output_real = [] #output signals from twiddle roms
  twiddle_factor_units_output_imag = []
  
  multipliers = [] #normal multiplers used in the complex multiplication task
  multiplier_signals = [] #signals used to communicate within the complex multipliers
  
  complex_multiplier_loaders = [] #units that do the pre-multiplication addition for the complex multiplication operation
  complex_multiplier_adders = [] #units that do the post-multiplcation addition for the complex multiplication operation
  multipliers_output_real = [] #output signals from the complex multipliers
  multipliers_output_imag = []
  
  complex_adders = [] #complex adder units used to sum outputs input value multiplication with twiddle factors
  complex_adders_output_real = [] #output signals from the adders
  complex_adders_output_imag = []
  complex_adders_output_trigger = [] #output triggers for adder units, used to trigger the next adder in the set, and reset the previous set
  
  tf_real= (()) #list of tuples of twiddle factor values
  tf_imag = (())  
  
  def __init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,tf_real,tf_imag,input_bitsize=0,output_bitsize=0,multiplier_bitsize=0,twiddle_factor_bitsize=0,verbosity=False):
    """
    DFT Constructor
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
	multiplier_bitsize -> the bit size of the result of the DFT operation
	twiddle_factor_bitsize -> the bit size of the twiddle factors used in the DFT
	tf_real -> list containing real parts of the twiddle factors used in the DFT
	tf_imag -> list containing imaginary parts of the twiddle factors used in the DFT
      
    """
    Actor.Actor.__init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize) #Call to base class constructor
    
    self.multiplier_bitsize = multiplier_bitsize
    self.twiddle_factor_bitsize = twiddle_factor_bitsize
  
    if(self.no_inputs):
      self.iteration_count = Signal(intbv(0,min=0,max=self.no_inputs+1))
      self.processing_count = Signal(intbv(0,min=0,max=self.no_inputs+1))
    
    self.tf_real = tf_real
    self.tf_imag = tf_imag
    
    
  def processing(self): #overiding processing logic
    """
    DFT processing behaviour
    primarily works with the two buffers and the internal signals
    """
    processing_input_trigger = self.processing_input_trigger #global actor signals have to be redeclared locally for this behaviour, for conversion purposes
    processing_output_enable = self.processing_output_enable
    output_buffer_real = self.output_buffer_real
    output_buffer_imag = self.output_buffer_imag
    input_buffer_real = self.input_buffer_real
    input_buffer_imag = self.input_buffer_imag
    processing_output_trigger = self.processing_output_trigger
    input_enable = self.input_enable
    processing_input_enable = self.processing_input_enable
    no_inputs = self.no_inputs
    no_outputs = self.no_outputs
    reset = self.reset
    clk = self.clk
    processing_flag = self.processing_flag
    busy = Signal(bool(0))
    stall_flag = Signal(bool(0))
    
    iteration_count = self.iteration_count
    processing_iteration = self.processing_iteration
    iteration_finished = self.iteration_finished
    iteration_start = self.iteration_start
    loop_count = Signal(intbv(0,min=0,max=self.no_inputs+1))
    processing_flag = Signal(bool(0))
    pull_up = self.pull_up
    
    complex_adders_output_trigger = self.complex_adders_output_trigger
    complex_adders_output_real = self.complex_adders_output_real
    complex_adders_output_imag = self.complex_adders_output_imag
	
    @always(clk.posedge,reset.posedge)
    def processing_logic():
      if(reset): #asynchronous reset
	processing_output_trigger.next = 0
	processing_input_enable.next = 1
	processing_flag.next = 0
	busy.next  = 1
	stall_flag.next = 0
	pull_up.next = 1

      elif(processing_flag):
	if(busy and (loop_count<2)):
	  loop_count.next = loop_count + 1
	  processing_iteration.next = not(processing_iteration) #trigger the adders

	elif(busy):
	  loop_count.next = 0
	  output_buffer_real[iteration_count].next = complex_adders_output_real[-1] #copy the output from the last iteration into the output buffer
	  output_buffer_imag[iteration_count].next = complex_adders_output_imag[-1]
	  
	  if(iteration_count<(no_inputs-1)):
	    iteration_count.next = iteration_count + 1 #increment the iterator
	    
	  else:
	    busy.next = 0
	  
	else:
	  iteration_count.next = 0
	  
	  processing_output_trigger.next = 1 #indicate that processing is done
	  processing_input_enable.next = 1
	  processing_flag.next = 0
	  busy.next = 1
	  loop_count.next = 0
	  stall_flag.next = 1
	
      
      else:
	if(stall_flag): stall_flag.next = 0 #stall for one clock cycle
	
	elif((processing_output_enable) and processing_input_trigger): #Only process if the trigger and enable line are high
	  processing_flag.next = 1
	  pull_up.next = 1
	  busy.next = 1
	  processing_input_enable.next = 0
	  processing_output_trigger.next  = 0
	  
	elif(processing_output_enable):
	  processing_output_trigger.next = 0
    
    return instances()
    
  def rom(self,dout, addr, CONTENT):
    """
    DFT rom method
    used to create memory used to store Twiddle Factors
    """
    @always_comb
    def read():
      dout.next = CONTENT[int(addr)]

    return read
    
  def multi(self,output,input_a,input_b,clk,reset,name,pull_up):
    """
    DFT multiplier method
    used to a multiplier
    """
    
    @always(clk.posedge)
    def multi_logic():
      output.next = input_a*input_b
      
    #Old depreciated method of overiding conversion
    __verilog__ =\
    """
    MULT18X18SIO #( .AREG(1), .BREG(1), .PREG(1), .B_INPUT(\"DIRECT\") ) %(name)s (.A(%(input_a)s),.B(%(input_b)s),.BCIN(),.CEA(%(pull_up)s),.CEB(%(pull_up)s),.CEP(%(pull_up)s),.CLK(%(clk)s),.RSTA(%(reset)s),.RSTB(%(reset)s),.RSTP(%(reset)s),.BCOUT(),.P(%(output)s));
    """
    
    return multi_logic
  
  #overiding verilog conversion varible so as to use hardware multiplier
  multi.verilog_code =\
  """
  MULT18X18SIO #( .AREG(1), .BREG(1), .PREG(1), .B_INPUT(\"DIRECT\") ) $name (.A($input_a),.B($input_b),.BCIN(),.CEA($self.pull_up),.CEB($self.pull_up),.CEP($self.pull_up),.CLK($clk),.RSTA($reset),.RSTB($reset),.RSTP($resett),.BCOUT(),.P($output));
  """
  #MULT18X18SIO #( .AREG(1), .BREG(1), .PREG(1), .B_INPUT("DIRECT") ) XLXI_37 (.A(XLXN_142[17:0]),.B(XLXN_141[17:0]),.BCIN(),.CEA(XLXN_148),.CEB(XLXN_148),.CEP(XLXN_148),.CLK(XLXN_140),.RSTA(reset),.RSTB(reset),.RSTP(reset),.BCOUT(),.P(XLXN_128[35:0]));
  
    
  def complex_multiplier_loader(self,input_a_real,input_a_imag,input_b_real,input_b_imag,multiplier_1_input_a_signal,multiplier_1_input_b_signal,multiplier_2_input_a_signal,multiplier_2_input_b_signal,multiplier_3_input_a_signal,multiplier_3_input_b_signal):
    """
    DFT complex_multiplier_loader
    module used to perform the preliminary addition before the multiplication operations required in complex multiplications
    """
    @always_comb
    def complex_multiplier_loader_logic():
      # (a+bj)*(c+dj)
      multiplier_1_input_a_signal.next = input_a_real #a
      multiplier_1_input_b_signal.next = input_b_real+input_b_imag #(c+d)
      
      multiplier_2_input_a_signal.next = (input_a_real+input_a_imag) #(a+b)
      multiplier_2_input_b_signal.next = input_b_imag# (d)
      
      multiplier_3_input_a_signal.next = (input_a_real-input_a_imag) #(a-b)
      multiplier_3_input_b_signal.next = input_b_real #(c)
      
    return complex_multiplier_loader_logic
      
    
  def complex_multiplier_adder(self,output_real,output_imag,multiplier_1_output,multiplier_2_output,multiplier_3_output):
    """
    DFT complex_multiplier_adder
    module used to perform the post-multiplication subtractions required in complex multiplications
    """
    @always_comb
    def complex_multiplier_adder_logic():
      
      output_real.next = multiplier_1_output - multiplier_2_output # (c+d)a - (a+b)d = ac-bd
      output_imag.next = multiplier_1_output - multiplier_3_output # (c+d)a - (a-b)c = (ad+bc)j
      
    return complex_multiplier_adder_logic
       
  def complex_adder(self,output_a_real,output_a_imag,output_a_trigger,input_a_real,input_a_imag,input_a_trigger,input_b_real,input_b_imag,input_b_trigger):
    """
    DFT complex_adder
    module used to perform complex additions, used in the adder tree after the multiplication stage of the DFT
    """
    @always(input_a_trigger,input_b_trigger)
    def complex_adder_adding_logic():
      output_a_real.next = input_a_real + input_b_real
      output_a_imag.next = input_a_imag + input_b_imag
      output_a_trigger.next = not(output_a_trigger)
      
    return complex_adder_adding_logic#,complex_adder_reset_logic
    
  def logic(self,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset):
    """
    DFT logic method
    calls all of the behavioural methods, for conversion purposes as well as all of the supporting modules used to perform those methods
    """
    self.twiddle_factor_units = [] #twiddle roms used to store twiddle values
    self.twiddle_factor_units_output_real = [] #output signals from twiddle roms
    self.twiddle_factor_units_output_imag = []
  
    self.multipliers = [] #normal multiplers used in the complex multiplication task
    self.multiplier_signals = [] #signals used to communicate within the complex multipliers
    
    self.complex_multiplier_loaders = [] #units that do the pre-multiplication addition for the complex multiplication operation
    self.complex_multiplier_adders = [] #units that do the post-multiplcation addition for the complex multiplication operation
    self.multipliers_output_real = [] #output signals from the complex multipliers
    self.multipliers_output_imag = []
  
    self.complex_adders = [] #complex adder units used to sum outputs input value multiplication with twiddle factors
    self.complex_adders_output_real = [] #output signals from the adders
    self.complex_adders_output_imag = []
    self.complex_adders_output_trigger = [] #output triggers for adder units, used to trigger the next adder in the set, and reset the previous set
    
    adder_stages = int(math.log(self.no_inputs)/math.log(2)) #calculating the required size of the adder tree
    #creating output triggers for the adders in the tree
    for i in range(int(self.no_inputs)-1): self.complex_adders_output_trigger.append(Signal(bool(0)))#,delay=1))
    
    #logic to create complex multiplications and twiddle factor units, and wire them up
    self.twiddle_factor_units_output_real.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize-1),max=2**(self.multiplier_bitsize-1))))
    
    adder_trigger_index = 0
    for i in range(self.no_inputs):
      self.twiddle_factor_units_output_real.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize-1),max=2**(self.multiplier_bitsize-1))))
      self.twiddle_factor_units.append(self.rom(self.twiddle_factor_units_output_real[-1],self.iteration_count,tuple(map(int,self.tf_real[i*self.no_inputs:i*self.no_inputs+self.no_inputs]))))
      
      self.twiddle_factor_units_output_imag.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize-1),max=2**(self.multiplier_bitsize-1))))
      self.twiddle_factor_units.append(self.rom(self.twiddle_factor_units_output_imag[-1],self.iteration_count,tuple(map(int,self.tf_imag[i*self.no_inputs:i*self.no_inputs+self.no_inputs]))))
      
      for j in range(3): #three multipliers needed per complex multiplication
	self.multiplier_signals.append(Signal(intbv(0,min=-2**(2*self.multiplier_bitsize-1),max=2**(2*self.multiplier_bitsize-1))))
	for k in range(2): #three signals needed per multipler -> output, input_a, input_b
	  self.multiplier_signals.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize-1),max=2**(self.multiplier_bitsize-1))))
	
	multi_name = "multi_%d_%d_%d" % (i,j,k)
	self.multipliers.append(self.multi(self.multiplier_signals[-3],self.multiplier_signals[-2],self.multiplier_signals[-1],self.clk,self.reset,multi_name,self.pull_up))
	
      self.complex_multiplier_loaders.append(self.complex_multiplier_loader(self.input_buffer_real[i],self.input_buffer_imag[i],self.twiddle_factor_units_output_real[-1],self.twiddle_factor_units_output_imag[-1],self.multiplier_signals[-8],self.multiplier_signals[-7],self.multiplier_signals[-5],self.multiplier_signals[-4],self.multiplier_signals[-2],self.multiplier_signals[-1]))
      
      self.multipliers_output_real.append(Signal(intbv(0,min=-2**(2*self.multiplier_bitsize-1),max=2**(2*self.multiplier_bitsize-1))))
      self.multipliers_output_imag.append(Signal(intbv(0,min=-2**(2*self.multiplier_bitsize-1),max=2**(2*self.multiplier_bitsize-1))))
      self.complex_multiplier_adders.append(self.complex_multiplier_adder(self.multipliers_output_real[-1],self.multipliers_output_imag[-1],self.multiplier_signals[-9],self.multiplier_signals[-6],self.multiplier_signals[-3]))
      
      #creating the first row of the adder tree, i.e. the stage straight after the complex multiplication
      if(i%2): #every 2nd value
	self.complex_adders_output_real.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize*2+adder_stages),max=2**(self.multiplier_bitsize*2+adder_stages))))
	self.complex_adders_output_imag.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize*2+adder_stages),max=2**(self.multiplier_bitsize*2+adder_stages))))
    
	self.complex_adders.append(self.complex_adder(self.complex_adders_output_real[-1],self.complex_adders_output_imag[-1],self.complex_adders_output_trigger[adder_trigger_index],self.multipliers_output_real[-2],self.multipliers_output_imag[-2],self.processing_iteration,self.multipliers_output_real[-1],self.multipliers_output_imag[-1],self.processing_iteration))
	adder_trigger_index += 1
	
      
    #logic to create adder tree, beyond 1st row
    output_offset = 0
    adders = self.no_inputs/4
    
    for j in range(adder_stages-2):
      for i in range(adders): 
	
	self.complex_adders_output_real.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize*2+adder_stages),max=2**(self.multiplier_bitsize*2+adder_stages))))
	self.complex_adders_output_imag.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize*2+adder_stages),max=2**(self.multiplier_bitsize*2+adder_stages))))

	self.complex_adders.append(self.complex_adder(self.complex_adders_output_real[-1],self.complex_adders_output_imag[-1],self.complex_adders_output_trigger[adder_trigger_index],self.complex_adders_output_real[output_offset],self.complex_adders_output_imag[output_offset],self.complex_adders_output_trigger[output_offset],self.complex_adders_output_real[output_offset+1],self.complex_adders_output_imag[output_offset+1],self.complex_adders_output_trigger[output_offset+1]))
	adder_trigger_index += 1
	output_offset += 2
	 
      adders = adders/2
      
    #last stage of output signals
    self.complex_adders_output_real.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize*2+adder_stages),max=2**(self.multiplier_bitsize*2+adder_stages))))
    self.complex_adders_output_imag.append(Signal(intbv(0,min=-2**(self.multiplier_bitsize*2+adder_stages),max=2**(self.multiplier_bitsize*2+adder_stages))))
	
    self.complex_adders.append(self.complex_adder(self.complex_adders_output_real[-1],self.complex_adders_output_imag[-1],self.complex_adders_output_trigger[adder_trigger_index],self.complex_adders_output_real[output_offset],self.complex_adders_output_imag[output_offset],self.complex_adders_output_trigger[output_offset],self.complex_adders_output_real[output_offset+1],self.complex_adders_output_imag[output_offset+1],self.complex_adders_output_trigger[output_offset+1]))
    
    #various logic instances created  
    tf_unit_insts = self.twiddle_factor_units
    multi_insts = self.multipliers
    complex_multi_loader_insts = self.complex_multiplier_loaders
    complex_multi_adder_insts = self.complex_multiplier_adders
    complex_adder_insts = self.complex_adders
    
    #processing_logic = self.processing()
    baseclass_logic = Actor.Actor.logic(self)
    
    return instances()
    
  def model(self,input_values_real,input_values_imag):
    """
    DFT model method
    performs the same operation as the processing method of the actor, but does it upon a Python list
    
    Parameters:
      input_values_real -> input list of the real values
      input_values_imag -> input list of the imaginary values
      
    Output:
      [output real values list, output imaginary values list]
    """
    output_values_real = []
    output_values_imag = []
    
    for k in range(len(input_values_real)):
      output_values_real.append([])
      output_values_imag.append([])
      for i in range(len(input_values_real[k])):
	temp_real = 0
	temp_imag = 0
	for j in range(self.no_inputs):
	  temp_real += (input_values_real[k][j]*self.tf_real[i*self.no_inputs+j] - input_values_imag[k][j]*self.tf_imag[i*self.no_inputs+j])
	  temp_imag += (input_values_real[k][j]*self.tf_imag[i*self.no_inputs+j] + input_values_imag[k][j]*self.tf_real[i*self.no_inputs+j])
	  
	output_values_real[-1].append(temp_real)
	output_values_imag[-1].append(temp_imag)
      
    return [output_values_real,output_values_imag]
    
  
  