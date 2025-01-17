import os
import shutil
import serial
import serial.tools.list_ports
import psutil
import tkinter as tk
from PIL import Image, ImageTk

class ShapeokoAccessDeniedError(Exception):
    def __init__(self, message, original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception

def list_serial_ports():
    return serial.tools.list_ports.comports()

def open_serial_port(port_device):
    return serial.Serial(port_device, 115200, timeout=1)

def send_gcode_command(ser, command, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            print(f"Sending g-code command: {command}")
            ser.write(f"{command}\n".encode())
            ser.flushInput()  # Clear the input buffer
            response = ser.readlines()  # Read all the lines available
            response = [line.decode('utf-8').strip() for line in response]
            if response is not None:
                print(f"Controller response: {response}")
            else:
                print(f"<No response received from controller>")
            return response
        except Exception as e:
            print(f"An error occurred while sending the G-code command: {e}")
            attempt += 1
    return None

def set_and_verify_parameters(ser):
    # G-code commands to set parameters
    commands = [
        "$100=26.667", # Set X-axis steps per millimeter
        "$101=26.667", # Set Y-axis steps per millimeter
        "$102=200",    # Set Z-axis steps per millimeter
        "$130=507",    # Set maximum travel (mm) along the X-axis
        "$131=490",    # Set maximum travel (mm) along the Y-axis
        "$132=140"     # Set maximum travel (mm) along the Z-axis
    ]

    # Send each command
    for command in commands:
        response = send_gcode_command(ser, command)

    # Verify the parameters
    verify_command = "$$"
    responses = send_gcode_command(ser, verify_command)
    failures = []
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
                failure = f"{param} not set correctly"
                failures.append(failure)
                print(failure)
    else:
        failure = "Failed to verify parameters with command '$$'. No response received from controller."
        failures.append(failure)
        print(failure)

    if failures:
        failureMessages = "\n".join(failures)
        show_message(
            "Controller Configuration Error",
            f"One or more failures occurred while verifying the Shapeoko controller configuration: \n{failureMessages}\r\n Please log out of the computer and log back in. You might also need to reset the controller by hitting the red E-STOP button and then turning it clockwise to reset the power to the controller. If this problem persists, you should report it under the Woodshop category on Talk.",
            image_path="error.png"
        )

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

def try_connect_and_configure(retries=4):
    attempts = 0
    while attempts < retries:
        print(f"Looking for Shapeoko controller. Connection attempt {attempts + 1}...")
        ports = list_serial_ports()
        try:
            for port in ports:
                print(f"Checking port: {port.device}")
                if "Shapeoko" in port.description:
                    try:
                        with open_serial_port(port.device) as ser:
                            response = send_gcode_command(ser, b"\r\n\r\n")
                            if 'Grbl' in " ".join(response):
                                print(f"Shapeoko controller found on port {port.device}.")
                                set_and_verify_parameters(ser)
                                # repl_loop(ser)  ### this is only here for testing purposes
                                return True
                    except serial.SerialException as e:
                        if "PermissionError" in str(e):
                            print(f"Access Denied error on port {port.device}: {e}")
                            raise ShapeokoAccessDeniedError(f"Access Denied error on port {port.device}: {e}", e)
                        else:
                            print(f"Error opening port {port.device}: {e}")
                            raise e
        except ShapeokoAccessDeniedError as e:
            show_message(
                "Access Denied",
                "An Access Denied error occurred while trying to connect to the Shapeoko controller. This usually means that Carbide Moion or some other CNC program is already connected to the controller. Please make sure all programs are closed, including Carbide Motion, and then try again.",
                image_path="oops.png"
            )
            attempts += 1
            continue
        except Exception as e:
            print(e)
            show_message(
                "Connection Error",
                f"The following error occurred while trying to connect to the Shapeoko controller: {e}\r\n Please make sure all programs are closed, especially Carbide Motion, and then try again. You might also need to reset the controller by hitting the red E-STOP button and then turning it clockwise to reset the power to the controller.",
                image_path="error.png"
            )
            attempts += 1
            continue
        show_message(
            "Shapeoko Controller Not Found",
            "The Shapeoko controller does not appear to be turned on and/or connected to the computer. "
            "Please make sure the e-stop switch is in the reset/up position by turning it clockwise until it clicks and pops up. "
            "Click OK or close this window when you've verified that the e-stop is reset and the controller is running.",
            image_path="estop_reset.png"
        )
        attempts += 1
    print(f"Connection failed after {attempts} attempts. Aborting.")
    show_message("Shapeoko Controller Not Found",
                 "The Shapeoko controller still couldn't be found after several attempts. You may need to reset the controller by hitting the red E-STOP button and then turning it clockwise to reset the power to the controller. If this problem persists, please report it in the Woodshop section of the DMS Talk forums.",
                 image_path="ohno.png")
    return False

def copy_file(file_name, source_dir, destination_dir):
    try:
        source_file_path = os.path.join(source_dir, file_name)
        destination_file_path = os.path.join(destination_dir, file_name)
        print(f"Copying '{file_name}' to '{destination_dir}'")
        shutil.copy(source_file_path, destination_file_path)
        print(f"File copied successfully.")
    except Exception as e:
        print(f"Failed to copy file '{file_name}': {e}")

def main():
    # Close Carbide Motion if it is running
    close_carbide_motion()

    # Try to connect to the Shapeoko controller and update onboard stepper configuration
    response = try_connect_and_configure()

    if response:
        # Get the path to the current user's AppData\Local\Carbide 3D\CarbideMotion6 directory
        destination_dir = os.path.join(
            os.getenv('LOCALAPPDATA'),
            'Carbide 3D',
            'CarbideMotion6'
        )
        # Ensure the destination directory exists
        os.makedirs(destination_dir, exist_ok=True)
        
        source_dir = os.path.dirname(__file__) # copy master files from the app folder
        copy_file("shapeoko.json", source_dir, destination_dir)

if __name__ == "__main__":
    main()
