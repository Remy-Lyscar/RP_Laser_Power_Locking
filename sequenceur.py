# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
Sequencer v3.4 | configured for manip_new_micro  

structure of sequence :
#FLAGS : flag1 flag2 ... flagN gate
{T[timing_flag]} EVENT_TYPE EVENT_CHANNEL EVENT_VALUE | EVENT_MASK | EVENT_TAG
...

with : 
    - EVENT_TYPE in available_events
    - flags in Wirings or lasers

If EVENT_TYPE == SYNCDIGOUT the channel is defined by the mask
Flags f_k are associated to mask components m_k :
    - if f_k is in wirrings, m_k can be "0" for off or "1" for on
    - if f_k is in laser, m_k is composed of two characters:
            - the first gives the laser mode
            - the second whether or not the ilock gate should be raised (for the current mode)

On a raising front of the gate, the EVENT_TAG is used to reference the index 
in the counter response array.


exemple of sequence :
================================================================================
#FLAGS : ir laser0 laser1 gate
{T[wait]} POSPULSE   7 0  |           | sync scope
{T[cool]} SYNCDIGOUT 0 0  | 1 00 21 1 | cooling
{T[wait]} SYNCDIGOUT 0 0  | 1 00 20 0 | wait for ilock
{T[wait]} SYNCDIGOUT 0 0  | 1 10 30 0 | wait for ilock
{T[cool]} SYNCDIGOUT 0 0  | 1 11 31 1 | cooling_eit
{T[wait]} SYNCDIGOUT 0 0  | 1 10 30 0 | wait for ilock
{T[heat]} SYNCDIGOUT 0 0  | 1 00 00 0 | heating
{T[gate]} SYNCDIGOUT 0 0  | 1 10 10 0 | wait before gate
{T[meas]} SYNCDIGOUT 0 0  | 1 10 10 1 | signal
{T[pump]} SYNCDIGOUT 0 0  | 0 00 20 0 | pump in metastable
{T[wait]} SYNCDIGOUT 0 0  | 0 10 10 0 | wait for ilock
{T[meas]} SYNCDIGOUT 0 0  | 0 11 11 1 | background
{T[wait]} SYNCDIGOUT 0 0  | 0 10 10 0 | wait for ilock
{T[wait]} SYNCDIGOUT 0 0  | 1 00 20 0 | wait for ilock
================================================================================
"""
import socket,imp

verbose = False

# dossier où les séquences sont stockées
sequence_directory = r"/home/ipiq/diogene/programmes/scripts_acquisition/micro_v2/sequences"
wirings_file = "wirings.py"

# Parametres reseau (IP et port du serveur sur l'arduino)
sequencer_address = ("192.168.1.209",23)

# On importe les paramètres de brachement correspondant
# aux sequences stockées dans 'sequence_directory'
wirings = imp.load_source("cp","{0:s}/{1:s}".format(sequence_directory,wirings_file)) 
Wirings = wirings.Wirings
lasers_cfg = wirings.lasers_cfg

# événements configurables en sequence,
# TODO : retranscrire la doc du programme de l'Arduino sur la description
#        de chaque événement.
available_events = {
                      'DIGOUT':'0',
                      'SYNCDIGOUT':'1',
                      'DIGIN':'10',
                      'TRIG':'20',
                      'ANALOGIN':'30',
                      'ANALOGOUT':'40',
                      'MESSAGE':'50',
                      'BROADCAST':'60',
                      'POSPULSE':'2',
                      'NEGPULSE':'3'
                    }
    
def template2cmd(sequence_template,timings,delay=1,cycles=0):
    """
    Convert a sequence template into a message of configuration for the sequencer.
    Calculate the timing of the events from the 'timings' dictionnary.
    arguments :
        - sequence_template : name of a template saved in the sequence_directory
        - timings : dictionary giving the timings of the sequence
        - delay : time before sequence is launched
        - cycles : number of repetitions, if 0 the sequencer will not stop
    returns :
        - message : a string to send to the sequencer
        - data_indexes : a dictionary giving the index of the data in the counter response
    """
    
    print("Writting sequencer command from template :")
    print("    > opening template : {0:s}".format(sequence_template))
    
    with open("{0:s}/{1:s}".format(sequence_directory,sequence_template),'r') as f:
        lines = f.readlines() 
    
    #retrieval of the flags of the sequence   
    flags = lines[0].strip().split(':')
    assert flags[0].strip() == '#FLAGS'
    flags = flags[1].strip().split()
    
    #number of events count
    #substitution of the timings in the template
    N_events = 0
    events = []
    for line in lines[1::]:        
        N_events += 1
        line = line.format(T = timings)    
        events.append(line)
    
    #initialisation of the message
    event_timing = 5  
    data_indexes = {}
    message = "{N_EVENTS:d}|{CYCLES:d}|{DELAY:d}|"
    message = message.format(N_EVENTS = N_events,
                             CYCLES = cycles,
                             DELAY = delay)
                             
    if verbose : print("         header      : "+message)
    
    event_tpl = "{TIMING:d}:{TYPE:s}:{CHANNEL:s}:{VALUE:s}:{MASK:d}|"
    previous_gate = 0
    
    #calculation of the message and data_indexes
    for k, event in enumerate(events):
        
        event = event.split("|")
        states = event[1].strip().split()
        event_tag = event[2].strip()
        
        event = event[0].strip().split()
        event_type = available_events[event[1]]
        event_channel = event[2]
        event_value = event[3]
        
        flags_on = parse_mask(flags,states)
        sequencer_ports = (Wirings[flag][0] for flag in flags_on)
        event_mask = sum((2**k for k in sequencer_ports))
           
        if "gate" in flags_on and not previous_gate:
            previous_gate = 1   
            counter_ports = (Wirings[flag][1] for flag in flags_on)
            index = sum((int(2**k) for k in counter_ports))
            data_indexes[event_tag] = index
        else :
            previous_gate = 0
        
        event_msg = event_tpl.format(TIMING = event_timing,
                                    TYPE = event_type,
                                    CHANNEL = event_channel,
                                    VALUE = event_value,
                                    MASK = event_mask)
        
        message += event_msg
        
        if verbose : print("         event no {0:02d} : {1:s}".format(k,event_msg))        
        event_timing += int(event[0])

    print("data indexes : ")
    for name in data_indexes:
        print("    {0:s} -> {1:d} + 2".format(name,data_indexes[name]))
        
    return message,data_indexes


def configure(message,ack = True):
    """
    send the string message to the sequencer
    """
    seq_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try :           
        seq_socket.connect(sequencer_address)
        seq_socket.send(message.strip())   
        if ack:
            ack = seq_socket.recv(4095)
    except :
        raise
    finally :
        seq_socket.close()
    return ack
    
    
def parse_mask(flags,states):
    """
    takes the sequence flags and their states
    returns the flags of the devices that should be activated
    """
    flags_on = ""
    
    for flag,state in zip(flags,states) :
    
        if state[0] != "0":
        
            if "laser" in flag :
                
                laser_id = flag+state[0]
                switches_flags = lasers_cfg[laser_id]["switches"]
                flags_on += switches_flags + " "
                
                if state[1] != "0":
                    ilock_id,ilock_ch = lasers_cfg[laser_id]["ilock"]
                    flags_on += "ilock{0}{1} ".format(ilock_id,ilock_ch)
            
            else :
                flags_on += flag + " "

    flags_on = flags_on.split()

    return flags_on
    
if __name__ == "__main__":
    sequence = "laser01.tpl"
    
    timings = {"cool" : 8000, "meas" : 300, "wait" : 20, "gate" : 5, "pump" : 100}
    
    message,dataCounter = template2cmd(sequence,timings)
    configure(message)
    
