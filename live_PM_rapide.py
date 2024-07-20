# -*- coding: utf-8 -*-
"""
Live PM
Plot a live recording of the photons scattered by the ion
Data is also logged in the influxdb database
cooling laser can be choosen from:
    - 'laser01' : horizontal mode 1
    - 'laser02' : horizontal mode 2
    - 'laser11' : vertical mode 1
    - 'laser12' : vertical mode 2
Can be set to automaticaly load an ion each time one is lost
log of the loading trials are recorded in 'loadtime.dat'
"""

from __future__ import division, print_function

import matplotlib.pyplot as plt
import numpy as np
import sys,time,argparse

##############################################################################################
parser = argparse.ArgumentParser(description="launch a live of the PM counts",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('laser',
                    help = 'laser to use for cooling',
                    choices=['laser01','laser02', 'laser0111', 'laser11','laser12'])
parser.add_argument('--dis_chop', action = "store_true",
                    help = "disable infrared chopping for background measurement",)
parser.add_argument('-a','--autoload',nargs = '?',type = int,
                    help = '''
                           activate autoload,
                           ion detection threshold can be supplied as an optional argument,
                           (default: %(const)d Hz).\n
                           ''',
                    const = 15000,default = False)
parser.add_argument('-f','--frequency', type = float,
                    help = "set cooling laser AOM frequency (MHz)",
                    default = 200)
parser.add_argument('-i','--ilock_setpoint', type = int,
                    help = "set cooling laser intensity setpoint",
                    default = 1500)
                    
parser.add_argument('-m','--multi_ion_threshold', type = int,
                    help = "multi_ion_threshold",
                    default = 30000)                     

args = parser.parse_args()

if not args.dis_chop :
    SeqTpl = args.laser + "_chop.tpl"
else :
    SeqTpl = args.laser + ".tpl"

print("**********************SEQ = ",SeqTpl)    
    
timings = {"meas" : 7361,"wait" : 130,"pump" : 100,} 

dataOrder = ["timestamp",
             "signal","background","intensity","frequency"]
             
Npts = 60
N_moyenne = 10

F = 1/N_moyenne/timings["meas"]*1e6

if args.autoload :
    autoload_threshold = args.autoload
max_trials = 20

plots = [
         {"title" : "signal and background (Hz)",
          "data" : ("signal","background"),
          "colors" : ("r","k"),
         },
         {"title" : "signal (Hz)",
          "data" : ("signal",),
          "colors" : ("b",),
         },
        ]
        
MAXMSGLEN = 256 # max length of a single udp message, exceeding character will be ignored
##############################################################################################           
           
sys.path.append('/home/ipiq/diogene_manips/scripts/common/parler')
sys.path.append('/home/ipiq/diogene_manips/scripts/common/libs_python')
sys.path.append('/home/ipiq/diogene_manips/scripts/common/utilities/python-vxi11')
sys.path.append('/home/ipiq/diogene_manips/scripts/artemis')
sys.path.append('/home/ipiq/diogene_manips/scripts/poseidon')
sys.path.append('/home/ipiq/diogene/programmes/TrapGUI_541m')
sys.path.append('/home/ipiq/diogene/programmes/scripts_acquisition')
sys.path.append('/home/ipiq/diogene/programmes/scripts_acquisition/micro_v2/autoload')     
sys.path.append('/home/ipiq/diogene/programmes/scripts_acquisition/instruments')

import ilock3
import faucon
import sequenceur as se
import autoload #autoload2ions as autoload
import RF_alim
import ipiq_log

rigol_id,rigol_channel = se.lasers_cfg[args.laser]["rf_alim"]
rigol = RF_alim.RF_alim(label = rigol_id)
rigol.set_freq(args.frequency,rigol_channel)
rigol.set_state("ON",rigol_channel)    

ilock_id,ilock_channel = se.lasers_cfg[args.laser]["ilock"]        
ilock3.set_setpoint(ilock_id,ilock_channel,args.ilock_setpoint)

message,dataCounter = se.template2cmd(SeqTpl,timings)

Nphase = len(dataCounter)
Ncycles = N_moyenne*Nphase
Ndata = Nphase 

data = dict((label,np.zeros(Npts)) for label in dataOrder)

se.configure(message)

print("after se.configure")

Nplots = len(plots)

plt.ion()

fig = plt.figure(figsize=(17, 12))
axes = []
for k in range(Nplots):
    ax = fig.add_subplot(Nplots,1,k+1)
    axes.append(ax)

ions = 0

while 1:
    ligne = -1            
    while ligne == -1 :
        faucon.configure(1,0,Ncycles,0)
        ligne = faucon.getdata(MAXMSGLEN,timeout = 1)
    
    #print "*int* separated colums :"
    t = time.time()
    data["timestamp"][0] = t
    
    msg = "\n{0:s} ".format(time.strftime("%H:%M:%S",time.localtime(t)))
    for k,val in enumerate(ligne):
        if val != "0" :
            msg += "| {0:d} : {1:s} ".format(k,val)
    print(msg)
    print("dataCounter",dataCounter)
    for label in dataCounter:
        k = dataCounter[label]
        data[label][0] = int(ligne[2+k])*F

    ilock_data = ilock3.getdata(ilock_id,ilock_channel,1024)               
    data["intensity"][0] = float(ilock_data[3]) #moy glissante : 4
    
    #data["frequency"][0] = rigol.get_freq(rigol_channel)
    
    data["signal"][0] -= data["background"][0]
    
    for label in dataOrder[1::]:
        ipiq_log.log2db({label: args.laser }, 'new_micro', str(data[label][0]))

    for label in dataOrder:
        data[label] = np.roll(data[label],-1)
    
    for p in range(Nplots) :
        
        ax = axes[p]
        ax.clear()
        plot = plots[p]
        
        title = plot["title"]
        labels = plot["data"]
        colors = plot["colors"]
        
        ax.set_ylabel(title) 
        
        for q,label in enumerate(labels):
            if label in dataCounter:
                
                print("{0: 3d} | {1:s} : {2:.0f} ph/s".format(dataCounter[label]+2,label,data[label][-1]))
            ax.plot(data[label],
                    color = colors[q],label = label)
        ax.legend(loc='lower left')
        ax.grid(True)
    
    plt.draw()
    #plt.pause(0.01)
    
    if args.autoload and (data["signal"][-1] < autoload_threshold):
        time.sleep(10)
        
        trials,success,LT = autoload.loadtrap(autoload_threshold, max_trials,args.laser)
        linetosave = "{ions : 4d}    {t_new : 14.2f}    {t_lost : 14.2f}    {trials : 3d}    {success : s}    {LT : 14.2f}"    
        #linetosave +="\n"
        
        ions += 1
        with open("loadtime.dat","a") as output_file:
            output_file.write(str(ions) + "\t" + str(time.time()) + "\t" + str(t) + "\t" + str(trials) + "\t" + str(success) + "\t" + str(LT)+ "\n")
            """
            output_file.write(linetosave.format(ions =  ions,
                                                t_new = time.time(),
                                                t_lost = t,
                                                trials = trials,
                                                success = str(success),
                                                LT = LT))   
            
            output_file.write("\n")                                           
            """
            
        print("ion in trap no {0:d}".format(ions))
        
        # on charge sequence de manip
        se.configure(message)
        
        time.sleep(0.8)		 

