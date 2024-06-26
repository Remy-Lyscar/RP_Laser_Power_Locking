#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 20 13:53:26 2024

@author: ipiq
"""

import time 
from pyrpl.async_utils import sleep
import numpy as np
import matplotlib.pyplot as plt 
from pyrpl import Pyrpl



# Opening of a Pyrpl session to interact with RedPitaya
HOSTNAME = "192.168.1.208"
p = Pyrpl(hostname = HOSTNAME)

# # Access the RedPitaya object in charge of communicating with the board
r = p.rp



# Setup the scope 
s = r.scope 
s.input1 = 'in1'
s.input2 = 'out1'




pid = r.pid0


# Setup the parameters of the PID 
pid.input = 'in1'
pid.output_direct = 'out1'
pid.setpoint = 
pid.p = 
pid.i = 
pid.d = 0
pid.ival = 0
pid.inputfilter = [0, 0, 0, 0]
pid.max_voltage = 
pid.min_voltage = 


# Quand on veut arrêter le PID il suffit de passer output_direct à 'off', 
# et on peut le faire en temps réel dans le terminal de commande 






