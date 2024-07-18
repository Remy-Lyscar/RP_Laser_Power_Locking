#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 18 16:33:08 2024

@author: ipiq
"""

import socket 
import ilock_RedPitaya as ilock
import sys,time,argparse



ilock_id_RP = "192.168.1.208"
channel = 1  # in1/out1 of the RedPitaya

parser = argparse.ArgumentParser(description="launch a live of the PM counts",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-i','--ilock_setpoint', type = int,
                    help = "set cooling laser intensity setpoint",
                    default = 100)


args = parser.parse_args()


ilock.set_setpoint(ilock_id_RP, channel, args.ilock_setpoint)


