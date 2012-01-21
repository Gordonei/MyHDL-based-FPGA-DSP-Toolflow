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
    input_strides = 0
    input_trigger = Signal(bool(0)) #used to indicate that new values have been written
    input_bitwidth = 0
    input_loop_count = Signal(intbv(0,max=255))
    input_stall = Signal(bool(0)) #full
    
    #output variables and signals
    no_outputs = 0
    output_index = Signal(intbv(0))
    output_strides = 0
    output_trigger = Signal(bool(0)) #used to indicate that new values have been read
    output_bitwidth = 0
    output_loop_count = Signal(intbv(0,max=256))
    output_stall = Signal(bool(1)) #starts off empty
    
    #class variables
    size = 0
    complex_valued = False
    buffer_real = []
    buffer_imag = []
    
    reset = Signal(bool(0))

    def __init__(self,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor):
        
        #input parameters
        self.no_inputs = no_inputs
        self.input_bitwidth = input_bitwidth
        
        #input signals
        #self.input_trigger = input_trigger
        #self.input_stall = input_stall
        
        #output parameters
        self.no_outputs = no_outputs
        self.output_bitwidth = output_bitwidth
        
        #output signals
        #self.output_trigger = output_trigger
        #self.output_stall = output_stall
        
        #arc parameters
        self.complex_valued = complex_valued
        self.size = lcm(self.no_inputs,self.no_outputs)*size_factor
        self.buffer_real = [Signal(intbv(0,min=-2**(self.output_bitwidth-1),max=2**(self.output_bitwidth-1))) for i in range(self.size)]
        if(complex_valued): self.buffer_imag = [Signal(intbv(0,min=-2**(self.output_bitwidth-1),max=2**(self.output_bitwidth-1))) for i in range(self.size)]
        
        self.input_index = Signal(intbv(0,min=-2**(self.size-1),max=2**(self.size-1)))
        
        self.output_index = Signal(intbv(0,min=-2**(self.size-1),max=2**(self.size-1)))
        
    def receiving(self):
        input_trigger = self.input_trigger
        output_trigger = self.output_trigger
        input_index = self.input_index
        output_index = self.output_index
        input_stall = self.input_stall
        reset = self.reset
        input_loop_count = self.input_loop_count
        output_loop_count = self.output_loop_count
        
        @always(input_trigger.posedge,reset.posedge)
        def receiving_behaviour():
            if(reset):
                input_index.next = 0
                input_stall.next = 0
                input_loop_count.next = 0
                
            elif(input_trigger): #data samples have been written into the Arc
                if((input_index+self.no_inputs)<self.size): #checking to see if the next set of samples is within the length of the storage array
                    input_index.next = input_index+self.no_inputs #increment the counter
                    
                    if(((input_index+self.no_inputs)>=output_index) and (input_loop_count>output_loop_count)): 
                        input_stall.next = 1 #checking if the FIFO is full, and hence stalling if so
                    #elif((input_loop_count==output_loop_count) and (input_index>self.no_inputs) and (output_index>self.no_outputs)): input_loop_count.next = 0 #reseting the loop counter
                    
                else: #loop around behaviour
                    input_index.next = 0 
                    input_loop_count.next = input_loop_count+1
                    
                    if((output_index<=self.no_inputs) and ((input_loop_count+1)>=output_loop_count)): 
                        input_stall.next = 1 #checking if the FIFO is full, and hence stalling if so
                    
        @always(output_trigger.posedge)
        def receiving_stall_behaviour():
            if(output_trigger and input_stall): #data has been read from the Arc, while in a full state
                if((((output_index+self.no_outputs)<=(input_index+self.no_inputs)<self.size) and (input_loop_count==output_loop_count)) or ((output_index+self.no_outputs>=self.size) and (input_loop_count==(output_loop_count+1)) and (self.no_outputs<=(input_index+self.no_inputs)))): input_stall.next = 0 #undoing the stall if the new read has freed up enough space
        #if((((output_index+self.no_outputs)<=(input_index+self.no_inputs))) and (output_loop_count<=input_loop_count) or (input_loop_count>output_loop_count)): output_stall.next = 0 #checking to see if there is now sufficient data in the Arc to be read

        return receiving_behaviour,receiving_stall_behaviour
        
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
        
        @always(output_trigger.posedge,reset.posedge)
        def transmitting_behaviour():
            if(reset):
                output_index.next = 0
                output_stall.next = 0
                output_loop_count.next = 0
                
            elif(output_trigger): #data has been read from the Arc
                if((output_index+self.no_outputs)<self.size): #if the read is within the current length of the storage array
                    output_index.next = output_index+self.no_outputs
                    
                    if(((output_index+self.no_outputs)>=input_index) and (output_loop_count==input_loop_count)): 
                        output_stall.next = 1 #checking to see if the array is now empty
                        
                    #elif((input_loop_count==output_loop_count) and (input_index>self.no_inputs) and (output_index>self.no_outputs)): output_loop_count.next = 0 #resetting the loop counter
                    
                else:
                    output_index.next = 0 #loop around behaviour
                    output_loop_count.next = output_loop_count+1
                    
                    if((input_index<=self.no_outputs) and ((output_loop_count+1)==input_loop_count)): 
                        output_stall.next = 1 #checking to see if the array is now empty
                
        @always(input_trigger.posedge)
        def transmitting_stall_behaviour():
            if(input_trigger and output_stall): #data has been written into the Arc, while in the empty state
                #if((((output_index+self.no_outputs)<=(input_index+self.no_inputs)<self.size) and (output_loop_count==input_loop_count)) or ((input_index+self.no_inputs) and ((input_loop_count+1)==output_loop_count) and (self.no_inputs < input_index + self.no_inputs))): output_stall.next = 0 #checking to see if there is now sufficient data in the Arc to be read
                if((((output_index+self.no_outputs)<=(input_index+self.no_inputs)<self.size) and (input_loop_count==output_loop_count)) or (((input_index+self.no_inputs)>=self.size) and ((input_loop_count+1)>=output_loop_count) and (self.no_outputs<=(input_index+self.no_inputs)))): output_stall.next = 0 #undoing the stall if the new read has freed up enough space

            
        return transmitting_behaviour,transmitting_stall_behaviour
    
    def logic(self):
        receive_inst = self.receiving()
        transmit_inst = self.transmitting()
        
        return instances()
        
        
        
        
        