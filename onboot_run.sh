#!/bin/bash
# This script auto-updates, and runs the slep-logger application for use on the pi
# This script should be run by /etc/rc.local
# Add a line at the bottom that reads: screen -d -m /home/pi/live-sleep-analyzer/onboot_run.sh

echo none >/sys/class/leds/led0/trigger

if ping -c 1 archive.raspberrypi.org &> /dev/null; then
  apt-get update
#  apt-get upgrade -y --force-yes
  apt-get install -y screen python-usb python-serial python-matplotlib python-sklearn vsftpd
fi

cd /home/pi

if [ ping -c 1 github.com &> /dev/null ] && [ ! -d live-sleep-analyzer/ ]; then
  git clone -q https://github.com/hospital-sleep-tracker/live-sleep-analyzer.git
fi

cd live-sleep-analyzer/

if ping -c 1 github.com &> /dev/null; then
  git fetch
fi

git reset --hard origin/master
while :
do
  python pysleep/sleep-logger.py
done

exit 1
