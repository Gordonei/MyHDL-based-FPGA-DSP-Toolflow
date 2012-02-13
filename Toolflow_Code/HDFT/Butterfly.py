'''
MyHDL-based FPGA DSP Toolflow
Butterfly processing unit, inherits the Actor Base Class
Created on 8 Feb 2012

@author: Gordon Inggs
'''
from myhdl import *
import Actor

def tf_real_f(i):
            value = i
            return value
        
def tf_imag_f(i):
            value = i
            return value

class Butterfly(Actor.Actor):
    name = "Butterfly"
    
    output_b = None
    
    tf_real = ()
    tf_imag = ()
    
    twiddle_bits = 0
    twiddle_factors_real = []
    twiddle_factors_imag = []
    
    twiddle_rom_line_real = Signal(intbv(0))
    twiddle_rom_line_imag = Signal(intbv(0))
    
    def __init__(self,clk,input_a,output_a,output_b,tf_real,tf_imag,twiddle_bits,scale=1):
        Actor.Actor.__init__(self,clk,input_a,output_a,scale)
        
        self.output_b = output_b
        
        self.tf_real = tf_real
        self.tf_imag = tf_imag
        
        self.twiddle_bits = twiddle_bits
        self.twiddle_factors_real = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(self.output_a.no_inputs)]
        self.twiddle_factors_imag = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(self.output_a.no_inputs)]
    
        self.twiddle_rom_line_real = Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1)))
        self.twiddle_rom_line_imag = Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1)))
        
        self.twiddle_rom_addr_real = Signal(intbv(0,min=0,max=output_a.no_inputs+1))
        self.twiddle_rom_addr_imag = Signal(intbv(0,min=0,max=output_a.no_inputs+1))
        
        self.tf_rom_inst_real = self.rom(self.twiddle_rom_line_real,self.twiddle_rom_addr_real,self.tf_real)
        self.tf_rom_inst_imag = self.rom(self.twiddle_rom_line_imag,self.twiddle_rom_addr_imag,self.tf_imag)
        
    def processing(self):
        enable = self.enable
        reset = self.reset
        input_a = self.input_a
        output_a = self.output_a
        output_b = self.output_b
        tf_real = self.tf_real
        tf_imag = self.tf_imag
        clk = self.clk
        
        output_stall = input_a.output_stall
        output_trigger = input_a.output_trigger
        output_index = input_a.output_index
        
        input_stall_a = output_a.input_stall
        input_trigger_a = output_a.input_trigger
        input_index_a = output_a.input_index
        
        input_stall_b = output_b.input_stall
        input_trigger_b = output_b.input_trigger
        input_index_b = output_b.input_index
        
        scale = self.scale
        no_inputs = input_a.no_outputs
        no_outputs = output_a.no_inputs
        
        input_buffer_real = input_a.buffer_real
        input_buffer_imag = input_a.buffer_imag
        output_buffer_a_real = output_a.buffer_real
        output_buffer_a_imag = output_a.buffer_imag
        output_buffer_b_real = output_b.buffer_real
        output_buffer_b_imag = output_b.buffer_imag
        
        ready = self.ready
        
        twiddle_rom_addr_real = self.twiddle_rom_addr_real
        twiddle_rom_addr_imag = self.twiddle_rom_addr_imag
        twiddle_rom_line_real = self.twiddle_rom_line_real
        twiddle_rom_line_imag = self.twiddle_rom_line_imag
        twiddle_factors_real = self.twiddle_factors_real
        twiddle_factors_imag = self.twiddle_factors_imag
        
        count = Signal(intbv(0,min=0,max=no_outputs+1))
        
        @always(enable.posedge,clk.posedge)
        def initialisation_behaviour():
            if(enable and clk and (count<(no_outputs))):
                ready.next = False
                
                twiddle_factors_real[count].next = twiddle_rom_line_real
                twiddle_factors_imag[count].next = twiddle_rom_line_imag
                
                if(count<(no_outputs-1)):
                    twiddle_rom_addr_real.next = count+1
                    twiddle_rom_addr_imag.next = count+1
   
                count.next = count+1
                
            elif(enable and clk):
                ready.next = True
        
        @always(enable.posedge,reset.posedge,clk)
        def processing_behaviour():
            if(enable and ready and not output_stall and not input_stall_a and not output_trigger and not input_trigger_a):# and not input_a.output_trigger and not output_a.input_trigger):
                for i in range(no_outputs):
                    output_buffer_a_real[input_index_a+i].next = input_buffer_real[output_index+i] + input_buffer_real[output_index+i+no_inputs/2]
                    output_buffer_a_imag[input_index_a+i].next = input_buffer_imag[output_index+i] + input_buffer_imag[output_index+i+no_inputs/2]
                
                input_trigger_a.next = True
            elif(enable and ready):
                input_trigger_a.next = False
           
        @always(enable.posedge,reset.posedge,clk)     
        def processing_behaviour_b():
            if(enable and ready and not output_stall and not input_stall_b and not output_trigger and not input_trigger_b):# and not input_a.output_trigger and not output_a.input_trigger):
                #print "%d: Processing - copying %s from input arc, starting at %d to output arc, starting at %d" % (now(),str(input_a.buffer_real[input_a.output_index:input_a.output_index+self.scale]),input_a.output_index,output_a.input_index)
                print twiddle_factors_real
                for i in range(no_outputs):
                    output_buffer_b_real[input_index_a+i].next = (input_buffer_real[output_index+i]-input_buffer_real[output_index+i+no_inputs/2])*twiddle_factors_real[i] - (input_buffer_imag[i]-input_buffer_imag[output_index+i+no_inputs/2])*twiddle_factors_imag[i]
                    output_buffer_b_imag[input_index_a+i].next = (input_buffer_real[output_index+i]-input_buffer_real[output_index+i+no_inputs/2])*twiddle_factors_imag[i] + (input_buffer_imag[i]-input_buffer_imag[output_index+i+no_inputs/2])*twiddle_factors_real[i]
                    
                output_trigger.next = True
                input_trigger_b.next = True
            elif(enable and ready):
                output_trigger.next = False
                input_trigger_b.next = False
                
        return processing_behaviour, processing_behaviour_b, initialisation_behaviour
    
    def model(self,input_data):
        output_data = [[],[]]
            
        for i in range(self.output_a.no_inputs):
            output_data[0].append(input_data[i]+input_data[i+self.output_a.no_inputs])
            output_data[1].append((input_data[i]-input_data[i+self.output_a.no_inputs])*(self.tf_real[i]+1.0j*self.tf_imag[i]))
           
        return output_data
    
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
        processing_inst = self.processing()
        
        tf_rom_inst_real = self.tf_rom_inst_real
        tf_rom_inst_imag = self.tf_rom_inst_imag
        
        return instances()
        
