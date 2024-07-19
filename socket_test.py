#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 10:45:13 2024

@author: ipiq
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





##### Connexion to the LAN to get lock instructions in a separate thread #####

# This program listens to the local network, waiting for connexions and sendings of the 
# power setpoins instructions
# It acts as a server receiving data from 'ilock_RedPitaya.py'

port = 1026
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
    
    
    
listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listen_socket.bind((ip, port))
listen_socket.listen()


listen_socket.listen()
print("Server is listening")

client_socket, client_address = listen_socket.accept()


try: 
    message = client_socket.recv(1024) # the message has type bytes 
    print(message)
    message = message.decode() # Convert bytes to string 
    
    power_setpoint = extract_setpoint(message)
    print(power_setpoint)
    
    
finally: 
    client_socket.close() # Even though exceptions occured finally the socket is closed 



listen_socket.close()