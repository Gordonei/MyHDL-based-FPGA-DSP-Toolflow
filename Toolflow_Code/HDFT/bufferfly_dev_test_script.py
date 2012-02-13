'''
MyHDL-based FPGA DSP Toolflow
Test Script for Butterfly Class
Created on 8 Feb 2012

@author: Gordon Inggs
'''
from myhdl import *
import Butterfly, Arc
import math,random

def butterfly_conversion_testbench(clk,reset,butterfly,input_arc,output_arc_a,output_arc_b):
    butterfly_logic_inst = butterfly.processing()
    
    tf_rom_inst_real = butterfly.tf_rom_inst_real
    tf_rom_inst_imag = butterfly.tf_rom_inst_imag
    
    input_arc_receiving_inst = input_arc.receiving()
    input_arc_transmitting_inst = input_arc.transmitting()
    
    output_arc_a_receiving_inst = output_arc_a.receiving()
    output_arc_a_transmitting_inst = output_arc_a.transmitting()
    
    output_arc_b_receiving_inst = output_arc_b.receiving()
    output_arc_b_transmitting_inst = output_arc_b.transmitting()
    
    return instances()

def test_bench_butterfly(clk,butterfly,input_arc,output_arc_a,output_arc_b,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data):
    butterfly_inst = butterfly.logic()
    
    input_arc_inst = input_arc.logic()
    output_arc_a_inst = output_arc_a.logic()
    output_arc_b_inst = output_arc_b.logic()
    
    #clk = Signal(bool(0))
    @always(delay(1))
    def clock(): 
        clk.next = not(clk)
    
    @instance
    def actor_enable():
        yield delay(0)
        print "%d: Actors being enabled" % now()
        butterfly.enable.next = 1
        yield delay(5)
    
    @instance
    def input_arc_test():
        count = 0
        while((count*no_inputs)<len(test_data[0])):
            yield delay(1)
            if(not input_arc.input_stall):
                print "%d: Inputing %s starting at location %d" % (now(),str(test_data[0][count*no_inputs:count*no_inputs+no_inputs]),input_arc.input_index)
                for i in range(no_inputs): 
                    input_arc.buffer_real[input_arc.input_index+i].next = int(test_data[0][count*no_inputs+i].real)
                    input_arc.buffer_imag[input_arc.input_index+i].next = int(test_data[0][count*no_inputs+i].imag)
                    
                input_arc.input_trigger.next = 1
                count += 1
                yield delay(1)
                input_arc.input_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Input Stalled" % now()
                
            #else: print "%d:Input Stalled" % now()
       
    @instance 
    def output_arc_a_test():
        count = 0
        output_data = []
        while((count*no_inputs)<len(test_data[0])):
            yield delay(1)
            if(not output_arc_a.output_stall):
                output_arc_a.output_trigger.next = 1
                print "%d: Outputting 1 real %s starting at location %d" % (now(),str(output_arc_a.buffer_real[output_arc_a.output_index:output_arc_a.output_index+no_outputs]),output_arc_a.output_index)
                print "%d: Outputting 1 complex %s starting at location %d" % (now(),str(output_arc_a.buffer_imag[output_arc_a.output_index:output_arc_a.output_index+no_outputs]),output_arc_a.output_index)
                for i in range(no_outputs): output_data.append(int(output_arc_a.buffer_real[output_arc_a.output_index+i])+1j*int(output_arc_a.buffer_imag[output_arc_a.output_index+i]))
                #output_data.extend(map(int,output_arc_a.buffer_real[output_arc_a.output_index:output_arc_a.output_index+no_outputs]))    
                count += 1
                yield delay(1)
                output_arc_a.output_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Output 1 Stalled" % now()
                
        print "Checking data for output 1"
        model_test_data = butterfly.model(test_data[0])[0]
        #print model_test_data
        for i in range(min(len(model_test_data),len(output_data))):
            if(output_data[i]!=model_test_data[i]):
                print "%d - %d %dj should be %d %dj" % (i,output_data[i].real,output_data[i].imag,model_test_data[i].real,model_test_data[i].imag)
                
            #else: print "%d: Output Stalled" % now()
            
    @instance 
    def output_arc_b_test():
        count = 0
        output_data = []
        while((count*no_inputs)<len(test_data[0])):
            yield delay(1)
            if(not output_arc_b.output_stall):
                output_arc_b.output_trigger.next = 1
                print "%d: Outputting 2 real %s starting at location %d" % (now(),str(output_arc_b.buffer_real[output_arc_b.output_index:output_arc_b.output_index+no_outputs]),output_arc_b.output_index)
                print "%d: Outputting 2 complex %s starting at location %d" % (now(),str(output_arc_b.buffer_imag[output_arc_b.output_index:output_arc_b.output_index+no_outputs]),output_arc_b.output_index)
                for i in range(no_outputs): output_data.append(int(output_arc_b.buffer_real[output_arc_b.output_index+i])+1j*int(output_arc_b.buffer_imag[output_arc_b.output_index+i]))
                count += 1
                yield delay(1)
                output_arc_b.output_trigger.next = 0
                #yield delay(1)
                
            else: print "%d: Output 2 Stalled" % now()
                
        print "Checking data for output 2"
        model_test_data = butterfly.model(test_data[0])[1]
        for i in range(min(len(model_test_data),len(output_data))):
           if(output_data[i]!=model_test_data[i]):
               print "%d - %d %dj should be %d %dj" % (i,output_data[i].real,output_data[i].imag,model_test_data[i].real,model_test_data[i].imag)
            #else: print "%d: Output Stalled" % now()
    
    return instances()

no_inputs = 1024
input_bitwidth = 8

tf_bitwidth = 8

no_outputs = no_inputs/2
output_bitwidth = input_bitwidth+tf_bitwidth+1

actor_scale = 1


complex_valued = True
size_factor = 1

#Simulation Parameters
test_set_size = 1
#test_data = [range(no_inputs*no_outputs*test_set_size)]

temp = []
for td in range(max(no_outputs,no_inputs)*test_set_size): 
    temp.append(int(random.random()*2**(input_bitwidth-1))+1j*int(random.random()*2**(input_bitwidth-1)))
    
#tf_real = [intbv(int(random.random()*2**(tf_bitwidth-1)),min=-2**(tf_bitwidth-1),max=2**(tf_bitwidth-1)) for i in range(tf_bitwidth-1)]
#tf_imag = [intbv(int(random.random()*2**(tf_bitwidth-1)),min=-2**(tf_bitwidth-1),max=2**(tf_bitwidth-1)) for i in range(tf_bitwidth-1)]
tf_real = []#intbv(0)[no_outputs*tf_bitwidth:0]
tf_imag = []#intbv(0)[no_outputs*tf_bitwidth:0]
for i in range(no_outputs):
    #tf_real[tf_bitwidth*i+tf_bitwidth:tf_bitwidth*i] = int(random.random()*2**(tf_bitwidth-1))#intbv(int(random.random()*2**(tf_bitwidth-1)),min=-2**(tf_bitwidth-1),max=2**(tf_bitwidth-1))
    #tf_imag[tf_bitwidth*i+tf_bitwidth:tf_bitwidth*i] = int(random.random()*2**(tf_bitwidth-1))# intbv(int(random.random()*2**(tf_bitwidth-1)),min=-2**(tf_bitwidth-1),max=2**(tf_bitwidth-1))
    tf_real.append(int(random.random()*2**(tf_bitwidth-1)))
    tf_imag.append(int(random.random()*2**(tf_bitwidth-1)))
    
tf_real = tuple(tf_real)
tf_imag = tuple(tf_imag)
   
#tf_real = map(int,tf_real)
#tf_imag = map(int,tf_imag)

test_data = []
test_data.append(temp)

reset = Signal(bool(False))
input_arc = Arc.Arc(reset,no_inputs,input_bitwidth,no_inputs,input_bitwidth,complex_valued,size_factor)
output_arc_a = Arc.Arc(reset,no_outputs,output_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)
output_arc_b = Arc.Arc(reset,no_outputs,output_bitwidth,no_outputs,output_bitwidth,complex_valued,size_factor)

clk = Signal(bool(False))
butterfly = Butterfly.Butterfly(clk,input_arc,output_arc_a,output_arc_b,tf_real,tf_imag,tf_bitwidth)

#Simulation
#signal_trace = traceSignals(test_bench_butterfly, clk, butterfly, input_arc,output_arc_a,output_arc_b,no_inputs,input_bitwidth,no_outputs,output_bitwidth,complex_valued,test_data)
#simulation = Simulation(signal_trace)
#simulation.run(50)

#Conversion
verilog_inst = toVerilog(butterfly_conversion_testbench,clk,reset,butterfly,input_arc,output_arc_a,output_arc_b)