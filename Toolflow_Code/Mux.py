#Mux class
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *
import Actor,math

class Mux(Actor.Actor):
  name = "Mux"
  
  no_input_lines = 0 #Internal variables
  input_line_no = Signal(intbv(0))
  
  input_line_real_array = [] #lists of input signals
  input_line_imag_array = []
  input_trigger_array = []
  input_enable_array = []
  
  muxes = [] #this list will hold the mux 2 instances that make up the mux
  muxes_signal_real = [] #these lists represent the internal signals that the mux 2 instances use to make up the N part mux
  muxes_signal_imag = []
  muxes_signal_trigger = []
  muxes_signal_enable = []
  
  def __init__(self,input_line_real_array,input_line_imag_array,input_trigger_array,input_enable_array,no_inputs,no_input_lines,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize=0,output_bitsize=0):
    """
    Mux Constructor
    Parameters:
      *Control Signals*
	clk -> clock signal, used to synchronise behaviour across the module
	reset -> asynchronous reset line, used to restart the behaviour of the module
    
      *Data Signals*
	**Input**
	  input_line_real_array -> list of input data lines for the real part of the input signals
	  input_line_imag_array -> list of input data lines for the imaginary part of the input signals
	  input_trigger_array -> list of input signals (1 bit) line used to indicate that data may be read into the actor
	  input_enable_array -> list of what is actually output signal lines used to indicate that the actor is ready to read new data
      
	**Output**
	  output_line_real -> output data line for the real part of the output signal
	  output_line_imag -> output data line for the imaginary part of the output signal
	  output_trigger -> output signal (1 bit) line used to indicate that data is ready to be read from the actor
	  output_enable -> actually an input signal line used to indicate to the module that the following actor is ready to read from it
      
      *Normal Parameters*
	no_inputs -> integer value specifying how many samples need to be read into the actor before it processes that data
	no_outputs -> integer value specifying how many samples will be produced  upon the completion of its processing activity
	input_bitsize -> the size of each of the input data lines
	output_bitsize -> the size of each of the output data line
      
    """
    #Appending the output signal (i.e. the input to the trigger) to mux signal lists
    self.muxes = [] #this list will hold the mux 2 instances that make up the mux
    self.muxes_signal_real = [] #these lists represent the internal signals that the mux 2 instances use to make up the N part mux
    self.muxes_signal_imag = []
    self.muxes_signal_trigger = []
    self.muxes_signal_enable = []
    
    self.muxes_signal_real.append(Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)))) #these lists represent the internal signals that the mux 2 instances use to make up the N part mux
    self.muxes_signal_imag.append(Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1))))
    self.muxes_signal_trigger.append(Signal(bool(0)))
    self.muxes_signal_enable.append(Signal(bool(1)))
    
    #The base class constructor, with the output from the muxes tree set to be the input
    Actor.Actor.__init__(self,self.muxes_signal_real[0],self.muxes_signal_imag[0],self.muxes_signal_trigger[0],self.muxes_signal_enable[0],no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,input_bitsize=input_bitsize,output_bitsize=output_bitsize,reset=reset,clk=clk)
    
    self.no_input_lines = no_input_lines #Internal variables
    self.input_line_no = Signal(intbv(0))
    if(self.no_input_lines): self.input_line_no = Signal(intbv(0,min=0,max=self.no_input_lines+1))
    
    self.input_line_real_array = input_line_real_array #Input lists of signals
    self.input_line_imag_array = input_line_imag_array
    self.input_trigger_array = input_trigger_array
    self.input_enable_array = input_enable_array
    
  def receiving(self):
    """
    Mux receiving behaviour
    primarily works with the actor input and control signals 
    """
    input_trigger = self.input_trigger #global actor signals have to be redeclared locally for this behaviour, for conversion purposes
    processing_input_enable = self.processing_input_enable
    input_count = self.input_count
    no_inputs = self.no_inputs
    reset = self.reset
    no_input_lines = self.no_input_lines
    input_line_no = self.input_line_no
    clk = self.clk
    receiving_flag = self.receiving_flag
    
    baseclass_receiving_logic = Actor.Actor.receiving(self) #calling the Actor base class receiving behaviour
    
    @always(clk.posedge,reset.posedge) #Iteration logic used to point the input to the next mux when the previous data set is complete
    def receiving_logic_2():
      if(reset==1): #reset logic
	input_line_no.next = 0
      
      elif((input_trigger==1) and (processing_input_enable==1)): #Accept input only if the processing input enable and trigger are high
	if((input_line_no<(no_input_lines)) and (input_count>=(no_inputs-1))):
	  input_line_no.next = input_line_no + 1 #point the mux logic to the next set of input lines
	  
    return instances()
    
  def mux2(self,a_real,a_imag,a_trigger,a_enable,b_real,b_imag,b_trigger,b_enable,z_real,z_imag,z_trigger,z_enable,sel,clk):
    """
    Simple 2 port mux used to build the larger mux
    """
    @always_comb
    def mux2_logic(): #Simple 2 input mux used to build N-port muxes (N%2=0)
      if(sel==0):
	z_real.next = a_real
	z_imag.next = a_imag
	z_trigger.next = a_trigger
	a_enable.next = z_enable
	
      else:
	z_real.next = b_real
	z_imag.next = b_imag
	z_trigger.next = b_trigger
	b_enable.next = z_enable
      
    return instances()
    
  def logic(self):
    """
    Mux logic method
    calls all of the behavioural methods and creates a mux tree that connects into the behavioural messages
    """
    #for loop for creating all of the 2 port muxes required
    output_offset = 0 #Variable for tracking where the output lines from the muxes will be in the list
    index_slice = int(math.log(self.no_input_lines)/math.log(2))-1 #Variable for tracking the bit which will be the select for a particular mux
    for i in range(int(math.log(self.no_input_lines)/math.log(2))-1):
      print 2**i
      for j in range(2**i): #Each stage has 2^(stage no) muxes
	for k in range(2): #Each mux has 2 input signals
	  self.muxes_signal_real.append(Signal(intbv(0,min=-2**(self.input_bitsize-1),max=2**(self.input_bitsize-1))))
	  self.muxes_signal_imag.append(Signal(intbv(0,min=-2**(self.input_bitsize-1),max=2**(self.input_bitsize-1))))
	  self.muxes_signal_trigger.append(Signal(bool(0)))
	  self.muxes_signal_enable.append(Signal(bool(0)))
	
	#Mux construction, using two input signals just generated and a signal previous added to the list
	self.muxes.append(self.mux2(self.muxes_signal_real[-2],self.muxes_signal_imag[-2],self.muxes_signal_trigger[-2],self.muxes_signal_enable[-2],self.muxes_signal_real[-1],self.muxes_signal_imag[-1],self.muxes_signal_trigger[-1],self.muxes_signal_enable[-1],self.muxes_signal_real[output_offset+j],self.muxes_signal_imag[output_offset+j],self.muxes_signal_trigger[output_offset+j],self.muxes_signal_enable[output_offset+j],self.input_line_no(index_slice),self.clk))
      
      output_offset += 2**i #offset is basically the sum of the muxes up to the end of the previous stage
      index_slice -= 1 #index slice moves from left to right, as output grows by factor 2
      
    #for loop for connecting lists of input signals to the inputs to the outermost stages of the mux
    index = self.no_input_lines/2
    for i in range(index):
      self.muxes.append(self.mux2(self.input_line_real_array[i*2],self.input_line_imag_array[i*2],self.input_trigger_array[i*2],self.input_enable_array[i*2],self.input_line_real_array[i*2+1],self.input_line_imag_array[i*2+1],self.input_trigger_array[i*2+1],self.input_enable_array[i*2+1],self.muxes_signal_real[output_offset+i],self.muxes_signal_imag[output_offset+i],self.muxes_signal_trigger[output_offset+i],self.muxes_signal_enable[output_offset+i],self.input_line_no(index_slice),self.clk))
    
    muxes_inst = self.muxes #list of the muxes created
    baseclass_logic = Actor.Actor.logic(self) #logic from the baseclass
    
    return instances()
    
  def model(self,input_values_real,input_values_imag): #takes lists of lists as arguments
    """
    Mux model method
    performs the same operation as the processing method of the mux, but does it upon a Python list. In this case it creates one long list of the many sublists supplied to it.
    
    Parameters:
      input_values_real -> input list of the real values
      input_values_imag -> input list of the imaginary values
      
    Output:
      [output real values list, output imaginary values list]
    """
    output_values_real = []
    output_values_imag = []
    
    for i in range(len(input_values_real)):
      output_values = Actor.Actor.model(self,[input_values_real[i]],[input_values_imag[i]])
      output_values_real.append(output_values[0][0])
      output_values_imag.append(output_values[1][0])
    
    return [output_values_real,output_values_imag] #returns lists of lists