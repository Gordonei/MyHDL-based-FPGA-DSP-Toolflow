'''
MyHDL-based FPGA DSP Toolflow
Test Script for Arc Base Class
Created on 23 Dec 2011

@author: Gordon Inggs
'''
from myhdl import *
import Arc,random

def test_bench_arc(reset,arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,verbose):
    
    arc_logic_inst = arc.logic()
    
    write_delay = 1
    
    @instance
    def arc_write_test():
        count = 0
        yield delay(write_delay)
        while(count*no_inputs<len(test_data[0])):
            
            yield delay(1)
            if(not arc.input_stall):
                arc.input_trigger.next = 1
                #yield delay(1)
                #if(not arc.input_stall):
                for i in range(no_inputs): arc.buffer_real[arc.input_index+i].next = test_data[0][count*no_inputs+i]
                    
                if(verbose): print "%d: Inputing %s at location %d - %s" % (now(),str(test_data[0][count*no_inputs:count*no_inputs+no_inputs]),arc.input_index,str(map(int,arc.buffer_real)))
                count += 1
                
                yield delay(1)
                arc.input_trigger.next = 0
                
            else:
                if(verbose): print "%d: Input Stalled" % now()
            
                
    @instance
    def arc_read_test():
        count = 0
        output_data = []
        while(count*no_outputs<len(test_data[0])):
            yield delay(1)
            if(not arc.output_stall):
                arc.output_trigger.next = 1
                #yield delay(1)
                #if(not arc.output_stall):
                if(verbose): print "%d: Outputting %s from location %d - %s" % (now(),str(map(int,arc.buffer_real[arc.output_index:arc.output_index+no_outputs])),arc.output_index,str(map(int,arc.buffer_real)))
                output_data.extend(map(int,arc.buffer_real[arc.output_index:arc.output_index+no_outputs]))
                count += 1
                    
                yield delay(1)
                arc.output_trigger.next = 0
                
            else:
                if(verbose): print "%d: Output Stalled" % now()
                
        
        error = False
        for i in range(min(len(test_data[0]),len(output_data))):
            if(output_data[i]!=test_data[0][i]):
                if(not error): print "problem with input size %d, ouput size %d and size factor %d" % (no_inputs,no_outputs,arc.size_factor)
                error = True
                if(verbose): print "%d - %d should be %d" % (i,output_data[i],test_data[0][i])
                
    
    """clk = Signal(bool(0))            
    @always(delay(5))
    def clk_driver():
        clk.next = not(clk)"""
                
    return instances()

input_range = range(1,11)
output_range = range(1,11)
size_factor_range = range(1,11)

#Simulation Parameters
test_set_size = 100
verbose = False

test_count = 1
for i_r in input_range:
    for o_r in output_range:
        for s_f in size_factor_range:
            print "Test %d: no_inputs=%d no_outputs=%d size_factor=%d:" % (test_count,i_r,o_r,s_f)
            test_count = test_count +1
            
            #Arc Parameters
            no_inputs = i_r
            input_bitwidth = 8

            no_outputs = o_r
            output_bitwidth = 8
    
            complex_valued = False
            size_factor = s_f

            temp = []
            for td in range(no_outputs*no_inputs*test_set_size): temp.append(int(random.random()*100))

            test_data = []
            test_data.append(temp)

            reset = Signal(bool(0))

            #Simulation
            #arc_test_bench_inst = test_bench_arc(no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data)
            #
            arc = Arc.Arc(reset,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)
            #signal_trace = traceSignals(test_bench_arc,reset,arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,verbose)
            test_bench = test_bench_arc(reset,arc,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data,verbose)
            simulation = Simulation(test_bench)
            simulation.run()
            print "\n"
