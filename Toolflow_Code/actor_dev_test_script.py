'''
MyHDL-based FPGA DSP Toolflow
Test Script for Actor Base Class
Created on 22 Jan 2012

@author: Gordon Inggs
'''
from myhdl import *
import Actor, Arc
import math,random

def actor_conversion_testbench(clk,reset,actor1,actor2,input_arc,actor1_actor2_arc,output_arc):
    
    actor1_logic_inst = actor1.processing()
    actor2_logic_inst = actor2.processing()
    
    input_arc_receiving_inst = input_arc.receiving()
    input_arc_transmitting_inst = input_arc.transmitting()
    
    actor1_actor2_receiving_inst = actor1_actor2_arc.receiving()
    actor1_actor2_transmitting_inst = actor1_actor2_arc.transmitting()
    
    output_arc_receiving_inst = output_arc.receiving()
    output_arc_transmitting_inst = output_arc.transmitting()
    
    return instances()

def test_bench_actor(actor1,actor2,input_arc,actor1_actor2_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk):
    
    actor1_logic_inst = actor1.logic()
    actor2_logic_inst = actor2.logic()
    
    input_arc_inst = input_arc.logic()
    actor1_actor2_arc_inst = actor1_actor2_arc.logic()
    output_arc_inst = output_arc.logic()
    
    #clk = Signal(bool(0))
    @always(delay(1))
    def clock(): 
        clk.next = not(clk)
    
    @instance
    def actor_enable():
        yield delay(5)
        print "%d: Actors being enabled" % now()
        actor1.enable.next = 1
        actor2.enable.next = 1
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
                input_arc.input_trigger.next = 1
                count += 1
                yield delay(1)
                input_arc.input_trigger.next = 0
                yield delay(1)
                
            else: print "%d: Input Stalled" % now()
                
            #else: print "%d:Input Stalled" % now()
       
    @instance 
    def output_arc_test():
        count = 0
        output_data = []
        while(count*no_outputs<len(test_data[0])):
            yield delay(1)
            if(not output_arc.output_stall):
                output_arc.output_trigger.next = 1
                print "%d: Outputting %s starting at location %d" % (now(),str(output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]),output_arc.output_index)
                output_data.extend(map(int,output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]))
                count += 1
                yield delay(1)
                output_arc.output_trigger.next = 0
                yield delay(1)
                
            else: print "%d: Output Stalled" % now()
                
        actor1.enable.next = 0
        actor2.enable.next = 0
        print "Checking data"
        for i in range(min(len(test_data[0]),len(output_data))):
            if(output_data[i]!=test_data[0][i]):
                print "%d - %d should be %d" % (i,output_data[i],test_data[0][i])
                
            #else: print "%d: Output Stalled" % now()
    
    return instances()

no_inputs = 1
input_bitwidth = 8

no_outputs = 1
output_bitwidth = 8

actor_scale = 1

complex_valued = False
size_factor = 5

#Simulation Parameters
test_set_size = 10
#test_data = [range(no_inputs*no_outputs*test_set_size)]

temp = []
for td in range(max(no_outputs,no_inputs)*test_set_size): 
    temp.append(int(random.random()*100))

test_data = []
test_data.append(temp)

reset = Signal(bool(False))
input_arc = Arc.Arc(reset,no_inputs,input_bitwidth,actor_scale,input_bitwidth,complex_valued,size_factor)
actor1_actor2_arc = Arc.Arc(reset,actor_scale,input_bitwidth,actor_scale,input_bitwidth,complex_valued,size_factor)
output_arc = Arc.Arc(reset,actor_scale,output_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)

clk = Signal(bool(False))
actor1 = Actor.Actor(clk,input_arc,actor1_actor2_arc,actor_scale)
actor2 = Actor.Actor(clk,actor1_actor2_arc,output_arc,actor_scale)

#Simulation
signal_trace = traceSignals(test_bench_actor,actor1,actor2,input_arc,actor1_actor2_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk)
simulation = Simulation(signal_trace)
simulation.run(100)

#Conversion

#verilog_inst = toVerilog(actor_conversion_testbench,clk,reset,actor1,actor2,input_arc,actor1_actor2_arc,output_arc)