import time
import socket
import numpy as np
import matplotlib.pyplot as plt
import communication_device as pzt


# UDP socket configuration
UDP_PORT = 37020
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(('', UDP_PORT))

# Variables
eps = 0.5
t0 = time.time()  # Initialize the start time
# PID controller parameters
alpha = 5
Kp = 1 / alpha  # Proportional gain
Ki = 0.00001     # Integral gain
integral = 0
# Lists to store time and frequency values for plotting
times = []
frequencies = []
# Initialize the plot
plt.ion()  # Interactive mode
fig, ax1 = plt.subplots()
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Frequency (Hz)')
def update_plot():
    freq_target = 290210320
    ax1.clear()
    ax1.plot(times, frequencies, 'b-')
    ax1.axhline(y=freq_target, color='g', linestyle='--')
    ax1.fill_between(times, freq_target - eps, freq_target + eps, color='green', alpha=0.3, label="Frequency range")
    ax1.legend()
    ax1.grid(True)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Frequency (MHz)')
    plt.pause(0.001)  # Pause to update the plot

ser = pzt.init_serial_connection()
vnow = pzt.read_voltage(ser)
pzt.write_voltage(ser,75)

while True:
    data = ''
    freq_target = 290210320
    data1, addr = client.recvfrom(1024)
    if data1 != data :   
        data1_str = data1.decode('utf-8')
        if data1_str[0]=='4':
            f_1033 = float(data1_str[1:])
            print("Laser 1033 =",f_1033)
            deltaf = f_1033 - freq_target
            print("Signal Error =", deltaf)

            # PID calculations
            proportional = deltaf
            integral += deltaf
            correction = (Kp * proportional) + (Ki * Kp * integral)
            print("Correction =", correction)
            
            deltaf = f_1033 - freq_target
            
            vnow = pzt.read_voltage(ser)

            # Apply correction based on the PID controller output
            if deltaf >  0:
                vnow += correction
            elif deltaf < 0:
                vnow -= - correction

            # Limit vnow between 2 and 145
            vnow = max(2, min(145, vnow))
            pzt.write_voltage(ser, vnow)
            print("Voltage adjusted to", vnow)

            # Record the data
            current_time = time.time() - t0
            times.append(current_time)
            frequencies.append(f_1033)

            # Limit lists to 100 data points to reduce memory usage
            if len(times) > 100:
                times.pop(0)
                frequencies.pop(0)

            # Update the plot
            update_plot()
            
            ser.flush()
        else :
            print("no data")