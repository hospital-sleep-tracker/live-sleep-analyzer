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
#include <ADXL362.h>

#define NUM_CAL_READINGS 15

ADXL362 xl;

int temp;
int xValue, yValue, zValue, Temperature;
int xOffset, yOffset, zOffset;

int xAverageRaw=0;
int yAverageRaw=0;
int zAverageRaw=0;
int xAverage=0;
int yAverage=0;
int zAverage=0;
int time = 0;

int lastXval;
int lastYval;
int lastZval;

void setup(){
    Serial.begin(9600);
    xl.begin();                   // Setup SPI protocol, issue device soft reset
    xl.beginMeasure();            // Switch ADXL362 to measure mode  
    xl.checkAllControlRegs();     // Burst Read all Control Registers, to check for proper setup
    
    // TODO: Zero out the values
    int xTotal = 0;
    int yTotal = 0;
    int zTotal = 0;
    for (int i = 0; i < NUM_CAL_READINGS; i++)
    {
      xTotal += xl.readXData();
      yTotal += xl.readYData();
      zTotal += xl.readZData();
    }
        Serial.print("XTotal: ");
        Serial.print(xTotal);

        Serial.print("    YTotal: ");
        Serial.print(yTotal);

        Serial.print("    ZTotal: ");
        Serial.print(zTotal);

    xOffset = xTotal / NUM_CAL_READINGS;
    yOffset = yTotal / NUM_CAL_READINGS;
    zOffset = zTotal / NUM_CAL_READINGS;
}

void loop(){
    time++;
    int xDiff;
    int yDiff;
    int zDiff;

    
    // read all three axis in burst to ensure all measurements correspond to same sample time
    for (int counter=0; counter < 3; counter++)
    {
     // xl.readXYZTData(xValue, yValue, zValue, Temperature);
      xValue= xl.readXData();
      yValue= xl.readYData();
      zValue= xl.readZData();
      xAverageRaw = xAverageRaw+xValue;
      yAverageRaw = yAverageRaw+yValue;
      zAverageRaw = zAverageRaw+zValue;
      
      delay(100);                // Arbitrary delay to make serial monitor easier to observe
    }
    xAverage=xAverageRaw/3;
    yAverage=yAverageRaw/3;
    zAverage=zAverageRaw/3;
    xAverageRaw=0;
    yAverageRaw=0;
    zAverageRaw=0;

    int currentX = xAverage -  xOffset;
    int currentY = yAverage - yOffset;
    int currentZ = zAverage - zOffset;

    xDiff = currentX - lastXval;
    yDiff = currentY - lastYval;
    zDiff = currentZ - lastZval;
    int actualMovement = (xDiff+yDiff+zDiff)/3;

//    Serial.print (time);
//    Serial.print (",");
//    Serial.print (xDiff);
//    Serial.print (",");
//    Serial.print (yDiff);
//    Serial.print (",");
//    Serial.print(zDiff);
    //Serial.print (",");
    Serial.print(abs(actualMovement));
    Serial.print ("\n");
    


    // Now that we've printed the differentials,
    // move our current Values into lastVals
    lastXval = currentX;
    lastYval = currentY;
    lastZval = currentZ;
}
