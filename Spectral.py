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
n = 30  # Frequency update interval in seconds
freq_increment = 20  # Frequency increment value
range = 50
# PID controller parameters
alpha = 16.999
Kp = 1 / alpha  # Proportional gain
Ki = 0.00001     # Integral gain
integral = 0

# Initialize freq_target
freq_target = np.loadtxt("/home/ipiq/diogene/Users/Valentin/Codes/freqtarget.txt", dtype=float)
fc = 274590100
# Lists to store time and frequency values for plotting
times = []
frequencies = []

# Initialize the plot
plt.ion()  # Interactive mode
fig, ax1 = plt.subplots()
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Frequency (Hz)')

def update_plot():
    ax1.clear()
    ax1.plot(times, frequencies, 'b-')
    ax1.axhline(y=freq_target, color='g', linestyle='--')
    ax1.fill_between(times, freq_target - eps, freq_target + eps, color='green', alpha=0.3, label="Frequency range")
    ax1.legend()
    ax1.grid(True)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Frequency (Hz)')
    plt.pause(0.001)  # Pause to update the plot

ser = pzt.init_serial_connection()
vnow = pzt.read_voltage(ser)

last_update_time = time.time()  # Initialize the last update time

# Initialize flag and timer
condition_flag = 1  # Start with the first condition
condition_timer = time.time()

while True:
    try:
        data1, addr = client.recvfrom(1024)
        print("Data received!")

        # Convert the string to a floating-point number
        try:
            f_1092 = float(data1)
            print("Frequency =", f_1092)
        except ValueError:
            print(f"Conversion error: {data1} is not a valid floating-point number")
            continue

    except socket.timeout:
        print("Socket timeout, retrying...")
        continue
    except Exception as e:
        print(f"An error occurred: {e}")
        continue
    
    deltaf = f_1092 - freq_target
    print("Signal Error =", deltaf)

    # PID calculations
    proportional = deltaf
    integral += deltaf
    correction = (Kp * proportional) + (Ki * Kp * integral)
    print("Correction =", correction)
    
    deltaf = f_1092 - freq_target

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
    frequencies.append(f_1092)

    # Limit lists to 100 data points to reduce memory usage
    if len(times) > 100:
        times.pop(0)
        frequencies.pop(0)

    # Update the plot
    update_plot()
    ser.flush()

    # Check if it's time to update freq_target
    if time.time() - last_update_time >= n:
        # If condition_flag is 1, apply the first condition for 1 minute
        if condition_flag == 1:
            # If freq_target is below the upper limit
            if freq_target < fc:
                freq_target += freq_increment
            else:
                # Switch to the second condition after 1 minute
                condition_flag = 2
                condition_timer = time.time()
        # If condition_flag is 2, apply the second condition for 1 minute
        elif condition_flag == 2:
            freq_target -= freq_increment


        # Update last update time
        last_update_time = time.time()

    # Check if it's time to switch conditions
    if time.time() - condition_timer >= 180:
        condition_flag = 2 if condition_flag == 1 else 1
        condition_timer = time.time()
