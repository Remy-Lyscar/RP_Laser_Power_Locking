#!/usr/bin/python3

import time
import numpy as np
import rp


#? Possible decimations:
#?  RP_DEC_1, RP_DEC_2, RP_DEC_4, RP_DEC_8, RP_DEC_16 , RP_DEC_32 , RP_DEC_64 ,
#?  RP_DEC_128, RP_DEC_256, RP_DEC_512, RP_DEC_1024, RP_DEC_2048, RP_DEC_4096, RP_DEC_8192,
#?  RP_DEC_16384, RP_DEC_32768, RP_DEC_65536

dec = rp.RP_DEC_1

trig_lvl = 0.5
trig_dly = 0

#? Possible acquisition trigger sources:
#?  RP_TRIG_SRC_DISABLED, RP_TRIG_SRC_NOW, RP_TRIG_SRC_CHA_PE, RP_TRIG_SRC_CHA_NE, RP_TRIG_SRC_CHB_PE,
#?  RP_TRIG_SRC_CHB_NE, RP_TRIG_SRC_EXT_PE, RP_TRIG_SRC_EXT_NE, RP_TRIG_SRC_AWG_PE, RP_TRIG_SRC_AWG_NE,
#?  RP_TRIG_SRC_CHC_PE, RP_TRIG_SRC_CHC_NE, RP_TRIG_SRC_CHD_PE, RP_TRIG_SRC_CHD_NE

acq_trig_sour = rp.RP_TRIG_SRC_NOW
N = 16384  # To modify: in order to have small samples on which we can make 
           # fast and in real-time operations 

# Initialize the interface
rp.rp_Init()

# Reset Acquisition
rp.rp_AcqReset()


##### Acquisition #####
# Set Decimation
rp.rp_AcqSetDecimation(dec)


# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)

# Start Acquisition
print("Acq_start")
rp.rp_AcqStart()

# Specify trigger - immediately
rp.rp_AcqSetTriggerSrc(acq_trig_sour)

# Trigger state
while 1:
    trig_state = rp.rp_AcqGetTriggerState()[1]
    if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
        break

## ! OS 2.00 or higher only ! ##
# Fill state
while 1:
    if rp.rp_AcqGetBufferFillState()[1]:
        break


### Get data and make operations with them ###
# RAWssh
ibuff = rp.i16Buffer(N)
res = rp.rp_AcqGetOldestDataRaw(rp.RP_CH_1, N, ibuff.cast())

# Volts
fbuff = rp.fBuffer(N)
res = rp.rp_AcqGetDataV(rp.RP_CH_1, 0, N, fbuff)

data_V = np.zeros(N, dtype = float)
data_raw = np.zeros(N, dtype = int)

for i in range(0, N, 1):
    data_V[i] = fbuff[i]
    data_raw[i] = ibuff[i]

print(f"Data in Volts: {data_V}")
print(f"Raw data: {data_raw}")


##### Operations on signal #####

# Compute an error signal

desired_value = 0.05 # The value to compare with: so far I don't know whether 
                     # I should set it in Volts or in mV
                     
error_signal = [data_V[i] - desired_value for i in range(len(data_V))]

# PID filter 
kp = None
ki = None
kd = None


correction_signal = []



##### Generation of a correction signal toward the AOM controller #####
        
    
#? Possible waveforms:
#?   RP_WAVEFORM_SINE, RP_WAVEFORM_SQUARE, RP_WAVEFORM_TRIANGLE, RP_WAVEFORM_RAMP_UP,
#?   RP_WAVEFORM_RAMP_DOWN, RP_WAVEFORM_DC, RP_WAVEFORM_PWM, RP_WAVEFORM_ARBITRARY,
#?   RP_WAVEFORM_DC_NEG, RP_WAVEFORM_SWEEP

channel = rp.RP_CH_1        # rp.RP_CH_2
waveform = rp.RP_WAVEFORM_ARBITRARY
freq = 10000
ampl = 1

N = 16384       # Number of samples in the buffer

##### Custom waveform setup #####
x = rp.arbBuffer(N)

# Reset generator
rp.rp_GenReset()


print("Gen_Start")
###### Generation #####
rp.rp_GenWaveform(channel, waveform)
rp.rp_GenArbWaveform(channel, x.cast(), N)
rp.rp_GenFreqDirect(channel, freq)
rp.rp_GenAmp(channel, ampl)

#? Possible trigger sources:
#?   RP_GEN_TRIG_SRC_INTERNAL, RP_GEN_TRIG_SRC_EXT_PE, RP_GEN_TRIG_SRC_EXT_NE

# Specify generator trigger source
rp.rp_GenTriggerSource(channel, rp.RP_GEN_TRIG_SRC_INTERNAL)

# Enable output synchronisation
rp.rp_GenOutEnableSync(True)

# Syncronise output channels
rp.rp_GenSynchronise()


# Release resources
rp.rp_Release()


