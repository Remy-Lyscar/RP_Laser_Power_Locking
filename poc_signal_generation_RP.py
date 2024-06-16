#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 11:07:00 2024

@author: ipiq
"""



##### POC - Generation of a sine signal toward AOM controller and observation of #####
##### the effect on the photodiode signal in real time                           #####


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
freq = 1000
ampl = 0.025

# Initialize the interface
rp.rp_Init()

# Reset generator
rp.rp_GenReset()

###### Generation #####
rp.rp_GenWaveform(channel, waveform)
rp.rp_GenFreqDirect(channel, freq)
rp.rp_GenAmp(channel, ampl)

# Enable output and trigger the generator
rp.rp_GenOutEnable(channel)
rp.rp_GenTriggerOnly(channel)

# Release resources
rp.rp_Release()

