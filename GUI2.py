import sys
import time
import socket
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QLineEdit, QCheckBox, QFileDialog
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import communication_device as pzt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Laser Lock GUI")
        self.setGeometry(100, 100, 800, 600)

        # Initialize the main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Set the layout
        layout = QVBoxLayout(self.main_widget)

        # Initialize plot
        self.fig, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Initialize labels
        self.freq_label = QLabel("Current Frequency: N/A")
        layout.addWidget(self.freq_label)

        # Initialize freq_target input box
        self.freq_target_edit = QLineEdit()
        self.freq_target_edit.setPlaceholderText("Enter Target Frequency")
        layout.addWidget(self.freq_target_edit)

        # Initialize the start and stop buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_program)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_program)
        layout.addWidget(self.stop_button)

        # Initialize the save button
        self.save_button = QPushButton("Save Figure")
        self.save_button.clicked.connect(self.save_figure)
        layout.addWidget(self.save_button)

        # Initialize the checkbox to show/hide the plot
        self.plot_checkbox = QCheckBox("Show Plot")
        self.plot_checkbox.setChecked(True)  # Default is to show the plot
        self.plot_checkbox.stateChanged.connect(self.toggle_plot)
        layout.addWidget(self.plot_checkbox)


        # UDP socket configuration
        self.UDP_PORT = 37020
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client.bind(('', self.UDP_PORT))

        # Variables
        self.eps = 0.5
        self.t0 = time.time()  # Initialize the start time
        self.freq_target = None
        self.timer = None

        # PID controller parameters
        self.alpha = 16.958
        self.Kp = 1 / self.alpha  # Proportional gain
        self.Ki = 0.0001          # Integral gain
        self.integral = 0

        # Lists to store time and frequency values for plotting
        self.times = []
        self.frequencies = []

        # Initially show the plot
        self.plot_visible = True

    def start_program(self):
        self.freq_target = float(self.freq_target_edit.text())
        if self.freq_target is None:
            print("Please enter a valid target frequency.")
            return
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1)  

    def stop_program(self):
        if self.timer is not None:
            self.timer.stop()
            self.timer = None

    def update_data(self):
        
        self.ser = pzt.init_serial_connection()
        self.vnow = pzt.read_voltage(self.ser)
        self.vnow = pzt.read_voltage(self.ser)
        self.vnow = pzt.read_voltage(self.ser)
        try:
            freq_target = float(self.freq_target_edit.text())
        except ValueError:
            print("Invalid target frequency value.")
            return

        try:
            data1, addr = self.client.recvfrom(1024)
            print("Data received!")

            # Convert the string to a floating-point number
            try:
                f_1092 = float(data1)
                print("Frequency =", f_1092)
                if -self.eps <= f_1092 - freq_target <= self.eps:
                    self.freq_label.setStyleSheet("QLabel { color : green; }")
                else:
                    self.freq_label.setStyleSheet("QLabel { color : red; }")
                self.freq_label.setText(f"Current Frequency: {f_1092}")
            except ValueError:
                print(f"Conversion error: {data1} is not a valid floating-point number")
                return

        except socket.timeout:
            print("Socket timeout, retrying...")
            return
        except Exception as e:
            print(f"An error occurred: {e}")
            return

        deltaf = f_1092 - freq_target
        print("Signal Error =", deltaf)

        # PID calculations
        proportional = np.abs(deltaf)
        self.integral += deltaf
        correction = (self.Kp * proportional) + (self.Ki * self.Kp * self.integral)
        print("Correction =", correction)

        # Apply correction based on the PID controller output
        if deltaf > 0:
            self.vnow += correction
        elif deltaf < 0:
            self.vnow -= correction

        # Limit vnow between 2 and 145
        self.vnow = max(2, min(145, self.vnow))
        try:
            pzt.write_voltage(self.ser, self.vnow)
        except Exception as e:
            print(f"Failed to write voltage: {e}")
            return
        print("Voltage adjusted to", self.vnow)

        # Record the data
        current_time = time.time() - self.t0
        self.times.append(current_time)
        self.frequencies.append(f_1092)

        # Limit lists to 100 data points to reduce memory usage
        if len(self.times) > 100:
            self.times.pop(0)
            self.frequencies.pop(0)

        # Update the plot if it's visible
        if self.plot_visible:
            self.update_plot()
        self.vnow = pzt.read_voltage(self.ser)
        self.vnow = pzt.read_voltage(self.ser)
        pzt.close_serial_connection(self.ser)
    def update_plot(self):
        self.ax1.clear()
        self.ax1.plot(self.times, self.frequencies, 'b-')
        self.ax1.axhline(y=self.freq_target, color='g', linestyle='--')
        self.ax1.fill_between(self.times, self.freq_target - self.eps, self.freq_target + self.eps, color='green', alpha=0.3, label="Frequency range")
        self.ax1.legend()
        self.ax1.grid(True)
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Frequency (Hz)')
        self.canvas.draw()

    def toggle_plot(self):
        self.plot_visible = self.plot_checkbox.isChecked()
        if not self.plot_visible:
            self.ax1.clear()
            self.canvas.draw()

    def save_figure(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Figure", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;All Files (*)")
        if filename:
            self.fig.savefig(filename)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())