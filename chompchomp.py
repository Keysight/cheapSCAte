"""
chompchomp.py
This script processes sigrok srzip session files, performs the following for all traces:
- Load the IO from inputs_outputs.bin
loop:
+ Find the trigger point in the 2nd acquisition channel given a trigger threshold value (in volts)
+ Store <samplesToKeep> number of samples in an array
+ Convert it to an inspector trace format (samples + input/output)
endloop;
- Return the trace set as a .trs file

IMPORTANT:
At the moment, all initialization variables (filenames, trace lengths, ... have to be hardcoded)

HOW TO USE:
Change the initialization variables values to the actual values you would like to use
from the acquired traces

The script will work assuming the following:
- All initialization variables are set to proper values
- Traces have the name index.zip (example: 0.zip, 1.zip, ..., 999.zip, ...)
- Measurement setup had CH1: signal, CH2: trigger
- Trigger condition is a rising edge and trigger high lasts for longer than 10 samples

"""

import numpy
import numpy as np
import zipfile
import Trace as trs

#########INITIALIZATION VARIABLES############
#Number of total traces
numberOfTraces=2000 #We have traces from 0.zip to 1999.zip

#Number of samples in each one of the captured traces
capturedTraceLength=131000

#Trigger value specified in volts
triggerThreshold=0.45 #Maximum trigger value is 0.5V

#Number of samples to keep
samplesToKeep=4500 #1 AES round seems to be around 187us; 1 sample @ 24MHz is 0.0417us; 1 round is roughly 4500 samples

#Ignore triggers within first ignoreTriggerSamples samples to
#avoid capturing already started operations (e.g. first 1024 samples)
ignoreTriggerSamples=1024
triggerTooLate=capturedTraceLength-samplesToKeep

#Length of input & output messages in bytes (this depends on crypto algorithm used!)
#AES block length is 128 bit == 16 bytes for input and 16 bytes for output
inputMessageLength=16
outputMessageLength=16

#Traceset init
ts = trs.TraceSet()
ts.new('output.trs',0,trs.TraceSet.CodingFloat, inputMessageLength+outputMessageLength, samplesToKeep)

#File with inputs&outputs
inoutFile=open('inputs_outputs.bin','r')

#########END OF INITIALIZATION VARIABLES############

print "Chomp chomp: trimming "+str(samplesToKeep)+" samples from "+str(numberOfTraces)+" traces"

#Loop through all the traces, find a trigger, dump the traces into the traceset
traceCount=0
for i in xrange(numberOfTraces):
	
	#Read io from file
	traceInput=np.fromfile(inoutFile, dtype='uint8', count=inputMessageLength)
	traceOutput=np.fromfile(inoutFile, dtype='uint8', count=outputMessageLength)
	
	#Open trace file from sigrok SRZIP session and load into buffer
	archive=zipfile.ZipFile(str(i)+'.zip', 'r')
	
	#Open trigger trace
	triggerTrace=archive.read('analog-1-2-1') #Trigger on CH2
	triggerSamples=np.frombuffer(triggerTrace, dtype='float32', count=capturedTraceLength)

	#Slow search for the trigger (sequential l2r), should be ok since the trigger should be close to the start of catpure;
	#better to implement some binary search if we don't know where the trigger actually is
	#Using 10 samples to check trigger condition (rising edge) to avoid weird spikes (slower but may be better)
	triggerSampleIndex=None
	for idx in xrange(len(triggerSamples)-10):
		if triggerSamples[idx]>=triggerThreshold:
			foundTrigger=True
			for j in xrange(10):
				if triggerSamples[idx+j]<triggerThreshold:
					foundTrigger=False
			if foundTrigger:
				triggerSampleIndex=idx
				break
			
	if triggerSampleIndex==None:
		print 'Trace '+str(i)+': trigger not found. Trace dropped.'
	elif triggerSampleIndex<ignoreTriggerSamples :
		print 'Trace '+str(i)+': trigger found too early in trace. Trace dropped.'
		triggerSampleIndex=None
	elif triggerSampleIndex>=triggerTooLate :
		print 'Trace '+str(i)+': trigger found too late in trace. Trace dropped.'
		triggerSampleIndex=None
	else:
		print 'Trace '+str(i)+': found trigger at sample '+str(triggerSampleIndex)
		traceCount+=1
	
	#Copy samples from sample trigger index into buffer and add it to the trace set
	if triggerSampleIndex!=None:
		samplesTrace=archive.read('analog-1-1-1') #Sample data on CH1
		capturedSamples=np.frombuffer(samplesTrace, dtype='float32', count=samplesToKeep, offset=triggerSampleIndex*4)
		trace=trs.Trace('',traceInput.tolist()+traceOutput.tolist() , capturedSamples.tolist())
		ts.addTrace(trace)

print 'Script finished! Captured traces: '+str(traceCount)
