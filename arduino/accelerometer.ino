/*
Connect SCLK, MISO, MOSI, and CSB of ADXL362 to
SCLK, MISO, MOSI, and DP 10 of Arduino
(check http://arduino.cc/en/Reference/SPI for details)
*/

#include <SPI.h>
#include <ADXL362.h>

ADXL362 xl;
const int NUM_CAL_READINGS = 3;
int time = 0;

int lastXval;
int lastYval;
int lastZval;

void setup(){
    Serial.begin(9600);
    xl.begin();                   // Setup SPI protocol, issue device soft reset
    xl.beginMeasure();            // Switch ADXL362 to measure mode
    xl.checkAllControlRegs();     // Burst Read all Control Registers, to check for proper setup

    // Set the last values
    int xTotal = 0;
    int yTotal = 0;
    int zTotal = 0;
    for (int i = 0; i < NUM_CAL_READINGS; i++)
    {
      xTotal += xl.readXData();
      yTotal += xl.readYData();
      zTotal += xl.readZData();
    }

    lastXval = xTotal / NUM_CAL_READINGS;
    lastYval = yTotal / NUM_CAL_READINGS;
    lastZval = zTotal / NUM_CAL_READINGS;
}

void loop(){
    time++;

    // read all three axis in burst to ensure all measurements correspond to same sample time
    int xAverage=0;
    int yAverage=0;
    int zAverage=0;
    for (int i=0; i<NUM_CAL_READINGS; i++)
    {
      xAverage += xl.readXData();
      yAverage += xl.readYData();
      zAverage += xl.readZData();

      delay(100);                // Arbitrary delay to make serial monitor easier to observe
    }
    xAverage = xAverage / 3;
    yAverage = yAverage / 3;
    zAverage = zAverage / 3;

    unsigned int xMovement = abs(xAverage - lastXval);
    unsigned int yMovement = abs(yAverage - lastYval);
    unsigned int zMovement = abs(zAverage - lastZval);
    unsigned int movementValue = xMovement+yMovement+zMovement;

    Serial.print(movementValue);
    Serial.print ("\n");

    // Now that we've printed the differentials,
    // move our current Values into lastVals
    lastXval = xAverage;
    lastYval = yAverage;
    lastZval = zAverage;
}
