Arduino
===============
This repository contains code which runs on the arduino. 


## Function Overview
####Setup
1. Prepare Accelerometer
2. Prepare Serial
3. Set Calibration Offset

####Loop
1. Sample X, Y, and Z values from the accelerometer 3 times each
2. Average these 3 samples for each
3. Find Differential Between Last Samples
4. Print Over Serial
5. Push Current Samples Onto Memory Stack