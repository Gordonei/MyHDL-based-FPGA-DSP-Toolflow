'''
MyHDL-based FPGA DSP Toolflow
Test Script for Reorderer Class
Created on 14 Feb 2012

@author: Gordon Inggs
'''
from myhdl import *
import Reorderer, Arc
import math,random

def reorderer_conversion_testbench(clk,reset,reorderer,input_arc,output_arc):
    
    reorderer_logic_inst = reorderer.processing()
    reorderer_index_rom_inst = reorderer.index_rom
    
    input_arc_receiving_inst = input_arc.receiving()
    input_arc_transmitting_inst = input_arc.transmitting()
    
    output_arc_receiving_inst = output_arc.receiving()
    output_arc_transmitting_inst = output_arc.transmitting()
    
    return instances()

def test_bench_reorderer(reorderer,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk):
    
    reorderer_logic_inst = reorderer.logic()
    
    input_arc_inst = input_arc.logic()
    output_arc_inst = output_arc.logic()
    
    #clk = Signal(bool(0))
    @always(delay(1))
    def clock(): 
        clk.next = not(clk)
    
    @instance
    def actor_enable():
        yield delay(0)
        print "%d: Actors being enabled" % now()
        reorderer.enable.next = 1
        yield delay(1)
    
    @instance
    def input_arc_test():
        count = 0
        while(count<len(test_data)):
            yield delay(1)
            if(not input_arc.input_stall):
                for i in range(no_inputs): 
                    input_arc.buffer_real[input_arc.input_index+i].next = test_data[count][i]
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
        output_data = []
        while(count<(len(test_data)*no_inputs/no_outputs)):
            yield delay(1)
            if(not output_arc.output_stall):
                output_arc.output_trigger.next = 1
                print "%d: Outputting %s starting at location %d" % (now(),str(output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]),output_arc.output_index)
                output_data.extend(map(int,output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]))
                count += 1
                yield delay(1)
                output_arc.output_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Output Stalled" % now()
                
        reorderer.enable.next = 0
        
        print "Checking data"
        temp_test_data = []
        for t_d in test_data:
            temp_test_data.extend(t_d)
        
        temp_test_data = reorderer.model(temp_test_data)
        for i in range(min(len(temp_test_data),len(output_data))):
            if(output_data[i]!=temp_test_data[i]):
                print "%d - %d should be %d" % (i,output_data[i],temp_test_data[i])
                
            #else: print "%d: Output Stalled" % now()
    
    return instances()

no_inputs = 256
input_bitwidth = 8

no_outputs = 1024
output_bitwidth = 8

actor_scale = 1024

complex_valued = False
size_factor = 1

#Simulation Parameters
test_set_size = 4
#test_data = [range(no_inputs*no_outputs*test_set_size)]

test_data = [[int(random.random()*2**(input_bitwidth-1)) for i in range(no_inputs)] for j in range(test_set_size)]

indices = range(actor_scale)

for i in range(actor_scale): indices.append(indices.pop(int(random.random()*actor_scale)))
indices = tuple(indices)

reset = Signal(bool(False))
input_arc = Arc.Arc(reset,no_inputs,input_bitwidth,actor_scale,input_bitwidth,complex_valued,size_factor)
output_arc = Arc.Arc(reset,actor_scale,output_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)

clk = Signal(bool(False))
reorderer = Reorderer.Reorderer(clk,input_arc,output_arc,indices,actor_scale)

#Simulation
#signal_trace = traceSignals(test_bench_reorderer,reorderer,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk)
#simulation = Simulation(signal_trace)
#simulation.run(5000)

#Conversion
verilog_inst = toVerilog(reorderer_conversion_testbench,clk,reset,reorderer,input_arc,output_arc)