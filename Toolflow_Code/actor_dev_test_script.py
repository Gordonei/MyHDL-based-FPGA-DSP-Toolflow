'''
MyHDL-based FPGA DSP Toolflow
Test Script for Actor Base Class
Created on 22 Jan 2012

@author: Gordon Inggs
'''
from myhdl import *
import Actor, Arc

def test_bench_actor(actor,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk):
    
    actor_logic_inst = actor.logic()
    input_arc_inst = input_arc.logic()
    output_arc_inst = output_arc.logic()
    
    #clk = Signal(bool(0))
    @always(delay(1))
    def clock(): 
        clk.next = not(clk)
    
    @instance
    def actor_enable():
        yield delay(0)
        print "%d: Actor being enabled" % now()
        actor.enable.next = 1
        yield delay(5)
    
    @instance
    def input_arc_test():
        count = 0
        while(count*no_inputs<len(test_data[0])):
            yield delay(1)
            if(not input_arc.input_stall):
                for i in range(no_inputs): 
                    input_arc.buffer_real[input_arc.input_index+i].next = test_data[0][count*no_inputs+i]
                    
                print "%d: Inputing %s" % (now(),str(test_data[0][count*no_inputs:count*no_inputs+no_inputs]))
                input_arc.input_trigger.next = 1
                count += 1
                yield delay(1)
                input_arc.input_trigger.next = 0
                yield delay(1)
                
            #else: print "%d:Input Stalled" % now()
       
    @instance 
    def output_arc_test():
        count = 0
        while(count*no_outputs<len(test_data[0])):
            yield delay(1)
            if(not output_arc.output_stall):
                output_arc.output_trigger.next = 1
                print "%d: Outputting %s" % (now(),str(output_arc.buffer_real[output_arc.output_index:output_arc.output_index+no_outputs]))
                count += 1
                yield delay(1)
                output_arc.output_trigger.next = 0
                yield delay(1)
                
            #else: print "%d: Output Stalled" % now()
    
    return instances()

no_inputs = 1
input_bitwidth = 8

no_outputs = 2
output_bitwidth = 8

complex_valued = False
size_factor = 10

#Simulation Parameters
test_set_size = 40
test_data = [range(no_inputs*no_outputs*test_set_size)]
input_arc = Arc.Arc(no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)
output_arc = Arc.Arc(no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)
clk = Signal(bool(0))
actor = Actor.Actor(input_arc,output_arc,clk)

#Simulation
signal_trace = traceSignals(test_bench_actor,actor,input_arc,output_arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,clk)
simulation = Simulation(signal_trace)
simulation.run(150)