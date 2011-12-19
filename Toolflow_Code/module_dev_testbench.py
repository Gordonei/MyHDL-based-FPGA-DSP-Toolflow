#Module Development Test bench
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#March 2011
import sys,inspect,random,DFT_Model,numpy
from myhdl import *

def test_bench_actor(cut,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset,testdata_real,testdata_imag,outputdata_real,outputdata_imag,refdata_real,refdata_imag,clk,input_bitsize,output_bitsize,tf_real=(),tf_imag=(),index_mapping=(),multiplier_bitsize=0,twiddle_factor_bitsize=0):
  line_delay = 0
  interconnect_line_real = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay)
  interconnect_line_imag = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay)
  interconnect_trigger = Signal(bool(0))
  interconnect_enable = Signal(bool(1))
  
  if(tf_real) :
    cut_inst_1 = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,tf_real,tf_imag,input_bitsize,output_bitsize,multiplier_bitsize,twiddle_factor_bitsize)
    cut_logic_inst = cut_inst_1.logic(input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset)
    
  elif(index_mapping):
    cut_inst_1 = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,index_mapping,input_bitsize,output_bitsize,)
    cut_logic_inst = cut_inst_1.logic()
  
  else:
    cut_inst_1 = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,interconnect_line_real,interconnect_line_imag,interconnect_trigger,interconnect_enable,no_outputs,reset,clk,input_bitsize,output_bitsize)
    cut_inst_2 = cut(interconnect_line_real,interconnect_line_imag,interconnect_trigger,interconnect_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize)
    cut_logic_inst = cut_inst_1.logic()
    cut_logic_inst_2 = cut_inst_2.logic()
  
  
  @always(delay(5))
  def clock_driver():
      clk.next = not(clk)
  
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
	  print "%d: input logic - %d" % (now(),input_count)
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
	  
      #else:
	#input_trigger.next = 0
	#transmit_flag.next = 1
	    #print "%d: inputing set %d value no %d - %d" % (now(),input_set_count,input_count,testdata_real[input_set_count][input_count])
  
  output_count = Signal(intbv(0))
  output_set_count = Signal(intbv(0))
  outputdata_real.append([])
  outputdata_imag.append([])
  receive_flag = Signal(bool(0))
  
  no_output_values = len(testdata_real[output_set_count])
  no_output_value_sets = len(testdata_real)
  
  if(index_mapping):
    no_output_values = no_output_values*no_output_value_sets
    no_output_value_sets = 1
  
  @always(clk.posedge)
  def output_logic():
    if(output_set_count<(no_output_value_sets)):
	#print "enable"
      output_enable.next = 1
	#output_enable_2.next = 1
	
    else:
      output_enable.next = 0
      
    if(output_trigger and (output_set_count<no_output_value_sets)):
      receive_flag.next = 1
      
    if(receive_flag):
      print "%d: output logic - %d" % (now(),output_count)
	#print "output - %d" % output_line_real
	#output_enable.next = 1
	#output_enable_2.next = 0
	
      outputdata_real[-1].append(intbv(int(output_line_real)))
      outputdata_imag[-1].append(intbv(int(output_line_imag)))
	#outputdata_real_2[-1].append(intbv(int(output_line_real_2)))
        #outputdata_imag_2[-1].append(intbv(int(output_line_imag_2)))
	
      if(output_count<(no_output_values-1)):
	output_count.next = output_count + 1
	  #yield delay(int(1*random.random())+1)
	
      else:
	receive_flag.next = 0
	output_count.next = 0
	output_set_count.next = output_set_count + 1
	  #yield delay(int(1*random.random())+1)
	  #print now()
	  #print output_set_count
	  #if(output_set_count==(len(testdata_real))):
	    #break
	    
	if(output_set_count<(no_output_value_sets-1)):
	  outputdata_real.append([])
	  outputdata_imag.append([])
	    #outputdata_real_2.append([])
	    #outputdata_imag_2.append([])
	    

  refdata = cut_inst_1.model(testdata_real,testdata_imag)
  if(not(tf_real) and not(index_mapping)): refdata = cut_inst_2.model(refdata[0],refdata[1])
  
  for rf in refdata[0]: refdata_real.append(rf)
  #refdata_real_2 = refdata[2]
  for rf in refdata[1]: refdata_imag.append(rf)
  #refdata_imag_2 = refdata[3]
  
  print tf_real
  print tf_imag
  
  return instances()
  
def test_bench_mux(cut,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset,testdata_real,testdata_imag,outputdata_real,outputdata_imag,refdata_real,refdata_imag,clk,input_bitsize,output_bitsize,no_input_lines):
  line_delay = 0
  
  cut_inst_1 = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,no_input_lines,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize)
  
  cut_logic_inst = cut_inst_1.logic()
  
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
      if(transmit_flag or input_enable[input_set_count] and not(done)):
	if(not(transmit_flag)):
	  transmit_flag.next = 1
	  input_trigger[input_set_count].next = 1
	
	elif((input_count<(len(testdata_real[input_set_count]))) and (input_set_count<(len(testdata_real)))):
	  print "%d: input logic - %d" % (now(),input_count)
	  input_line_real[input_set_count].next = testdata_real[input_set_count][input_count]
	  input_line_imag[input_set_count].next = testdata_imag[input_set_count][input_count]
	  input_count.next = input_count + 1
	
	elif((input_set_count<(len(testdata_real)-1))):
	  transmit_flag.next = 0
	  input_trigger[input_set_count].next = 0
	  input_count.next = 0
	  input_set_count.next = input_set_count + 1
	  
	else:
	  transmit_flag.next = 0
	  input_trigger[input_set_count].next = 0
	  done.next = 1
	
      else:
	input_trigger[input_set_count].next = 0
	  
      #else:
	#input_trigger.next = 0
	#transmit_flag.next = 1
	    #print "%d: inputing set %d value no %d - %d" % (now(),input_set_count,input_count,testdata_real[input_set_count][input_count])
  
  output_count = Signal(intbv(0))
  output_set_count = Signal(intbv(0))
  outputdata_real.append([])
  outputdata_imag.append([])
  receive_flag = Signal(bool(0))
  
  @always(clk.posedge)
  def output_logic():
    if(output_set_count<(len(testdata_real))):
	#print "enable"
      output_enable.next = 1
	#output_enable_2.next = 1
	
    else:
      output_enable.next = 0
      
    if(output_trigger and (output_set_count<len(testdata_real))):
      receive_flag.next = 1
      
    if(receive_flag):
      print "%d: output logic - %d" % (now(),output_count)
	#print "output - %d" % output_line_real
	#output_enable.next = 1
	#output_enable_2.next = 0
	
      outputdata_real[-1].append(intbv(int(output_line_real)))
      outputdata_imag[-1].append(intbv(int(output_line_imag)))
	#outputdata_real_2[-1].append(intbv(int(output_line_real_2)))
        #outputdata_imag_2[-1].append(intbv(int(output_line_imag_2)))
	
      if(output_count<(len(testdata_real[output_set_count])-1)):
	output_count.next = output_count + 1
	  #yield delay(int(1*random.random())+1)
	
      else:
	receive_flag.next = 0
	output_count.next = 0
	output_set_count.next = output_set_count + 1
	  #yield delay(int(1*random.random())+1)
	  #print now()
	  #print output_set_count
	  #if(output_set_count==(len(testdata_real))):
	    #break
	    
	if(output_set_count<(len(testdata_real)-1)):
	  outputdata_real.append([])
	  outputdata_imag.append([])
	    #outputdata_real_2.append([])
	    #outputdata_imag_2.append([])
	    

  refdata = cut_inst_1.model(testdata_real,testdata_imag)
  
  for rf in refdata[0]: refdata_real.append(rf)
  #refdata_real_2 = refdata[2]
  for rf in refdata[1]: refdata_imag.append(rf)
  #refdata_imag_2 = refdata[3]
  
  return instances()
  
def test_bench_dac(cut,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset,testdata_real,testdata_imag,outputdata_real,outputdata_imag,outputdata_real_2,outputdata_imag_2,refdata_real,refdata_imag,clk,output_line_real_2,output_line_imag_2,output_trigger_2,output_enable_2,refdata_real_2,refdata_imag_2,tf_real,tf_imag,twiddle_bits,input_bitsize,output_bitsize,output_bitsize_2):
  line_delay = 0
  
  no_outputs = no_inputs/2
  no_outputs_2 = no_outputs
  cut_inst_1 = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,output_line_real_2,output_line_imag_2,output_trigger_2,output_enable_2,no_outputs_2,reset,clk,twiddle_bits,tf_real,tf_imag,input_bitsize,output_bitsize,output_bitsize_2)
		  #(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,output_line_real_2,output_line_imag_2,output_trigger_2,output_enable_2,no_outputs_2,reset,clk,twiddle_bits=0,tf_real=[],tf_imag=[],input_bitsize=0,output_bitsize=0,output_bitsize_2=0)
  cut_logic_inst = cut_inst_1.logic()
  
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
	  print "%d: input logic - %d" % (now(),input_count)
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
	  
      #else:
	#input_trigger.next = 0
	#transmit_flag.next = 1
	    #print "%d: inputing set %d value no %d - %d" % (now(),input_set_count,input_count,testdata_real[input_set_count][input_count])
  
  output_count = Signal(intbv(0))
  output_set_count = Signal(intbv(0))
  outputdata_real.append([])
  outputdata_imag.append([])
  receive_flag = Signal(bool(0))
  output_delay = Signal(intbv((int(random.random()*6)+10)))
  #output_trigger_2.next = 1
  
  @always(clk.posedge)
  def output_logic():
    if((output_set_count<(len(testdata_real))) and (output_delay==0)):
	#print "enable"
      output_enable.next = 1
      output_delay.next = int(random.random()*6) + 10
	#output_enable_2.next = 1
	
    else:
      #output_enable.next = 0
      output_delay.next = output_delay - 1
      
    if(output_trigger and (output_set_count<len(testdata_real))):
      receive_flag.next = 1
      
    if(receive_flag):
      print "%d: output logic - %d" % (now(),output_count)
	#print "output - %d" % output_line_real
	#output_enable.next = 1
	#output_enable_2.next = 0
	
      outputdata_real[-1].append(intbv(int(output_line_real)))
      outputdata_imag[-1].append(intbv(int(output_line_imag)))
	
      if(output_count<(len(testdata_real[output_set_count])/2-1)):
	output_count.next = output_count + 1
	  #yield delay(int(1*random.random())+1)
	
      else:
	receive_flag.next = 0
	output_count.next = 0
	output_set_count.next = output_set_count + 1
	output_enable.next = 0
	  #yield delay(int(1*random.random())+1)
	  #print now()
	  #print output_set_count
	  #if(output_set_count==(len(testdata_real))):
	    #break
	    
	if(output_set_count<(len(testdata_real)-1)):
	  outputdata_real.append([])
	  outputdata_imag.append([])
  
  output_count_2 = Signal(intbv(0))
  output_set_count_2 = Signal(intbv(0))
  outputdata_real_2.append([])
  outputdata_imag_2.append([])
  receive_flag_2 = Signal(bool(0))
  output_delay_2 = Signal(intbv((int(random.random()*6)+5)))


  @always(clk.posedge)
  def output_logic_2():
    if(output_set_count_2<(len(testdata_real)) and (output_delay_2==0)):
      output_enable_2.next = 1
      output_delay_2.next = int(random.random()*5) + 10
	
    else:
      output_delay_2.next = output_delay_2 - 1
      #output_enable_2.next = 0
      
    if(output_trigger_2 and (output_set_count_2<len(testdata_real))):
      receive_flag_2.next = 1
      
    if(receive_flag_2):
      outputdata_real_2[-1].append(intbv(int(output_line_real_2)))
      outputdata_imag_2[-1].append(intbv(int(output_line_imag_2)))
	
      if(output_count_2<(len(testdata_real[output_set_count_2])/2-1)):
	output_count_2.next = output_count_2 + 1
	
      else:
	receive_flag_2.next = 0
	output_count_2.next = 0
	output_set_count_2.next = output_set_count_2 + 1
	output_enable_2.next = 0
	    
	if(output_set_count_2<(len(testdata_real)-1)):
	  outputdata_real_2.append([])
	  outputdata_imag_2.append([])

  refdata = cut_inst_1.model(testdata_real,testdata_imag)
  
  for rf in refdata[0]: refdata_real.append(rf)
  for rf in refdata[2]: refdata_real_2.append(rf)
  for rf in refdata[1]: refdata_imag.append(rf)
  for rf in refdata[3]: refdata_imag_2.append(rf)
  
  return instances()

def VerilogVersion(cut,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset,output_line_real_2=None,output_line_imag_2=None,output_trigger_2=None,output_enable_2=None,cut2=None):
  #cut_inst_logic = cut.logic()
  cut_receive_inst = cut.receiving()
  cut_transmit_inst = cut.transmiting()
  cut_process_inst = cut.processing()
  if(cut2):
    #cut2_inst_logic = cut2.logic()
    cut2_receive_inst = cut2.receiving()
    cut2_transmit_inst = cut2.transmiting()
    cut2_process_inst = cut2.processing()
  
  return instances()

module_name = sys.argv[1]

mut = __import__(module_name)

for m in inspect.getmembers(mut):
  if(m[0]==module_name):
    cut = m[1]

print ("Working with class \"%s\"" % cut.name) #Print Class name
#cut_inst = cut(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)

no_inputs = int(sys.argv[2]) #number of samples in a set
input_bitsize = 16
frequency  = 2*numpy.pi/10

input_sets = int(sys.argv[3])
testdata_real = [[int(numpy.sin(frequency*i/((j+1)*10))*2**(input_bitsize-1)) for i in range(no_inputs)] for j in range(input_sets)]
testdata_imag = [[0 for i in range(no_inputs)] for j in range(input_sets)]

#print testdata_real

outputdata_real = []
outputdata_imag = []

no_input_lines = len(testdata_real) 

#line_delay = int(random.random()*1)+1
line_delay = 0

input_line_real = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay) #Input signals
input_line_imag = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay)
input_trigger = Signal(bool(0),delay=line_delay)
input_enable = Signal(bool(1),delay=line_delay)

#no_outputs = len(testdata_real[0])#Output parameters
no_outputs = len(testdata_real[0])#Output parameters
#no_outputs_2 = len(testdata[0])/2
output_bitsize = 16+36
#output_bitsize_2 = 16
  
output_line_real = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)),delay=line_delay) #Output signals
output_line_imag = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)),delay=line_delay)
output_trigger = Signal(bool(0),delay=line_delay)
output_enable = Signal(bool(1),delay=line_delay)

reset = Signal(bool(0))
clk = Signal(bool(0))
index_mapping = []


#print index_mapping
#index_mapping = tuple(range(no_inputs-1,-1,-1))

refdata_real = []
refdata_imag = []

if(sys.argv[1]=="Actor"):
  signal_trace = traceSignals(test_bench_actor,cut=cut,input_line_real=input_line_real,input_line_imag=input_line_imag,input_trigger=input_trigger,input_enable=input_enable,output_line_real=output_line_real,output_line_imag=output_line_imag,output_trigger=output_trigger,output_enable=output_enable,testdata_real=testdata_real,testdata_imag=testdata_imag,outputdata_real=outputdata_real,outputdata_imag=outputdata_imag,reset=reset,refdata_real=refdata_real,refdata_imag=refdata_imag,clk=clk,input_bitsize=input_bitsize,output_bitsize=output_bitsize)
  
if(sys.argv[1]=="Unscrambler"):
  no_outputs = no_inputs*input_sets
  
  source_list = range(no_outputs)
  for i in range(no_outputs): index_mapping.append(source_list.pop(int(random.random()*(len(source_list)-1))))
  index_mapping = tuple(index_mapping)
  
  print testdata_real
  print index_mapping
  signal_trace = traceSignals(test_bench_actor,cut=cut,input_line_real=input_line_real,input_line_imag=input_line_imag,input_trigger=input_trigger,input_enable=input_enable,output_line_real=output_line_real,output_line_imag=output_line_imag,output_trigger=output_trigger,output_enable=output_enable,testdata_real=testdata_real,testdata_imag=testdata_imag,outputdata_real=outputdata_real,outputdata_imag=outputdata_imag,reset=reset,refdata_real=refdata_real,refdata_imag=refdata_imag,clk=clk,input_bitsize=input_bitsize,output_bitsize=output_bitsize,index_mapping=index_mapping)

elif(sys.argv[1]=="DivideAndConquer"):
  no_outputs = no_inputs/2
  no_outputs_2 = no_inputs/2
  
  twiddle_bits = 8
  tf = DFT_Model.HybridFFTDFT.twiddle_factors(DFT_Model.HybridFFTDFT(0,0,0,0,0,0,0),no_inputs,no_inputs/2,twiddle_bits)
  tf_real = tuple(tf[0])
  tf_imag = tuple(tf[1])
  
  refdata_real_2 = []
  refdata_imag_2 = []
  outputdata_real_2 = []
  outputdata_imag_2 = []
  
  output_bitsize_2 = output_bitsize
  output_line_real_2 = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)),delay=line_delay) #Output signals
  output_line_imag_2 = Signal(intbv(0,min=-2**(output_bitsize-1),max=2**(output_bitsize-1)),delay=line_delay)
  output_trigger_2 = Signal(bool(0),delay=line_delay)
  output_enable_2 = Signal(bool(1),delay=line_delay)
  
  signal_trace = traceSignals(test_bench_dac,cut=cut,input_line_real=input_line_real,input_line_imag=input_line_imag,input_trigger=input_trigger,input_enable=input_enable,output_line_real=output_line_real,output_line_imag=output_line_imag,output_trigger=output_trigger,output_enable=output_enable,output_line_real_2=output_line_real_2,output_line_imag_2=output_line_imag_2,output_trigger_2=output_trigger_2,output_enable_2=output_enable_2,testdata_real=testdata_real,testdata_imag=testdata_imag,outputdata_real=outputdata_real,outputdata_imag=outputdata_imag,outputdata_real_2=outputdata_real_2,outputdata_imag_2=outputdata_imag_2,reset=reset,refdata_real=refdata_real,refdata_imag=refdata_imag,refdata_real_2=refdata_real_2,refdata_imag_2=refdata_imag_2,clk=clk,tf_real=tf_real,tf_imag=tf_imag,twiddle_bits=twiddle_bits,input_bitsize=input_bitsize,output_bitsize=output_bitsize,output_bitsize_2=output_bitsize_2)

elif(sys.argv[1]=="Mux"):
  input_line_real = [Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay) for i in range(no_input_lines)] #Input signals
  input_line_imag = [Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay) for i in range(no_input_lines)]
  input_trigger = [Signal(bool(0),delay=line_delay) for i in range(no_input_lines)]
  input_enable = [Signal(bool(0),delay=line_delay) for i in range(no_input_lines)]

  signal_trace = traceSignals(test_bench_mux,cut=cut,input_line_real=input_line_real,input_line_imag=input_line_imag,input_trigger=input_trigger,input_enable=input_enable,output_line_real=output_line_real,output_line_imag=output_line_imag,output_trigger=output_trigger,output_enable=output_enable,testdata_real=testdata_real,testdata_imag=testdata_imag,outputdata_real=outputdata_real,outputdata_imag=outputdata_imag,reset=reset,refdata_real=refdata_real,refdata_imag=refdata_imag,clk=clk,input_bitsize=input_bitsize,output_bitsize=output_bitsize,no_input_lines=no_input_lines)

elif(sys.argv[1]=="DFT"):
  multiplier_bitsize = 18
  tf = DFT_Model.HybridFFTDFT.twiddle_factors_power(DFT_Model.HybridFFTDFT(0,0,0,0,0,0,0),no_inputs,multiplier_bitsize-2)
  #tf_1 = [[[1 for i in range(no_inputs)] for j in range(no_inputs)],[[1 for i in range(no_inputs)] for j in range(no_inputs)]]
  
  tf_real = []
  tf_imag = []
  for t_f in tf[0]:
    tf_real.extend(t_f)
    #print t_f
  for t_f in tf[1]:
    tf_imag.extend(t_f)
    #print t_f
  
  tf_real = tuple(tf_real)
  tf_imag = tuple(tf_imag)
  
  signal_trace = traceSignals(test_bench_actor,cut=cut,input_line_real=input_line_real,input_line_imag=input_line_imag,input_trigger=input_trigger,input_enable=input_enable,output_line_real=output_line_real,output_line_imag=output_line_imag,output_trigger=output_trigger,output_enable=output_enable,testdata_real=testdata_real,testdata_imag=testdata_imag,outputdata_real=outputdata_real,outputdata_imag=outputdata_imag,reset=reset,refdata_real=refdata_real,refdata_imag=refdata_imag,clk=clk,input_bitsize=input_bitsize,output_bitsize=output_bitsize,tf_real=tf_real,tf_imag=tf_imag,multiplier_bitsize=multiplier_bitsize)

sim = Simulation(signal_trace)
sim.run(100000)

#for i in range(len(refdata_real)):
  #print (outputdata_real[i])
  #print (refdata_real[i])
  
#print testdata_real
#print id(refdata_real)
print outputdata_real
#print outputdata_real_2
print refdata_real
#print refdata_real_2

for i in range(len(outputdata_real)):
  print "\nTest on array %d" % i
  for j in range(len(outputdata_real[i])):
    print "\tTest on value %d" % j
    #print outputdata_real[i][j]
    #print refdata_real[i][j]
    #if(sys.argv[1]!="Unscrambler"):
    if (outputdata_real[i][j] != refdata_real[i][j]):
      print "Real Value Mismatch: %d %d" % (i,j)
      print "myhdl: %d vs model: %d" % (outputdata_real[i][j],refdata_real[i][j])
      
    if (outputdata_imag[i][j] != refdata_imag[i][j]):
      print "Imaginary Value Mismatch: %d %d" % (i,j)
      print "myhdl: %d vs model: %d" % (outputdata_imag[i][j],refdata_imag[i][j])
      
    if(sys.argv[1]=="DivideAndConquer"):
      if (outputdata_real_2[i][j] != refdata_real_2[i][j]):
	print "Real Value Mismatch 2: %d %d" % (i,j)
	print "myhdl: %d vs model: %d" % (outputdata_real_2[i][j],refdata_real_2[i][j])
      
      if (outputdata_imag_2[i][j] != refdata_imag_2[i][j]):
	print "Imaginary Value Mismatch 2: %d %d" % (i,j)
	print "myhdl: %d vs model: %d" % (outputdata_imag_2[i][j],refdata_imag_2[i][j])
	
    """else:
      if (outputdata_real[i][j] != refdata_real[0][i*len(outputdata_real[i])+j]):
	print "Real Value Mismatch: %d %d" % (i,j)
	print "myhdl: %d vs model: %d" % (outputdata_real[i][j],refdata_real[0][i*len(outputdata_real[i])+j])
	
      if (outputdata_imag[i][j] != refdata_imag[0][i*len(outputdata_real[i])+j]):
	print "Imaginary Value Mismatch: %d %d" % (i,j)
	print "myhdl: %d vs model: %d" % (outputdata_imag[i][j],refdata_imag[0][i*len(outputdata_real[i])+j])"""
    #else:
      #print "No mismatch: %d %d" % (i,j)
      #print "%d %d" % (outputdata[i][j],refdata[i][j])

if((sys.argv[1]=="DFT")):
  twiddle_factor_bitsize = 8
  cut_inst = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,tf_real,tf_imag,input_bitsize,output_bitsize,multiplier_bitsize,twiddle_factor_bitsize)
  #toVerilog(VerilogVersion,cut_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset)
  
  #print cut_inst.multi.verilog_code
  """a = Signal(intbv(0)[17:])
  b = Signal(intbv(0)[17:])
  c = Signal(intbv(0)[35:])
  clk = Signal(bool(0))
  reset = Signal(bool(0))
  name = "lalala"
  print cut_inst.multi.verilog_code
  toVerilog(cut.multi,cut_inst,a,b,c,clk,reset,name)"""
  toVerilog(cut.logic,cut_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset)
  
elif(sys.argv[1]=="Actor"):
  input_bitsize = 24
  output_bitsize = 16
  
  interconnect_line_real = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay)
  interconnect_line_imag = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay)
  interconnect_trigger = Signal(bool(0))
  interconnect_enable = Signal(bool(1))
  
  cut_inst = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,interconnect_line_real,interconnect_line_imag,interconnect_trigger,interconnect_enable,no_outputs,reset,clk,input_bitsize,output_bitsize)
  cut_inst_2 = cut(interconnect_line_real,interconnect_line_imag,interconnect_trigger,interconnect_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize)
   
  toVerilog(VerilogVersion,cut_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset,cut2=cut_inst_2)
  #toVHDL(VerilogVersion,cut_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset,cut2=cut_inst_2)
  
elif(sys.argv[1]=="Mux"):
  cut_inst = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,no_input_lines,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,input_bitsize,output_bitsize)
  
  faux_input_line_real = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay) #Input signals
  faux_input_line_imag = Signal(intbv(0,min=-2**(input_bitsize-1),max=2**(input_bitsize-1)),delay=line_delay)
  faux_input_trigger = Signal(bool(0),delay=line_delay)
  faux_input_enable = Signal(bool(1),delay=line_delay)
  
  toVerilog(VerilogVersion,cut_inst,faux_input_line_real,faux_input_line_imag,faux_input_trigger,faux_input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset)
  
elif(sys.argv[1]=="DivideAndConquer"):
  cut_inst = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,output_line_real_2,output_line_imag_2,output_trigger_2,output_enable_2,no_outputs_2,reset,clk,twiddle_bits,tf_real,tf_imag,input_bitsize,output_bitsize,output_bitsize_2)
  
  toVerilog(VerilogVersion,cut_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset,output_line_real_2,output_line_imag_2,output_trigger_2,output_enable_2)
  
elif(sys.argv[1]=="Unscrambler"):
  cut_inst = cut(input_line_real,input_line_imag,input_trigger,input_enable,no_inputs,output_line_real,output_line_imag,output_trigger,output_enable,no_outputs,reset,clk,index_mapping,input_bitsize,output_bitsize,)
    
  toVerilog(VerilogVersion,cut_inst,input_line_real,input_line_imag,input_trigger,input_enable,output_line_real,output_line_imag,output_trigger,output_enable,reset)