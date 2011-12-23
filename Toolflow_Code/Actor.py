'''
MyHDL-based FPGA DSP Toolflow
Actor Base Class

Created on 22 Dec 2011

@author: Gordon Inggs
'''
from myhdl import *
import Arc

class Actor:
    name = "Actor"
    
    input_a = Arc.Arc()
    
    output_a = Arc.Arc()
    
    enable = Signal(bool(0))
    reset = Signal(bool(0))
    
    def __init__(self,input_a,output_a):
        
        self.input_a = self.input_a
        
        self.output_a = self.ouput_a
        
    def processing(self):
        enable = self.enable
        reset = self.reset
        input_a = self.input_a
        output_a = self.output_a
        
        @always(enable.posedge,reset.posedge,input_a.output_stall,output_a.input_stall)
        def processing_behaviour():
            if(enable and not input_a.output_stall and not output_a.input_stall):
                for i in range(input_a.no_inputs):
                    output_a.buffer_real[output_a.input_index+i].next = input_a.buffer_real[input_a.output_index+i] #Actor just copies data from input to output
                    if(output_a.complex_valued and input_a.complex_valued): output_a.buffer_imag[output_a.input_index+i].next = input_a.buffer_imag[input_a.output_index+i]
                    
                input_a.output_trigger.next = 1
                output_a.input_trigger.next = 1
                
            else:
                input_a.output_trigger.next = 0
                output_a.input_trigger.next = 0
                
        return processing_behaviour
    
    def logic(self):
        processing_inst = self.processing()
        
        return instances()
    
    def model(self,input_data):
        output_data = input_data
        
        return output_data
    
    
    
    
    
    
    
    
