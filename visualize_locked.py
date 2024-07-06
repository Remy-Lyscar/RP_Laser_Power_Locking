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
from scipy.stats import norm

# pathlib.Path.rmdir( mpl.get_cachedir())


plt.style.use('science')




current_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(current_dir, 'Figures et Data')
df_dir = os.path.join(current_dir, 'Dataframes')


if not os.path.exists(figures_dir):
    os.makedirs(figures_dir)
    


free = pickle.load(open(os.path.join(df_dir,'free_running_signal_jeu_4_juillet.pkl'), "rb"))
locked = pickle.load(open(os.path.join(df_dir,'locked_laser_jeu_4_juillet.pkl'), "rb"))

times_free = free['times']
times_locked = locked['times']
signal_free = free['signal']
signal_locked = locked['signal']



times_free = np.array(times_free)
signal_free = np.array(signal_free)
times_locked = np.array(times_locked)
signal_locked = np.array(signal_locked)


### Calibration of the laser : 

a = 570.2381  # microW / V
b = 7.7619    # microW

def P(V): 
    return a*V +b # microW

signal_locked = P(signal_locked)


m = np.mean(signal_locked)
d = np.std(signal_locked, ddof = 1)

y_up = m + d
y_down = m - d


y_up2 = m + 2*d
y_down2 = m - 2*d



print(y_up - y_down)
print(y_up2 - y_down2)


fig = plt.figure()
plt.plot(times_locked, signal_locked, color = 'cornflowerblue', marker = '.', linestyle = '', zorder = 0)

xmax = times_locked[np.argmax(signal_locked)]
ymax = signal_locked.max()
xmin = times_locked[np.argmin(signal_locked)]
ymin = signal_locked.min()
ax=plt.gca()
x_bounds = ax.get_xbound()
y_bounds = ax.get_ybound()
ax.set_xlim(x_bounds[0], x_bounds[1])
ax.set_ylim(y_bounds[0], y_bounds[1])
# plt.hlines(y_up2, x_bounds[0] ,x_bounds[1], colors ='orange', linestyles='dashed')
# plt.hlines(y_down2, x_bounds[0] ,x_bounds[1], colors='orange', linestyles='dashed')
plt.hlines(y_up, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'std = {d:.4f}')
plt.hlines(y_down, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'red bandwidth: {y_up - y_down:.4f} microWatts')
plt.hlines(m, x_bounds[0] ,x_bounds[1], colors='black', linestyles='dashed', zorder=1, label = f'mean = {m:.4f}') 


plt.legend(fontsize=20) 
plt.xlabel('times (seconds)')
plt.ylabel('Power (microWatts)')
plt.title(f'Power of the blue laser (422nm): Power setpoint = {P(0.08):.4f} microWatts')
plt.rc('axes', titlesize=20)
plt.rc('axes', labelsize = 20) 
plot_file = os.path.join(figures_dir, "locked_laser.png")
plt.show()



err_locked = [signal_locked[i] - m for i in range(len(signal_locked))]


mean, std = norm.fit(err_locked)


fig = plt.figure()
plt.hist(err_locked, bins = 'auto', zorder = 0, color = 'cornflowerblue', density = True)
ax=plt.gca()
x_bounds = ax.get_xbound()
y_bounds = ax.get_ybound()
ax.set_xlim(x_bounds[0], x_bounds[1])
ax.set_ylim(y_bounds[0], y_bounds[1])
# plt.vlines(errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1, label = f'std: {errstd:.4f}' )
# plt.vlines(-errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1)
# plt.vlines(2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
# plt.vlines(-2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
plt.xlabel('Dispersion (microWatts)')
plt.ylabel('Number of points')
# plt.rc('axes', titlesize=20)
# plt.rc('axes', labelsize = 20) 
x =np.linspace(x_bounds[0], x_bounds[1], 100)
plt.plot(x, norm.pdf(x, mean, std), zorder = 1, color = 'red', label = f'Gaussian fitting: \n mean = {mean:.4f} \n std = {std:.4f}')
plt.legend()
plt.show()