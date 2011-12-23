#Divide and Conquer class
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *
import Actor

class DivideAndConquer(Actor.Actor):
  name = "DivideAndConquer"
  
  input_enable_2 = Signal(bool(0))
  
  no_outputs_2 = 0 #2nd Output parameters
  output_count_2 = Signal(intbv(0))
  output_bitsize_2 = 0
  
  output_line_real_2 = Signal(intbv(0)) #2nd Output signals
  output_line_imag_2 = Signal(intbv(0))
  output_trigger_2 = Signal(bool(0))
  output_enable_2 = Signal(bool(0))
  
  output_buffer_real_2 = [] #2nd Output buffers
  output_buffer_imag_2 = []
  
  twiddle_bits = 0
  twiddle_factors_real = []
  twiddle_factors_imag = []
  
  processing_input_enable_2 = Signal(bool(1)) #2nd internal signals
  processing_output_enable_2 = Signal(bool(1)) 
  processing_output_trigger_2 = Signal(bool(0))
  
  twiddle_rom_line_real = Signal(intbv(0))
  twiddle_rom_line_imag = Signal(intbv(0))
  
  tf_real = ()
  tf_imag = ()
  
  transmitting_flag_2 = Signal(bool(0))
  processing_flag_2 = Signal(bool(0))
  
  def __init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,output_line_real_2,output_line_imag_2,output_trigger_2,output_enable_2,no_outputs_2,reset,clk,twiddle_bits=0,tf_real=[],tf_imag=[],input_bitsize=0,output_bitsize=0,output_bitsize_2=0):#,verbosity=False):
    """
    DivideAndConquer Constructor
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
	  
	  output_line_real_2 -> output data line for the real part of the 2nd output signal
	  output_line_imag_2 -> output data line for the imaginary part of the 2nd output signal
	  output_trigger_2 -> output signal (1 bit) line used to indicate that the 2nd set of output data is ready to be read from the actor
	  output_enable_2 -> actually an input signal line used to indicate to the module that the following actor is ready to read from the 2nd set of the output data
      
      *Normal Parameters*
	no_inputs -> integer value specifying how many samples need to be read into the actor before it processes that data
	no_outputs -> integer value specifying how many samples will be produced in the first dataset upon the completion of its processing activity
	no_outputs_2 -> integer value specifying how many samples will be produced in the second dataset upon the completion of its processing activity
	input_bitsize -> the bit size of each of the input data lines
	output_bitsize -> the bit size of each of the output data lines
	output_bitsize_2 -> the bit size of each of the output data lines for the second dataset
	twiddle_bits -> the bit size of the twiddle factors used in the divide and conquer Operation
	tf_real -> a list containing the real parts of the twiddle factors required by the divide and conquer operation
	tf_imag -> a list containing the imaginary parts of the twiddle factors required by the divide and conquer operation
      
    """
    Actor.Actor.__init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,input_bitsize=input_bitsize,output_bitsize=output_bitsize,reset=reset,clk=clk)#,verbosity=verbosity)
    
    self.no_outputs_2 = no_outputs_2
    if(self.no_outputs_2): self.output_count_2 = Signal(intbv(0,min=0,max=self.no_outputs_2+1)) #internal count variable
    self.output_bitsize_2 = output_bitsize_2
    
    self.output_line_real_2 = output_line_real_2
    self.output_line_imag_2 = output_line_imag_2
    self.output_trigger_2 = output_trigger_2
    self.output_enable_2 = output_enable_2
    
    self.output_bitsize_2 = output_bitsize_2
    if(self.output_bitsize_2): 
      self.output_buffer_real_2 = [Signal(intbv(0,min=-2**(self.output_bitsize_2-1),max=2**(self.output_bitsize_2-1))) for i in range(no_outputs_2)]
      self.output_buffer_imag_2 = [Signal(intbv(0,min=-2**(self.output_bitsize_2-1),max=2**(self.output_bitsize_2-1))) for i in range(no_outputs_2)]
    else: 
      self.output_buffer_real_2 = [Signal(intbv(0)) for i in range(no_outputs_2)]
      self.output_buffer_imag_2 = [Signal(intbv(0)) for i in range(no_outputs_2)]
      
    self.twiddle_bits = twiddle_bits
    self.twiddle_factors_real = [Signal(intbv(0)) for i in range(no_outputs_2)]
    self.twiddle_factors_imag = [Signal(intbv(0)) for i in range(no_outputs_2)]
    
    if(self.twiddle_bits):
      self.twiddle_factors_real = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(no_outputs_2)]
      self.twiddle_factors_imag = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(no_outputs_2)]
    
    self.twiddle_rom_line_real = Signal(intbv(0))
    self.twiddle_rom_line_imag = Signal(intbv(0))
    
    if(self.twiddle_bits):
      self.twiddle_rom_line_real = Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1)))
      self.twiddle_rom_line_imag = Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1)))
    
    self.processing_input_enable_2 = Signal(bool(1))
    self.processing_output_enable_2 = Signal(bool(1))
    self.processing_output_trigger_2 = Signal(bool(0))
    self.transmitting_flag_2 = Signal(bool(0))
    
    self.twiddle_rom_addr_real = Signal(intbv(0,min=0,max=self.no_outputs+1))
    self.twiddle_rom_addr_imag = Signal(intbv(0,min=0,max=self.no_outputs+1))
      
    self.tf_real = tuple(map(int,tf_real))
    self.tf_imag = tuple(map(int,tf_imag))
    
    self.transmitting_flag_2 = Signal(bool(0))
    self.processing_flag_2 = Signal(bool(0))
    
  def receiving(self):
    """
    DivideAndConquer receiving behaviour
    primarily works with the actor input and control signals. Note that although this behaviour appears extremely similar to the Actor receiving behaviour, it requires both processing behaviours to be complete, and so the logic is different.
    """
    input_trigger = self.input_trigger #global actor signals have to be redeclared locally for this behaviour, for conversion purposes
    processing_input_enable = self.processing_input_enable
    processing_input_enable_2 = self.processing_input_enable_2
    input_count = self.input_count
    no_inputs = self.no_inputs
    no_outputs = self.no_outputs
    input_buffer_real = self.input_buffer_real
    input_buffer_imag = self.input_buffer_imag
    input_line_real = self.input_line_real
    input_line_imag = self.input_line_imag
    input_enable = self.input_enable
    processing_input_trigger = self.processing_input_trigger
    reset = self.reset
    receiving_flag = self.receiving_flag
    clk = self.clk
    stall_flag = Signal(bool(0))
    
    twiddle_rom_addr_real = self.twiddle_rom_addr_real
    twiddle_rom_addr_imag = self.twiddle_rom_addr_imag
    twiddle_rom_line_real = self.twiddle_rom_line_real
    twiddle_rom_line_imag = self.twiddle_rom_line_imag
    twiddle_factors_real = self.twiddle_factors_real
    twiddle_factors_imag = self.twiddle_factors_imag
    
    @always(clk.posedge,reset.posedge)
    def receiving_logic():
      if(reset==1): #asynchronous reset
	input_count.next = 0
	input_enable.next = 1
	processing_input_trigger.next = 0
	receiving_flag.next = 0
	stall_flag.next = 0
	twiddle_rom_addr_real.next = 0
	twiddle_rom_addr_imag.next = 0
      
      elif(receiving_flag==1):
	if(input_count<(no_inputs)): #Populating the input buffer
	  input_buffer_real[int(input_count)].next = input_line_real
	  input_buffer_imag[int(input_count)].next = input_line_imag
	  
	  if(input_count<(no_outputs)): #Also populate the twiddle factor buffer
	    twiddle_factors_real[input_count].next = twiddle_rom_line_real
	    twiddle_factors_imag[input_count].next = twiddle_rom_line_imag
	    
	    if(input_count<(no_outputs-1)):
	      twiddle_rom_addr_real.next = input_count+1
	      twiddle_rom_addr_imag.next = input_count+1
	      
	    else:
	      twiddle_rom_addr_real.next = 0
	      twiddle_rom_addr_imag.next = 0
	  
	  input_count.next = input_count + 1
	
	else: #When the input buffer is full, copy the last value, trigger the processing and stall the input
	  input_count.next = 0
	  input_enable.next = 0
	  processing_input_trigger.next = 1
	  receiving_flag.next = 0
	  stall_flag.next = 1
	  
      else:
	if(stall_flag): #stall for a clock cycle
	  stall_flag.next = 0
	
	elif((input_trigger==1) and (processing_input_enable==1) and (processing_input_enable_2==1)): #Note the requirement for both processing input enables.
	  receiving_flag.next = 1
	  input_enable.next = 0
	  processing_input_trigger.next = 0
	  
	elif((processing_input_enable==1) and (processing_input_enable_2==1)): # if there is no data waiting to be read and the internal processing is done, indicate that internal processing may start
	  input_enable.next = 1
	  processing_input_trigger.next = 0
	  
    return receiving_logic
    
  def processing(self):
    """
    DivideAndConquer processing behaviour
    primarily works with the input and two outputs buffers and the internal control signals
    """
    processing_input_trigger = self.processing_input_trigger #global actor signals have to be redeclared locally for this behaviour, for conversion purposes
    processing_output_enable = self.processing_output_enable
    processing_output_enable_2 = self.processing_output_enable_2
    output_buffer_real = self.output_buffer_real
    output_buffer_imag = self.output_buffer_imag
    output_buffer_real_2 = self.output_buffer_real_2
    output_buffer_imag_2 = self.output_buffer_imag_2
    input_buffer_real = self.input_buffer_real
    input_buffer_imag = self.input_buffer_imag
    processing_output_trigger = self.processing_output_trigger
    processing_output_trigger_2 = self.processing_output_trigger_2
    input_enable = self.input_enable
    twiddle_factors_real = self.twiddle_factors_real
    twiddle_factors_imag = self.twiddle_factors_imag
    no_inputs = self.no_inputs
    no_outputs = self.no_outputs
    processing_input_enable = self.processing_input_enable
    processing_input_enable_2 = self.processing_input_enable_2
    reset = self.reset
    clk = self.clk
    busy = Signal(bool(0))
    busy_2 = Signal(bool(0))
    stall_flag = Signal(bool(0))
    stall_flag_2 = Signal(bool(0))
    processing_flag = self.processing_flag
    processing_flag_2 = self.processing_flag_2
    twiddle_bits = self.twiddle_bits
    
    @always(reset.posedge,clk.posedge)
    def processing_logic(): #Processing logic for the upper part of the divide and conquer operation, which is a sum operation
      if(reset==1):
	processing_output_trigger.next = 0
	processing_input_enable.next = 1
	processing_flag.next = 0
	busy.next  = 1
	stall_flag.next = 0
      
      elif(processing_flag==1): #Only process if the trigger and enable line are high
	if(busy==1):
	  for i in range(no_outputs): #The upper part of the divide and conquer is the sum operation
	    output_buffer_real[i].next = ((input_buffer_real[i]+input_buffer_real[i+no_outputs]) << (twiddle_bits-1)) 
	    output_buffer_imag[i].next = ((input_buffer_imag[i]+input_buffer_imag[i+no_outputs]) << (twiddle_bits-1))
	  busy.next = 0
	
	else:
	  processing_output_trigger.next = 1
	  processing_input_enable.next = 1
	  processing_flag.next = 0
	  busy.next = 1
	  stall_flag.next = 1
	
      else:
	if(stall_flag==1): stall_flag.next = 0
	
	elif((processing_input_trigger==1) and (processing_output_enable==1)):
	  processing_flag.next = 1
	  busy.next = 1
	  processing_input_enable.next = 0
	  processing_output_trigger.next  = 0
	  
	elif(processing_output_enable==1):
	  processing_output_trigger.next = 0
	  
	elif(processing_input_trigger==1):
	  processing_input_enable.next = 0
    
    @always(reset.posedge,clk.posedge)
    def processing_logic_2(): #Processing logic for the lower part of the divide and conquer operation, which is a difference and then multiply operation
      if(reset):
	processing_output_trigger_2.next = 0
	processing_input_enable_2.next = 1
	processing_flag_2.next = 0
	busy_2.next  = 1
	stall_flag_2.next = 0
      
      elif(processing_flag_2==1): #Only process if the trigger and enable line are high
	if(busy_2):
	  for i in range(no_outputs): #difference and multiply by the twiddle factor operation.
	    temp_real = (input_buffer_real[i]-input_buffer_real[i+no_outputs])
	    temp_imag = (input_buffer_imag[i]-input_buffer_imag[i+no_outputs])
	    output_buffer_real_2[i].next = (temp_real*twiddle_factors_real[i]-temp_imag*twiddle_factors_imag[i])
	    output_buffer_imag_2[i].next = (temp_imag*twiddle_factors_real[i]+temp_real*twiddle_factors_imag[i])
	  
	  busy_2.next = 0
	
	else:
	  processing_output_trigger_2.next = 1
	  processing_input_enable_2.next = 1
	  processing_flag_2.next = 0
	  busy_2.next = 1
	  stall_flag_2.next = 1
	
      else:
	if(stall_flag_2): stall_flag_2.next = 0
	
	elif((processing_input_trigger==1) and (processing_output_enable_2==1)):
	  processing_flag_2.next = 1
	  busy_2.next = 1
	  processing_input_enable_2.next = 0
	  processing_output_trigger_2.next  = 0
	  
	elif(processing_output_enable_2==1):
	  processing_output_trigger_2.next = 0
	  
	elif(processing_input_trigger==1):
	  processing_input_enable_2.next = 0
    
    return instances()
  
  def transmiting(self):
    """
    DivideAndConquer transmitting behaviour
    primarily works with the actor output and control signals. It calls the base Actor class transmitting method, and adds additional transmitting behaviour for the second output buffer.
    """
    baseclass_transmiting_inst = Actor.Actor.transmiting(self) #call the base class method transmitting method for the top output set
    
    output_enable = self.output_enable
    
    output_line_real_2 = self.output_line_real_2
    output_line_imag_2 = self.output_line_imag_2
    processing_output_trigger_2 = self.processing_output_trigger_2
    output_enable_2 = self.output_enable_2
    
    output_count_2 = self.output_count_2
    no_outputs_2 = self.no_outputs_2
    
    output_buffer_real_2 = self.output_buffer_real_2
    output_buffer_imag_2 = self.output_buffer_imag_2
    processing_output_enable_2 = self.processing_output_enable_2
    output_trigger_2 = self.output_trigger_2
    reset = self.reset
    transmitting_flag_2 = self.transmitting_flag_2
    clk = self.clk
    stall_flag_2 = Signal(bool(0))
    pending_flag_2 = Signal(bool(0))
    
    @always(clk.posedge,reset.posedge)
    def transmiting_logic_2():
      if(reset==1): #asynchronous reset
	output_count_2.next = 0
	output_line_real_2.next = 0
	output_line_imag_2.next = 0
	processing_output_enable_2.next = 1
	output_trigger_2.next = 0
	transmitting_flag_2.next = 0
	stall_flag_2.next = 1
	pending_flag_2.next = 1
	
      elif(transmitting_flag_2==1):
	if(output_count_2<(no_outputs_2)):
	  output_line_real_2.next = output_buffer_real_2[int(output_count_2)] #Outputing values
	  output_line_imag_2.next = output_buffer_imag_2[int(output_count_2)]
	  processing_output_enable_2.next = 0
	  output_count_2.next = output_count_2 + 1
	  
	  #transmitting_flag.next = 0
	  
	else: #When the output buffer has been fully transmitted...
	  output_trigger_2.next = 0 #indicate that there are no new values available
	  output_count_2.next = 0
	  transmitting_flag_2.next = 0
	  processing_output_enable_2.next = 1 #indicate that processing may run again
	  stall_flag_2.next = 1
	
      else:
	if(stall_flag_2==1): stall_flag_2.next = 0 #stall for a clock cycle
	
	elif((output_enable_2==1) and (processing_output_trigger_2==1)): #if output is allowed and processing is complete, start the transmitting behaviour
	  transmitting_flag_2.next = 1
	  output_trigger_2.next = 1
	  processing_output_enable_2.next = 0
	  pending_flag_2.next = 0
	  
	elif((output_enable_2==1) and (pending_flag_2 != 1)): #if output is allowed and there is no output data pending, indicate that processing can occur
	  processing_output_enable_2.next = 1
	  
	elif(processing_output_trigger_2==1): #if processing is complete, but output is not allowed, raise the pending flag and stall any future processing
	  pending_flag_2.next = 1
	  processing_output_enable_2.next = 0
    
    return instances()
    
  def rom(self,dout, addr, CONTENT):
    """
    DivideAndConquer rom behaviour
    this independent module is used to provide the ROM for the twiddle factors that are required
    """
    @always_comb
    def read():
      dout.next = CONTENT[int(addr)]

    return read
    
  def logic(self):
    """
    DivideAndConquer logic method
    calls all of the behavioural methods, for conversion purposes
    """
    baseclass_logic = Actor.Actor.logic(self) #Calls the behavioural methods by calling the Base Class Actor logic method
      
    twiddle_rom_real_inst = self.rom(self.twiddle_rom_line_real,self.twiddle_rom_addr_real,self.tf_real) #Creates a rom for the real and imaginary parts of the twiddle factors
    twiddle_rom_imag_inst = self.rom(self.twiddle_rom_line_imag,self.twiddle_rom_addr_imag,self.tf_imag)
    
    return instances()
    
  def model(self,input_values_real,input_values_imag):
    """
    DivideAndConquer model method
    performs the same operation as the processing method of the actor, but does it upon a Python list
    
    Parameters:
      input_values_real -> input list of the real values
      input_values_imag -> input list of the imaginary values
      
    Output:
      [output real values list, output imaginary values list,output real values list for second dataset, output imaginary values list for second dataset]
    """
    output_values_real = []
    output_values_imag = []
    output_values_real_2 = []
    output_values_imag_2 = []
    
    for i_v in range(len(input_values_real)):
      output_values_imag.append([])
      output_values_imag_2.append([])
      output_values_real.append([])
      output_values_real_2.append([])
      for i in range(len(input_values_real[i_v])/2):
	output_values_real[-1].append((input_values_real[i_v][i]+input_values_real[i_v][len(input_values_real[i_v])/2+i]) << (self.twiddle_bits-1))
	output_values_imag[-1].append((input_values_imag[i_v][i]+input_values_imag[i_v][len(input_values_imag[i_v])/2+i]) << (self.twiddle_bits-1))
	
	temp_real = (input_values_real[i_v][i]-input_values_real[i_v][len(input_values_real[i_v])/2+i])
	temp_imag = (input_values_imag[i_v][i]-input_values_imag[i_v][len(input_values_imag[i_v])/2+i])
	
	output_values_real_2[-1].append(temp_real*self.tf_real[i]-temp_imag*self.tf_imag[i])
	output_values_imag_2[-1].append(temp_real*self.tf_imag[i]+temp_imag*self.tf_real[i])
	
    return [output_values_real,output_values_imag,output_values_real_2,output_values_imag_2]
      