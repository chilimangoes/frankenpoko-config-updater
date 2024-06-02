import serial
import serial.tools.list_ports
import psutil
import tkinter as tk
from PIL import Image, ImageTk

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

def show_message(title, message, image_path=None):
    root = tk.Tk()
    root.title(title)
    root.state('zoomed')  # Open the window maximized

    # Create the message label
    msg = tk.Label(root, text=message, font=("Arial", 16), wraplength=root.winfo_screenwidth() - 40)
    msg.pack(padx=20, pady=10)  # Double the horizontal padding

    # Function to update wraplength on window resize
    def update_wraplength(event):
        new_width = root.winfo_width() - 40
        msg.config(wraplength=new_width)

    root.bind('<Configure>', update_wraplength)

    # Load and display the image if provided
    if image_path:
        try:
            image = Image.open(image_path)
            photo = ImageTk.PhotoImage(image)
            img_label = tk.Label(root, image=photo)
            img_label.image = photo  # Keep a reference to avoid garbage collection
            img_label.pack(padx=10, pady=10)
        except Exception as e:
            print(f"Error loading image: {e}")

    # Create the OK button
    ok_button = tk.Button(root, text="OK", font=("Arial", 18), command=root.destroy)
    ok_button.pack(pady=10)

    # Run the Tkinter main loop
    root.mainloop()

def try_connect(retries=2):
    attempts = 0
    while attempts < retries:
        try:
            ser = find_shapeoko_controller()
            if ser is not None:
                print("Shapeoko controller found.")
                set_and_verify_parameters(ser)
                repl_loop(ser)
                ser.close()
                return
        except serial.SerialException as e:
            if "Access Denied" in str(e):
                show_message(
                    "Access Denied",
                    "An Access Denied error occurred. Please make sure Carbide Motion is not running and try again."
                )
                attempts += 1
                continue
        attempts += 1
        show_message(
            "Shapeoko Controller Not Found",
            "The Shapeoko controller does not appear to be turned on and/or connected to the computer. "
            "Please make sure the e-stop switch is in the reset/up position by turning it clockwise until it clicks and pops up. "
            "Click OK or close this window when you've verified that the e-stop is reset and the controller is running.",
            image_path="estop_reset.png"
        )

    show_message("Shapeoko Controller Not Found",
                 "The Shapeoko controller still could not be found after several attempts. "
                 "You may need to report this issue in the Woodshop section on Talk.")

def main():
    # Close Carbide Motion if it is running
    close_carbide_motion()

    # Try to connect to the Shapeoko controller
    try_connect(retries=2)

if __name__ == "__main__":
    main()
