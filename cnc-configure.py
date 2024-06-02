import serial
import serial.tools.list_ports

def find_shapeoko_controller():
    # List all available serial ports
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Checking port: {port.device}")
        if "Shapeoko" in port.description:
            print(f"Shapeoko controller found on port: {port.device}")
            try:
                ser = serial.Serial(port.device, 115200, timeout=1)
                return ser
            except (OSError, serial.SerialException) as e:
                print(f"Error opening port {port.device}: {e}")
    return None

def send_gcode_command(ser, command, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            ser.write(f"{command}\n".encode())
            ser.flushInput()  # Clear the input buffer
            response = ser.readlines()  # Read all the lines available
            return [line.decode('utf-8').strip() for line in response]
        except Exception as e:
            print(f"An error occurred while sending the G-code command: {e}")
            attempt += 1
    return None

def main():
    # Find the Shapeoko controller
    ser = find_shapeoko_controller()
    if ser is None:
        print("Shapeoko controller not found.")
        return

    while True:
        # Read G-code command from user
        command = input("Enter G-code command (or 'exit' to quit): ")
        if command.lower() == 'exit':
            break

        # Send the G-code command
        responses = send_gcode_command(ser, command)
        if responses is not None:
            for response in responses:
                print(f"Response: {response}")
        else:
            print("Failed to get a response from the Shapeoko controller.")

    # Close the serial connection
    ser.close()

if __name__ == "__main__":
    main()
