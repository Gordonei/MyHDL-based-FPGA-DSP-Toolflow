'''
MyHDL-based FPGA DSP Toolflow
Test Script for Arc Base Class
Created on 23 Dec 2011

@author: Gordon Inggs
'''
from myhdl import *
import Arc

#Code from http://stackoverflow.com/questions/147515/least-common-multiple-for-3-or-more-numbers
def gcd(a, b):
    """Return greatest common divisor using Euclid's Algorithm."""
    while b:      
        a, b = b, a % b
    return a

def lcm(a, b):
    """Return lowest common multiple."""
    return a * b // gcd(a, b)
#end of code from http://stackoverflow.com/questions/147515/least-common-multiple-for-3-or-more-numbers

def test_bench_arc(arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data):
    
    arc_logic_inst = arc.logic()
    
    @instance
    def arc_write_test():
        count = 0
        while(count<len(test_data[0])):
            yield delay(1)
            if(not arc.input_stall):
                for i in range(no_inputs): arc.buffer_real[arc.input_index+i].next = test_data[0][count+i]
                arc.input_trigger.next = 1
                count = count + 1
                yield delay(5)
                arc.input_trigger.next = 0
                yield delay(5)
                
    @instance
    def arc_read_test():
        count = 0
        while(count<len(test_data[0])):
            yield delay(1)
            if(not arc.output_stall):
                print "%d: %s" % (now(),str(arc.buffer_real[arc.output_index:arc.output_index+no_outputs]))
                arc.output_trigger.next = 1
                count + 1
                yield delay(6)
                arc.output_trigger.next = 0
                yield delay(6)
                
    
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
test_data = [range(16)]

#Simulation
#arc_test_bench_inst = test_bench_arc(no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data)
#
arc = Arc.Arc(no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)
signal_trace = traceSignals(test_bench_arc,arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data)
simulation = Simulation(signal_trace)
simulation.run(300)
