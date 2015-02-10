# Hospital Sleep Tracker
This project is funded by [Enabling Engineering](http://nuweb9.neu.edu/enable/) team at [Northeastern University](http://neu.edu).

# Installation
##### On a Raspberry Pi
The Raspbian distribution of the Raspberry Pi can be used as a host system to log sleep for later analysis. Future plans might use the Pi as a central HUB to wirelessly track sleep from multiple patients simultaneously. The below instructions cover setting up the tracking scripts on a fresh Raspbian image. Run the following commands from the home directory of the pi to set it up.
```
git clone https://github.com/hospital-sleep-tracker/live-sleep-analyzer.git
cd live-sleep-analyzer/
cp initialize_sleeptracker.sh ../
```
Then add the following line to the bottom of etc/rc.local (above the `exit 0`):
`/home/pi/initialize_sleeptracker.sh &`

##### In a Developer Environment
In order to interface with the USB device, you will need the following dependencies on your machine:
- libusb
- virtualenv
- python
- and of course, Git

After cloning the repo, create and activate a virtualenv for your python libraries
```
git clone git@github.com:hospital-sleep-tracker/live-sleep-analyzer.git
cd live-sleep-analyzer/
virtualenv ~/Virtualenvs/hospital-sleep-tracker
source ~/Virtualenvs/hospital-sleep-tracker/bin/activate
pip install -r requirements.txt
```

---

# Usage
### **Data Collection:** Logging Live Sleep from Teensy onto Pi via Serial
*Primarily run on the Raspberry Pi, this script is useful for pure sleep-data collection. No graphs, analysis, or flashy features. The script searches for a USB connected serial and begins tracking data into a timestamped logfile. A new logfile can be started simply by disconnecting and reconnecting the USB device.*
 **WARNING: This script may interfere with other connected USB devices. Please remove any and all unnecessary USB devices before starting the script. **

##### Usage
`python sleep-logger.py [-h]`

##### Data Source:
Serial (Teensy) (future wifi support?)

##### Supported Operations
- [x] Save to logfile
- [ ] Real-time graphing (short-term)
- [ ] Session graphing (long-term)
- [ ] Real-time analysis
- [ ] Session analysis (after-the-fact)

---

### **After-the-fact Analysis:** Analyzing Data from Existing Logfile
*Useful for testing machine-learning algorithms on existing sleep logfiles. These algorithms are shared by the Nurse Station use case (below).*

##### Usage
`python post-analyze.py [-h] FILENAME`

##### Data Source:
Sleep File

##### Supported Operations
- [ ] Save to logfile
- [x] Real-time graphing (short-term)
- [x] Session graphing (long-term)
- [x] Real-time analysis
- [x] Session analysis (after-the-fact)

---

### **Nurse Station:** Graphically Analyzing Real-time Data
*Useful for testing the actual use case of this product. This simulates the system a nurse or caretaker would be using to monitor the sleep of a patient. This includes live graphs of the patient's sleep movements and information on their current sleep cycle. A logfile is created with sleep data from the current session. This is a sort of 'combination' of the other two use cases.*

##### Usage
`python realtime-analysis.py [-h]`

##### Data Source: 
Serial (Teensy)
- [x] Save to logfile
- [x] Realtime graphing (short-term)
- [x] Session graphing (long-term)
- [x] Realtime analysis
- [x] Session analysis (after-the-fact)