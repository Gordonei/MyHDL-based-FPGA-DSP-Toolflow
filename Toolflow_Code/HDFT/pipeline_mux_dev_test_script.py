'''
MyHDL-based FPGA DSP Toolflow
Test Script for Actor Base Class
Created on 22 Jan 2012

@author: Gordon Inggs
'''
from myhdl import *
import Pipeline_Mux, Arc
import math,random

def mux_conversion_testbench(clk,reset,mux,input_arc,output_arc):
    
    mux_logic_inst = mux.processing()
    
    input_arc_receiving_inst = [i_a.receiving() for i_a in input_arc]
    input_arc_transmitting_inst = [i_a.transmitting() for i_a in input_arc]
    
    output_arc_receiving_inst = output_arc.receiving()
    output_arc_transmitting_inst = output_arc.transmitting()
    
    return instances()

def test_bench_mux(mux,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk):
    
    mux_logic_inst = mux.logic()
    
    input_arc_inst = [i_a.logic() for i_a in input_arc]
    output_arc_inst = output_arc.logic()
    
    #clk = Signal(bool(0))
    @always(delay(1))
    def clock(): 
        clk.next = not(clk)
    
    @instance
    def actor_enable():
        yield delay(0)
        print "%d: Actors being enabled" % now()
        mux.enable.next = 1
        yield delay(5)
    
    @instance
    def input_arc_test():
        count = 0
        loop_count = 0
        while(loop_count<len(test_data)):
            yield delay(1)
            if(not input_arc[loop_count].input_stall):
                print "%d: Inputing %s starting at location %d" % (now(),str(test_data[loop_count][count*no_inputs:count*no_inputs+no_inputs]),input_arc[loop_count].input_index)
                for i in range(no_inputs):
                    input_arc[loop_count].buffer_real[input_arc[loop_count].input_index+i].next = test_data[loop_count][count*no_inputs+i]
                input_arc[loop_count].input_trigger.next = 1
                if(((count+1)*no_inputs)<len(test_data[loop_count])): count += 1
                else:
                    loop_count += 1
                    count = 0
                    
                yield delay(1)
                if(loop_count<len(test_data)): input_arc[loop_count].input_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Input Stalled" % now()
                
            #else: print "%d:Input Stalled" % now()
       
    @instance 
    def output_arc_test():
        count = 0
        loop_count = 0
        output_data = []
        while(loop_count<len(test_data)):
            yield delay(1)
            if(not output_arc.output_stall):
                output_arc.output_trigger.next = 1
                print "%d: Outputting %s starting at location %d" % (now(),str(output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]),output_arc.output_index)
                output_data.extend(map(int,output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]))
                
                if(((count+1)*no_inputs)<len(test_data[loop_count])): count += 1
                else:
                    loop_count += 1
                    count = 0
                    
                yield delay(1)
                if(loop_count<len(test_data)): output_arc.output_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Output Stalled" % now()
                
        mux.enable.next = 0
        print "Checking data"
        for j in range(len(test_data)):
            for i in range(len(test_data[j])):
                if(output_data[i+j*len(test_data[j])]!=test_data[j][i]):
                    print "set %d #%d - %d should be %d" % (j,i,output_data[i+j*len(test_data[j])],test_data[j][i])
                
            #else: print "%d: Output Stalled" % now()
    
    return instances()

no_inputs = 10
input_bitwidth = 8

no_outputs = 10
output_bitwidth = 8

actor_scale = 10

complex_valued = False
size_factor = 1

#Simulation Parameters
test_set_size = 16
#test_data = [range(no_inputs*no_outputs*test_set_size)]

temp = []
for i in range(test_set_size):
    temp.append([])
    for td in range(max(no_outputs,no_inputs)): 
        temp[-1].append(int(random.random()*2**(input_bitwidth-1)))

test_data = temp

reset = Signal(bool(False))
input_arc = [Arc.Arc(reset,no_inputs,input_bitwidth,actor_scale,input_bitwidth,complex_valued,size_factor) for i in range(test_set_size)]
output_arc = Arc.Arc(reset,actor_scale,output_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)

clk = Signal(bool(False))
mux = Pipeline_Mux.Pipeline_Mux(clk,input_arc,output_arc,actor_scale)

#Simulation
signal_trace = traceSignals(test_bench_mux,mux,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk)
#simulation = Simulation(signal_trace)
#simulation.run(100)

#Conversion
verilog_inst = toVerilog(mux_conversion_testbench,clk,reset,mux,input_arc,output_arc)