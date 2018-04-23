#!/bin/bash
#
# Capture script for the Hantek-6022BE scope and sending some data via a UART interface
# Sends 16 random input bytes to the UART interface via some USB-to-serial adapter and attempts to read 16 bytes back
# This is a typical scenario e.g. for performing SCA on an AES implementation
# Configuration for this file can be used with the Riscure Pinata board
#
# Dependencies:
# Requires xxd and libsigrok installed, as well as a working sigrok-cli with the drivers for the Hantek6022 scope
# Can easily support any scope that libsigrok supports by changing the parameters for the sigrok-cli line
# Script comes as-is, use it carefully (no safety checks on parameters!)
#
# Author: Rafael Boix Carpi (boixcarpi@riscure.com)
# Version:0.01
# Date: 20170430

# ##########Script initialization###########

START_TIME=$SECONDS

#Check that we got number of attempts to capture traces; otherwise default to 10
if [ -z "$1" ]; then 
   printf "************************************************************************\n"
   printf "WARNING: unspecified number of traces to capture\n"
   printf "Capturing default number of traces = 10\n"
   printf "Example commandline for capturing 1000 iterations: %s 1000\n" "$0"
   RESULTTRACES="10"
   printf "************************************************************************\n"
else
   RESULTTRACES=$1
fi

#Store traces in a timestamped folder
CAPTUREFOLDER=$(date +%Y%m%d_%H%M)
printf "Traces stored in folder %s\n" "$CAPTUREFOLDER"
mkdir $CAPTUREFOLDER

#This script requires stty and USB to UART cable found in /dev/ttyUSB0 for configuration!
printf "Configuring UART in /dev/ttyUSB0 to 115200bps 8n1... \n"
stty -F /dev/ttyUSB0 115200 cs8 -cstopb -parenb raw

# ####Start loop for n iterations (given as parameter to the script as $1) ####
INDEX=0
printf "\nStarting capture script, number of capture attempts: %d\n" "$RESULTTRACES"
while [ $INDEX -lt $RESULTTRACES ]; do

# ##########Iteration start###########
printf "Acquiring trace %05d: " "$INDEX"
# Random INPUTTEXT
PRINTABLEINPUT=`xxd -u -p -l16 /dev/urandom`


# Try reading response from device (16 bytes) from serial port

xxd -u -l16 -p < /dev/ttyUSB0 >out.txt &
PIDxxd=$!


# Scope capture start
# Start a 1M Samples, 48MHz capture with sigrok in the background (eventually outputs a file called $INDEX); store its PID to wait for it later
sigrok-cli --driver=hantek-6xxx --config samplerate=48m --channels CH1,CH2  --samples=1M --output-file $CAPTUREFOLDER/$INDEX.zip &
PIDsigrok=$!

# Wait 0.1s for sending the message; uncomment line below if your laptop is ugly slow
#sleep 0.1

# Send INPUTTEXT to serial port
printf "input 0x$PRINTABLEINPUT, " 
# Note that we send an additional 0xAE byte to the target in order for the board to encrypt
echo -ne '\xAE' > /dev/ttyUSB0
echo -ne $PRINTABLEINPUT | xxd -l 16 -r -p > /dev/ttyUSB0

# Debug
# PRINTABLEOUTPUT=`xxd -u -p -l16 /dev/urandom`
wait $PIDxxd
PRINTABLEOUTPUT=`cat ./out.txt`
rm out.txt
printf "output 0x$PRINTABLEOUTPUT\n"

#Wait for sigrok to finish (if not finished already)
wait $PIDsigrok

#Log I/O to file IO.bin
echo -ne $PRINTABLEINPUT$PRINTABLEOUTPUT | xxd -l 32 -r -p >> $CAPTUREFOLDER/inputs_outputs.bin

# ##########Iteration end#############
   
let INDEX=INDEX+1 
done
# ####End loop after n iterations ####

#Inform user of successful end
printf "Capture script finished! Total acquisition time: $(($SECONDS - $START_TIME)) seconds\n\n"
