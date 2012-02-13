'''
MyHDL-based FPGA DSP Toolflow
Pipeline Mux unit, inherits the Actor Base Class
Created on 9 Feb 2012

@author: Gordon Inggs
'''
from myhdl import *
import Actor

class Pipeline_Mux(Actor.Actor):
    name = "Pipeline_Mux"
    
    input_a = []
    
    input_line_no = Signal(intbv(0))
    
    def __init__(self, clk, input_a, output_a, scale=1):
        Actor.Actor.__init__(self, clk, input_a, output_a, scale)
        
        self.input_line_no = Signal(intbv(0,min=0,max=len(input_a)))
        
    def processing(self):
        enable = self.enable
        reset = self.reset
        input_a = self.input_a
        output_a = self.output_a
        clk = self.clk
        input_line_no = self.input_line_no
        
        output_stall = [i_a.output_stall for i_a in self.input_a]
        output_trigger = [i_a.output_trigger for i_a in self.input_a]
        output_index = [i_a.output_index for i_a in self.input_a]
        
        input_stall = output_a.input_stall
        input_trigger = output_a.input_trigger
        input_index = output_a.input_index
        
        scale = self.scale
        
        input_buffer_real = []
        for i_a in self.input_a:
            input_buffer_real.extend(i_a.buffer_real)
            
        no_inputs = len(self.input_a[0].buffer_real)
        
        output_buffer_real = output_a.buffer_real
        
        ready = self.ready
        
        #@always(enable.posedge,reset.posedge,input_a.output_stall,output_a.input_stall,clk.posedge)
        @always(enable.posedge,clk.posedge)
        def initialisation_behaviour():
            if(not ready): ready.next = True
        
        @always(enable.posedge,reset.posedge,clk)
        def processing_behaviour():
            if(enable and ready and not output_stall[input_line_no] and not input_stall and not output_trigger[input_line_no] and not input_trigger):# and not input_a.output_trigger and not output_a.input_trigger):
                #print "%d: Processing - copying %s from input arc, starting at %d to output arc, starting at %d" % (now(),str(input_a.buffer_real[input_a.output_index:input_a.output_index+self.scale]),input_a.output_index,output_a.input_index)
                
                for i in range(scale): #Assumes that arcs have appropriate number of inputs and outputs set
                    output_buffer_real[input_index+i].next = input_buffer_real[input_line_no*no_inputs+output_index[input_line_no]+i] #Actor just copies data from input to output
                    #if(output_a.complex_valued and input_a.complex_valued): output_a.buffer_imag[input_index+i].next = input_a.buffer_imag[output_index+i]
                    
                output_trigger[input_line_no].next = True
                input_trigger.next = True
                
            elif(ready):
                output_trigger[input_line_no].next = False
                input_trigger.next = False
                
                if(input_line_no<(len(input_a)-1) and output_trigger[input_line_no] and input_trigger): input_line_no.next = input_line_no+1
                elif(output_trigger[input_line_no] and input_trigger): input_line_no.next = 0
                
        """@always(clk.negedge)
        def processing_behaviour_toggle():
            if(input_a.output_trigger): input_a.output_trigger.next = 0
            if(output_a.input_trigger): output_a.input_trigger.next = 0"""
                
        return processing_behaviour,initialisation_behaviour#,processing_behaviour_toggle
    
    def model(self,input_a):
        output_dataset = []
        for i in input_a:
            output_dataset.extend(i)