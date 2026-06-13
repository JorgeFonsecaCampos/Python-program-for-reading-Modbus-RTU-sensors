# Python-program-for-reading-Modbus-RTU-sensors
Python program for reading Modbus RTU sensors related to the manuscript Real-Time Monitoring of Environmental Variables in Microalgae Cultures with Modbus Sensors and Python

## Usage instructions
To run the program in Windows OS, follow the next steps:
1. Follow the steps to install PyGObject provided in https://pygobject.gnome.org/getting_started.html
2. Install the MSYS2 Packages: 
    -pyserial.
    -libadwaita.
    -pip.
3. Create a Python virtual environment in the path \msys64\home
4. Activate the virtual environment and move to the folder bin
5. Install the PyModbus package with pip
6. Modify the line include-system-site-packages to true in the file pyvenv.cfg created in the folder of the Python virtual environment
7 Move to the bin folder the Python App and the file style_microalgae_monitor.css
8 Run the program through the command python “filename-app.py”

To run the program in Linux OS, follow the next steps:
1. Follow the steps to install PyGObject provided in https://pygobject.gnome.org/getting_started.html
2. Create a Python virtual environment
3. Activate the virtual environment
4. Install with pip the PyModbus and pyserial packages
5. Modify the line include-system-site-packages with true in the file pyvenv.cfg created in the folder of the Python virtual environment
6. Move to the bin folder the Python App and the file style_microalgae_monitor.css
7. Run the program through the command python “filename-app.py”
Note: The application was tested only in Linux with the Gnome Desktop

