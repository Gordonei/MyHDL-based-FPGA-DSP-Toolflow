#Unscrambler class
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *
import Actor

class Unscrambler(Actor.Actor):
  name = "Unscrambler"
  
  index_mapping = ()
  index_mapping_array = []
  
  index_addr = Signal(intbv(0))
  index_output = Signal(intbv(0))
  
  processing_count = Signal(intbv(0))
  
  def __init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,index_mapping,input_bitsize=0,output_bitsize=0,verbosity=False):
    """
    Unscrambler Constructor
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
	index_mapping -> the list containing the index remapping of the data being passed through the module
      
    """
    Actor.Actor.__init__(self,input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,input_bitsize=input_bitsize,output_bitsize=output_bitsize,clk=clk,reset=reset) #Call to base Actor class
    
    if(self.input_bitsize): 
      self.input_buffer_real = [Signal(intbv(0,min=-2**(self.input_bitsize-1),max=2**(self.input_bitsize-1))) for i in range(no_outputs)]
      self.input_buffer_imag = [Signal(intbv(0,min=-2**(self.input_bitsize-1),max=2**(self.input_bitsize-1))) for i in range(no_outputs)]
    else: 
      self.input_buffer_real = [Signal(intbv(0)) for i in range(no_inputs)]
      self.input_buffer_imag = [Signal(intbv(0)) for i in range(no_inputs)]
    
    self.index_mapping = index_mapping
    self.index_addr = Signal(intbv(0,min=0,max=self.no_outputs+1))
    self.index_output = Signal(intbv(0,min=0,max=self.no_outputs+1))
    
    for i in range(self.no_outputs): self.index_mapping_array.append(Signal(intbv(0,min=0,max=self.no_outputs+1)))
    
    self.processing_count = Signal(intbv(0,min=0,max=no_outputs+1))
    
  def receiving(self):
    """
    Unscrambler receiving method
    primarily works with input data signals
    """
    input_trigger = self.input_trigger #global actor signals have to be redeclared locally for this behaviour, for conversion purposes
    processing_input_enable = self.processing_input_enable
    input_count = self.input_count
    no_inputs = self.no_inputs
    input_buffer_real = self.input_buffer_real
    input_buffer_imag = self.input_buffer_imag
    input_line_real = self.input_line_real
    input_line_imag = self.input_line_imag
    input_enable = self.input_enable
    processing_input_trigger = self.processing_input_trigger
    reset = self.reset
    receiving_flag = self.receiving_flag
    stall_flag = Signal(bool(0))
    clk = self.clk
    no_outputs = self.no_outputs
    
    index_mapping_array = self.index_mapping_array
    index_addr = self.index_addr
    index_output = self.index_output
    processing_count = self.processing_count
    
    @always(clk.posedge,reset.posedge)
    def receiving_logic():
      if(reset==1):
	input_count.next = 0
	input_enable.next = 1
	processing_input_trigger.next = 0
	receiving_flag.next = 0
	stall_flag.next = 0
	index_addr.next = 0
      
      elif(receiving_flag==1):
	if(input_count<(no_inputs)): #Populating the input buffer
	  if(index_addr<(no_outputs-1)):
	    temp_index = input_count+processing_count*no_inputs
	    input_buffer_real[temp_index].next = input_line_real
	    input_buffer_imag[temp_index].next = input_line_imag
	    index_mapping_array[temp_index].next = index_output #populating the index_mapping array with the index remapping array
	    index_addr.next = index_addr+1
	    
	  input_count.next = input_count + 1
	
	else: #When the input buffer is full, copy the last value, trigger the processing and stall the input
	  input_count.next = 0
	  input_enable.next = 0
	  processing_input_trigger.next = 1
	  receiving_flag.next = 0
	  stall_flag.next = 1
	  
      else:
	if(stall_flag==1): #Stall for a clock cycle
	  stall_flag.next = 0
	
	elif((input_trigger==1) and (processing_input_enable==1)):
	  receiving_flag.next = 1
	  input_enable.next = 0
	  processing_input_trigger.next = 0
	  
	elif(processing_input_enable==1):
	  input_enable.next = 1
	  processing_input_trigger.next = 0
	  
    return receiving_logic
    
  def processing(self):
    """
    Unscrambler processing behaviour
    primarily works with internal data signals
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
    index_mapping_array = self.index_mapping_array
    clk = self.clk
    processing_flag = self.processing_flag
    processing_count = self.processing_count
    bit_shift = self.bit_shift
    
    busy = Signal(bool(0))
    stall_flag = Signal(bool(0))
    
    
    @always(clk.posedge,reset.posedge)
    def processing_logic():
      if(reset==1): #asynchronous reset
	processing_output_trigger.next = 0
	processing_input_enable.next = 1
	processing_flag.next = 0
	busy.next  = 1
	stall_flag.next = 0
      
      elif(processing_flag==1):
	if(busy==1):
	  if(processing_count<(int(no_outputs/no_inputs)-1)):
	    busy.next = 0
	    processing_count.next = processing_count + 1
	    
	  else:
	    busy.next = 0
	    processing_count.next = processing_count + 1
	    for i in range(no_outputs):
	      output_buffer_real[i].next = (input_buffer_real[index_mapping_array[i]]>> bit_shift) #copying to the output buffer according to the index remapping
	      output_buffer_imag[i].next = (input_buffer_imag[index_mapping_array[i]]>> bit_shift)
	 
	else:
	  processing_input_enable.next = 1
	  processing_flag.next = 0
	  busy.next = 1
	  stall_flag.next = 1
	  if(processing_count>(int(no_outputs/no_inputs)-1)):
	    processing_output_trigger.next = 1
	
      else:
	if(stall_flag): stall_flag.next = 0 #stall a clock cycle
	
	elif((processing_input_trigger==1) and (processing_output_enable==1)):
	  processing_flag.next = 1
	  busy.next = 1
	  processing_input_enable.next = 0
	  processing_output_trigger.next  = 0
	  
	elif(processing_output_enable==1):
	  processing_output_trigger.next = 0
	  
	elif(processing_input_trigger==1):
	  processing_input_enable.next = 0
    
    return processing_logic
    
  def logic(self):
    """
    Unscrambler logic method
    calls all of the behavioural methods, for conversion purposes, as well as the remapping index memory
    """
    index_rom_inst = self.rom(self.index_output,self.index_addr,self.index_mapping)
    baseclass_logic = Actor.Actor.logic(self)
    
    return instances()
    
  def rom(self,dout, addr, CONTENT):
    """
    Unscrambler rom method
    creates a module for storing data
    """
    @always_comb
    def read():
      dout.next = CONTENT[int(addr)]

    return read
    
  def model(self,input_values_real,input_values_imag):
    """
    Unscrambler model method
    performs the same operation as the processing method of the actor, but does it upon a Python list
    
    Parameters:
      input_values_real -> input list of the real values
      input_values_imag -> input list of the imaginary values
      
    Output:
      [output real values list, output imaginary values list]
    """
    output_values_real = []
    output_values_imag = []
    
    temp_real = []
    temp_imag = []
    
    for iv in input_values_real: temp_real.extend(iv)
    for iv in input_values_imag: temp_imag.extend(iv)
    
    for i in range(self.no_outputs):
      output_values_real.append(temp_real[self.index_mapping[i]])
      output_values_imag.append(temp_imag[self.index_mapping[i]])
    
    return [[output_values_real],[output_values_imag]]
    
    
    