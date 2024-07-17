#!/usr/bin/env python
#
# Communicate with arduino ilock code 
# v2 adds the ilock_id parameter (useful when several ilock arduino are deployed)  
# v3 adds functions to control ilock from a script
# to log the ilock broadcast launch the following command line :
# stdbuf -oL ./ilock3.py <ilock_id> w<channel> <ack> >> <file_name>
# to display this log use :
# tail -f <file_name>

import sys, time
import socket, string
import threading

directory = "/home/ipiq/diogene/diogene_manips/scripts/common/libs_python"

ip=('192.168.1.223', '192.168.1.224', '192.168.1.225', '192.168.1.226')
port=23
udpport=(9890)
threads=[]
"""
ack : 'acknoledge', lecture de la reponse de l'arduino 
"""

def set_setpoint(ilock_id,channel,setpoint,ack=0):
    message = "@{ch:d}:2:{setpt:.0f}:".format(ch = channel,setpt = setpoint)
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
      

      
def configure(ilock_id, message, ack):   

    ilock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ilock_socket.connect((ip[ilock_id], port))
    ilock_socket.send(message.strip())

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


def udplisten(ilock_id,channel,l):
    """
    Continuously listen to broadcasted data     
    """
    ilock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    ilock_socket.bind(('', udpport+2*ilock_id+channel))
    while(1):
        dataFromClient, address = ilock_socket.recvfrom(l)
        print("{0:.2f} {1:s}".format(time.time(), dataFromClient))
        
    
def getdata(ilock_id,channel, maxmsglen):
    """
    Returns one broadcasted dataline : 
        0 - Arduino_id 
        1 - channel
        2 - setpoint
        3 - raw_adc_reading
        4 - smoothed_adc_reading
        5 - proportional_correction
        6 - integral_correction
        7 - dac_output      
    if from_file is True, try to read it from the last log in the file ilock<ilock_id><channel>.tmp
    """        
    ilock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try : 
        ilock_socket.bind(('', udpport+2*ilock_id+channel))
        # get one line
        dataFromClient, address = ilock_socket.recvfrom(maxmsglen)
        return string.split(dataFromClient)
    finally :
        ilock_socket.close()
       


if __name__ == '__main__' :

    ilock_id=int(sys.argv[1])
    msg=sys.argv[2]
    ack=int(sys.argv[3])
    if msg[0]=='l':
        print(getdata(ilock_id,int(msg[1]),1024))
    if msg[0]=='w':
        udplisten(ilock_id,int(msg[1]),1024)
    else:
        print('ilock_id: ', ilock_id, 'ip ', ip[ilock_id], 'message: ', msg, ' ack:',ack)
        print(configure(ilock_id, msg, ack))
        
        
        
        
        
