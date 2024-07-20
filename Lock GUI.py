import sys
import time
import socket
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QCheckBox, QLabel, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import communication_device as pzt

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
        # UDP socket configuration
        UDP_PORT = 37020
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(('', UDP_PORT))

        # PID controller parameters
        alpha = 16.999
        Kp = 1 / alpha  # Proportional gain
        Ki = 0.00001    # Integral gain
        integral = 0

        # Initialize the plot data
        t0 = time.time()  # Initialize the start time

        ser = pzt.init_serial_connection()
        vnow = pzt.read_voltage(ser)
        pzt.write_voltage(ser, 75)

        while self.running:
            try:
                data1, addr = client.recvfrom(1024)
                f_1092 = float(data1)

            except Exception as e:
                print(f"An error occurred: {e}")
                continue

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

        # Layouts
        main_layout = QVBoxLayout()
        control_layout = QHBoxLayout()
        freq_layout = QVBoxLayout()

        # Start/Stop Buttons
        self.start_button = QPushButton('Start Lock')
        self.start_button.clicked.connect(self.start_control)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_control)

        # Frequency Target Input
        self.target_freq_input = QLineEdit(self)
        self.target_freq_input.setPlaceholderText('Enter target frequency')

        # Checkbox for live plot
        self.live_plot_checkbox = QCheckBox('Live Plot')
        self.live_plot_checkbox.setChecked(True)

        # Current Frequency Display
        self.current_freq_label = QLabel('Current Frequency: -- MHz')
        self.current_freq_label.setStyleSheet('color: black')

        # Frequency Adjust Buttons
        self.increase_freq_button = QPushButton('+1 MHz')
        self.increase_freq_button.clicked.connect(self.increase_target_freq)
        self.decrease_freq_button = QPushButton('-1 MHz')
        self.decrease_freq_button.clicked.connect(self.decrease_target_freq)

        # Save Plot Button
        self.save_plot_button = QPushButton('Save Plot')
        self.save_plot_button.clicked.connect(self.save_plot)

        # Reset Button
        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.reset_target_freq)

        # Matplotlib Figure
        self.fig, self.ax1 = plt.subplots()
        self.canvas = FigureCanvas(self.fig)

        # Adding widgets to layouts
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
            self.ax1.plot(times, frequencies, 'b-')
            self.ax1.axhline(y=target_freq, color='g', linestyle='--')
            self.ax1.fill_between(times, target_freq - self.pid_thread.eps, target_freq + self.pid_thread.eps, color='green', alpha=0.3, label="Frequency range")
            self.ax1.legend()
            self.ax1.grid(True)
            self.ax1.set_xlabel('Time (s)')
            self.ax1.set_ylabel('Frequency (MHz)')
            self.canvas.draw()

def main():
    app = QApplication(sys.argv)
    gui = PIDControllerGUI()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
