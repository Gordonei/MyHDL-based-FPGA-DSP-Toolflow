'''
MyHDL-based FPGA DSP Toolflow
Arc Base Class

Created on 22 Dec 2011
@author: Gordon Inggs
'''
from myhdl import *

#Code from http://stackoverflow.com/questions/147515/least-common-multiple-for-3-or-more-numbers
def gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:      
        a, b = b, a % b
    return a

def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)
#end of code from http://stackoverflow.com/questions/147515/least-common-multiple-for-3-or-more-numbers

class Arc:
    name = "Arc"
    
    #input variables and signals
    no_inputs = 0
    input_index = Signal(intbv(0))
    input_trigger = Signal(bool(0)) #used to indicate that new values have been written
    input_bitwidth = 0
    input_loop_count = Signal(intbv(0,max=255))
    input_stall = Signal(bool(0)) #full
    
    #output variables and signals
    no_outputs = 0
    output_index = Signal(intbv(0))
    output_trigger = Signal(bool(0)) #used to indicate that new values have been read
    output_bitwidth = 0
    output_loop_count = Signal(intbv(0,max=255))
    output_stall = Signal(bool(1)) #starts off empty
    
    #class variables
    size = 0
    complex_valued = False
    buffer_real = []
    buffer_imag = []
    
    reset = Signal(bool(0))

    def __init__(self,reset,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor):
        
        #input parameters
        self.no_inputs = no_inputs
        self.input_bitwidth = input_bitwidth
        
        #output parameters
        self.no_outputs = no_outputs
        self.output_bitwidth = output_bitwidth
        
        #arc parameters
        self.complex_valued = complex_valued
        self.size = lcm(self.no_inputs,self.no_outputs)*size_factor
        
        #Generating the buffer(s)
        self.buffer_real = [Signal(intbv(0,min=-2**(self.output_bitwidth-1),max=2**(self.output_bitwidth-1))) for i in range(self.size)]
        if(complex_valued): self.buffer_imag = [Signal(intbv(0,min=-2**(self.output_bitwidth-1),max=2**(self.output_bitwidth-1))) for i in range(self.size)]
        
        #input signals
        self.input_trigger = Signal(bool(False))
        self.input_stall = Signal(bool(False))
        self.input_index = Signal(intbv(0,min=0,max=self.size))
        self.input_loop_count = Signal(intbv(0,min=0,max=255))
        
        self.reset = reset
        
        #output signals
        self.output_trigger = Signal(bool(False))
        self.output_stall = Signal(bool(True)) #Starts empty
        self.output_index = Signal(intbv(0,min=0,max=self.size))
        self.output_loop_count = Signal(intbv(0,min=0,max=255))
        
        #print id(self.input_trigger)
        
    def receiving(self):
        input_trigger = self.input_trigger
        output_trigger = self.output_trigger
        input_index = self.input_index
        output_index = self.output_index
        input_stall = self.input_stall
        reset = self.reset
        input_loop_count = self.input_loop_count
        output_loop_count = self.output_loop_count
        no_inputs = self.no_inputs
        no_outputs = self.no_outputs
        size = self.size
        output_stall = self.output_stall
        
        input_increment_flag = Signal(bool(0))
        
        @always(input_trigger.posedge,reset.posedge,output_trigger.posedge)
        def receiving_behaviour():
            if(reset):
                input_index.next = 0
                input_stall.next = False
                input_loop_count.next = 0
                
            
            elif(output_trigger and input_stall): #data has been read from the Arc, while in a full state
                if((((output_index+no_outputs)<=(input_index+no_inputs)) and ((input_index+no_inputs)<=size) and (input_loop_count==output_loop_count)) or (((output_index+no_outputs)>=size) and (input_loop_count==(output_loop_count+1)) and (no_outputs<=(input_index+no_inputs)))): input_stall.next = False #undoing the stall if the new read has freed up enough space
        
            elif(input_trigger and not input_stall): #data samples are being written into the Arc and the Arc is accepting values
                if((input_index+no_inputs)<size):# and not(((input_index<output_index) and (input_index+self.no_inputs)>=output_index) and (input_loop_count>=output_loop_count))): #checking to see if the next set of samples is within the length of the storage array
                    
                    if((input_index<output_index) and ((input_index+no_inputs)>output_index) and (input_loop_count>=output_loop_count)): input_stall.next = True
                    else: input_index.next = input_index + no_inputs #increment the input pointer 
                        
                    #elif((input_loop_count==output_loop_count) and (input_index>self.no_inputs) and (output_index>self.no_outputs)): input_loop_count.next = 0 #reseting the loop counter
                    
                else: #and not(((output_index<=self.no_inputs) and ((input_loop_count+1)==output_loop_count)))): #loop around behaviour
                    if((output_index<no_inputs) and ((input_loop_count+1)>=output_loop_count)): input_stall.next = True# or (((input_loop_count+1)>output_loop_count) and (output_index<=input_index))): 
                    else:
                        input_index.next = 0 
                        input_loop_count.next = input_loop_count+1
                    #checking if the FIFO is full, and hence stalling if so
                        
                #else: input_stall.next = 1 #checking if the FIFO is full, and hence stalling if so
            
        #if((((output_index+self.no_outputs)<=(input_index+self.no_inputs))) and (output_loop_count<=input_loop_count) or (input_loop_count>output_loop_count)): output_stall.next = 0 #checking to see if there is now sufficient data in the Arc to be read
        
        return receiving_behaviour#,receiving_stall_behaviour
        
    def transmitting(self):
        input_trigger = self.input_trigger
        output_trigger = self.output_trigger
        input_index = self.input_index
        output_index = self.output_index
        input_stall = self.input_stall
        reset = self.reset
        input_loop_count = self.input_loop_count
        output_loop_count = self.output_loop_count
        output_stall = self.output_stall
        no_inputs = self.no_inputs
        no_outputs = self.no_outputs
        size = self.size
        
        
        @always(output_trigger.posedge,reset.posedge,input_trigger.posedge)
        def transmitting_behaviour():
            if(reset):
                output_index.next = 0
                output_stall.next = True
                output_loop_count.next = 0
                
                
            elif(input_trigger and output_stall): #data has been written into the Arc, while in the empty state (output_index+no_outputs)<size)
                #if((((output_index+self.no_outputs)<=(input_index+self.no_inputs)<self.size) and (output_loop_count==input_loop_count)) or ((input_index+self.no_inputs) and ((input_loop_count+1)==output_loop_count) and (self.no_inputs < input_index + self.no_inputs))): output_stall.next = 0 #checking to see if there is now sufficient data in the Arc to be read
                if((((output_index+no_outputs)<=(input_index+no_inputs)) and ((input_index+no_inputs)<=size) and (input_loop_count==output_loop_count)) or (((input_index+no_inputs)>=size) and ((input_loop_count+1)>=output_loop_count) and ((output_index+no_outputs)<=no_inputs))): output_stall.next = False #undoing the stall if the new read has freed up enough space
                
            elif(output_trigger and not output_stall): #data has been read from the Arc
                if((output_index+no_outputs) < size): #if the read is within the current length of the storage array
                    if((output_index<input_index) and ((output_index+no_outputs)>input_index) and (output_loop_count>=input_loop_count)):
                        #if((input_index<output_index) and ((input_index+no_inputs)>=output_index) and (input_loop_count>=output_loop_count)):
                        output_stall.next = True #checking to see if the array is now empty
                        
                    else:
                        output_index.next = output_index + no_outputs
                    #elif((input_loop_count==output_loop_count) and (input_index>self.no_inputs) and (output_index>self.no_outputs)): output_loop_count.next = 0 #resetting the loop counter
                          
                else:
                    if(((input_index<=no_outputs) and ((output_loop_count+1)>=input_loop_count))): #or ((output_loop_count+1)>input_loop_count)): 
                        output_stall.next = True #checking to see if the array is now empty
                        
                    else:
                        output_index.next = 0 #loop around behaviour
                        output_loop_count.next = output_loop_count + 1
                        
        return transmitting_behaviour#,transmitting_stall_behaviour
    
    def logic(self):
        receive_inst = self.receiving()
        transmit_inst = self.transmitting()
        
        return instances()
        
        
        
        
        