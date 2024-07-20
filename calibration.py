import time 
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
import pickle 
import os  
from scipy.optimize import curve_fit
import scienceplots 


plt.style.use('science')

'''
The process of the calibration was the following. 
    - Use the PID to lock the photodiode voltage at different values of voltage setpoint
    - Measure the power of the laser after the semi-reflective blade for each value of the voltage setpoint
    - Plot power P as a function of voltage V and make a linear fitting
    - coefficients of the calibration fit are used in the programm 'power_lock_422_sequence.ipy'

'''


V = np.array([0.05, 0.1, 0.147, 0.195, 0.244, 0.292, 0.264, 0.216, 0.12, 0.169, 0.024, 0.072])
P = np.array([37, 65.5, 94, 120, 148, 174, 159, 130, 76, 103, 21, 48.5])


def linear_fit(x, a, b): 
    return a*x + b


plt.plot(V,P, 'b.')
plt.xlabel ('Photodiode Voltage (V)')
plt.ylabel('Laser power (microWatts)')
plt.grid()
popt, pcov = curve_fit(linear_fit, V, P)
a = popt[0]
b = popt[1]
plt.plot(V, linear_fit(V, a, b), color='red', linestyle = 'dashed', label = f'{a:.4f}x + {b:.4f}')
perr3 = np.sqrt(np.diag(pcov))
plt.legend()
plt.show()


print(a, b)