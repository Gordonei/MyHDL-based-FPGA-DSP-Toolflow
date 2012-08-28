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
    
    scale = 1
    
    enable = Signal(bool(0))
    reset = Signal(bool(0))
    clk = Signal(bool(0))
    ready = Signal(bool(0))
    
    def __init__(self,clk,input_a,output_a,scale=1):
        
        self.input_a = input_a
        
        self.output_a = output_a
        
        self.clk = clk
        
        self.scale = scale
        
        self.ready = Signal(bool(False))
        
    def processing(self):
        enable = self.enable
        reset = self.reset
        input_a = self.input_a
        output_a = self.output_a
        clk = self.clk
        
        output_stall = input_a.output_stall
        output_trigger = input_a.output_trigger
        output_index = input_a.output_index
        
        input_stall = output_a.input_stall
        input_trigger = output_a.input_trigger
        input_index = output_a.input_index
        
        scale = self.scale
        
        input_buffer_real = input_a.buffer_real
        output_buffer_real = output_a.buffer_real
        
        ready = self.ready
        
        #@always(enable.posedge,reset.posedge,input_a.output_stall,output_a.input_stall,clk.posedge)
        @always(enable.posedge,clk.posedge)
        def initialisation_behaviour():
            if(not ready): ready.next = True
        
        @always(enable.posedge,reset.posedge,clk.posedge)
        def processing_behaviour():
            """print enable
            print ready
            print output_stall
            print input_stall
            print output_trigger
            print input_trigger"""
            
            if(enable and ready and not output_stall and not input_stall and not output_trigger and not input_trigger):# and not input_a.output_trigger and not output_a.input_trigger):
                #print "%d: Processing - copying %s from input arc, starting at %d to output arc, starting at %d" % (now(),str(input_a.buffer_real[input_a.output_index:input_a.output_index+self.scale]),input_a.output_index,output_a.input_index)
                
                for i in range(scale): #Assumes that arcs have appropriate number of inputs and outputs set
                    output_buffer_real[input_index+i].next = input_buffer_real[output_index+i] #Actor just copies data from input to output
                    #if(output_a.complex_valued and input_a.complex_valued): output_a.buffer_imag[input_index+i].next = input_a.buffer_imag[output_index+i]
                    
                output_trigger.next = True
                input_trigger.next = True
                
            elif(ready):
                output_trigger.next = False
                input_trigger.next = False
                
        """@always(clk.negedge)
        def processing_behaviour_toggle():
            if(input_a.output_trigger): input_a.output_trigger.next = 0
            if(output_a.input_trigger): output_a.input_trigger.next = 0"""
                
        return processing_behaviour,initialisation_behaviour#,processing_behaviour_toggle
    
    def logic(self):
        processing_inst = self.processing()
        
        return instances()
    
    def model(self,input_data):
        output_data = input_data
        
        return output_data
    
    
    
    
    
    
    
    
