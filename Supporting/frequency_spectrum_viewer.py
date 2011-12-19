#Time Signal File Viewer Script
#Rhino Project Toolflow
#Gordon Inggs
#December 2010
import sys,numpy,matplotlib.pyplot as plt

print "Frequency Viewer Script"
if (len(sys.argv)<3): print "usage: python frequency_spectrum_viwer.py \"[input file1],[input_file_2],etc.\" \"[sampling frequency 1],[sampling frequency 2]\""

else:
  #Reading in Input Data
  input_files=[]
  for s in sys.argv[1].split(","): input_files.append(open(s))
  samp_freqs = []
  for s in sys.argv[2].split(","): samp_freqs.append(int(s))
  
  fig = 1
  input_datasets = []
  for i_f in input_files:
    source_data = (i_f.read()).split("\n")[:-1]
    input_datasets.append([])
    for sd in source_data:
      temp_val = sd.split(" ")
      input_datasets[-1].append(float(temp_val[0]) + 1.0j*float(temp_val[1]))
      
    input_data = numpy.array(input_datasets[-1])
  
    print "Data read in successfully from %s" % i_f.name
    print "%d data points present" % len(input_data)
    print "Signal Power Max = %d" % max(input_data**2)
    print "Signal Power Min = %d" % min(input_data**2)
    print "Signal Power Mean = %d\n" % (sum(input_data**2)/len(input_data))
  
    plt.figure(fig)
    fig += 1
    plt.title(i_f.name)
    samp_freq = samp_freqs[fig-2]
    
    temp_data = []
    for i_d in input_data: temp_data.append((i_d.real**2+i_d.imag**2)**0.5) #calculating the magnitude
    input_data = temp_data
    
    plot_data = list(input_data[len(input_data)/2:]) #rotating the DFT
    plot_data.extend(list(input_data[:len(input_data)/2]))
    x_axis = [] 
    for x in range(-len(plot_data)/2,len(plot_data)/2): x_axis.append(x*samp_freq/len(input_data)) #creating frequency labels
    plot_data = 10*numpy.log(numpy.array(plot_data)/max(numpy.array(plot_data)))/numpy.log(10)
    
    plt.plot(x_axis,plot_data,'-o')
  
  plt.show()