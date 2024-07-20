import sys
import socket
import numpy as np
import matplotlib.pyplot as plt
import time
from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QCheckBox, QLabel, 
                             QFileDialog, QMainWindow, QTabWidget, QComboBox)
from PyQt5.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import communication_device as pzt
import communication_device_etherlight as eth

# LASER LOCK SYSTEM
pzt.ser.close()

# First application classes
class PIDThread(QThread):
    update_signal = pyqtSignal(float, float, str)

    def __init__(self, target_freq, eps):
        super().__init__()
        self.target_freq = target_freq
        self.eps = eps
        self.running = False
        self.times = []
        self.frequencies = []

    def run(self):
        UDP_PORT = 37020
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(('', UDP_PORT))

        alpha = 16.999
        Kp = 1 / alpha
        Ki = 0.00001
        integral = 0

        t0 = time.time()
        ser = pzt.init_serial_connection()
        vnow = pzt.read_voltage(ser)
        pzt.write_voltage(ser, 75)

        while self.running:
            time.sleep(0.1)
            data1, addr = client.recvfrom(1024)
            data1_str = data1.decode('utf-8')
            if data1_str[0]=='1':
                f_1092 = float(data1_str[1:])
                deltaf = f_1092 - self.target_freq
                proportional = deltaf
                integral += deltaf
                correction = (Kp * proportional) + (Ki * Kp * integral)

                if deltaf > 0:
                    vnow += correction
                elif deltaf < 0:
                    vnow -= -correction

                vnow = max(2, min(145, vnow))
                pzt.write_voltage(ser, vnow)

                current_time = time.time() - t0
                self.times.append(current_time)
                self.frequencies.append(f_1092)

                if len(self.times) > 100:
                    self.times.pop(0)
                    self.frequencies.pop(0)

                status = "green" if -self.eps <= deltaf <= self.eps else "red"
                self.update_signal.emit(f_1092, self.target_freq, status)

                ser.flush()
                time.sleep(0.1)

    def start_control(self, target_freq, eps):
        self.target_freq = target_freq
        self.eps = eps
        self.running = True
        self.start()

    def stop_control(self):
        self.running = False
        self.wait()

    def get_data(self):
        return self.times, self.frequencies


class PIDControllerGUI(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.pid_thread = PIDThread(target_freq=0.0, eps=0.5)
        self.original_target_freq = 0.0
        self.pid_thread.update_signal.connect(self.update_display)

    def initUI(self):
        self.setWindowTitle('Laser Lock GUI')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        freq_layout = QVBoxLayout()

        self.start_button = QPushButton('Start Lock')
        self.start_button.clicked.connect(self.start_control)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_control)

        self.target_freq_input = QLineEdit(self)
        self.target_freq_input.setPlaceholderText('274589050')

        self.live_plot_checkbox = QCheckBox('Live Plot')
        self.live_plot_checkbox.setChecked(True)

        self.current_freq_label = QLabel('Current Frequency: -- MHz')
        self.current_freq_label.setStyleSheet('color: black')

        self.increase_freq_button = QPushButton('+1 MHz')
        self.increase_freq_button.clicked.connect(self.increase_target_freq)
        self.decrease_freq_button = QPushButton('-1 MHz')
        self.decrease_freq_button.clicked.connect(self.decrease_target_freq)

        self.save_plot_button = QPushButton('Save Plot')
        self.save_plot_button.clicked.connect(self.save_plot)

        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_target_freq)

        self.fig, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.target_freq_input)
        control_layout.addWidget(self.live_plot_checkbox)
        control_layout.addWidget(self.save_plot_button)
        control_layout.addWidget(self.reset_button)

        freq_layout.addWidget(self.current_freq_label)
        freq_layout.addWidget(self.increase_freq_button)
        freq_layout.addWidget(self.decrease_freq_button)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(freq_layout)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

    def start_control(self):
        try:
            target_freq = float(self.target_freq_input.text())
        except ValueError:
            target_freq = 0.0
        self.original_target_freq = target_freq
        eps = 0.5  # Set epsilon as needed
        self.pid_thread.start_control(target_freq, eps)

    def stop_control(self):
        self.pid_thread.stop_control()

    def increase_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target += 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def decrease_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target -= 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def reset_target_freq(self):
        self.target_freq_input.setText(str(self.original_target_freq))
        self.pid_thread.target_freq = self.original_target_freq

    def save_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            self.fig.savefig(file_path)

    def update_display(self, current_freq, target_freq, status):
        self.current_freq_label.setText(f'Current Frequency: {current_freq} Hz')
        self.current_freq_label.setStyleSheet(f'color: {status}')

        if self.live_plot_checkbox.isChecked():
            times, frequencies = self.pid_thread.get_data()
            self.ax1.clear()
            self.ax1.plot(times, frequencies, 'b-', label='Measured Frequency')
            self.ax1.axhline(y=target_freq, color='g', linestyle='--', label='Target Frequency')
            self.ax1.fill_between(times, target_freq - self.pid_thread.eps, target_freq + self.pid_thread.eps, color='green', alpha=0.3, label="Frequency range")
            self.ax1.legend()  # Ensure legend includes labeled artists
            self.ax1.grid(True)
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Frequency (MHz)')
            self.canvas.draw()
# Second application classes
class PIDThread1(QThread):
    update_signal = pyqtSignal(float, float, str)

    def __init__(self, target_freq, eps):
        super().__init__()
        self.target_freq = target_freq
        self.eps = eps
        self.running = False
        self.times = []
        self.frequencies = []

    def run(self):
        UDP_PORT = 37020
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(('', UDP_PORT))

        alpha = 16.999
        Kp = 1 / alpha
        Ki = 0.00001
        integral = 0

        t0 = time.time()
        ser1 = eth.init_serial_connection_1()
        vnow = eth.read_voltage_z(ser1)
        eth.write_voltage_z(ser1, 75)

        while self.running:
            time.sleep(0.1)
            data1, addr = client.recvfrom(1024)
            data1_str = data1.decode('utf-8')
            if data1_str[0]=='4':
                f_1033 = float(data1_str[1:])
                deltaf = f_1033 - self.target_freq
                proportional = deltaf
                integral += deltaf
                correction = (Kp * proportional) + (Ki * Kp * integral)

                if deltaf > 0:
                    vnow += correction
                elif deltaf < 0:
                    vnow -= -correction

                vnow = max(2, min(145, vnow))
                eth.write_voltage_z(ser1, vnow)

                current_time = time.time() - t0
                self.times.append(current_time)
                self.frequencies.append(f_1033)

                if len(self.times) > 100:
                    self.times.pop(0)
                    self.frequencies.pop(0)

                status = "green" if -self.eps <= deltaf <= self.eps else "red"
                self.update_signal.emit(f_1033, self.target_freq, status)

                ser1.flush()
                time.sleep(0.1)

    def start_control(self, target_freq, eps):
        self.target_freq = target_freq
        self.eps = eps
        self.running = True
        self.start()

    def stop_control(self):
        self.running = False
        self.wait()

    def get_data(self):
        return self.times, self.frequencies


class PIDControllerGUI1(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.pid_thread = PIDThread(target_freq=0.0, eps=0.5)
        self.original_target_freq = 0.0
        self.pid_thread.update_signal.connect(self.update_display)

    def initUI(self):
        self.setWindowTitle('Laser Lock GUI')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        freq_layout = QVBoxLayout()

        self.start_button = QPushButton('Start Lock')
        self.start_button.clicked.connect(self.start_control)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_control)

        self.target_freq_input = QLineEdit(self)
        self.target_freq_input.setPlaceholderText('290210320')

        self.live_plot_checkbox = QCheckBox('Live Plot')
        self.live_plot_checkbox.setChecked(True)

        self.current_freq_label = QLabel('Current Frequency: -- MHz')
        self.current_freq_label.setStyleSheet('color: black')

        self.increase_freq_button = QPushButton('+1 MHz')
        self.increase_freq_button.clicked.connect(self.increase_target_freq)
        self.decrease_freq_button = QPushButton('-1 MHz')
        self.decrease_freq_button.clicked.connect(self.decrease_target_freq)

        self.save_plot_button = QPushButton('Save Plot')
        self.save_plot_button.clicked.connect(self.save_plot)

        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_target_freq)

        self.fig, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.target_freq_input)
        control_layout.addWidget(self.live_plot_checkbox)
        control_layout.addWidget(self.save_plot_button)
        control_layout.addWidget(self.reset_button)

        freq_layout.addWidget(self.current_freq_label)
        freq_layout.addWidget(self.increase_freq_button)
        freq_layout.addWidget(self.decrease_freq_button)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(freq_layout)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

    def start_control(self):
        try:
            target_freq = float(self.target_freq_input.text())
        except ValueError:
            target_freq = 0.0
        self.original_target_freq = target_freq
        eps = 0.5  # Set epsilon as needed
        self.pid_thread.start_control(target_freq, eps)

    def stop_control(self):
        self.pid_thread.stop_control()

    def increase_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target += 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def decrease_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target -= 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def reset_target_freq(self):
        self.target_freq_input.setText(str(self.original_target_freq))
        self.pid_thread.target_freq = self.original_target_freq

    def save_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            self.fig.savefig(file_path)

    def update_display(self, current_freq, target_freq, status):
        self.current_freq_label.setText(f'Current Frequency: {current_freq} Hz')
        self.current_freq_label.setStyleSheet(f'color: {status}')

        if self.live_plot_checkbox.isChecked():
            times, frequencies = self.pid_thread.get_data()
            self.ax1.clear()
            self.ax1.plot(times, frequencies, 'b-', label='Measured Frequency')
            self.ax1.axhline(y=target_freq, color='g', linestyle='--', label='Target Frequency')
            self.ax1.fill_between(times, target_freq - self.pid_thread.eps, target_freq + self.pid_thread.eps, color='green', alpha=0.3, label="Frequency range")
            self.ax1.legend()  # Ensure legend includes labeled artists
            self.ax1.grid(True)
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Frequency (MHz)')
            self.canvas.draw()
# First application classes
class PIDThread2(QThread):
    update_signal = pyqtSignal(float, float, str)

    def __init__(self, target_freq, eps):
        super().__init__()
        self.target_freq = target_freq
        self.eps = eps
        self.running = False
        self.times = []
        self.frequencies = []

    def run(self):
        UDP_PORT = 37020
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(('', UDP_PORT))

        alpha = 16.999
        Kp = 1 / alpha
        Ki = 0.00001
        integral = 0

        t0 = time.time()
        ser = pzt.init_serial_connection()
        vnow = pzt.read_voltage(ser)
        pzt.write_voltage(ser, 75)

        while self.running:
            time.sleep(0.1)
            data1, addr = client.recvfrom(1024)
            data1_str = data1.decode('utf-8')
            if data1_str[0]=='3':
                f_1003 = float(data1_str[1:])
                deltaf = f_1003 - self.target_freq
                proportional = deltaf
                integral += deltaf
                correction = (Kp * proportional) + (Ki * Kp * integral)

                if deltaf > 0:
                    vnow += correction
                elif deltaf < 0:
                    vnow -= -correction

                vnow = max(2, min(145, vnow))
                pzt.write_voltage(ser, vnow)

                current_time = time.time() - t0
                self.times.append(current_time)
                self.frequencies.append(f_1003)

                if len(self.times) > 100:
                    self.times.pop(0)
                    self.frequencies.pop(0)

                status = "green" if -self.eps <= deltaf <= self.eps else "red"
                self.update_signal.emit(f_1003, self.target_freq, status)

                ser.flush()
                time.sleep(0.1)

    def start_control(self, target_freq, eps):
        self.target_freq = target_freq
        self.eps = eps
        self.running = True
        self.start()

    def stop_control(self):
        self.running = False
        self.wait()

    def get_data(self):
        return self.times, self.frequencies


class PIDControllerGUI2(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.pid_thread = PIDThread(target_freq=0.0, eps=0.5)
        self.original_target_freq = 0.0
        self.pid_thread.update_signal.connect(self.update_display)

    def initUI(self):
        self.setWindowTitle('Laser Lock GUI')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        freq_layout = QVBoxLayout()

        self.start_button = QPushButton('Start Lock')
        self.start_button.clicked.connect(self.start_control)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_control)

        self.target_freq_input = QLineEdit(self)
        self.target_freq_input.setPlaceholderText('298616060')

        self.live_plot_checkbox = QCheckBox('Live Plot')
        self.live_plot_checkbox.setChecked(True)

        self.current_freq_label = QLabel('Current Frequency: -- MHz')
        self.current_freq_label.setStyleSheet('color: black')

        self.increase_freq_button = QPushButton('+1 MHz')
        self.increase_freq_button.clicked.connect(self.increase_target_freq)
        self.decrease_freq_button = QPushButton('-1 MHz')
        self.decrease_freq_button.clicked.connect(self.decrease_target_freq)

        self.save_plot_button = QPushButton('Save Plot')
        self.save_plot_button.clicked.connect(self.save_plot)

        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_target_freq)

        self.fig, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.target_freq_input)
        control_layout.addWidget(self.live_plot_checkbox)
        control_layout.addWidget(self.save_plot_button)
        control_layout.addWidget(self.reset_button)

        freq_layout.addWidget(self.current_freq_label)
        freq_layout.addWidget(self.increase_freq_button)
        freq_layout.addWidget(self.decrease_freq_button)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(freq_layout)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

    def start_control(self):
        try:
            target_freq = float(self.target_freq_input.text())
        except ValueError:
            target_freq = 0.0
        self.original_target_freq = target_freq
        eps = 0.5  # Set epsilon as needed
        self.pid_thread.start_control(target_freq, eps)

    def stop_control(self):
        self.pid_thread.stop_control()

    def increase_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target += 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def decrease_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target -= 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def reset_target_freq(self):
        self.target_freq_input.setText(str(self.original_target_freq))
        self.pid_thread.target_freq = self.original_target_freq

    def save_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            self.fig.savefig(file_path)

    def update_display(self, current_freq, target_freq, status):
        self.current_freq_label.setText(f'Current Frequency: {current_freq} Hz')
        self.current_freq_label.setStyleSheet(f'color: {status}')

        if self.live_plot_checkbox.isChecked():
            times, frequencies = self.pid_thread.get_data()
            self.ax1.clear()
            self.ax1.plot(times, frequencies, 'b-', label='Measured Frequency')
            self.ax1.axhline(y=target_freq, color='g', linestyle='--', label='Target Frequency')
            self.ax1.fill_between(times, target_freq - self.pid_thread.eps, target_freq + self.pid_thread.eps, color='green', alpha=0.3, label="Frequency range")
            self.ax1.legend()  # Ensure legend includes labeled artists
            self.ax1.grid(True)
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Frequency (MHz)')
            self.canvas.draw()


# Fourth application classes
class PIDThread3(QThread):
    update_signal = pyqtSignal(float, float, str)

    def __init__(self, target_freq, eps):
        super().__init__()
        self.target_freq = target_freq
        self.eps = eps
        self.running = False
        self.times = []  
        self.frequencies = []

    def run(self):
        UDP_PORT = 37020
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(('', UDP_PORT))

        alpha = 16.999
        Kp = 1 / alpha
        Ki = 0.00001
        integral = 0

        t0 = time.time()
        ser = pzt.init_serial_connection()
        vnow = pzt.read_voltage(ser)
        pzt.write_voltage(ser, 75)

        while self.running:
            time.sleep(0.1)
            data1, addr = client.recvfrom(1024)
            data1_str = data1.decode('utf-8')
            print(data1_str)
            if data1_str[0]=='2':
                f_461 = float(data1_str[1:])
                deltaf = f_461 - self.target_freq
                proportional = deltaf
                integral += deltaf
                correction = (Kp * proportional) + (Ki * Kp * integral)

                if deltaf > 0:
                    vnow += correction 
                elif deltaf < 0:
                    vnow -= -correction

                vnow = max(2, min(145, vnow))
                pzt.write_voltage(ser, vnow)

                current_time = time.time() - t0
                self.times.append(current_time)
                self.frequencies.append(f_1092)

                if len(self.times) > 100:
                    self.times.pop(0)
                    self.frequencies.pop(0)

                status = "green" if -self.eps <= deltaf <= self.eps else "red"
                self.update_signal.emit(f_461, self.target_freq, status)

                ser.flush()
                time.sleep(0.1)

    def start_control(self, target_freq, eps):
        self.target_freq = target_freq
        self.eps = eps
        self.running = True
        self.start()

    def stop_control(self):
        self.running = False
        self.wait()

    def get_data(self):
        return self.times, self.frequencies


class PIDControllerGUI3(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.pid_thread = PIDThread(target_freq=0.0, eps=0.5)
        self.original_target_freq = 0.0
        self.pid_thread.update_signal.connect(self.update_display)

    def initUI(self):
        self.setWindowTitle('Laser Lock GUI')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        freq_layout = QVBoxLayout()

        self.start_button = QPushButton('Start Lock')
        self.start_button.clicked.connect(self.start_control)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_control)

        self.target_freq_input = QLineEdit(self)
        self.target_freq_input.setPlaceholderText('650504420')

        self.live_plot_checkbox = QCheckBox('Live Plot')
        self.live_plot_checkbox.setChecked(True)

        self.current_freq_label = QLabel('Current Frequency: -- MHz')
        self.current_freq_label.setStyleSheet('color: black')

        self.increase_freq_button = QPushButton('+1 MHz')
        self.increase_freq_button.clicked.connect(self.increase_target_freq)
        self.decrease_freq_button = QPushButton('-1 MHz')
        self.decrease_freq_button.clicked.connect(self.decrease_target_freq)

        self.save_plot_button = QPushButton('Save Plot')
        self.save_plot_button.clicked.connect(self.save_plot)

        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_target_freq)

        self.fig, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.target_freq_input)
        control_layout.addWidget(self.live_plot_checkbox)
        control_layout.addWidget(self.save_plot_button)
        control_layout.addWidget(self.reset_button)

        freq_layout.addWidget(self.current_freq_label)
        freq_layout.addWidget(self.increase_freq_button)
        freq_layout.addWidget(self.decrease_freq_button)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(freq_layout)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

    def start_control(self):
        try:
            target_freq = float(self.target_freq_input.text())
        except ValueError:
            target_freq = 0.0
        self.original_target_freq = target_freq
        eps = 0.5  # Set epsilon as needed
        self.pid_thread.start_control(target_freq, eps)

    def stop_control(self):
        self.pid_thread.stop_control()

    def increase_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target += 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def decrease_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target -= 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def reset_target_freq(self):
        self.target_freq_input.setText(str(self.original_target_freq))
        self.pid_thread.target_freq = self.original_target_freq

    def save_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            self.fig.savefig(file_path)

    def update_display(self, current_freq, target_freq, status):
        self.current_freq_label.setText(f'Current Frequency: {current_freq} Hz')
        self.current_freq_label.setStyleSheet(f'color: {status}')

        if self.live_plot_checkbox.isChecked():
            times, frequencies = self.pid_thread.get_data()
            self.ax1.clear()
            self.ax1.plot(times, frequencies, 'b-', label='Measured Frequency')
            self.ax1.axhline(y=target_freq, color='g', linestyle='--', label='Target Frequency')
            self.ax1.fill_between(times, target_freq - self.pid_thread.eps, target_freq + self.pid_thread.eps, color='green', alpha=0.3, label="Frequency range")
            self.ax1.legend()  # Ensure legend includes labeled artists
            self.ax1.grid(True)
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Frequency (MHz)')
            self.canvas.draw()


class FrequencyControlThread(QThread):
    data_received = pyqtSignal(float, float)  # Signal to update the GUI

    def __init__(self, n, freq_increment, freq_targets, switch_interval, parent=None):
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

        self.freq_targets = freq_targets  # List of frequency targets
        self.freq_target = float(self.freq_targets[0])  # Start with the first frequency target

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

# Second application class (replacing the original one)
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
        self.n_input = QComboBox(self)
        self.n_input.addItems(['30', '60', '90'])

        self.freq_increment_label = QLabel('Frequency Increment:', self)
        self.freq_increment_input = QLineEdit(self)
        self.freq_increment_input.setText('20')
        self.freq_targets = ['274589050', '290210320', '298616060', '650504420']
        self.freq_target_label = QLabel('Frequency Target:', self)
        self.freq_target_input = QComboBox(self)
        self.freq_target_input.addItems(self.freq_targets)

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
        n = int(self.n_input.currentText())  # Read current text from QComboBox
        freq_increment = float(self.freq_increment_input.text())
        freq_target_index = self.freq_target_input.currentIndex()  # Get selected index
        freq_target = float(self.freq_targets[freq_target_index])  # Convert to float

        switch_interval = int(self.switch_interval_input.text())

        if self.control_thread is None:
            self.control_thread = FrequencyControlThread(n, freq_increment, self.freq_targets, switch_interval)
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

class PIDThread5(QThread):
    update_signal = pyqtSignal(float, float, str)

    def __init__(self, target_freq, eps):
        super().__init__()
        self.target_freq = target_freq
        self.eps = eps
        self.running = False
        self.times = []
        self.frequencies = []

    def run(self):
        UDP_PORT = 37020
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(('', UDP_PORT))

        alpha = 16.999
        Kp = 1 / alpha
        Ki = 0.00001
        integral = 0

        t0 = time.time()
        ser = pzt.init_serial_connection()
        vnow = pzt.read_voltage(ser)
        pzt.write_voltage(ser, 75)

        while self.running:
            time.sleep(0.1)
            data1, addr = client.recvfrom(1024)
            data1_str = data1.decode('utf-8')
            if data1_str[0]=='5':
                f_1092_newmicro = float(data1_str[1:])
                deltaf = f_1092_newmicro - self.target_freq
                proportional = deltaf
                integral += deltaf
                correction = (Kp * proportional) + (Ki * Kp * integral)

                if deltaf > 0:
                    vnow += correction
                elif deltaf < 0:
                    vnow -= -correction

                vnow = max(2, min(145, vnow))
                pzt.write_voltage(ser, vnow)

                current_time = time.time() - t0
                self.times.append(current_time)
                self.frequencies.append(f_1092_newmicro)

                if len(self.times) > 100:
                    self.times.pop(0)
                    self.frequencies.pop(0)

                status = "green" if -self.eps <= deltaf <= self.eps else "red"
                self.update_signal.emit(f_1092_newmicro, self.target_freq, status)

                ser.flush()
                time.sleep(0.1)

    def start_control(self, target_freq, eps):
        self.target_freq = target_freq
        self.eps = eps
        self.running = True
        self.start()

    def stop_control(self):
        self.running = False
        self.wait()

    def get_data(self):
        return self.times, self.frequencies


class PIDControllerGUI5(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.pid_thread = PIDThread(target_freq=0.0, eps=0.5)
        self.original_target_freq = 0.0
        self.pid_thread.update_signal.connect(self.update_display)

    def initUI(self):
        self.setWindowTitle('Laser Lock GUI')
        self.setGeometry(100, 100, 800, 600)

        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        freq_layout = QVBoxLayout()

        self.start_button = QPushButton('Start Lock')
        self.start_button.clicked.connect(self.start_control)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_control)

        self.target_freq_input = QLineEdit(self)
        self.target_freq_input.setPlaceholderText('274589050')

        self.live_plot_checkbox = QCheckBox('Live Plot')
        self.live_plot_checkbox.setChecked(True)

        self.current_freq_label = QLabel('Current Frequency: -- MHz')
        self.current_freq_label.setStyleSheet('color: black')

        self.increase_freq_button = QPushButton('+1 MHz')
        self.increase_freq_button.clicked.connect(self.increase_target_freq)
        self.decrease_freq_button = QPushButton('-1 MHz')
        self.decrease_freq_button.clicked.connect(self.decrease_target_freq)

        self.save_plot_button = QPushButton('Save Plot')
        self.save_plot_button.clicked.connect(self.save_plot)

        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_target_freq)

        self.fig, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.target_freq_input)
        control_layout.addWidget(self.live_plot_checkbox)
        control_layout.addWidget(self.save_plot_button)
        control_layout.addWidget(self.reset_button)

        freq_layout.addWidget(self.current_freq_label)
        freq_layout.addWidget(self.increase_freq_button)
        freq_layout.addWidget(self.decrease_freq_button)

        main_layout.addLayout(control_layout)
        main_layout.addLayout(freq_layout)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

    def start_control(self):
        try:
            target_freq = float(self.target_freq_input.text())
        except ValueError:
            target_freq = 0.0
        self.original_target_freq = target_freq
        eps = 0.5  # Set epsilon as needed
        self.pid_thread.start_control(target_freq, eps)

    def stop_control(self):
        self.pid_thread.stop_control()

    def increase_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target += 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def decrease_target_freq(self):
        try:
            current_target = float(self.target_freq_input.text())
        except ValueError:
            current_target = 0.0
        current_target -= 1.0
        self.target_freq_input.setText(str(current_target))
        self.pid_thread.target_freq = current_target

    def reset_target_freq(self):
        self.target_freq_input.setText(str(self.original_target_freq))
        self.pid_thread.target_freq = self.original_target_freq

    def save_plot(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Plot", "", "PNG Files (*.png);;All Files (*)", options=options)
        if file_path:
            self.fig.savefig(file_path)

    def update_display(self, current_freq, target_freq, status):
        self.current_freq_label.setText(f'Current Frequency: {current_freq} Hz')
        self.current_freq_label.setStyleSheet(f'color: {status}')

        if self.live_plot_checkbox.isChecked():
            times, frequencies = self.pid_thread.get_data()
            self.ax1.clear()
            self.ax1.plot(times, frequencies, 'b-', label='Measured Frequency')
            self.ax1.axhline(y=target_freq, color='g', linestyle='--', label='Target Frequency')
            self.ax1.fill_between(times, target_freq - self.pid_thread.eps, target_freq + self.pid_thread.eps, color='green', alpha=0.3, label="Frequency range")
            self.ax1.legend()  # Ensure legend includes labeled artists
            self.ax1.grid(True)
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Frequency (MHz)')
            self.canvas.draw()
if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Create a tab widget
    tab_widget = QTabWidget()

    # Create instances of the PIDControllerGUI for three tabs
    pid_widget1 = PIDControllerGUI()
    pid_widget2 = PIDControllerGUI1()
    pid_widget3 = PIDControllerGUI2()
    pid_widget4 = PIDControllerGUI3()
    pid_widget5 = PIDControllerGUI5()

    # Add the PIDControllerGUI instances to the tab widget
    tab_widget.addTab(pid_widget1, "F_1092")
    tab_widget.addTab(pid_widget2, "F_1033")
    tab_widget.addTab(pid_widget3, "F_1003")
    tab_widget.addTab(pid_widget4, "F_461")
    tab_widget.addTab(pid_widget5, "F_1092_new_µ")
    # Add the frequency control tab
    frequency_widget = FrequencyControlApp()
    tab_widget.addTab(frequency_widget, "Spectral Analysis")

    tab_widget.setWindowTitle('Laser Control System')
    tab_widget.resize(800, 600)
    tab_widget.show()

    sys.exit(app.exec_())
