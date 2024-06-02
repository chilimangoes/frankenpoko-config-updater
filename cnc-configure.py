import serial
import serial.tools.list_ports
import psutil

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

def set_and_verify_parameters(ser):
    # G-code commands to set parameters
    commands = [
        "$100=26.667",  # Set X-axis steps per millimeter
        "$101=26.667",  # Set Y-axis steps per millimeter
        "$102=200",    # Set Z-axis steps per millimeter
        "$130=507",    # Set maximum travel (mm) along the X-axis
        "$131=490",    # Set maximum travel (mm) along the Y-axis
        "$140=140"     # Set maximum travel (mm) along the Z-axis
    ]

    # Send each command
    for command in commands:
        response = send_gcode_command(ser, command)
        if response is not None:
            print(f"Set command response: {response}")
        else:
            print(f"Failed to set parameter with command: {command}")

    # Verify the parameters
    verify_command = "$$"
    responses = send_gcode_command(ser, verify_command)
    if responses is not None:
        print("Verification of parameters:")
        for response in responses:
            print(f"Response: {response}")
        # Check if all parameters are correctly set
        for command in commands:
            param, value = command.split('=')
            found = any(param in response and value in response for response in responses)
            if found:
                print(f"{param} set correctly to {value}")
            else:
                print(f"{param} not set correctly")
    else:
        print("Failed to verify parameters with command: $$")

def repl_loop(ser):
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

def close_carbide_motion():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == 'carbidemotion.exe':
            print(f"Found running process carbidemotion.exe with PID {proc.info['pid']}. Terminating it.")
            proc.terminate()
            proc.wait()
            print("Process terminated.")
            return True
    print("carbidemotion.exe is not running.")
    return False

def main():
    # Close Carbide Motion if it is running
    close_carbide_motion()

    # Find the Shapeoko controller
    ser = find_shapeoko_controller()
    if ser is None:
        print("Shapeoko controller not found.")
        return

    # Set and verify parameters
    set_and_verify_parameters(ser)

    # Start the REPL loop
    repl_loop(ser)

    # Close the serial connection
    ser.close()

if __name__ == "__main__":
    main()
