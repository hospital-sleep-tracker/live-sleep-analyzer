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

#define NUM_CAL_READINGS 15

ADXL362 xl;

int temp;
int xValue, yValue, zValue, Temperature;
int xOffset, yOffset, zOffset;


unsigned long time = 0;

int lastXval = 0;
int lastYval = 0;
int lastZval = 0;

void setup(){
    Serial.begin(9600);
    xl.begin();                   // Setup SPI protocol, issue device soft reset
    xl.beginMeasure();            // Switch ADXL362 to measure mode  
    xl.checkAllControlRegs();     // Burst Read all Control Registers, to check for proper setup
    delay(100);
    
    // set initial readings
    lastXval = xl.readXData();
    lastYval = xl.readYData();
    lastZval = xl.readZData();
}

void loop(){
    time++;

    int xSums = 0;
    int ySums = 0;
    int zSums = 0;

    // Take 3 samples to average out jitter
    for (int counter = 0; counter < 3; counter++)
    {
      xSums += xl.readXData();
      ySums += xl.readYData();
      zSums += xl.readZData();
    }

    // Calculate average (which is the current values) of those 3 readings
    int currentX = xSums / 3;
    int currentY = ySums / 3;
    int currentZ = zSums / 3;

    // calculate difference between last readings
    int xDiff = currentX - lastXval;
    int yDiff = currentY - lastYval;
    int zDiff = currentZ - lastZval;

    unsigned int actualMovement = abs(xDiff)+abs(yDiff)+abs(zDiff);

    // print results
    Serial.print (time);
    Serial.print (",");
    Serial.print(actualMovement);
    Serial.print ("\n");
    // Serial.println();
    
    
    // Now that we've printed the differentials,
    // move our current Values into lastVals
    lastXval = currentX;
    lastYval = currentY;
    lastZval = currentZ;

    delay(100);
}