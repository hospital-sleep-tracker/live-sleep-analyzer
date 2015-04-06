/*
 ADXL362_SimpleRead.ino -  Simple XYZ axis reading example
 for Analog Devices ADXL362 - Micropower 3-axis accelerometer
 go to http://www.analog.com/ADXL362 for datasheet


 License: CC BY-SA 3.0: Creative Commons Share-alike 3.0. Feel free
 to use and abuse this code however you'd like. If you find it useful
 please attribute, and SHARE-ALIKE!

 Created June 2012
 by Anne Mahaffey - hosted on http://annem.github.com/ADXL362

Connect SCLK, MISO, MOSI, and CSB of ADXL362 to
SCLK, MISO, MOSI, and DP 10 of Arduino
(check http://arduino.cc/en/Reference/SPI for details)
*/

#include <SPI.h>
#include "ADXL362.h"

#define DEBUG 0
#define NUM_AVG_READINGS 3

ADXL362 xl;

int lastXval;
int lastYval;
int lastZval;

int xOffset = 0;
int yOffset = 0;
int zOffset = 0;

void setup(){
    Serial.begin(9600);
    xl.begin();                   // Setup SPI protocol, issue device soft reset
    xl.beginMeasure();            // Switch ADXL362 to measure mode
    // xl.checkAllControlRegs();     // Burst Read all Control Registers, to check for proper setup
    delay(100);

    // set initial readings
    lastXval = xl.readXData();
    lastYval = xl.readYData();
    lastZval = xl.readZData();
}

void loop() {
    int xSums = 0;
    int ySums = 0;
    int zSums = 0;

    int xReadings[NUM_AVG_READINGS];
    int yReadings[NUM_AVG_READINGS];
    int zReadings[NUM_AVG_READINGS];

    // Take 3 samples to average out jitter
    for (int counter = 0; counter < NUM_AVG_READINGS; counter++)
    {
        xReadings[counter] = xl.readXData();
        yReadings[counter] = xl.readYData();
        zReadings[counter] = xl.readZData();
    }

    // Calculate average (which is the current values) of those 3 readings
    for (int counter = 0; counter < NUM_AVG_READINGS; counter++)
    {
        xSums += xReadings[counter];
        ySums += yReadings[counter];
        zSums += zReadings[counter];
    }
    int currentX = xSums / 3;
    int currentY = ySums / 3;
    int currentZ = zSums / 3;

    // calculate difference between last readings
    int xDiff = currentX - lastXval;
    int yDiff = currentY - lastYval;
    int zDiff = currentZ - lastZval;

    unsigned int actualMovement = abs(xDiff) + abs(yDiff) + abs(zDiff);

    if (DEBUG) {
        for (int counter = 0; counter < NUM_AVG_READINGS; counter++)
        {
            Serial.print(xReadings[counter]);
            Serial.print(",");
            Serial.print(yReadings[counter]);
            Serial.print(",");
            Serial.println(zReadings[counter]);
        }
        // Serial.print("RawX:");
        // Serial.print(xReadings);
        // Serial.print("\tRawY:");
        // Serial.print(yReadings);
        // Serial.print("\tRawZ:");
        // Serial.print(zReadings);
        // Serial.print("\tMovement:");
    }

    // print results
    Serial.println(actualMovement);

    // Now that we've printed the differentials,
    // move our current Values into lastVals
    lastXval = currentX;
    lastYval = currentY;
    lastZval = currentZ;

    delay(100);
}