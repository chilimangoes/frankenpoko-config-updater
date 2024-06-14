# Summary

A small Python script that can be run to ensure our Shapeoko controller settings and Carbide Motion machine setup are configured correctly.

# Background

Carbide Motion is poorly-written for use in a multi-user environment, such as a makerspace. If you have a Shapeoko CNC machine that is used from a computer where multiple users are able to log in and use the machine, Carbide 3D do not offer any means of locking down the settings or making sure the machine is configured correctly for each user. This script attempts to mitigate these issues by doing the following:

1. Check to make sure the controller is turned on and attached and prompt the user if it can't be found.
2. Connect to the Shapeoko controller and send a set of `$` commands to update configuration stored on the controller, such as the steps/mm and bounds for each axis.
3. Copy a known-good `shapeoko.json` file into the `AppData\Local\Carbide 3D\CarbideMotion6` folder for the currently logged in user. 

At Dallas Makerspace, we have an X-Carve CNC that was converted to use a Shapeoko 3 controller and this repo currently has settings for that machine. Settings can be changed to fit your needs by updating the list of commands in the `set_and_verify_parameters(ser)` method in `cnc-configure.py` and replacing the `shapeoko.json` file in this repo with your own copy. The messages displayed to the user can also be customized by editing the `cnc-configure.py` script and/or editing the photos displayed with the messages. For example, this could be used to instruct users on how to turn on or reset the CNC controller for your specific hardware setup.

If you configure the script to run each time a user logs in, then the attached Shapeoko controller and Carbide Motion software will be configured correctly before they open Carbide Motion to use the CNC. If a user does run through the setup wizard in Carbide Motion and download a new configuration to the controller, they may mess up the machine configuration for themselves for the current session, but it won't be messed up for other users, and logging out and back in should fix the configuration for them as well.

# Development / Environment Setup

1. Install Python
2. Create/activate venv: `python -m venv .venv`
3. Activate venv: `.venv\Scripts\activate`
4. Install dependencies: `pip install Pillow psutil pyserial`

# Running the script

```powershell
> cd path\to\local\repository\root
> .venv\Scripts\activate`
> python cnc-configure.py
```

