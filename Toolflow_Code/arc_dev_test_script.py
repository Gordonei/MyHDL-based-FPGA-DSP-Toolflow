'''
MyHDL-based FPGA DSP Toolflow
Test Script for Arc Base Class
Created on 23 Dec 2011

@author: Gordon Inggs
'''
from myhdl import *
import Arc

def test_bench_arc(arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data):
    
    arc_logic_inst = arc.logic()
    
    write_delay = 0
    
    @instance
    def arc_write_test():
        count = 0
        yield delay(write_delay)
        while(count*no_inputs<len(test_data[0])):
            yield delay(1)
            if(not arc.input_stall):
                for i in range(no_inputs): 
                    arc.buffer_real[arc.input_index+i].next = test_data[0][count*no_inputs+i]
                    
                print "%d: Inputing %s" % (now(),str(test_data[0][count*no_inputs:count*no_inputs+no_inputs]))
                arc.input_trigger.next = 1
                count += 1
                yield delay(1)
                arc.input_trigger.next = 0
                yield delay(1)
                
            else: print "%d: Input Stalled" % now()
            
                
    @instance
    def arc_read_test():
        count = 0
        while(count*no_outputs<len(test_data[0])):
            yield delay(1)
            if(not arc.output_stall):
                arc.output_trigger.next = 1
                print "%d: Outputting %s" % (now(),str(arc.buffer_real[arc.output_index:arc.output_index+no_outputs]))
                count += 1
                yield delay(1)
                arc.output_trigger.next = 0
                yield delay(1)
                
            else: print "%d: Output Stalled" % now()
                
    
    """clk = Signal(bool(0))            
    @always(delay(5))
    def clk_driver():
        clk.next = not(clk)"""
                
    return instances()

#Arc Parameters
no_inputs = 1
input_bitwidth = 8

no_outputs = 2
output_bitwidth = 8

complex_valued = False
size_factor = 10

#Simulation Parameters
test_set_size = 40
test_data = [range(no_inputs*no_outputs*test_set_size)]

#Simulation
#arc_test_bench_inst = test_bench_arc(no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data)
#
arc = Arc.Arc(no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)
signal_trace = traceSignals(test_bench_arc,arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data)
simulation = Simulation(signal_trace)
simulation.run(50)
