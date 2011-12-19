#Signal File Generator Script
#Rhino Project Toolflow
#Gordon Inggs
#January 2010
import sys,numpy,matplotlib.pyplot as plt,math

print "Complex Signal Generator Script"
if len(sys.argv)<8: 
  print "usage: python complex_signal_file_generator.py [base frequency] [rate of increase] [sampling frequency] [length (in seconds)] [output file name] [waveform type] [Bit Width]"
  print "waveform types: linear_chirp, white_noise, sine"

else:
  print "reading in data"
  base_freq = float(sys.argv[1])
  rate_increase = float(sys.argv[2])
  samp_freq = float(sys.argv[3])
  length = float(sys.argv[4])
  output_file = open(sys.argv[5],"w")
  waveform = sys.argv[6]
  max_value = 2**(int(sys.argv[7])-1)
  if (max_value <= 0.5): max_value = 0
  
  num_samples = int(length*samp_freq)
  output_data = [0]*num_samples
  
  if(waveform=="linear_chirp"):
    print "generating linear chirp"
    max_freq = base_freq+num_samples/samp_freq*rate_increase
    if(max_freq > samp_freq/2):
      rate_increase = int(2*samp_freq/num_samples*(samp_freq**2/2-base_freq))
      print "rate of increase constricted to %d to avoid aliasing" % length
     
    for n in range(num_samples):
      temp_freq = base_freq+rate_increase*n/samp_freq
      output_data[n] = numpy.sin(2.0*numpy.pi*(temp_freq)*n/samp_freq)
      
  elif(waveform=="white_noise"):
    print "generating noise"
    for n in range(num_samples): output_data[n] = math.floor(numpy.random.rand()*2-1)
      #print ("%d - %d" % (n,output_data[n]))
      
  elif(waveform=="sine"):
    print "generating sine wave"
    for n in range(num_samples): output_data[n] = numpy.sin(2.0*numpy.pi*(base_freq)*n/samp_freq)
   
  if(max_value): output_data = map(int,map(math.floor,numpy.array(output_data)*max_value))
  
  if (max_value):
    for ov in output_data:
      if(ov==max_value): ov = ov-1
      output_file.write("%d %d\n"% (ov,0))
      
  else:
    for ov in output_data:
      if(ov==max_value): ov = ov-1
      output_file.write("%f %f\n"% (ov,0.0))

  
      
  





