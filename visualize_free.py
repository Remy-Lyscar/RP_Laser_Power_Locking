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
from scipy.stats import norm 
# import pathlib
# import matplotlib as mpl

# pathlib.Path.rmdir( mpl.get_cachedir())


plt.style.use('science')




current_dir = os.path.dirname(os.path.abspath(__file__))
figures_dir = os.path.join(current_dir, 'Figures et Data')
df_dir = os.path.join(current_dir, 'Dataframes')


if not os.path.exists(figures_dir):
    os.makedirs(figures_dir)
    

### Data ###
free = pickle.load(open(os.path.join(df_dir,'free_running_signal_jeu_4_juillet.pkl'), "rb"))
locked = pickle.load(open(os.path.join(df_dir,'locked_laser_jeu_4_juillet.pkl'), "rb"))

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



m = np.mean(signal_free)
d = np.std(signal_free, ddof = 1)

y_up = m + d
y_down = m - d

y_up2 = m + 2*d
y_down2 = m - 2*d


print(y_up - y_down)
print(y_up2 - y_down2)



fig = plt.figure()
plt.plot(times_free, signal_free, color = 'cornflowerblue', marker = '.', linestyle = '', zorder = 0)

xmax = times_free[np.argmax(signal_free)]
ymax = signal_free.max()
xmin = times_free[np.argmin(signal_free)]
ymin = signal_free.min()
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


plt.legend(fontsize = 20) 
plt.xlabel('times (seconds)')
plt.ylabel('Power (microWatts) ')
plt.title('Power of the blue laser (422nm) : free-running')
plt.rc('axes', titlesize=40)
plt.rc('axes', labelsize = 40) 
plot_file = os.path.join(figures_dir, "free_laser.png")
plt.grid()
plt.show()




### Polynomial fitting: 
    
def fit_function(x, a, b, c,d, e):  
    return a*x*4 + b*x**3 + c*x**2 + d*x +e 


### On va fitter par segments de 1000s, soit environ 2000 points

signal_free_seg = []
times_free_seg = []

Y_fit = []

n = 1000
q = len(times_free)//n
r = len(times_free)%n

for i in range(q): 
    signal_free_seg.append(signal_free[i*n:(i+1)*n])
    times_free_seg.append(times_free[i*n:(i+1)*n])
    
    popt, pcov = curve_fit(fit_function, times_free_seg[i], signal_free_seg[i])
    a, b, c, d, e = popt[0], popt[1], popt[2], popt[3], popt[4]
    # perr = np.sqrt(np.diag(pcov))
    Y_fit.append(fit_function(times_free_seg[i], a, b, c, d, e))
    


signal_free_seg.append(signal_free[q*n:])
times_free_seg.append(times_free[q*n:])

popt, pcov = curve_fit(fit_function, times_free_seg[q], signal_free_seg[q])
a, b, c, d,e  = popt[0], popt[1], popt[2], popt[3], popt[4]
# perr = np.sqrt(np.diag(pcov))
Y_fit.append(fit_function(times_free_seg[q], a, b, c, d, e))


Y_fit = np.concatenate([Y_fit[0], Y_fit[1], Y_fit[2], Y_fit[3], Y_fit[4], Y_fit[5], Y_fit[6]])

# print(Y_fit)

fig = plt.figure() 
plt.plot(times_free, signal_free, color = 'cornflowerblue', linestyle = '', marker = '.', zorder = 0)
plt.plot(times_free,Y_fit, color = 'red', zorder = 1, label = 'polynomial fitting' )
plt.legend(fontsize = 20)
plt.xlabel('times (seconds)')
plt.ylabel('Power (microWatts) ')
plt.title('Power of the blue laser (422nm) : free-running')
plt.rc('axes', titlesize=20)
plt.rc('axes', labelsize = 20) 
plt.grid()
plt.show()



err_free = [signal_free[i] - Y_fit[i] for i in range(len(signal_free))]


mean, std = norm.fit(err_free)


fig = plt.figure()
plt.hist(err_free, bins = 'auto', zorder = 0, color = 'cornflowerblue', density = True)
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
plt.ylabel('Probability')
# plt.rc('axes', titlesize=20)
# plt.rc('axes', labelsize = 20) 
x =np.linspace(x_bounds[0], x_bounds[1], 100)
plt.plot(x, norm.pdf(x, mean, std), zorder = 1, color = 'red', label = f'Gaussian fitting: \n mean = {mean:.4f} \n std = {std:.4f}')
plt.legend()
plt.show()

























