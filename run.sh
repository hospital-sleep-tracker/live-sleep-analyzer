#!/bin/bash
apt-get install -Y libusb git virtualenv python
git reset hard origin/master
source ~/Virtualenvs/hospital-sleep-tracker/bin/activate
pip install -r requirements.txt
while :
do
  python ./main.py
done