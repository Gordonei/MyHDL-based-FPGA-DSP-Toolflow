#Scalable Hybrid FFT-DFT Sequential Model
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#February 2011
import sys, numpy, math, random, time
from myhdl import intbv

class HybridFFTDFT:
  #Public Variables
  input_file = ""
  samp_freq = 0
  output_file = ""
  input_bits = 0
  twiddle_bits = 0
  dft_size = 0
  dft_bits = 0
  output_bits = 0
  
  #Private Variables
  input_values_real = []
  input_values_imag = []
  output_values_real = []
  output_values_imag = []
  num_stages = 0
  subarrays_real = []
  subarrays_imag = []
  dft_real = []
  dft_imag = []
  
  def __init__(self,i_f,o_f,i_b,t_b,d_s,d_b,o_b):
    self.input_file = i_f
    self.output_file = o_f
    self.input_bits = i_b
    self.twiddle_bits = t_b
    self.dft_size = d_s
    self.dft_bits = d_b
    self.output_bits = o_b
    
    self.input_values_real = []
    self.input_values_imag = []
    self.input_values_real = []
    self.input_values_imag = []
    self.output_values_real = []
    self.output_values_imag = []
    self.num_stages = 0
    self.subarrays_real = []
    self.subarrays_imag = []
    self.dft_real = []
    self.dft_imag = []
    
  def twiddle_factors(self,N,stage_length,bits):
    """Method for generating twiddle factors for a particular stage of the butterfly or DAC"""
    segments = 2*numpy.pi/N
    stage = numpy.log(N/stage_length)/numpy.log(2) #Calculating which stage of the divide and conquer operation this is
    
    Wn_real = numpy.cos(segments)
    Wn_imag = -1*numpy.sin(segments)

    tf_real = []
    tf_imag = []
    for i in range(stage_length): #For the length of the stage, each twiddle factor is calculated
      value = (Wn_real+1.0j*Wn_imag)**(i*2**(stage-1))
      if(bits): #scaling the twiddle factors
	value_real = int(value.real*(2**(bits-1)))
	value_imag = int(value.imag*(2**(bits-1)))
	
	if((value_real>=2**(bits-1)) and (value_imag>=2**(bits-1))):
	  tf_real.append(intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1)))
	
	elif(value_real>=2**(bits-1)):
	  tf_real.append(intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag,min=-2**(bits-1),max=2**(bits-1)))
	  
	elif(value_imag>=2**(bits-1)):
	  tf_real.append(intbv(value_real,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1)))
	
	else:
	  tf_real.append(intbv(value_real,min=-2**(bits-1),max=2**(bits-1)))
	  tf_imag.append(intbv(value_imag,min=-2**(bits-1),max=2**(bits-1)))
	  
      else:
	value_real = value.real
	value_imag = value.imag
	
	tf_real.append(value_real)
	tf_imag.append(value_imag)

    return [tf_real,tf_imag] #list of twiddle factors is returned
    
  def twiddle_factors_power(self,size,bits):
    """Another method for generating twiddle factors, this time for the direct DFT"""
    segment_size = 2*numpy.pi/size
    base = numpy.cos(segment_size)-1.0j*(numpy.sin(segment_size))
    
    tf_power_real = []
    tf_power_imag = []
    for i in range(size):
      tf_power_real.append([])
      tf_power_imag.append([])
      
      for n in range(size):
	value = base**(i*n)
	value_real = value.real
	value_imag = value.imag
	
	if(bits): #scaling the twiddle factors
	  value_real = int(value_real*2**(bits-1))
	  value_imag = int(value_imag*2**(bits-1))
	  
	  if((value_real>=2**(bits-1)) and (value_imag>=2**(bits-1))):
	    value_real = intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1))
	
	  elif(value_real>=2**(bits-1)):
	    value_real = intbv(value_real-1,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag,min=-2**(bits-1),max=2**(bits-1))
	  
	  elif(value_imag>=2**(bits-1)):
	    value_real = intbv(value_real,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag-1,min=-2**(bits-1),max=2**(bits-1))
	
	  else:
	    value_real = intbv(value_real,min=-2**(bits-1),max=2**(bits-1))
	    value_imag = intbv(value_imag,min=-2**(bits-1),max=2**(bits-1))
	
	tf_power_real[-1].append(value_real)
	tf_power_imag[-1].append(value_imag)
    
    
    return [tf_power_real,tf_power_imag]
  
  def DFT(self):
    """Method for performing the direct DFT"""
    segments = 2*numpy.pi/self.dft_size #Calculating Twiddle Factors for DFT
    Wn_real = numpy.cos(segments)
    Wn_imag = -1.0*numpy.sin(segments)

    tf_power = self.twiddle_factors_power(self.dft_size,self.dft_bits)
    tf_power_real = tf_power[0]
    tf_power_imag = tf_power[1]
    
    for data in range(len(self.subarrays_real)):
      self.dft_real.append([])
      self.dft_imag.append([])
      
      for w in range(self.dft_size):
	temp_real = 0.0
	temp_imag = 0.0
	  
	dft_bound = 1
	if(self.dft_bits): #checking if DFT has a set input bitsize
	  dft_bound = 2**(2*self.dft_bits+self.dft_size-1)
	  
	  temp_real = intbv(0,min=-dft_bound,max=dft_bound)
	  temp_imag = intbv(0,min=-dft_bound,max=dft_bound)
	  
	  if(self.output_bits): 
	    real_overflow_tracking = 2*self.dft_bits+int(self.dft_size/32.0)
	    imag_overflow_tracking = 2*self.dft_bits+int(self.dft_size/32.0)
	    overflow_flag = False
	    

	for d in range(self.dft_size): #Inner loop of DFT
	  input_value_real_scaled = self.subarrays_real[data][d]
	  input_value_imag_scaled = self.subarrays_imag[data][d]
	  
	  
	  if(self.twiddle_bits):
	    dc_bound = 2**(self.twiddle_bits*(self.num_stages-1)+self.input_bits-1) #Bit size for input data for DFT - input_bitwidth + twiddle_factor_bitwidth*number_stages
	    scaling_factor = (2.0**(self.dft_bits-1))/dc_bound #scaling factor for input to DFT = (DFT input size)/(D&C output bound)
	    dc_bound = 2**(self.twiddle_bits*(self.num_stages-1)+self.input_bits-1) #Bit size for input data for DFT - input_bitwidth + )twiddle_factor_bitwidth*number_stages-1)
	    scaling_factor = (2.0**(self.dft_bits-1))/dc_bound #scaling factor for input to DFT = (DFT input size)/(D&C output bound)
	    
	    if(((self.twiddle_bits*(self.num_stages-1)+self.input_bits-1)-(self.dft_bits-1)) >=0 ):
	      input_value_real_scaled = (self.subarrays_real[data][d] >> ((self.twiddle_bits*(self.num_stages-1)+self.input_bits-1)-(self.dft_bits-1)))
	      input_value_imag_scaled = (self.subarrays_imag[data][d] >> ((self.twiddle_bits*(self.num_stages-1)+self.input_bits-1)-(self.dft_bits-1)))
	    else:
	      input_value_real_scaled = self.subarrays_real[data][d]
	      input_value_imag_scaled = self.subarrays_imag[data][d]
	    
	  value = (input_value_real_scaled +1.0j*input_value_imag_scaled)*(tf_power_real[w][d]+1.0j*tf_power_imag[w][d])
	  
	  temp_real += int(value.real)
	  temp_imag += int(value.imag)

	  
	  if(self.output_bits): #Checking to see if an overflow has occurred
	    if(temp_real>(2**(real_overflow_tracking-1))):
	      overflow_flag = True
	      real_overflow_tracking += 1
	      
	    if(temp_imag>(2**(imag_overflow_tracking-1))):
	      overflow_flag = True
	      imag_overflow_tracking += 1
	      
	    if(temp_real<-(2**(2*self.dft_bits-1))):
	      temp_real = temp_real/2
	      
	    if(temp_imag<-(2**(2*self.dft_bits-1))):
	      temp_imag = temp_imag/2
	    
	  
	  overflow_flag = False
	  value_bits = 0
	  if(self.output_bits): #Checking to see if an overflow has occurred
	    if(temp_real>(2**(real_overflow_tracking-1))):
	      overflow_flag = True
	      real_overflow_tracking += 1
	      
	    if(temp_imag>(2**(imag_overflow_tracking-1))):
	      overflow_flag = True
	      imag_overflow_tracking += 1
	      
	    if(temp_real<-(2**(real_overflow_tracking-1))):
	      overflow_flag = True
	      real_overflow_tracking += 1
	      
	    if(temp_imag<-(2**(imag_overflow_tracking-1))):
	      overflow_flag = True
	      imag_overflow_tracking += 1
	
	temp_real_scaled = temp_real
	temp_imag_scaled = temp_imag
	
	
	if(self.output_bits):
	  output_bound = 2**(self.output_bits) #Output bit size
	  real_scaling_factor = 1.0*output_bound/(2**(real_overflow_tracking)) #scaling factor for output from DFT = output bit size / (output bit size from DFT, as tracked by overflow monitor variable)
	  imag_scaling_factor = 1.0*output_bound/(2**(imag_overflow_tracking)) #scaling factor for output from DFT = output bit size / (output bit size from DFT, as tracked by overflow monitor variable)
	  
	  if(((2*self.dft_bits+int(self.dft_size/16.0))-self.output_bits)>=0):
	    temp_real_scaled = intbv(int(temp_real_scaled >> ((2*self.dft_bits+int(self.dft_size/16.0))-self.output_bits)),min=-output_bound,max=output_bound)
	    temp_imag_scaled = intbv(int(temp_imag_scaled >> ((2*self.dft_bits+int(self.dft_size/16.0))-self.output_bits)),min=-output_bound,max=output_bound)
	
	self.dft_real[-1].append(temp_real_scaled)
	self.dft_imag[-1].append(temp_imag_scaled)
	
  
  def readdata(self):
    """Method for reading input data from file"""
    input_bound = 2**(self.input_bits-1)
    
    source_data = (self.input_file.read()).split("\n")[:-1]
    if(input_bound>0.5):
      for sd in source_data:
	temp_val = sd.split(" ")
	self.input_values_real.append(intbv(int(temp_val[0]),min=-input_bound,max=(input_bound)))
	self.input_values_imag.append(intbv(int(temp_val[1]),min=-input_bound,max=(input_bound)))
    else:
      for sd in source_data:
	temp_val = sd.split(" ")
	self.input_values_real.append(float(temp_val[0]))
	self.input_values_imag.append(float(temp_val[1]))
	
    ##print len(self.input_values_real)
    self.num_stages = int(numpy.ceil(numpy.log(len(self.input_values_real)/self.dft_size)/numpy.log(2)))+1 #Calculating number of stages required
    ##print numpy.shape(self.input_values_real)
      
  def divide_and_conquer(self):
    """Method for performing divide and conquer operations"""
    self.subarrays_real = [self.input_values_real] #Starting out with the complete signal
    self.subarrays_imag = [self.input_values_imag]
    bits = (self.input_bits)
    
    for i in range(1,self.num_stages): #Loop for each stage
      bits += self.twiddle_bits #bound grows for each stage by the size of twiddle factors (twiddle bits -1) + 1 (in case of overflow) 
      dc_bound = 2**(bits-1) 
      stage_length = len(self.input_values_real)/(2**i) #Calculating the length of the subarrays at this length
    
      temp_real = []
      temp_imag = []
      for subset in range(len(self.subarrays_real)): #Breakdown of each subarray into two further subarrays
	upper_real = self.subarrays_real[subset][:stage_length] #splitting subarray into upper and lower parts of butterfly
	upper_imag = self.subarrays_imag[subset][:stage_length]
	
	lower_real = self.subarrays_real[subset][stage_length:]
	lower_imag = self.subarrays_imag[subset][stage_length:]

	temp_real.append([])
	temp_imag.append([])
	
	for j in range(len(upper_real)):
	  value_real = (upper_real[j]+lower_real[j])
	  value_imag = (upper_imag[j]+lower_imag[j])
	
	  if(self.twiddle_bits):
	    value_real = int(value_real*2**(self.twiddle_bits-1))
	    value_imag = int(value_imag*2**(self.twiddle_bits-1))
	    
	    if((value_real>=dc_bound) and (value_imag>=dc_bound)):
	      value_real = value_real-1
	      value_imag = value_imag-1
	
	    elif(value_real>=dc_bound):
	       value_real = value_real-1
	  
	    elif(value_imag>=dc_bound):
	      value_imag = value_imag-1
	    
	    temp_real[-1].append(intbv(value_real,min=-dc_bound,max=dc_bound))#upper branch of butterfly is only addition
	    temp_imag[-1].append(intbv(value_imag,min=-dc_bound,max=dc_bound))
	
	  else:
	    temp_real[-1].append(value_real)
	    temp_imag[-1].append(value_imag)
	
	temp_tf = self.twiddle_factors(len(self.input_values_real),stage_length,self.twiddle_bits) #twiddle factors needed for lower butterfly

	temp_sub_real = []
	temp_sub_imag = []
	temp_real.append([])
	temp_imag.append([])
	for j in range(len(lower_real)):
	  temp_sub_real.append(upper_real[j]-lower_real[j])#lower branch of butterfly is subtraction
	  temp_sub_imag.append(upper_imag[j]-lower_imag[j])
	  
	  value = (temp_sub_real[j]+1.0j*temp_sub_imag[j])*(temp_tf[0][j]+1.0j*temp_tf[1][j]) #Multiplication by twiddle factors
	  
	  if(self.twiddle_bits):
	    temp_real[-1].append(int(value.real))
	    temp_imag[-1].append(int(value.imag))
	  
	  else:
	    temp_real[-1].append(value.real)
	    temp_imag[-1].append(value.imag)
	
      self.subarrays_real = temp_real #the subarrays replace the larger subsets
      self.subarrays_imag = temp_imag
      
      
  def unscramble(self):
    """Method for undoing the decimation caused by the divide and conquer operations"""
    for d in self.dft_real: self.output_values_real.extend(d)
    for d in self.dft_imag: self.output_values_imag.extend(d)
    ui = range(len(self.output_values_real))
    
    N_D = len(self.input_values_real)/self.dft_size #Number of DFTs performed for a particular stage, starting with the final stage
    D_S = self.dft_size #The size of a DFT performed for a particular stage
    bound = 2**(self.output_bits-1)

    for k in range(self.num_stages-1): #For each stage of decimation
      temp_ui = [0.0]*len(self.output_values_real)
      temp_real = [0.0]*len(self.output_values_real) #Creating temp list for placing the unscrambled data into
      temp_imag = [0.0]*len(self.output_values_imag)
      if(self.twiddle_bits):
	temp_real = [intbv(0,min=-bound,max=bound)]*len(self.output_values_real) #Creating temp list for placing the unscrambled data into
	temp_imag = [intbv(0,min=-bound,max=bound)]*len(self.output_values_imag)
      
      for i in range(N_D/2): #Iterating over the data in this stage of decimation
	start = i*D_S*2 #start and finish values are not rearranged, and so are copied straight across
	finish = i*D_S*2 + D_S*2-1
	
	temp_real[start] = self.output_values_real[start]
	temp_imag[start] = self.output_values_imag[start]
	temp_ui[start] = ui[start]
	
	temp_real[finish] = self.output_values_real[finish]
	temp_imag[finish] = self.output_values_imag[finish]
	temp_ui[finish] = ui[finish]

	upper = start+1 #starting point for the upper and lower branches of the rearrangement operation are calculated
	lower = start+D_S
      
	index = start+1
	for j in range(D_S-1): #Iterating over the remaining data in this stage of decimation, and assigning values to the correct part of the dataset
	  temp_real[index] = self.output_values_real[lower] #lower values are first, then the upper value
	  temp_imag[index] = self.output_values_imag[lower]
	  temp_ui[index] = ui[lower]
	  
	  temp_real[index+1] = self.output_values_real[upper]
	  temp_imag[index+1] = self.output_values_imag[upper]
	  temp_ui[index+1] = ui[upper]
      
	  index += 2 #indices are iterated
	  lower += 1
	  upper += 1

      self.output_values_real = temp_real #copy the unscrambled data to the output array
      self.output_values_imag = temp_imag
      ui = temp_ui
      
      D_S = D_S*2 #Increase the size of the "DFT" for the next stage of decimation reversal
      N_D = N_D/2 #Half the number of DFTs performed
      
    ##print ui
      
  def writedata(self):
    for i in range(len(self.output_values_real)):
      if(self.twiddle_bits):self.output_file.write("%d %d\n"% (self.output_values_real[i],self.output_values_imag[i]))
      else: self.output_file.write("%f %f\n"% (self.output_values_real[i],self.output_values_imag[i]))
  
if __name__ == "__main__":
  print "Scalable DFT-FFT sequential model"
  print "usage: python DFT_Model.py [input filename] [output filename] [input bit width] [twiddle factor bit width] [DFT Size] [Multiplier input bit width] [Output bit width]"

  input_file = open(sys.argv[1])
  output_file = open(sys.argv[2],"w")
  input_bits = int(sys.argv[3])
  twiddle_bits = int(sys.argv[4])
  dft_size = int(sys.argv[5])
  dft_bits = int(sys.argv[6])
  output_bits = int(sys.argv[7])
  
  hfd = HybridFFTDFT(input_file,output_file,input_bits,twiddle_bits,dft_size,dft_bits,output_bits)
  print "Reading data"
  hfd.readdata()
  print "Dividing up data"
  hfd.divide_and_conquer()
  print "DFTing"
  hfd.DFT()
  print "Unscrambling"
  hfd.unscramble()
  print "Writing data"
  hfd.writedata()
  