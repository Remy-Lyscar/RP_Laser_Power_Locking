import time
import socket
import numpy as np
import matplotlib.pyplot as plt
import communication_device as pzt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QLineEdit
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class FrequencyControlThread(QThread):
    data_received = pyqtSignal(float, float)  # Signal to update the GUI

    def __init__(self, n, freq_increment, freq_target, switch_interval, parent=None):
        super(FrequencyControlThread, self).__init__(parent)
        self.udp_port = 37020
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.client.bind(('', self.udp_port))

        self.eps = 0.5
        self.t0 = time.time()
        self.n = n
        self.freq_increment = freq_increment
        self.fc = 274590100
        self.range = 50
        self.alpha = 16.999
        self.Kp = 1 / self.alpha
        self.Ki = 0.00001
        self.integral = 0

        self.freq_target = freq_target
        self.times = []
        self.frequencies = []

        self.ser = pzt.init_serial_connection()
        self.vnow = pzt.read_voltage(self.ser)

        self.last_update_time = time.time()
        self.condition_flag = 1
        self.condition_timer = time.time()
        self.switch_interval = switch_interval

    def run(self):
        while True:
            try:
                data1, addr = self.client.recvfrom(1024)
                f_1092 = float(data1)
            except Exception as e:
                continue

            deltaf = f_1092 - self.freq_target
            proportional = deltaf
            self.integral += deltaf
            correction = (self.Kp * proportional) + (self.Ki * self.Kp * self.integral)
            
            if deltaf >  0:
                self.vnow += correction
            elif deltaf < 0:
                self.vnow -= - correction

            self.vnow = max(2, min(145, self.vnow))
            pzt.write_voltage(self.ser, self.vnow)

            current_time = time.time() - self.t0
            self.times.append(current_time)
            self.frequencies.append(f_1092)

            if len(self.times) > 100:
                self.times.pop(0)
                self.frequencies.pop(0)

            self.data_received.emit(current_time, f_1092)
            self.ser.flush()

            if time.time() - self.last_update_time >= self.n:
                if self.condition_flag == 1:
                    if self.freq_target < self.fc:
                        self.freq_target += self.freq_increment
                    else:
                        self.condition_flag = 2
                        self.condition_timer = time.time()
                elif self.condition_flag == 2:
                    self.freq_target -= self.freq_increment
                self.last_update_time = time.time()

            if time.time() - self.condition_timer >= self.switch_interval/2:
                self.condition_flag = 2 if self.condition_flag == 1 else 1
                self.condition_timer = time.time()

class FrequencyControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Spectral Analysis')

        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_control)
        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_control)
        self.stop_button.setEnabled(False)

        self.clear_button = QPushButton('Clear Plot', self)
        self.clear_button.clicked.connect(self.clear_plot)
        self.clear_button.setEnabled(False)

        self.freq_label = QLabel('Current Frequency: ', self)
        self.freq_label.setStyleSheet("QLabel { color : black; }")

        self.n_label = QLabel('Lock Duration (s):', self)
        self.n_input = QLineEdit(self)
        self.n_input.setText('30')

        self.freq_increment_label = QLabel('Frequency Increment:', self)
        self.freq_increment_input = QLineEdit(self)
        self.freq_increment_input.setText('20')

        self.freq_target_label = QLabel('Frequency Target:', self)
        self.freq_target_input = QLineEdit(self)
        self.freq_target_input.setText('274590000')

        self.switch_interval_label = QLabel('Analysis Duration (s):', self)
        self.switch_interval_input = QLineEdit(self)
        self.switch_interval_input.setText('180')

        self.figure, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Frequency (MHz)')

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.freq_label)
        layout.addWidget(self.n_label)
        layout.addWidget(self.n_input)
        layout.addWidget(self.freq_increment_label)
        layout.addWidget(self.freq_increment_input)
        layout.addWidget
        layout.addWidget(self.freq_target_label)
        layout.addWidget(self.freq_target_input)
        layout.addWidget(self.switch_interval_label)
        layout.addWidget(self.switch_interval_input)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.clear_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.control_thread = None

    def start_control(self):
        n = int(self.n_input.text())
        freq_increment = float(self.freq_increment_input.text())
        freq_target = float(self.freq_target_input.text())
        switch_interval = int(self.switch_interval_input.text())

        if self.control_thread is None:
            self.control_thread = FrequencyControlThread(n, freq_increment, freq_target, switch_interval)
            self.control_thread.data_received.connect(self.update_plot)
            self.control_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    def stop_control(self):
        if self.control_thread is not None:
            self.control_thread.terminate()
            self.control_thread.ser.close()
            self.control_thread = None

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.clear_button.setEnabled(False)

    def update_plot(self, current_time, frequency):
        self.ax1.clear()
        self.ax1.plot(self.control_thread.times, self.control_thread.frequencies, 'b-')
        self.ax1.axhline(y=self.control_thread.freq_target, color='g', linestyle='--')
        self.ax1.fill_between(self.control_thread.times, 
                              self.control_thread.freq_target - self.control_thread.eps, 
                              self.control_thread.freq_target + self.control_thread.eps, 
                              color='green', alpha=0.3, label="Frequency range")
        self.ax1.legend()
        self.ax1.grid(True)
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Frequency (MHz)')
        self.canvas.draw()
        
        if abs(frequency - self.control_thread.freq_target) <= self.control_thread.eps:
            self.freq_label.setStyleSheet("QLabel { color : green; }")
        else:
            self.freq_label.setStyleSheet("QLabel { color : red; }")

        self.freq_label.setText(f'Current Frequency: {frequency:.2f} Hz')

    def clear_plot(self):
        self.ax1.clear()
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication([])
    window = FrequencyControlApp()
    window.show()
    app.exec_()
