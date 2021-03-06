#! /bin/bash

echo "mirroring from monitoring stations at `date`"

echo "switching SD-card to RW mode"
/usr/bin/rpi-rw

echo "mid-pi"
python solar_mirror.py --config=mirror_mid-pi.ini mirror
echo "top-pi"
python solar_mirror.py --config=mirror_top-pi.ini mirror
echo "bottom-pi"
python solar_mirror.py --config=mirror_bottom-pi.ini mirror
echo "mirroring finished"

echo "started saving data"
echo "mounting diskstation"
mount /mnt/diskstation
if test -d /mnt/diskstation/solar; then
	echo "mirroring log files to diskstation"
	cp -a *.log /mnt/diskstation/solar/
	echo "mirroring data to diskstation"
	cp -a csvdb /mnt/diskstation/solar/ 
fi

echo "unmounting diskstation"
umount /mnt/diskstation

echo "switching SD-card to read-only mode"
/usr/bin/rpi-ro

echo "mirroring completed at `date`"
