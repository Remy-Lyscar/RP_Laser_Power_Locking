#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 10:09:05 2024

@author: ipiq
"""


"""
Power-locking of the blue laser 422 nm


The calibration is given so that one chooses the power wanted, and the voltage setpoint 
of the PID is adjusted using the calibration

"""


import time 
from pyrpl.async_utils import sleep
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
import os 
from pyrpl import Pyrpl
import pickle 
import socket
import threading
import re # regular expressions



# Location of the file
current_dir = os.path.dirname(os.path.abspath(__file__))

# If needed, this is the location of the PyRPL library 
# /home/ipiq/anaconda3/envs/pyrpl-env(3)/lib/python3.6/site-packages/pyrpl/


##### Calibration of the laser #####

# Powermeter: FieldMaster 

# See 'calibration.py' to see how the calibration was made

a = 570.8734952583208
b = 7.9447061286260565

def V(P): 
    return (P-b)/a


##### Pyrpl Session will be launch in a specific thread #####

class PyrplThread(threading.Thread): 
    
    def __init__(self, name = "pthread"): 
        threading.Thread.__init__(self, name = "pthread")   # Rename the pyrpl thread to avoid conflicts with names of the threads used by PyRPl itself
        
        
    def run(self):
        
        ##### RedPitaya and PyRPL #####

        # Opening of a Pyrpl session to interact with RedPitaya
        HOSTNAME = "192.168.1.208"
        # The config file, here 'blue422nm', is specific to each laser. The changes on one config file 
        # do not affect the other lasers 

        monitor_server_name = "monitor_server"
        p = Pyrpl('blue422nm', hostname = HOSTNAME, reloadserver = True)


        # # Access the RedPitaya object in charge of communicating with the board
        r = p.rp


        # Reset modules 

        # PID Module
        pid = r.pid0
        pid1 = r.pid1
        pid2 = r.pid2
        pid.output_direct = 'off' 
        pid1.output_direct = 'off'
        pid2.output_direct = 'off'

        # ASG module
        asg0 = r.asg0
        asg1 = r.asg1
        asg0.output_direct = 'off'
        asg1.output_direct = 'off'



        # Setup the scope 
        s = r.scope 
        s.input1 = 'in1'
        s.input2 = 'out1'
        s.trigger_source = 'immediately' 


        # Setup the parameters of the PID before to get the instructions for power setpoint
        pid.input = 'in1'
        pid.pause_gains = 'pid'
        pid.p = 100
        pid.i = 0.001
        pid.d = 0
        pid.ival = 0 
        pid.inputfilter = [0, 0, 0, 0]
        pid.max_voltage = 1
        pid.min_voltage = -1  
    
    
    def set_setpoint(self, new_setpoint):
        
        pid.setpoint = new_setpoint
        pid.output_direct = 'out1'        # pid output is set to ON if it was OFF before
        



##### Connexion to the LAN to get lock instructions in a separate thread #####

# This program listens to the local network, waiting for connexions and sendings of the 
# power setpoins instructions
# It acts as a server receiving data from 'ilock_RedPitaya.py'

port = 1025
ip = "192.168.1.21"



def extract_setpoint(msg): 
    '''
    This function is used to retrieve the information on power setpoint from the message
    received from the client, sent with 'ilock_RedPitaya.py'
    '''
    
    pattern = r"@(\d+):2:(\d+):"
    
    # search the message using the regex pattern
    match = re.search(pattern, msg)
    
    # If a match is found, extract the setpoint 
    if match: 
        setpoint = int(match.group(2))
        return setpoint
    else: 
        return None
    
    
    

class ClientThread(threading.Thread):

    def __init__(self, client_socket, PyrplSession):

        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.PyrplSession = PyrplSession

    def run(self): 
        # This function is called by threading.Thread.start()
        
        
        try: 
            message = client_socket.recv(1024) # the message has type bytes 
            print(message)
            # power_setpoint = message.decode() # bytes converted to string
            
            power_setpoint = extract_setpoint(message)
            print(power_setpoint)
            
            # Now the instructions are given to the pid by calling a method on the PyrplSession object
            if power_setpoint is not None: 
                new_setpoint = V(power_setpoint)
                print(new_setpoint)
                
                self.PyrplSession.set_setpoint(new_setpoint)
                
        finally: 
            client_socket.close() # Even though expections occured finally the socket is closed 




##### Program begins to run the threads #####


PyrplSession = PyrplThread()
PyrplSession.start()



### The three next lines have to be commented if the listen_socket has already been 
# bound to a specific port. Otherwise, if listen_socket is not defined when running 
# the programm, then uncomment them, run, and comment them again to avoid socket error or OSerror.

# listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# listen_socket.bind((ip, port))

while True:
    listen_socket.listen()
    client_socket, client_address = listen_socket.accept()
    newthread = ClientThread(client_socket)
    newthread.start()
    
    
# listen_socket.close() is never called: Is it a problem? Actually when this programm runs listen_socket always listens to the LAN 
# It may be necessary to kill the process (indeed to kill all python processes) if the following error occurs: 
    
# oserror: [errno 98] address already in use

# The command to kill is :  kill -9 $(ps -A | grep python | awk '{print $1}')
    
    