import time
import socket
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
import communication_device as pzt

class FrequencyControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Frequency Control")

        self.serial_connected = False
        self.udp_port = 37020
        self.eps = 0.5
        self.t0 = time.time()
        self.alpha = 16.958
        self.kp = 1 / self.alpha
        self.ki = 0.0001
        self.integral = 0
        self.times = []
        self.frequencies = []

        self.setup_ui()
        self.init_serial_connection()
        self.init_udp_socket()
        self.run()

    def setup_ui(self):
        self.figure, self.ax = plt.subplots()
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Frequency (Hz)')

        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.voltage_label = ttk.Label(self.control_frame, text="Voltage:")
        self.voltage_label.pack(side=tk.LEFT, padx=5)

        self.voltage_value = ttk.Label(self.control_frame, text="0")
        self.voltage_value.pack(side=tk.LEFT, padx=5)

        self.freq_label = ttk.Label(self.control_frame, text="Frequency:")
        self.freq_label.pack(side=tk.LEFT, padx=5)

        self.freq_value = ttk.Label(self.control_frame, text="0")
        self.freq_value.pack(side=tk.LEFT, padx=5)

        self.exit_button = ttk.Button(self.control_frame, text="Exit", command=self.root.quit)
        self.exit_button.pack(side=tk.RIGHT, padx=5)

    def init_serial_connection(self):
        try:
            self.ser = pzt.init_serial_connection()
            self.serial_connected = True
            pzt.write_voltage(self.ser, 75)
            self.vnow = pzt.read_voltage(self.ser)
            self.voltage_value.config(text=str(self.vnow))
        except Exception as e:
            print(f"Serial connection initialization failed: {e}")
            self.serial_connected = False

    def init_udp_socket(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client.bind(('', self.udp_port))

    def update_plot(self):
        self.ax.clear()
        self.ax.plot(self.times, self.frequencies, 'b-')
        self.ax.axhline(y=self.freq_target, color='g', linestyle='--')
        self.ax.fill_between(self.times, self.freq_target - self.eps, self.freq_target + self.eps, color='green', alpha=0.3, label="Frequency range")
        self.ax.legend()
        self.ax.grid(True)
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Frequency (Hz)')
        self.canvas.draw()

    def run(self):
        self.freq_target = np.loadtxt("/home/ipiq/diogene/Users/Valentin/Codes/freqtarget.txt", dtype=float)

        try:
            data1, addr = self.client.recvfrom(1024)
            print("Data received!")

            try:
                f_1092 = float(data1)
                print("Frequency =", f_1092)
                self.freq_value.config(text=str(f_1092))
            except ValueError:
                print(f"Conversion error: {data1} is not a valid floating-point number")
                self.root.after(100, self.run)
                return

        except socket.timeout:
            print("Socket timeout, retrying...")
            self.root.after(100, self.run)
            return
        except Exception as e:
            print(f"An error occurred: {e}")
            self.root.after(100, self.run)
            return

        deltaf = f_1092 - self.freq_target
        print("Signal Error =", deltaf)

        proportional = np.abs(deltaf)
        self.integral += deltaf
        correction = (self.kp * proportional) + (self.ki * self.kp * self.integral)
        print("Correction =", correction)

        if deltaf > 0:
            self.vnow += correction
        elif deltaf < 0:
            self.vnow -= correction

        self.vnow = max(2, min(145, self.vnow))

        if self.serial_connected:
            pzt.write_voltage(self.ser, self.vnow)
            print("Voltage adjusted to", self.vnow)
            self.voltage_value.config(text=str(self.vnow))

        current_time = time.time() - self.t0
        self.times.append(current_time)
        self.frequencies.append(f_1092)

        if len(self.times) > 100:
            self.times.pop(0)
            self.frequencies.pop(0)

        self.update_plot()
        self.root.after(100, self.run)

if __name__ == "__main__":
    root = tk.Tk()
    app = FrequencyControlApp(root)
    root.mainloop()
