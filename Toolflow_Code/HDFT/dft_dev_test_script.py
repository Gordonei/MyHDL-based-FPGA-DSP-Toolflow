'''
MyHDL-based FPGA DSP Toolflow
Test script for DFT Actor Class - simulates and converts to Verilog
Created on 13 Feb 2012

@author: Gordon Inggs
'''
'''
MyHDL-based FPGA DSP Toolflow
Test Script for Actor Base Class
Created on 22 Jan 2012

@author: Gordon Inggs
'''
from myhdl import *
import DFT, Arc
import math,random

def dft_conversion_testbench(clk,reset,dft,input_arc,output_arc):
    
    dft_logic_inst = dft.processing()
    dft_tf_rom_inst_real = dft.tf_rom_inst_real
    dft_tf_rom_inst_imag = dft.tf_rom_inst_imag
    
    input_arc_receiving_inst = input_arc.receiving()
    input_arc_transmitting_inst = input_arc.transmitting()
    
    output_arc_receiving_inst = output_arc.receiving()
    output_arc_transmitting_inst = output_arc.transmitting()
    
    return instances()

def test_bench_dft(dft,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk):
    
    dft_logic_inst = dft.logic()
    
    input_arc_inst = input_arc.logic()
    output_arc_inst = output_arc.logic()
    
    #clk = Signal(bool(0))
    @always(delay(1))
    def clock(): 
        clk.next = not(clk)
    
    @instance
    def dft_enable():
        yield delay(0)
        print "%d: DFT being enabled" % now()
        dft.enable.next = 1
        yield delay(5)
    
    @instance
    def input_arc_test():
        count = 0
        while(count*no_inputs<len(test_data[0])):
            yield delay(1)
            if(not input_arc.input_stall):
                print "%d: Inputing %s starting at location %d" % (now(),str(test_data[0][count*no_inputs:count*no_inputs+no_inputs]),input_arc.input_index)
                for i in range(no_inputs): 
                    input_arc.buffer_real[input_arc.input_index+i].next = test_data[0][count*no_inputs+i]
                    input_arc.buffer_imag[input_arc.input_index+i].next = test_data[0][count*no_inputs+i]
                input_arc.input_trigger.next = 1
                count += 1
                yield delay(1)
                input_arc.input_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Input Stalled" % now()
                
            #else: print "%d:Input Stalled" % now()
       
    @instance 
    def output_arc_test():
        count = 0
        output_data_real = []
        output_data_imag = []
        while(count*no_outputs<len(test_data[0])):
            yield delay(1)
            if(not output_arc.output_stall):
                output_arc.output_trigger.next = 1
                print "%d: Outputting %s starting at location %d" % (now(),str(output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]),output_arc.output_index)
                output_data_real.extend(map(int,output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]))
                output_data_imag.extend(map(int,output_arc.buffer_imag[output_arc.output_index:output_arc.output_index+no_outputs]))
                count += 1
                yield delay(1)
                output_arc.output_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Output Stalled" % now()
                
        dft.enable.next = 0
        print "Checking data"
        test_data[0] = [(t_d+1.0j*t_d) for t_d in test_data[0]]
        test_data[0] = dft.model(test_data[0])
        for i in range(min(len(test_data[0]),len(output_data_real))):
            if(output_data_real[i]!=test_data[0][i].real):
                print "%d - real %d should be %d" % (i,output_data_real[i],test_data[0][i].real)
            if(output_data_imag[i]!=test_data[0][i].imag):
                print "%d - imag %d should be %d" % (i,output_data_imag[i],test_data[0][i].imag)
                
            #else: print "%d: Output Stalled" % now()
    
    return instances()

twiddle_bits = 4

no_inputs = 10
input_bitwidth = 8

no_outputs = 10
output_bitwidth = input_bitwidth+twiddle_bits+no_inputs

actor_scale = 10

complex_valued = True
size_factor = 1

#Simulation Parameters
test_set_size = 1
#test_data = [range(no_inputs*no_outputs*test_set_size)]

temp = []
for td in range(max(no_outputs,no_inputs)*test_set_size): 
    temp.append(int(random.random()*2**(input_bitwidth-1)))

test_data = []
test_data.append(temp)

tf_real = []
tf_imag = []
for i in range(no_inputs):
    tf_real.append(tuple([int(random.random()*2**(twiddle_bits-1)) for j in range(no_inputs)]))
    tf_imag.append(tuple([int(random.random()*2**(twiddle_bits-1)) for j in range(no_inputs)]))
    
tf_real = tuple(tf_real)
tf_imag = tuple(tf_imag)

reset = Signal(bool(False))
input_arc = Arc.Arc(reset,no_inputs,input_bitwidth,actor_scale,input_bitwidth,complex_valued,size_factor)
output_arc = Arc.Arc(reset,actor_scale,output_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)

clk = Signal(bool(False))
dft = DFT.DFT(clk,input_arc,output_arc,tf_real,tf_imag,twiddle_bits,actor_scale)

#Simulation
signal_trace = traceSignals(test_bench_dft,dft,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk)
#simulation = Simulation(signal_trace)
#simulation.run(1000)

#Conversion

verilog_inst = toVerilog(dft_conversion_testbench,clk,reset,dft,input_arc,output_arc)
