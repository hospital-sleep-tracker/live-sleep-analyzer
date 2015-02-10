# Live Sleep Analyzer
This project is funded by [Enabling Engineering](http://nuweb9.neu.edu/enable/) team at [Northeastern University](http://neu.edu).

## Installation
##### Raspberry Pi
The Raspbian distribution of the Raspberry Pi can be used as a host system to simply log sleep. The below instructions cover setting up the tracking scripts on a fresh Raspbian image. Run the following commands from the home directory of the pi to set it up.
```
git clone https://github.com/hospital-sleep-tracker/live-sleep-analyzer.git
cd live-sleep-analyzer/
cp initialize_sleeptracker.sh ../
```
Then add the following line to the bottom of etc/rc.local (above the `exit 0`):
`/home/pi/initialize_sleeptracker.sh &`

##### Developer Environment
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
## Usage Instructions
### Use Case: Logging sleep from teensy onto Pi via serial (data collection)
**Data Source:** Serial (Teensy) (future wifi support?)
- [x] Save to logfile
- [ ] Real-time graphing (short-term)
- [ ] Session graphing (long-term)
- [ ] Real-time analysis
- [ ] Session analysis (after-the-fact)

### Use Case: Analyzing data from logfile (after-the-fact analysis)
**Data Source:** File
- [ ] Save to logfile
- [x] Real-time graphing (short-term)
- [x] Session graphing (long-term)
- [x] Real-time analysis
- [x] Session analysis (after-the-fact)

### Use Case: Analyzing real-time data live on PC (nurse with a screen)
**Data Source:** Serial (Teensy)
- [x] Save to logfile
- [x] Realtime graphing (short-term)
- [x] Session graphing (long-term)
- [x] Realtime analysis
- [x] Session analysis (after-the-fact)