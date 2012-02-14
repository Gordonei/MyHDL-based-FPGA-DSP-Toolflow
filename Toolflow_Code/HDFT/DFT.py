'''
MyHDL-based FPGA DSP Toolflow
DFT unit, inherits the Actor Base Class
Created on 13 Feb 2012

@author: Gordon Inggs
'''
from myhdl import *
import Actor

class DFT(Actor.Actor):
    name = "DFT"
    
    tf_real = ()
    tf_imag = ()
    
    twiddle_bits = 0
    twiddle_factors_real = []
    twiddle_factors_imag = []
    
    twiddle_bits = 0
    twiddle_factors_real = (())
    twiddle_factors_imag = (())
    twiddle_rom_line_real = []
    twiddle_rom_line_imag = []
    twiddle_rom_addr_real = []
    twiddle_rom_addr_imag = []
    
    def __init__(self,clk,input_a,output_a,tf_real,tf_imag,twiddle_bits,scale=1):
        Actor.Actor.__init__(self,clk,input_a,output_a,scale)
        
        self.twiddle_bits = twiddle_bits
        self.twiddle_factors_real = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(self.output_a.no_inputs*self.output_a.no_inputs)]
        self.twiddle_factors_imag = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(self.output_a.no_inputs*self.output_a.no_inputs)]
    
        self.twiddle_rom_line_real = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(self.output_a.no_inputs)]
        self.twiddle_rom_line_imag = [Signal(intbv(0,min=-2**(self.twiddle_bits-1),max=2**(self.twiddle_bits-1))) for i in range(self.output_a.no_inputs)]
        
        self.twiddle_rom_addr_real = Signal(intbv(0,min=0,max=output_a.no_inputs+1))
        self.twiddle_rom_addr_imag = Signal(intbv(0,min=0,max=output_a.no_inputs+1))
        
        self.tf_real = tf_real
        self.tf_imag = tf_imag
            
        self.tf_rom_inst_real = [self.rom(self.twiddle_rom_line_real[i],self.twiddle_rom_addr_real,self.tf_real[i]) for i in range(output_a.no_inputs)]
        self.tf_rom_inst_imag = [self.rom(self.twiddle_rom_line_imag[i],self.twiddle_rom_addr_imag,self.tf_imag[i]) for i in range(output_a.no_inputs)]
        
    def processing(self):
        enable = self.enable
        reset = self.reset
        input_a = self.input_a
        output_a = self.output_a
        clk = self.clk
        
        output_stall = input_a.output_stall
        output_trigger = input_a.output_trigger
        output_index = input_a.output_index
        
        input_stall_a = output_a.input_stall
        input_trigger_a = output_a.input_trigger
        input_index_a = output_a.input_index
        
        scale = self.scale
        no_inputs = input_a.no_outputs
        no_outputs = output_a.no_inputs
        output_bitwidth = output_a.input_bitwidth
        
        input_buffer_real = input_a.buffer_real
        input_buffer_imag = input_a.buffer_imag
        
        output_buffer_real = output_a.buffer_real
        output_buffer_imag = output_a.buffer_imag
        
        ready = self.ready
        
        twiddle_rom_addr_real = self.twiddle_rom_addr_real
        twiddle_rom_addr_imag = self.twiddle_rom_addr_imag
        twiddle_rom_line_real = self.twiddle_rom_line_real
        twiddle_rom_line_imag = self.twiddle_rom_line_imag
        twiddle_factors_real = self.twiddle_factors_real
        twiddle_factors_imag = self.twiddle_factors_imag
        
        count = Signal(intbv(0,min=0,max=no_inputs+1))
        
        @always(enable.posedge,clk.posedge)
        def initialisation_behaviour():
            if(enable and clk and (count<(no_inputs))):
                ready.next = False
                
                for i in range(no_inputs):
                    twiddle_factors_real[no_inputs*count+i].next = twiddle_rom_line_real[i]
                    twiddle_factors_imag[no_inputs*count+i].next = twiddle_rom_line_imag[i]
                
                if(count<(no_outputs-1)):
                    twiddle_rom_addr_real.next = count+1
                    twiddle_rom_addr_imag.next = count+1
   
                count.next = count + 1
                
            elif(enable and clk):
                ready.next = True
                
        @always(enable.posedge,reset.posedge,clk)
        def processing_behaviour():
            if(enable and ready and not output_stall and not input_stall_a and not output_trigger and not input_trigger_a):# and not input_a.output_trigger and not output_a.input_trigger):
                for i in range(no_inputs):
                    temp_value_real = intbv(0,min=-2**(output_bitwidth-1),max=2**(output_bitwidth-1))
                    temp_value_imag = intbv(0,min=-2**(output_bitwidth-1),max=2**(output_bitwidth-1))
                    for j in range(no_inputs):
                        temp_value_real += input_buffer_real[output_index+j]*(twiddle_factors_real[j*no_inputs+i]+twiddle_factors_imag[j*no_inputs+i]) - twiddle_factors_imag[j*no_inputs+i]*(input_buffer_real[output_index+j]+input_buffer_imag[output_index+j])
                        temp_value_imag += input_buffer_real[output_index+j]*(twiddle_factors_real[j*no_inputs+i]+twiddle_factors_imag[j*no_inputs+i]) + twiddle_factors_real[j*no_inputs+i]*(input_buffer_imag[output_index+j]-input_buffer_real[output_index+j])
                    
                    output_buffer_real[input_index_a+i].next = temp_value_real
                    output_buffer_imag[input_index_a+i].next = temp_value_imag
                    
                input_trigger_a.next = True
            elif(enable and ready):
                input_trigger_a.next = False
                
        return processing_behaviour,initialisation_behaviour
                
    def model(self,input_data):
        output_data = []
        
        for i in range(len(input_data)):
            temp_value = 0.0
            count = 0
            for i_d in input_data:
                temp_value += (i_d)*(self.tf_real[i][count]+1j*self.tf_imag[i][count])
                count += 1
                
            output_data.append(temp_value)
           
        return output_data
    
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
        
        tf_rom_inst_real = self.tf_rom_inst_real
        tf_rom_inst_imag = self.tf_rom_inst_imag
        
        return instances()