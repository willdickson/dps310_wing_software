from __future__ import print_function
import sys
import time
import numpy as np
import serial
import matplotlib
import matplotlib.pyplot as plt
import signal

class PressureStreamer(serial.Serial):

    BufferSize = 500 
    Baudrate = 115200

    def __init__(self,port='/dev/ttyACM0',timeout=1.0):
        param = {'baudrate': self.Baudrate, 'timeout': timeout}
        super(PressureStreamer,self).__init__(port,**param)
        time.sleep(1.0)
        while self.in_waiting > 0:
            value = self.read()

        self.t_start = time.time() 
        self.t_list = []
        self.data = []
        self.running = False
        signal.signal(signal.SIGINT, self.sigint_handler)

        self.plot_list = [0]
        self.plt_title = 'Pressure Stream Centered at Zero'
        self.t_range = [-60.0,1.0]
        self.p_range = [98000, 99000]
        #self.p_range = [-300, 300]
        self.x_lab = 't [sec]'
        self.y_lab = 'P [Pa]'
        self.line_list = []
        self.setup_plots()


    def sigint_handler(self,signum,frame):
        self.running = False

    def setup_plots(self):

        plt.ion()
        self.fig = plt.figure(1)
        self.ax = plt.subplot(111)
        plt.xlim(self.t_range[0],self.t_range[1])
        plt.ylim(self.p_range[0],self.p_range[1])
        plt.grid('on')
        plt.xlabel(self.x_lab)
        plt.ylabel(self.y_lab)

    def update_plots(self):
        if len(self.t_list) == 2:
            # Create lines when we have two data points
            t0, t1  = self.t_list
            label_list = []
            for ind in self.plot_list:
                x0, x1 = self.data[ind]
                line, = plt.plot([t0,x0], [t1,x1])
                self.line_list.append(line)
                label_list.append('sens {}'.format(ind))
            plt.figlegend(self.line_list,label_list,'upper right')

        elif len(self.t_list) > 2:
            for ind in self.plot_list:
                line = self.line_list[ind]
                values = self.data[ind]
                line.set_data(self.t_list,values)
                self.ax.set_xlim(min(self.t_list),max(self.t_list))
                #self.fig.canvas.flush_events()
                #time.sleep(0.001)
                #plt.pause(0.0001)

    def read_data(self): 
        line = self.readline()
        if line:
            line = line.strip()
            line = line.split(',')
            values = [float(item) for item in line]
            if not self.data:
                self.data = [[item] for item in values]
            else:
                for item_list, item in zip(self.data,values):
                    item_list.append(item)
                    if len(item_list) >  self.BufferSize:
                        item_list.pop(0)
            self.t_list.append(time.time() -  self.t_start)
            if len(self.t_list) > self.BufferSize:
                self.t_list.pop(0)


    def run(self):
        
        # Start data stream
        self.running = True
        self.write('b\n')

        # Read data and plot data
        while self.running: 
            self.read_data()
            self.update_plots()

            print(len(self.t_list),len(self.data[self.plot_list[0]]))

        # Stop data stream
        self.write('e\n')
        

# ---------------------------------------------------------------------------------------
if __name__ == '__main__':

    streamer = PressureStreamer()
    streamer.run()
