#Hybrid DFT Error Analysis Script
#Rhino Project Software Defined Radio Toolflow
#Gordon Inggs
#February 2011

import sys,DFT_Model,numpy,matplotlib.pyplot as plt

print "Frequency Spectrum Error Analysis Script"
if (len(sys.argv)<2): print "usage: python dft_error_analysis.py [input file] [DFT Max index] [Output bit max]"

else:
  input_file = open(sys.argv[1])
  values = range(int(sys.argv[2]))[3:]
  
  errordata = []
  msedata = []
  dftvalues = []
  for v in values:
    #variables for experiment
    output_file = open("tempdata/temp.dat","w")
    input_bits = 8
    twiddle_bits = 0
    dft_size = 2
    output_bits = 2**v
    dftvalues.append(output_bits)
    dft_bits = 0
    sample_rate = 1000
    print "%d output bits" % output_bits
    
    d = DFT_Model.HybridFFTDFT(input_file,output_file,input_bits,twiddle_bits,dft_size,dft_bits,output_bits) #setting up algorithm
    d.readdata()
    
    tempdata = []
    for j in range(len(d.input_values_real)): tempdata.append((d.input_values_real[j]) + 1.0j*(d.input_values_imag[j]))
    
    tempdata = (numpy.fft).fft(tempdata) #reference FFT data
    
    refdata = []
    for t in tempdata:
      refdata.append(abs(t))
      
    tempdata = []
    for r in refdata:
      tempdata.append(r/max(refdata)) #calculating the power and normalising reference FFT
      
    refdata = tempdata
  
    d.twiddle_bits = 8
    d.output_bits = 2**v
    d.dft_bits = 18
    msedata.append([])
    
    #for loop that varies the size of the direct DFT used in the algorithm
    for i in range(1,int(sys.argv[3])):
      d.dft_real = []
      d.dft_imag = []
      d.output_values_real = []
      d.output_values_imag = []
      d.subarrays_real = []
      d.subarrays_imag = []
      d.dft_size = 2**i
      
      d.readdata() #performing the DFT using fixed point model
      d.divide_and_conquer()
      d.DFT()
      d.unscramble()
      
      output_values_real = d.output_values_real 
      output_values_imag = d.output_values_imag
      
      output_bound = 2**(d.output_bits-1)
      testdata = []
      for j in range(len(d.output_values_real)): testdata.append(abs(1.0*output_values_real[j]+ 1.0j*output_values_imag[j])) #calculating the magnitude
  
      refdata_range = max(refdata) - min(refdata)
      testdata_range = max(testdata) - min(testdata)
      
      tempdata = []
      for t in testdata: tempdata.append(t/max(testdata)) #normalising testdata
      testdata = tempdata
      
      testdata_range = max(testdata) - min(testdata)
      
      mse = []
      for j in range(len(testdata)):
	if(max(testdata)): mse.append((1.0*testdata[j]-1.0*refdata[j])**2.0) #calculating the square of the error
	
      msedata[-1].append(numpy.mean(mse)**0.5) #taking the root of the mean square error
      print "dft of size %d:\t\t\t\t%.16f" % (2**i,msedata[-1][-1])
  
  outputdata = open("error_analysis/mse_dftsize.dat","w")
  outputbitvalues = []
  for i in range(1,int(sys.argv[3])): outputbitvalues.append(2**i)
  
  for m in msedata:
    for d in m: outputdata.write("%.10f "%d)
    outputdata.write("\n")
  
  fig = plt.figure() #plotting results
  ax = fig.add_subplot(1,1,1)
  
  output_bits = 3
  for m in msedata:
    ax.plot(outputbitvalues,m,'-o',label="%d output bit size"%(2**output_bits))
    output_bits +=1
    
  plt.title("RMSE vs DFT Size for Hybrid DFT Algorithm")
  plt.legend(loc="upper right")
  plt.show()