'''
MyHDL-based FPGA DSP Toolflow
Test Script for Systems
Created on 29 August 2012

@author: Gordon Inggs
'''
from myhdl import *
import Actor, Arc
import random

def serial_loader(clk,enable,reset,input_line,arc):
    
    count = Signal(intbv(0,min=0,max=arc.no_inputs+1))
    no_inputs = arc.no_inputs
    input_trigger = arc.input_trigger
    buffer_real = arc.buffer_real
    
    @always(clk.posedge,reset.posedge)
    def serial_loader_behaviour():
        if(reset==True):
            count.next = 0
        
        elif(enable==True and count<(no_inputs)):
            buffer_real[count].next = input_line
            count.next = count + 1
            
        elif(enable==True and count==no_inputs):
            input_trigger.next = True
            
        else: input_trigger.next = False
    
    return serial_loader_behaviour

def datasource(clk,enable,reset,output_line,dataset):
    
    count = Signal(intbv(0,min=0,max=len(dataset)+1))
    
    @always(clk.posedge,reset.posedge)
    def datasource_behaviour():
        if(reset==True):
            count.next = 0
            
        elif(enable==True):
            output_line.next = dataset[count]
            if(count<(len(dataset)-1)): count.next = count+1
        
    return datasource_behaviour

def datachecker(clk,enable,reset,input_line,correct,arc):
    test_data = [Signal(intbv(0,min=-2**(arc.output_bitwidth-1),max=2**(arc.output_bitwidth-1))) for i in range(arc.size)]
    count = Signal(intbv(0,min=0,max=arc.size+1))
    data_correct = Signal(bool(True))
    
    arc_size = arc.size
    output_stall = arc.output_stall
    output_trigger = arc.output_trigger
    buffer_real = arc.buffer_real
    no_inputs = arc.no_inputs
    
    @always(clk.posedge,reset.posedge)
    def datachecker_behaviour():
        if(reset==True):
            for t_d in range(arc_size): test_data[t_d].next = 0
            data_correct.next = True
            
        elif(enable and count<arc_size):
            test_data[count].next = input_line
            count.next = count+1
            data_correct.next = True
            
        elif(enable and output_stall==False):
            output_trigger.next = True
            for t_d in range(int(arc_size)):
                if(test_data[t_d]!=buffer_real[t_d]):
                    data_correct.next = False
                    
        else:
            correct.next = data_correct
            output_trigger.next = False
        
    return datachecker_behaviour

def system_test_bench(clk,enable,reset,data_correct,arc,test_data):
    arc_receiving_inst = arc.receiving()
    arc_transmitting_inst = arc.transmitting()
    
    data_line = Signal(intbv(0,min=-2**(arc.input_bitwidth-1),max=2**(arc.input_bitwidth-1)))
    
    datasource_inst = datasource(clk,enable,reset,data_line,test_data)
    serial_loader_inst = serial_loader(clk,enable,reset,data_line,arc)
    datachecker_inst = datachecker(clk,enable,reset,data_line,data_correct,arc)
    
    return instances()
    
def system_test_bench_sim(no_inputs,input_bitwidth,no_outputs,output_bitwidth):
    clk = Signal(bool(False))
    enable = Signal(bool(False))
    reset = Signal(bool(False))
    data_correct = Signal(bool(False))
    
    arc = Arc.Arc(reset,no_inputs,input_bitwidth,no_outputs,output_bitwidth,False,1)
    test_data = [int(random.random()*255)-128 for i in range(no_inputs)]
    
    @always(delay(1))
    def clock(): 
        clk.next = not(clk)
        
    @instance
    def actor_enable():
        yield delay(1)
        enable.next = True
        yield delay(1)
        
    @always(data_correct.posedge)
    def data_correct_check():
        print "Data Correct Signal Detected!"
    
    system_test_bench_inst = system_test_bench(clk,enable,reset,data_correct,arc,test_data)
    
    return instances()
    
no_inputs = 128
input_bitwidth = 8
no_outputs = 128
output_bitwidth = 8
    
system_test_bench_sim_inst = system_test_bench_sim(no_inputs,input_bitwidth,no_outputs,output_bitwidth)
simulation = Simulation(system_test_bench_sim_inst)
simulation.run(100)

clk = Signal(bool(False))
enable = Signal(bool(False))
reset = Signal(bool(False))
data_correct = Signal(bool(False))

arc = Arc.Arc(reset,no_inputs,input_bitwidth,no_outputs,output_bitwidth,False,1)

test_data = tuple([int(random.random()*255)-128 for i in range(no_inputs)])

verilog_inst = toVerilog(system_test_bench,clk,enable,reset,data_correct,arc,test_data)