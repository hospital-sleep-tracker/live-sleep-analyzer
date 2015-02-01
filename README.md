# Live Sleep Analyzer
This project is funded by [Enabling Engineering](http://nuweb9.neu.edu/enable/) team at [Northeastern University](http://neu.edu). 

## Installation
#### Install dependencies
In order to interface with the USB device, you will need the following dependencies on your machine:
- libusb
- virtualenv
- python
- and of course, Git

#### Clone the Repository
```
git clone git@github.com:djosborne/SerialDataPlotter.git
cd SerialDataPlotter
```

#### Create your Python Environment
Create a python virtual environment directory and install all your python system dependencies into it.
```
virtualenv ~/Virtualenvs/hospital-sleep-tracker
source ~/Virtualenvs/hospital-sleep-tracker/bin/activate
pip install -r requirements.txt
```