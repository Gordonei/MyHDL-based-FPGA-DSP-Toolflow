#System Development Test bench
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
from myhdl import *
import HDFT,DFT_Model,sys

def test_bench_hdft(hdft_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,clk,reset,outputdata_real,outputdata_imag,testdata_real,testdata_imag):
  hdft_logic_inst = hdft_inst.logic()
  
  @always(delay(5))
  def clock_driver():
      clk.next = not(clk)
      #print "%d: clock value - %d" % (now(),clk)
      
  @instance
  def reset_pulse_logic():
    reset.next = 1
    #print now()
    yield delay(1)
    #print now()
    reset.next = 0
    yield delay(1)
    #print now()
    
  input_count = Signal(intbv(0))
  input_set_count = Signal(intbv(0))
  transmit_flag = Signal(bool(0))
  done = Signal(bool(0))
  
  @always(clk.posedge,reset.posedge)
  def input_logic():
    #yield delay(int(1*random.random())+1)
    if(reset):
      input_count.next = 0
      input_set_count.next = 0
    
    else:
	#print "inputing set %d" % input_set_count
	#input_trigger.next = 0
      if(transmit_flag or input_enable and not(done)):
	if(not(transmit_flag)):
	  transmit_flag.next = 1
	  input_trigger.next = 1
	
	elif((input_count<(len(testdata_real[input_set_count]))) and (input_set_count<(len(testdata_real)))):
	  #print "%d: input logic - %d" % (now(),input_count)
	  input_line_real.next = testdata_real[input_set_count][input_count]
	  input_line_imag.next = testdata_imag[input_set_count][input_count]
	  input_count.next = input_count + 1
	
	elif((input_set_count<(len(testdata_real)-1))):
	  transmit_flag.next = 0
	  input_trigger.next = 0
	  input_count.next = 0
	  input_set_count.next = input_set_count + 1
	  
	else:
	  transmit_flag.next = 0
	  input_trigger.next = 0
	  done.next = 1
	
      else:
	input_trigger.next = 0
	
  output_count = Signal(intbv(0))
  output_set_count = Signal(intbv(0))
  outputdata_real.append([])
  outputdata_imag.append([])
  receive_flag = Signal(bool(0))
  
  no_output_values = len(testdata_real[output_set_count])
  no_output_value_sets = len(testdata_real)
	  
  @always(clk.posedge)
  def output_logic():
    if(output_set_count<(no_output_value_sets)):
      output_enable.next = 1
	
    else:
      output_enable.next = 0
      
    if(output_trigger and (output_set_count<no_output_value_sets)):
      receive_flag.next = 1
      
    if(receive_flag):
      #print "%d: output logic - %d" % (now(),output_count)
	
      outputdata_real[-1].append(intbv(int(output_line_real)))
      outputdata_imag[-1].append(intbv(int(output_line_imag)))
	
      if(output_count<(no_output_values-1)):
	output_count.next = output_count + 1
	
      else:
	receive_flag.next = 0
	output_count.next = 0
	output_set_count.next = output_set_count + 1
	    
	if(output_set_count<(no_output_value_sets-1)):
	  outputdata_real.append([])
	  outputdata_imag.append([])
  
  return instances()
    
def writedata(output_file,output_values_real,output_values_imag):
    for i in range(len(output_values_real)):
      for j in range(len(output_values_real[i])):
	output_file.write("%d %d\n"% (output_values_real[i][j],output_values_imag[i][j]))
	
def HDFT_Verilog(sut,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset):
  #sut_inst_logic = sut.logic()
  sut_dac_receive_logic = [d.receiving() for d in sut.dacs]
  sut_dac_processing_logic = [d.processing() for d in sut.dacs]
  sut_dac_transmiting_logic = [d.transmiting() for d in sut.dacs]
  sut_dac_twiddle_rom_real_logic = [d.rom(d.twiddle_rom_line_real,d.twiddle_rom_addr_real,d.tf_real) for d in sut.dacs]
  sut_dac_twiddle_rom_imag_logic = [d.rom(d.twiddle_rom_line_real,d.twiddle_rom_addr_real,d.tf_real) for d in sut.dacs]
  
  twiddle_rom_real_inst = self.rom(self.twiddle_rom_line_real,self.twiddle_rom_addr_real,self.tf_real)
  twiddle_rom_imag_inst = self.rom(self.twiddle_rom_line_imag,self.twiddle_rom_addr_imag,self.tf_imag)
  
  sut_mux_receive_logic = sut.mux.receiving()
  sut_mux_processing_logic = sut.mux.processing()
  sut_mux_transmiting_logic = sut.mux.transmiting()
  
  sut_dft_receiving_logic = sut.dft.receiving()
  sut_dft_processing_logic = sut.dft.processing()
  sut_dft_transmiting_logic = sut.dft.transmiting()
  
  sut_unscrambler_receiving_logic = sut.unscrambler.receiving()
  sut_unscrambler_processing_logic = sut.unscrambler.processing()
  sut_unscrambler_transmiting_logic = sut.unscrambler.transmiting()
  
  return instances()
    
print "Hybrid DFT System model"
print "usage: python system_dev_testbench.py [input filename] [output filename] [input bit width] [twiddle factor bit width] [DFT Size] [Multiplier input bit width] [Output bit width]"

input_file = open(sys.argv[1])
output_file = open(sys.argv[2],"w")
input_bitsize = int(sys.argv[3])
twiddle_bitsize = int(sys.argv[4])
dft_size = int(sys.argv[5])
dft_bitsize = int(sys.argv[6])
output_bitsize = int(sys.argv[7])

hdft_model = DFT_Model.HybridFFTDFT(input_file,output_file,input_bitsize,twiddle_bitsize,dft_size,dft_bitsize,output_bitsize)
hdft_model.readdata()

#test data read in from file
testdata_real = [hdft_model.input_values_real]
testdata_imag = [hdft_model.input_values_imag]

no_inputs = len(testdata_real[0])
no_outputs = no_inputs

#test signals
input_line_real = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)))
input_line_imag = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)))
input_trigger = Signal(bool(0))
input_enable = Signal(bool(1))

output_line_real = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)))
output_line_imag = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)))
output_trigger = Signal(bool(0))
output_enable = Signal(bool(1))

clk = Signal(bool(0))
reset = Signal(bool(0))

#HDFT object instance and reference data generated by model
hdft_inst = HDFT.HDFT(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize=input_bitsize,output_bitsize=output_bitsize,twiddle_bitsize=twiddle_bitsize,multiplier_bitsize=dft_bitsize,dft_size=dft_size)
#refdata = hdft_inst.model(testdata_real[0],testdata_imag[0])
#refdata_real = refdata[0]
#refdata_imag = refdata[1]

#lists for holding output from model
outputdata_real = []
outputdata_imag = []

#Simulation object
"""signal_trace = traceSignals(test_bench_hdft,hdft_inst=hdft_inst,input_line_real=input_line_real,input_line_imag=input_line_imag,input_trigger=input_trigger,input_enable=input_enable,output_line_real=output_line_real,output_line_imag=output_line_imag,output_trigger=output_trigger,output_enable=output_enable,testdata_real=testdata_real,testdata_imag=testdata_imag,outputdata_real=outputdata_real,outputdata_imag=outputdata_imag,reset=reset,clk=clk)
sim = Simulation(signal_trace)
sim.run(100000)

print len(outputdata_real[0])

writedata(output_file,outputdata_real,outputdata_imag)"""

#Conversion to Verilog
#toVerilog(HDFT_Verilog,hdft_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset)
toVerilog(HDFT.HDFT.logic,hdft_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,clk,reset)