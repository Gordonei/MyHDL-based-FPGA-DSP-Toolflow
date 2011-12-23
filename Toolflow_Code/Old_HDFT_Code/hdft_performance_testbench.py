#HDFT Performance Evaluation Test bench
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *
import sys,math,HDFT,DFT_Model

def Counter(clk,reset,enable,output,done,period,n):
    subcount = Signal(intbv(0,min=0,max=period+1))
    
    @always(clk.posedge,reset.posedge)
    def inc_logic():
        if(reset==1):
            output.next = 0
            done.next = 0
            subcount.next = 0
            
        elif((subcount<(period-1)) and (enable==0)):
            subcount.next = subcount + 1
            
        elif((output<(n-1)) and (enable==0)):
            output.next = output + 1
            subcount.next = 0
            
        elif(enable==1):
            done.next = 1
        
    return inc_logic

def rom(addr,output,content):
    @always_comb
    def rom_logic():
        output.next = content[addr]
        
    return rom_logic

def performance_test_bench(clk,reset,microsecound_count,testdata_real,input_bitsize,twiddle_bitsize,dft_size,dft_bitsize,output_bitsize):
    input_trigger = Signal(bool(1))
    output_line_real = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)))
    output_line_imag = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)))
    output_trigger = Signal(bool(0))
    output_enable = Signal(bool(1))
    
    #50 MHz clock
    @always(delay(10))
    def clock_driver():
      clk.next = not(clk)
      #if((clk==1) and (output_trigger==1)): print "%d - %d" % (now(),output_line_real)
      
    @instance
    def reset_pulse_logic():
        reset.next = 1
        yield delay(1)
        reset.next = 0
        input_trigger.next = 1
        output_enable.next = 1
        yield delay(1)
        
    #@always(output_trigger.posedge)
    @instance
    def detect_finish():
        yield output_trigger
        print "%d - done -> %d!" % (now(),microsecound_count)
        
    @instance
    def start_trigger():
        yield delay(5)
        input_trigger.next = 1
    
    hdft_tb_inst = hdft_test_bench(clk,reset,microsecound_count,input_trigger,output_line_real,output_line_imag,output_trigger,output_enable,testdata_real,input_bitsize,twiddle_bitsize,dft_size,dft_bitsize,output_bitsize)
    
    return instances()

def hdft_test_bench(clk,reset,microsecound_count,input_trigger,output_line_real,output_line_imag,output_trigger,output_enable,testdata_real,input_bitsize,twiddle_bitsize,dft_size,dft_bitsize,output_bitsize):
    input_line_real = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)))
    input_line_imag = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)))
    input_enable = Signal(bool(1))
    
    input_rom_signal = Signal(intbv(0,min=0,max=len(testdata_real)+1))
    input_done_flag = Signal(bool(0))
    performance_done_flag = Signal(bool(0))
    
    input_rom = rom(input_rom_signal,input_line_real,tuple(testdata_real))
    input_counter = Counter(clk,reset,output_trigger,input_rom_signal,input_done_flag,0,len(testdata_real))
    performance_counter = Counter(clk,reset,output_trigger,microsecound_count,performance_done_flag,50,256)
    
    no_inputs = len(testdata_real)
    no_outputs = no_inputs
    hdft_inst = HDFT.HDFT(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize,twiddle_bitsize,dft_bitsize,dft_size)
    hdft_logic_inst = hdft_inst.logic(input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,clk,reset)

    return instances()

print "Hybrid DFT Performance Evaluation Test Bench"
print "usage: python system_dev_testbench.py [input filename] [input bit width] [twiddle factor bit width] [DFT Size] [Multiplier input bit width] [Output bit width]"

input_file = open(sys.argv[1])
input_bitsize = int(sys.argv[2])
twiddle_bitsize = int(sys.argv[3])
dft_size = int(sys.argv[4])
dft_bitsize = int(sys.argv[5])
output_bitsize = int(sys.argv[6])

hdft_model = DFT_Model.HybridFFTDFT(input_file,"",input_bitsize,twiddle_bitsize,dft_size,dft_bitsize,output_bitsize)
hdft_model.readdata()

#test data read in from file
testdata_real = map(int,hdft_model.input_values_real)

clk = Signal(bool(0))
reset = Signal(bool(0))

microsecound_count = Signal(intbv(0)[8:])

signal_trace = traceSignals(performance_test_bench,clk,reset,microsecound_count,testdata_real,input_bitsize,twiddle_bitsize,dft_size,dft_bitsize,output_bitsize)
sim = Simulation(signal_trace)
sim.run(100000)

input_trigger = Signal(bool(1))
output_line_real = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)))
output_line_imag = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)))
output_trigger = Signal(bool(0))
output_enable = Signal(bool(1))
    
#toVerilog(hdft_test_bench,clk,reset,microsecound_count,input_trigger,output_line_real,output_line_imag,output_trigger,output_enable,testdata_real,input_bitsize,twiddle_bitsize,dft_size,dft_bitsize,output_bitsize)