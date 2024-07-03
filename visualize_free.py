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
    

### Data ###
free = pickle.load(open(os.path.join(df_dir,'free_running_signal_mer_3_juillet.pkl'), "rb"))
locked = pickle.load(open(os.path.join(df_dir,'locked_laser_mer_3_juillet.pkl'), "rb"))

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
plt.hlines(y_up2, x_bounds[0] ,x_bounds[1], colors ='orange', linestyles='dashed')
plt.hlines(y_down2, x_bounds[0] ,x_bounds[1], colors='orange', linestyles='dashed')
plt.hlines(y_up, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'std = {d:.4f}')
plt.hlines(y_down, x_bounds[0] ,x_bounds[1], colors='red', linestyles='dashed', zorder=1, label = f'red bandwidth: {y_up - y_down:.4f} microWatts')
plt.hlines(m, x_bounds[0] ,x_bounds[1], colors='black', linestyles='dashed', zorder=1, label = f'mean = {m:.4f}') 


plt.legend(fontsize = 20) 
plt.xlabel('times (seconds)')
plt.ylabel('Power (microWatts) ')
plt.title('Power of the blue laser (422nm) : free-running')
plt.rc('axes', titlesize=20)
plt.rc('axes', labelsize = 20) 
plot_file = os.path.join(figures_dir, "free_laser.png")
plt.grid()
plt.show()




# def fit_function(x, a, b, c, d, e, f, g, h, i, j, k, l):
#     return a*x**11 + b*x**10 + c*x**9 + d*x**8+ e*x**7 + f*x**6 + g*x**5 + h*x**4 + i*x**3 + j*x**2 +k*x + l 



# popt, pcov = curve_fit(fit_function, times_free, signal_free)
# a, b, c, d, e, f, g, h, i, j,  k, l = popt[0], popt[1], popt[2], popt[3], popt[4], popt[5], popt[6], popt[7], popt[8], popt[9], popt[10], popt[11]
# perr = np.sqrt(np.diag(pcov))
# fig = plt.figure()
# plt.plot(times_free, signal_free, times_free, fit_function(times_free, a, b, c, d, e, f, g, h, i, j, k, l))
# plt.show()


# Y = fit_function(times_free, a, b, c, d, e, f, g,h, i, j , k , l)
# err_free = [signal_free[i] - Y[i] for i in range(len(times_free))]



# Y = []
# T = []
# nmoy = 20
# N = int(len(signal_free)/nmoy)
# for i in range(0, N-1, nmoy): 
#     for k in range(nmoy): 
#         Y.append(sum(signal_free[i*nmoy:(i+1)*nmoy]))
#         T.append((times_free[(i+1)*nmoy] - times_free[i*nmoy])/2)
        


# fig = plt.figure()
# plt.plot(times_free, signal_free, color = 'cornflowerblue', marker = '.', linestyle = '', zorder = 0)
# plt.plot(T, Y, label = 'post-processing average')
# plt.legend(fontsize = 20) 
# plt.xlabel('times (seconds)')
# plt.ylabel('Power (microWatts) ')
# plt.title('Power of the blue laser (422nm) : free-running')
# plt.rc('axes', titlesize=20)
# plt.rc('axes', labelsize = 20) 
# plt.grid()
# plt.show()




# err_free = []
# errstd = np.std(err_free, ddof = 1)


# fig = plt.figure()
# plt.hist(err_free, bins = 'auto', zorder = 0)
# ax=plt.gca()
# x_bounds = ax.get_xbound()
# y_bounds = ax.get_ybound()
# ax.set_xlim(x_bounds[0], x_bounds[1])
# ax.set_ylim(y_bounds[0], y_bounds[1])
# plt.vlines(errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1, label = f'std: {errstd:.4f}' )
# plt.vlines(-errstd, y_bounds[0], y_bounds[1], colors = 'red', linestyles = 'dashed', zorder = 1)
# plt.vlines(2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
# plt.vlines(-2*errstd, y_bounds[0], y_bounds[1], colors = 'orange', linestyles = 'dashed', zorder = 1)
# plt.xlabel('Dispersion (microWatts)')
# plt.ylabel('Number of points')
# plt.legend()
# plt.show()
