#!/usr/bin/python3

import time
import numpy as np
import rp


#? Possible waveforms:
#?   RP_WAVEFORM_SINE, RP_WAVEFORM_SQUARE, RP_WAVEFORM_TRIANGLE, RP_WAVEFORM_RAMP_UP,
#?   RP_WAVEFORM_RAMP_DOWN, RP_WAVEFORM_DC, RP_WAVEFORM_PWM, RP_WAVEFORM_ARBITRARY,
#?   RP_WAVEFORM_DC_NEG, RP_WAVEFORM_SWEEP

channel = rp.RP_CH_1        # rp.RP_CH_2
waveform = rp.RP_WAVEFORM_SINE
freq = 100000
ampl = 1.0

ncyc = 3
nor = 1
period = 10

trig_lvl = 0.5
trig_dly = 0

#? Possible decimations:
#?  RP_DEC_1, RP_DEC_2, RP_DEC_4, RP_DEC_8, RP_DEC_16, RP_DEC_32, RP_DEC_64,
#?  RP_DEC_128, RP_DEC_256, RP_DEC_512, RP_DEC_1024, RP_DEC_2048, RP_DEC_4096, RP_DEC_8192,
#?  RP_DEC_16384, RP_DEC_32768, RP_DEC_65536

# RP_DEC_1 corresponds to the maximum sampling rate (125 Ms/s), or equivalently to the buffer with the minimum time scale (130 microseconds)

dec = rp.RP_DEC_1

#? Possible generation trigger sources:
#?  RP_GEN_TRIG_SRC_INTERNAL, RP_GEN_TRIG_SRC_EXT_PE, RP_GEN_TRIG_SRC_EXT_NE

gen_trig_sour = rp.RP_GEN_TRIG_SRC_INTERNAL

#? Possible acquisition trigger sources:
#?  RP_TRIG_SRC_DISABLED, RP_TRIG_SRC_NOW, RP_TRIG_SRC_CHA_PE, RP_TRIG_SRC_CHA_NE, RP_TRIG_SRC_CHB_PE,
#?  RP_TRIG_SRC_CHB_NE, RP_TRIG_SRC_EXT_PE, RP_TRIG_SRC_EXT_NE, RP_TRIG_SRC_AWG_PE, RP_TRIG_SRC_AWG_NE,
#?  RP_TRIG_SRC_CHC_PE, RP_TRIG_SRC_CHC_NE, RP_TRIG_SRC_CHD_PE, RP_TRIG_SRC_CHD_NE

acq_trig_sour = rp.RP_TRIG_SRC_AWG_PE

N = 16384 # Number of the samples in a full buffer 



# Initialize the interface
rp.rp_Init()

# Reset Generation and Acquisition
rp.rp_GenReset()
rp.rp_AcqReset()

###### Generation #####
print("Gen_start")
rp.rp_GenWaveform(channel, waveform)
rp.rp_GenFreqDirect(channel, freq)
rp.rp_GenAmp(channel, ampl)

# Change to burst mode
rp.rp_GenMode(channel, rp.RP_GEN_MODE_BURST)
rp.rp_GenBurstCount(channel, ncyc)                  # Ncyc
rp.rp_GenBurstRepetitions(channel, nor)             # Nor
rp.rp_GenBurstPeriod(channel, period)               # Period


# Specify generator trigger source
rp.rp_GenTriggerSource(channel, gen_trig_sour)

# Enable output synchronisation
rp.rp_GenOutEnableSync(True)
rp.rp_GenOutEnable(channel)


##### Acquisition #####
# Set Decimation
rp.rp_AcqSetDecimation(dec)

#? Possible triggers:
#?  RP_T_CH_1, RP_T_CH_2, RP_T_CH_3, RP_T_CH_4, RP_T_CH_EXT

# Set trigger level and delay
rp.rp_AcqSetTriggerLevel(rp.RP_T_CH_1, trig_lvl)
rp.rp_AcqSetTriggerDelay(trig_dly)


# Start Acquisition
print("Acq_start")
rp.rp_AcqStart()

# Specify trigger - input 1 positive edge
rp.rp_AcqSetTriggerSrc(acq_trig_sour)


rp.rp_GenTriggerOnly(channel)       # Trigger generator

print(f"Trigger state: {rp.rp_AcqGetTriggerState()}")

# Trigger state
while 1:
    trig_state = rp.rp_AcqGetTriggerState()[1]
    if trig_state == rp.RP_TRIG_STATE_TRIGGERED:
        break

## ! OS 2.00 or higher only ! ##
# Fill state
print(f"Fill state: {rp.rp_AcqGetBufferFillState()}")

## ! OS 2.00 or higher only ! ##
while 1:
    if rp.rp_AcqGetBufferFillState()[1]:
        break


### Get data ###
# Volts
fbuff = rp.fBuffer(N)
res = rp.rp_AcqGetDataV(rp.RP_CH_1, 0, N, fbuff)

data_V = np.zeros(N, dtype = float)

for i in range(0, N, 1):
    data_V[i] = fbuff[i]

print(f"Data in Volts: {data_V}")

# Release resources
rp.rp_Release()