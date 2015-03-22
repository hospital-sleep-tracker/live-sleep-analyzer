__author__ = 'dano'

import math
from sklearn import linear_model
from matplotlib import pyplot
from matplotlib.widgets import Slider
from utils import SleepAnalyzer, SleepEntryStore


class PostSessionCoefficientGraph(SleepAnalyzer):
    def __init__(self, **kwargs):
        super(PostSessionCoefficientGraph, self).__init__(**kwargs)
        pyplot.figure("PostSessionCoefficientGraph")
        pyplot.ion()
        pyplot.show()

        # self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 250))
        # self.line, = self.ax.plot(self.sleep_entries, lw=2)

    def show(self):
        super(PostSessionCoefficientGraph, self).show()
        x_values = [[x] for x in range(0, len(self.movement_coefficients))]
        y_values = [[y] for y in self.movement_coefficients]
        # regr = linear_model.LinearRegression()
        # regr.fit(x_values, y_values)
        pyplot.figure("PostSessionCoefficientGraph")

        # pyplot.clf()
        plot, = pyplot.plot(x_values, y_values, color='black')
        axframe = pyplot.axes([0.25, .1, 0.65, 0.03])
        sframe = Slider(axframe, 'Frame', 0, 99, valinit=0, valfmt='%d')
        # pyplot.scatter(x_values, movement_values, color='red')
        # pyplot.plot(x_values, regr.predict(x_values), color='blue', linewidth=3)
        pyplot.draw()


class LiveSessionLastEntriesGraph(SleepAnalyzer):
    def __init__(self, **kwargs):
        super(LiveSessionLastEntriesGraph, self).__init__(**kwargs)

    def add_entry(self, sleep_entry):
        super(LiveSessionLastEntriesGraph, self).add_entry(sleep_entry)
        x_values = [[x] for x in range(0, len(self.last_movement_sums))]
        y_values = [[y] for y in self.last_movement_sums]
        movement_values = [[y.movement_value] for y in self.last_entries]
        regr = linear_model.LinearRegression()
        regr.fit(x_values, y_values)
        pyplot.figure("LiveSessionLastEntriesGraph")
        pyplot.clf()
        pyplot.scatter(x_values, y_values, color='black')
        pyplot.scatter(x_values, movement_values, color='red')
        pyplot.plot(x_values, regr.predict(x_values), color='blue', linewidth=3)
        pyplot.pause(.05)


class PostSessionBigEntriesScatter(SleepAnalyzer):
    # WORKING
    def show(self):
        super(PostSessionBigEntriesScatter, self).show()
        x_values = [[sleep_entry.index] for sleep_entry in self.big_movement_entries]
        y_values = [[sleep_entry.movement_value] for sleep_entry in self.big_movement_entries]
        pyplot.figure("PostSessionBigEntriesScatter")
        # pyplot.clf()
        pyplot.axes(xlim=(0, max(x[0] for x in x_values)), ylim=(0, max(y[0] for y in y_values)))
        pyplot.scatter(x_values, y_values, color='black')

        # pyplot.scatter(x_values, movement_values, color='red')
        # pyplot.plot(x_values, regr.predict(x_values), color='blue', linewidth=3)
        # pyplot.pause(.05)
        pyplot.draw()
        pyplot.show()



class LiveSessionFullGraph(SleepEntryStore):
    """ NOT CURRENTLY WORKING
    Graph which shows the entire session as a whole.
    This class doesn't need to hook into add_entry. It simply waits until the final self.show is called
    to display all the session details on a graph."""
    def __init__(self, **kwargs):
        super(LiveSessionFullGraph, self).__init__(**kwargs)
        pyplot.figure("LiveSessionFullGraph")
        pyplot.ion()
        pyplot.show()
        self.sleep_entries = []

        # self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 250))
        # self.line, = self.ax.plot(self.sleep_entries, lw=2)

    def add_entry(self, sleep_entry):
        super(LiveSessionFullGraph, self).add_entry(sleep_entry)
        x_values = [[x] for x in range(0, len(self.sleep_entries))]
        y_values = [[y.movement_value] for y in self.sleep_entries]
        # regr = linear_model.LinearRegression()
        # regr.fit(x_values, y_values)
        pyplot.figure("LiveSessionFullGraph")

        # pyplot.clf()
        plot, = pyplot.plot(sleep_entry.index, sleep_entry.movement_value, color='black')
        # pyplot.scatter(x_values, movement_values, color='red')
        # pyplot.plot(x_values, regr.predict(x_values), color='blue', linewidth=3)
        pyplot.draw()


class PostSessionFullGraph(SleepAnalyzer):
    """ CURRENTLY WORKING
    Graph which shows the entire session as a whole.
    This class doesn't need to hook into add_entry. It simply waits until the final self.show is called
    to display all the session details on a graph."""
    def __init__(self, **kwargs):
        super(PostSessionFullGraph, self).__init__(**kwargs)
        pyplot.figure("PostSessionFullGraph")
        # pyplot.ion()
        # pyplot.show()
        self.sleep_entries = []

        # self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 250))
        # self.line, = self.ax.plot(self.sleep_entries, lw=2)

    def show(self):
        super(PostSessionFullGraph, self).show()
        x_values = [[x.index] for x in self.sleep_entries]
        y_values = [[y.movement_value] for y in self.sleep_entries]
        # regr = linear_model.LinearRegression()
        # regr.fit(x_values, y_values)
        pyplot.figure("PostSessionFullGraph")


        # pyplot.clf()
        self.fig, self.ax = pyplot.subplots()
        pyplot.subplots_adjust(left=0.25, bottom=0.25)
        self.plot, = pyplot.plot(x_values[0:50], y_values[0:50], color='black')
        self.axis = pyplot.axis([0, 50, 0, 250])
        axcolor = 'lightgoldenrodyellow'
        axfreq = pyplot.axes([0.25, 0.1, 0.65, 0.03], axisbg=axcolor)
        # axamp  = pyplot.axes([0.25, 0.15, 0.65, 0.03], axisbg=axcolor)

        self.sfreq = Slider(axfreq, 'Freq', 0, len(self.sleep_entries), valinit=1)
        # self.samp = Slider(axamp, 'Amp', 0.1, 10.0, valinit=1)
        self.sfreq.on_changed(self.update)
        # self.samp.on_changed(self.update)
        pyplot.draw()
        pyplot.show()

    def update(self, value):
        value = int(math.floor(value))
        # amp = self.samp.val
        freq = self.sfreq.val
        # self.axis = pyplot.axis([value, value + self.MOVEMENT_HISTORY_SIZE, 0, 250])
        self.plot.set_ydata([[x.movement_value] for x in self.sleep_entries[value:(value + self.MOVEMENT_HISTORY_SIZE)]])
        self.plot.set_xdata([[x.index] for x in self.sleep_entries[value:(value + self.MOVEMENT_HISTORY_SIZE)]])
        self.ax.set_xlim(value, value + self.MOVEMENT_HISTORY_SIZE)
        self.fig.canvas.draw_idle()

class Graph(SleepEntryStore):
    def __init__(self, **kwargs):
        super(Graph, self).__init__(**kwargs)
        pyplot.ion()
        # self.ax = pyplot.axes(xlim=(0, 50), ylim=(0, 200))
        self.ax = pyplot.axes()
        self.line, = pyplot.plot(self.sleep_entries, lw=2)

    def add_entry(self, sleep_entry):
        super(Graph, self).add_entry(sleep_entry)
        self.line.set_data(range(0, len(self.sleep_entries)), [x.movement_value for x in self.sleep_entries if x.movement_value > 3])
        self.ax.relim()
        self.ax.autoscale_view()
        pyplot.draw()

    def show(self):
        super(Graph, self).show()