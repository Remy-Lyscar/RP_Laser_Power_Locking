import serial
import time
import re


# Initialize serial connection 
def init_serial_connection(port='/dev/ttyACM1', baudrate=115200):
    ser = serial.Serial(port, baudrate, timeout=1)
    return ser
ser = init_serial_connection()
def close_serial_connection(ser):
    if ser:
        ser.close()

# Write voltage to the device
def write_voltage(ser, voltage):


    command = f'xvoltage={voltage}\r\n'
    ser.write(command.encode())
    ser.close()
    ser.open()
    time.sleep(0.01)  # Increased delay to allow processing

# Read voltage from the device
def read_voltage(ser):
    ser.close()
    ser.open()
    ser.flush()
    command = 'xvoltage?\r\n'
    ser.write(command.encode())

    time.sleep(0.01)  # Increased delay to allow processing
    response = ser.readline().decode().strip()
    response = ser.readline().decode().strip()
    # Extract the numeric part from the response
    match = re.search(r'[-+]?[0-9]*\.?[0-9]+', response)
    if match:
        try:
            voltage = float(match.group(0))
            return voltage
        except ValueError:
            return "Invalid response format"
    else:
        return "No valid numeric value found in response"
