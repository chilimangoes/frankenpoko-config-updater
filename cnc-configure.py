import serial
import serial.tools.list_ports

def find_grbl_controller():
    # List all available serial ports
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Try to open each port and check for GRBL response
        try:
            ser = serial.Serial(port.device, 115200, timeout=1)
            ser.write(b"\r\n\r\n")
            ser.flushInput()
            for _ in range(50):  # Try for up to 50 iterations (5 second total)
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    if 'Grbl' in response:
                        return ser
            ser.close()  # Close the port if it's not GRBL
        except (OSError, serial.SerialException):
            continue
    return None

def send_gcode_command(ser, command, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            ser.write(f"{command}\n".encode())
            for _ in range(50):  # Try for up to 50 iterations (5 seconds total)
                if ser.in_waiting > 0:
                    response = ser.readline().decode('utf-8').strip()
                    return response
        except Exception as e:
            print(f"An error occurred while sending the G-code command: {e}")
            attempt += 1
    return None

def main():
    # Find the GRBL controller
    ser = find_grbl_controller()
    if ser is None:
        print("GRBL controller not found.")
        return

    # Send a G-code command
    command = "$$"  # Example command to list GRBL settings
    response = send_gcode_command(ser, command)
    if response is not None:
        print(f"Response: {response}")
    else:
        print("Failed to get a response from the GRBL controller.")

    # Close the serial connection
    ser.close()

if __name__ == "__main__":
    main()
