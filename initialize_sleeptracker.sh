#!/bin/bash
echo none >/sys/class/leds/ACT/trigger
echo 0 >/sys/class/leds/ACT/brightness

if ping -c 1 archive.raspberrypi.org &> /dev/null; then
  apt-get update
  apt-get upgrade -y --force-yes
  apt-get install -y python-usb python-serial python-matplotlib vsftpd
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
  python sleep-logger.py
done

exit 1
