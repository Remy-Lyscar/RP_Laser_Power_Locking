import time 
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
import pickle 
import os 
# import path
import allantools 
# import tqdm 
from scipy.optimize import curve_fit
import scienceplots 
from numpy.fft import fft
# import pathlib
# import matplotlib as mpl

# pathlib.Path.rmdir( mpl.get_cachedir())


plt.style.use('science')




current_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(current_dir, 'Figures et Data')
df_dir = os.path.join(current_dir, 'Dataframes')


if not os.path.exists(figures_dir):
    os.makedirs(figures_dir)
    


free = pickle.load(open(os.path.join(df_dir,'free_running_signal_mer_26_juin.pkl'), "rb"))
locked = pickle.load(open(os.path.join(df_dir,'locked_laser_mer_26_juin.pkl'), "rb"))

times_free = free['times']
times_locked = locked['times']
signal_free = free['signal']
signal_locked = locked['signal']



times_free = np.array(times_free)
signal_free = np.array(signal_free)



### Calibration of the laser : 

a = 570.2381  # microW / V
b = 7.7619    # microW

def P(V): 
    return a*V +b # microW


signal_free = P(signal_free)


def fit_function(tau, a, b): 
    return a*tau**b


### Free running signal ### 

t = np.logspace(0,3.55, 50)
t2, ad2, aderr2, adn2 = allantools.oadev(signal_free, rate = 0.25, data_type = 'phase', taus = t)
# Rq: je mets les deux en type 'phase' car c'est le seul qui marche pour le signal_locked -> Pourquoi ??


fig = plt.figure()
plt.loglog(t2, ad2, label = 'free running laser', color = 'b', linestyle = '', marker = '.')
plt.xlabel('Taus (seconds)')
plt.ylabel('Overlapping Allan deviation')
plt.grid()
popt, pcov = curve_fit(fit_function, t2,ad2)
a2 = popt[0]
b2 = popt[1]
plt.loglog(t2, fit_function(t2, *popt), color='r', linestyle = 'dashed', label = f'fit:  a = {a2:.4f} \n b = {b2:.4f}')
perr2 = np.sqrt(np.diag(pcov))
plt.legend()
plt.show()