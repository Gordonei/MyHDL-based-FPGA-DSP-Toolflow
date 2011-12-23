#Actor Base class
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *

class Actor:
  name = "Actor"
  
  no_inputs = 0 #Input parameters
  input_count = Signal(intbv(0))
  input_bitsize = 0
  
  input_line_real = Signal(intbv(0)) #Input signals
  input_line_imag = Signal(intbv(0))
  input_trigger = Signal(bool(0))
  input_enable = Signal(bool(1))
  
  input_buffer_real = [] #Input buffers
  input_buffer_imag = []
  
  no_outputs = 0 #Output parameters
  output_count = Signal(intbv(0))
  output_bitsize = 0
  
  bit_shift = 0
  
  output_line_real = Signal(intbv(0)) #Output signals
  output_line_imag = Signal(intbv(0))
  output_trigger = Signal(bool(0))
  output_enable = Signal(bool(0))
  
  output_buffer_real = [] #Output buffers
  output_buffer_imag = []
  
  reset = Signal(bool(0))
  clk = Signal(bool(0))
  
  processing_input_trigger = Signal(bool(0))
  processing_input_enable = Signal(bool(1))
  processing_output_trigger = Signal(bool(0))
  processing_output_enable = Signal(bool(1))
  receiving_flag = Signal(bool(0))
  transmitting_flag = Signal(bool(0))
  processing_flag = Signal(bool(0))
  receive_stall_flag = Signal(bool(0))
  
  verbosity = False
  
  def __init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize=0,output_bitsize=0,verbosity=False):
    """
    Actor Constructor
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
	input_bitsize -> the size of each of the input data lines
	output_bitsize -> the size of each of the output data line
      
    """
    self.no_inputs = no_inputs
    if(self.no_inputs): self.input_count = Signal(intbv(0,min=0,max=self.no_inputs+1))
    self.input_bitsize = input_bitsize
    
    self.input_line_real = input_line_real
    self.input_line_imag = input_line_imag
    self.input_trigger = input_trigger
    self.input_enable = input_enable
    
    if(self.input_bitsize): #creating input buffers
      self.input_buffer_real = [Signal(intbv(0,min=-2**(self.input_bitsize-1),max=2**(self.input_bitsize-1))) for i in range(no_inputs)]
      self.input_buffer_imag = [Signal(intbv(0,min=-2**(self.input_bitsize-1),max=2**(self.input_bitsize-1))) for i in range(no_inputs)]
    else: 
      self.input_buffer_real = [Signal(intbv(0)) for i in range(no_inputs)]
      self.input_buffer_imag = [Signal(intbv(0)) for i in range(no_inputs)]
      
    self.no_outputs = no_outputs
    if(self.no_outputs): self.output_count = Signal(intbv(0,min=0,max=self.no_outputs+1)) #internal count variable
    self.output_bitsize = output_bitsize
    
    self.output_line_real = output_line_real
    self.output_line_imag = output_line_imag
    self.output_trigger = output_trigger
    self.output_enable = output_enable
    
    if(self.output_bitsize): #creating output buffer
      self.output_buffer_real = [Signal(intbv(0,min=-2**(self.output_bitsize-1),max=2**(self.output_bitsize-1))) for i in range(no_outputs)]
      self.output_buffer_imag = [Signal(intbv(0,min=-2**(self.output_bitsize-1),max=2**(self.output_bitsize-1))) for i in range(no_outputs)]
    else: 
      self.output_buffer_real = [Signal(intbv(0)) for i in range(no_outputs)]
      self.output_buffer_imag = [Signal(intbv(0)) for i in range(no_outputs)]
      
    self.reset = reset
    self.clk = clk
      
    self.verbosity = verbosity
    
    self.processing_input_enable = Signal(bool(1)) #creating internal control signals
    self.processing_input_trigger = Signal(bool(0))
    self.processing_output_enable = Signal(bool(1))
    self.processing_output_trigger = Signal(bool(0))
    
    self.receiving_flag = Signal(bool(0))
    self.transmitting_flag = Signal(bool(0))
    self.processing_flag = Signal(bool(0))
    self.receive_stall_flag = Signal(bool(0))
    
    if((self.input_bitsize-self.output_bitsize)>0): #calculating if there is any truncation i.e. input bitsize > output bitsize
      self.bit_shift = (self.input_bitsize-self.output_bitsize)
      
  def receiving(self):
    """
    Actor receiving behaviour
    primarily works with the actor input and control signals 
    """
    input_line_real = self.input_line_real #global actor signals have to be redeclared locally for this behaviour, for conversion purposes
    input_line_imag = self.input_line_imag
    input_trigger = self.input_trigger
    input_enable = self.input_enable
    reset = self.reset
    clk = self.clk
    
    input_count = self.input_count
    no_inputs = self.no_inputs
    input_buffer_real = self.input_buffer_real
    input_buffer_imag = self.input_buffer_imag
    
    processing_input_enable = self.processing_input_enable
    processing_input_trigger = self.processing_input_trigger
    
    receiving_flag = self.receiving_flag
    receive_stall_flag = self.receive_stall_flag
    
    @always(clk.posedge,reset.posedge)
    def receiving_logic():
      if(reset==1): #asynchronous reset
	input_count.next = 0
	input_enable.next = 0
	processing_input_trigger.next = 0
	receiving_flag.next = 0
	receive_stall_flag.next = 0
      
      elif((receiving_flag==1)):
	if(input_count<(no_inputs)): #Populating the input buffer
	  input_buffer_real[int(input_count)].next = input_line_real
	  input_buffer_imag[int(input_count)].next = input_line_imag
	    
	  input_count.next = input_count + 1
	
	else: #When the input buffer is full, copy the last value, trigger the processing and stall the input
	  input_count.next = 0
	  input_enable.next = 0
	  processing_input_trigger.next = 1
	  receiving_flag.next = 0
	  receive_stall_flag.next = 1
	  
      else:
	if((receive_stall_flag==1)): #stall for a clock cycle
	  receive_stall_flag.next = 0
	
	elif((input_trigger==1) and (processing_input_enable==1)): #if there is data waiting to be read and there is no internal processing going on, start the receive behaviour
	  receiving_flag.next = 1
	  input_enable.next = 0 #indicate no new inputs
	  processing_input_trigger.next = 0 #indicate that processing can not occur (while data is being read)
	  
	elif((processing_input_enable==1)): # if there is no data waiting to be read and the internal processing is done, indicate that internal processing may start
	  input_enable.next = 1
	  processing_input_trigger.next = 0
	  
    return receiving_logic
    
  def transmiting(self):
    """
    Actor transmitting behaviour
    primarily works with the actor output and control signals 
    """
    processing_output_trigger = self.processing_output_trigger #global actor signals have to be redeclared locally for this behaviour, for conversion purposes
    output_enable = self.output_enable
    output_count = self.output_count
    no_outputs = self.no_outputs
    output_line_real = self.output_line_real
    output_line_imag = self.output_line_imag
    output_buffer_real = self.output_buffer_real
    output_buffer_imag = self.output_buffer_imag
    processing_output_enable = self.processing_output_enable
    output_trigger = self.output_trigger
    reset = self.reset
    transmitting_flag = self.transmitting_flag
    clk = self.clk
    stall_flag = Signal(bool(0))
    pending_flag = Signal(bool(0))
    
    @always(clk.posedge,reset.posedge)
    def transmiting_logic():
      if(reset==1): #asynchronous reset
	output_count.next = 0
	output_line_real.next = 0
	output_line_imag.next = 0
	processing_output_enable.next = 1
	output_trigger.next = 0
	transmitting_flag.next = 0
	stall_flag.next = 1
	pending_flag.next = 0
	
      elif((transmitting_flag==1)):
	if(output_count<(no_outputs)):
      	  output_line_real.next = output_buffer_real[int(output_count)] #Outputing values
	  output_line_imag.next = output_buffer_imag[int(output_count)]
	  processing_output_enable.next = 0
	  output_count.next = output_count + 1
	  
	else: #When the output buffer has been fully transmitted...
	  output_trigger.next = 0 #indicate that there are no new values available
	  output_count.next = 0
	  transmitting_flag.next = 0
	  processing_output_enable.next = 1 #indicate that processing may run again
	  stall_flag.next = 1
	
      else:
	if(stall_flag==1): stall_flag.next = 0 #stall for a clock cycle
	
	elif((output_enable==1) and (processing_output_trigger==1)): #if output is allowed and processing is complete, start the transmitting behaviour
	  transmitting_flag.next = 1
	  output_trigger.next = 1
	  processing_output_enable.next = 0
	  pending_flag.next = 0
	  
	elif((output_enable==1) and (pending_flag!=1)): #if output is allowed and there is no output data pending, indicate that processing can occur
	  processing_output_enable.next = 1
	  
	elif((processing_output_trigger==1)): #if processing is complete, but output is not allowed, raise the pending flag and stall any future processing
	  pending_flag.next = 1
	  processing_output_enable.next = 0
    
    return transmiting_logic
    
  def processing(self):
    """
    Actor processing behaviour
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
    bit_shift = self.bit_shift
    
    @always(reset.posedge,clk.posedge)
    def processing_logic():
      if(reset==1): #asynchronous reset
	processing_output_trigger.next = 0
	processing_input_enable.next = 1
	processing_flag.next = 0
	busy.next  = 1
	stall_flag.next = 0
      
      elif(processing_flag==1): #Only process if the trigger and enable line are high
	if(busy==1):
	  for i in range(no_inputs): #trivial behaviour - copies values from input buffer to output buffer
	    output_buffer_real[i].next = (int(input_buffer_real[i]) >> bit_shift)
	    output_buffer_imag[i].next = (int(input_buffer_imag[i]) >> bit_shift)
	  busy.next = 0
	
	else: #when complete set all of the control signals correctly
	  processing_output_trigger.next = 1
	  processing_input_enable.next = 1
	  processing_flag.next = 0
	  busy.next = 1
	  stall_flag.next = 1
	
      else:
	if(stall_flag==1): stall_flag.next = 0 #stall for a clock cycle
	
	elif((processing_input_trigger==1) and (processing_output_enable==1)): #if the input trigger is set and the output is allowed, start processing
	  processing_flag.next = 1
	  busy.next = 1
	  processing_input_enable.next = 0
	  processing_output_trigger.next  = 0
	  
	elif(processing_output_enable==1): #if only output is allowed, indicate that there is no new data
	  processing_output_trigger.next = 0
	  
	elif(processing_input_trigger==1): #if the input trigger is set, indicate to stall the input data
	  processing_input_enable.next = 0
    
    return processing_logic
  
  def logic(self):
    """
    Actor logic method
    calls all of the behavioural methods, for conversion purposes
    """
    receive_inst = self.receiving()
    transmit_inst = self.transmiting()
    process_inst = self.processing()
    
    return instances()
    
  def model(self,input_values_real,input_values_imag):
    """
    Actor model method
    performs the same operation as the processing method of the actor, but does it upon a Python list
    
    Parameters:
      input_values_real -> input list of the real values
      input_values_imag -> input list of the imaginary values
      
    Output:
      [output real values list, output imaginary values list]
    """
    output_values_real = []
    output_values_imag = []
    
    for i_v in input_values_real:
      temp = []
      for i in i_v:
	temp.append(i >> self.bit_shift)
	
      output_values_real.append(temp)
	
    for i_v in input_values_imag:
      temp = []
      for i in i_v:
	temp.append(i >> self.bit_shift)
	
      output_values_imag.append(temp)
    
    return [output_values_real,output_values_imag]