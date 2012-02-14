'''
MyHDL-based FPGA DSP Toolflow
Reorderer unit, inherits the Actor Base Class
Created on 13 Feb 2012

@author: Gordon Inggs
'''
from myhdl import *
import Actor

class Reorderer(Actor.Actor):
    name = "Reorderer"
    
    indices = ()
    index_array = []
    
    index_rom_line = Signal(intbv(0))
    index_rom_addr = Signal(intbv(0))
    
    index_rom = None
    
    def __init__(self,clk,input_a,output_a,indices,scale=1):
        Actor.Actor.__init__(self,clk,input_a,output_a,scale)
        
        self.indices = indices
        
        self.index_rom_line = Signal(intbv(0,min=0,max=len(indices)))
        self.index_rom_addr = Signal(intbv(0,min=0,max=len(indices)))
        
        self.index_rom = self.rom(self.index_rom_line,self.index_rom_addr,self.indices)
        self.index_array = [Signal(intbv(0,min=0,max=self.scale)) for i in range(self.scale)]
        
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
        no_inputs = input_a.no_outputs
        no_outputs = output_a.no_inputs
        
        input_buffer_real = input_a.buffer_real
        output_buffer_real = output_a.buffer_real
        
        ready = self.ready
        
        index_array = self.index_array
        index_rom_line = self.index_rom_line
        index_rom_addr = self.index_rom_addr
        
        count = Signal(intbv(0,min=0,max=scale+1))
        
        #@always(enable.posedge,reset.posedge,input_a.output_stall,output_a.input_stall,clk.posedge)
        @always(enable.posedge,clk.posedge)
        def initialisation_behaviour():
            if(enable and clk and (count<scale)):
                ready.next = False
                
                index_array[count].next = index_rom_line
                
                if(count<(scale-1)): index_rom_addr.next = count+1
   
                count.next = count + 1
                
            elif(enable and clk): ready.next = True
        
        @always(enable.posedge,reset.posedge,clk)
        def processing_behaviour():
            if(enable and ready and not output_stall and not input_stall and not output_trigger and not input_trigger):# and not input_a.output_trigger and not output_a.input_trigger):
                #print "%d: Processing - copying %s from input arc, starting at %d to output arc, starting at %d" % (now(),str(input_a.buffer_real[input_a.output_index:input_a.output_index+self.scale]),input_a.output_index,output_a.input_index)
                
                for i in range(scale): #Assumes that arcs have appropriate number of inputs and outputs set
                    output_buffer_real[index_array[input_index+i]].next = input_buffer_real[output_index+i] #Actor just copies data from input to output
                    #if(output_a.complex_valued and input_a.complex_valued): output_a.buffer_imag[input_index+i].next = input_a.buffer_imag[output_index+i]
                    
                output_trigger.next = True
                input_trigger.next = True
                
            elif(ready):
                output_trigger.next = False
                input_trigger.next = False
                
        return processing_behaviour,initialisation_behaviour
        
    def rom(self,dout, addr, CONTENT):
        """
        DFT rom behaviour
        this independent module is used to provide the ROM for the twiddle factors that are required
        """
        @always_comb
        def read():
            dout.next = CONTENT[int(addr)]

        return read
    
    def logic(self):
        processing_inst = self.processing()
        
        index_rom = self.index_rom
        
        return instances()
    
    def model(self,input_dataset):
        output_dataset = [0 for i in range(len(input_dataset))]
        
        for i in range(len(input_dataset)):
            output_dataset[self.indices[i]] = input_dataset[i] 
        
        return output_dataset