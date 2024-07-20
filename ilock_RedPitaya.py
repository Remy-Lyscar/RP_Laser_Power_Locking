#!/usr/bin/env python
#
# Communicate with RedPitaya ilock code implemented with PyRPL module
# Server side is on mini1 and called 'power_lock_422_sequence.py' (for blue 422 nm cooling laser)

import sys, time
import socket, string
import threading


directory = "/home/ipiq/diogene/diogene_manips/scripts/common/libs_python"

ip = "192.168.1.21"  # So far only the mini1 computer can communicate with the RP using a specific branch of PyRPl
port=1025  # port on the server side, ie on mini1 for the listen_socket 
# see the server code at: /home/ipiq/diogene/Users/Valentin/Codes/RedPitaya/Codes RedPitaya/power_lock_422.ipy

# udpport=(9890)
# threads=[]
"""
ack : 'acknoledge', lecture de la reponse de l'arduino 
"""

def set_setpoint(ilock_id,channel,setpoint,ack=0):
    # set_setpoint must be called with ilock_id = "192.168.1.21" to avoid conflits with the ilock_id of the Arduino cards
    message = "@{ch:d}:2:{setpt:d}:".format(ch = channel,setpt = setpoint)
    # the setpoint part of the message is sent as an int to match the regex pattern in 'power_lock_422.ipy'
    # Anyway this value is initially an int. The conversion in float will be done in 'power_lock_422.ipy'
    data = configure(ilock_id,message,ack)
    return data
    
def lock_enable(ilock_id,channel,enable,ack=0):
    message = "@{ch:d}:1:{en:d}:".format(ch = channel,en = enable)
    data = configure(ilock_id,message,ack)
    return data
  
def set_pin_in(ilock_id,channel,PIN_IN ,ack=0):
    message = "@{ch:d}:0:{pin_in:.0f}:".format(ch = channel,pin_in = PIN_IN)
    data = configure(ilock_id,message,ack)
    return data

def set_n_avg(ilock_id,channel,N_AVG ,ack=0):
    message = "@{ch:d}:4:{n_avg:.0f}:".format(ch = channel,n_avg = N_AVG)
    data = configure(ilock_id,message,ack)
    return data  

def set_ki(ilock_id,channel,KI,ack=0):
    message = "@{ch:d}:5:{ki:.0f}:".format(ch = channel,ki = KI)
    data = configure(ilock_id,message,ack)
    return data    
  
def set_kp(ilock_id,channel,KP,ack=0):
    message = "@{ch:d}:6:{kp:.0f}:".format(ch = channel,kp = KP)
    data = configure(ilock_id,message,ack)
    return data 
      

      
def configure(ilock_id, message, ack = 0):   

    ilock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ilock_socket.connect((ilock_id, port)) 
    ilock_socket.sendall(message.strip())  # The message contains the instruction for intensity setpoint
    # .sendall() makes it automatic to send all data to the server, even though
    # the size of the data is larger than the size of a server buffer
    
    if (ack==1):
        print("ready to receive data")
        data=""
        buf = ilock_socket.recv(1)
    
        data = buf
        while ((buf != '!') and (buf)):
            buf = ilock_socket.recv(1)
            data=data+buf
        return data
        ilock_socket.close()
    else:
        ilock_socket.close()
        return 1
    


# def udplisten(ilock_id,channel,l):
#     """
#     Continuously listen to broadcasted data     
#     """
#     ilock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
#     ilock_socket.bind(('', udpport+2*ilock_id+channel))
#     while(1):
#         dataFromClient, address = ilock_socket.recvfrom(l)
#         print("{0:.2f} {1:s}".format(time.time(), dataFromClient))
        
    
# def getdata(ilock_id,channel, maxmsglen):
#     """
#     Returns one broadcasted dataline : 
#         0 - RedPitaya_id 
#         1 - channel
#         2 - setpoint
#         3 - raw_adc_reading
#         4 - smoothed_adc_reading
#         5 - proportional_correction
#         6 - integral_correction
#         7 - dac_output      
#     if from_file is True, try to read it from the last log in the file ilock<ilock_id><channel>.tmp
#     """        
#     ilock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try : 
#         ilock_socket.bind(('', udpport+2*ilock_id+channel))
#         # get one line
#         dataFromClient, address = ilock_socket.recvfrom(maxmsglen)
#         return string.split(dataFromClient)
#     finally :
#         ilock_socket.close()


# A new function getdata using TCP is implemented below,
# but so far communication from mini1 has not been implemented. This programm
# does not wait for any response and getdata should not be used in a sequence using RP ilock
# until the response from 'power_lock_422.ipy' on mini1 has been implemented 

def getdata(ilock_id, channel, maxmsglen):
    """
       Returns one broadcasted dataline : 
           0 - RedPitaya_id 
           1 - channel
           2 - setpoint
           3 - raw_adc_reading
           4 - smoothed_adc_reading
           5 - proportional_correction
           6 - integral_correction
           7 - dac_output
    """
    
    getdata_port = ""
    
    getdata_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: 
        getdata_socket.bind(('', getdata_port))
        getdata_socket.listen()
        client_socket, client_address = getdata_socket.accept()
        dataFromClient, address = getdata_socket.recvfrom(maxmsglen)
        return string.split(dataFromClient)
    finally: 
        getdata_socket.close()


if __name__ == '__main__' :

    ilock_id=int(sys.argv[1]) # command-line arguments start at index 1, index 0 is reserved for the name of the python file 
    msg=sys.argv[2]
    ack=int(sys.argv[3])
    if msg[0]=='l':
        print(getdata(ilock_id,int(msg[1]),1024))
    if msg[0]=='w':
        udplisten(ilock_id,int(msg[1]),1024)
    else:
        print('ilock_id: ', ilock_id, 'ip ', ip[ilock_id], 'message: ', msg, ' ack:',ack)
        print(configure(ilock_id, msg, ack)) # Should return 1 if everything went well 
        
        
        
        
        
