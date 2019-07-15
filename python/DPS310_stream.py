from __future__ import print_function
import sys
import time
import threading
import serial
import atexit
import signal
import Queue

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

class PressureStreamer(serial.Serial):


    def __init__(self,param):
        self.param = param
        port_param = {k:self.param[k] for k in ('baudrate', 'timeout')}
        super(PressureStreamer,self).__init__(self.param['port'],**port_param)
        self.lock = threading.Lock()
        self.daq_thread = threading.Thread(target=self.read_data)
        self.daq_thread.daemon = True
        self.daq_queue = Queue.Queue()

        signal.signal(signal.SIGINT,self.sigint_handler)
        atexit.register(self.atexit)

        while self.in_waiting > 0:
            value = self.read()

        self.running = False
        self.t_list = []
        self.data_list = []
        self.live_plot = LivePlot(self.param)


    def atexit(self):
        print('quiting')
        with self.lock:
            self.write('e\n')
            self.running = False

    def sigint_handler(self,signum,frame):
        with self.lock:
            self.running = False
        exit(0)


    def read_data(self): 
        with self.lock:
            running = self.running
            start_t = self.start_t

        while running:
            with self.lock:
                line = self.readline()
                running = self.running
            if line:
                line = line.strip()
                line = line.split(',')
                values = [float(item) for item in line]
                elapsed_t = time.time() - start_t
                data_dict = {'elapsed_t': elapsed_t, 'values': values}
                self.daq_queue.put(data_dict)


    def run(self):

        data_count = 0
        
        # Start data stream
        self.running = True
        with self.lock:
            self.write('b\n')
        self.start_t = time.time() 
        self.daq_thread.start()


        with open(self.param['datafile'],'w') as fid:

            while True: 
                print('queue size: {} '.format(self.daq_queue.qsize()))
                new_data = False
                while True:
                    try:
                        data_dict = self.daq_queue.get_nowait() 
                        new_data = True
                    except Queue.Empty:
                        break

                    # Write data to file
                    fid.write('{:0.3f} '.format(data_dict['elapsed_t']))
                    for i, value in enumerate(data_dict['values']):
                        fid.write('{:0.3f}'.format(value))
                        if i < len(data_dict['values']) -1:
                            fid.write(' ')
                    fid.write('\n')

                    # Append new items to time and data lists
                    data_count += 1
                    self.t_list.append(data_dict['elapsed_t'])
                    if not self.data_list:
                        self.data_list = [[value] for value in data_dict['values']]
                    else:
                        for value_list, value in zip(self.data_list, data_dict['values']):
                            value_list.append(value)

                # Remove data older than t - t_window from t_list and data_list
                if new_data and len(self.t_list) > 2: 
                    while self.t_list[-1] - self.t_list[0] > self.param['t_window']:
                        self.t_list.pop(0)
                        for value_list in self.data_list:
                            value_list.pop(0)
                    self.live_plot.update(self.t_list, self.data_list)


class LivePlot(object):

    def __init__(self, param):
        self.param = param
        self.p_range = self.param['p_range'] 
        self.line_list = []
        self.setup_plots()

    def setup_plots(self):
        plt.ion()
        self.fig = plt.figure(1,figsize=self.param['figsize'])
        self.ax = plt.subplot(111)
        plt.grid('on')
        plt.xlabel('t (sec)')
        plt.ylabel('P (Pa)')
        label_list = []
        for ind in self.param['plot_list']:
            line, = plt.plot([0.0,self.param['t_window']], [0,0])
            self.line_list.append(line)
            self.ax.set_xlim(0.0,self.param['t_window'])
            self.ax.set_ylim(self.p_range[0],self.p_range[1])
            line.set_xdata([])
            line.set_ydata([])
            label_list.append('sens {}'.format(ind))
        plt.figlegend(self.line_list,label_list,'upper right')


    def update(self, t_list, data_list): 
        for i, ind in enumerate(self.param['plot_list']):
            line = self.line_list[i]
            values = data_list[ind]
            line.set_xdata(t_list)
            line.set_ydata(values)
            self.ax.set_xlim(min(t_list),max(self.param['t_window'],max(t_list)))
        self.fig.canvas.flush_events()
        plt.pause(0.02)

# ---------------------------------------------------------------------------------------
if __name__ == '__main__':



    param = {
            'port'      : '/dev/ttyACM0',
            'baudrate'  : 115200, 
            'timeout'   : 0.1, 
            'figsize'   : (20,5),
            't_window'  : 5.0,
            'p_range'   : (98300, 98400),
            'plot_list' : [0,26],
            'datafile'  : 'data.txt',
            }

    streamer = PressureStreamer(param)
    streamer.run()
