###### Native Python #######
import re
import time

###### Reference files from interwebz #######
import serial
import matplotlib
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import animation as animation

ser = serial.Serial()
ser.baudrate = 9600
ser.port= 'COM3'
ser.open()

fig = plt.figure()
ax = plt.axes(xlim=(0, 100), ylim=(0, 200))
line, = ax.plot([], [], lw=2)
i=1
buffer = [100,120,140];
def init():
    line.set_data([], [])
    return line,

def animate(i):
    output=str(ser.read(4))
    outputre=re.split("\W+",output)
    buffer.append(outputre[1])
    x = np.linspace(0,100,len(buffer))
   # y = int(outputre[1])
    y=buffer
    line.set_data(x, y)
    #print (outputre[1])
    #print (buffer)
    return line,

anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=100, interval=20, blit=True)
plt.show()
#while True:
#    output=str(ser.read(4))
#    outputre=re.split("\W+",output)
#    #print(output)
#    print (outputre[1])
#    #time.sleep(1)

