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
    
    input_a = None#Arc.Arc(0,0,0,0,False,0)
    
    output_a = None#Arc.Arc(0,0,0,0,False,0)
    
    enable = Signal(bool(0))
    reset = Signal(bool(0))
    clk = Signal(bool(0))
    
    def __init__(self,input_a,output_a,clk):
        
        self.input_a = input_a
        
        self.output_a = output_a
        
        self.clk = clk
        
    def processing(self):
        enable = self.enable
        reset = self.reset
        input_a = self.input_a
        output_a = self.output_a
        clk = self.clk
        
        @always(enable.posedge,reset.posedge,input_a.output_stall,output_a.input_stall,clk.posedge)
        def processing_behaviour():
            if(enable and not input_a.output_stall and not output_a.input_stall and not input_a.output_trigger and not output_a.input_trigger):
                print "%d: Processing" % now()
                for i in range(input_a.no_inputs):
                    output_a.buffer_real[output_a.input_index+i].next = input_a.buffer_real[input_a.output_index+i] #Actor just copies data from input to output
                    if(output_a.complex_valued and input_a.complex_valued): output_a.buffer_imag[output_a.input_index+i].next = input_a.buffer_imag[input_a.output_index+i]
                    
                input_a.output_trigger.next = 1
                output_a.input_trigger.next = 1
                
            else:
                input_a.output_trigger.next = 0
                output_a.input_trigger.next = 0
                
        @always(clk.posedge)
        def processing_behaviour_toggle():
            if(input_a.output_trigger): input_a.output_trigger.next = 0
            if(output_a.input_trigger): output_a.input_trigger.next = 0
                
        return processing_behaviour,processing_behaviour_toggle
    
    def logic(self):
        processing_inst = self.processing()
        
        return instances()
    
    def model(self,input_data):
        output_data = input_data
        
        return output_data
    
    
    
    
    
    
    
    
