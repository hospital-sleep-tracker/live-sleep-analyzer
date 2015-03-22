from matplotlib import pyplot
from utils import SleepAnalyzer


class PostSessionGraphs(SleepAnalyzer):
    def show(self):
        super(PostSessionGraphs, self).show()
        pyplot.figure("PostSessionGraphs")
        nrows = 2
        ncols = 1

        # Graph 1
        if self.big_movement_entries:
            pyplot.subplot(nrows, ncols, 1)
            x_values = [[sleep_entry.index] for sleep_entry in self.big_movement_entries]
            y_values = [[sleep_entry.movement_value] for sleep_entry in self.big_movement_entries]
            pyplot.xlim(xmin=0, xmax=max(x[0] for x in x_values))
            pyplot.ylim(ymin=0, ymax=max(y[0] for y in y_values))
            pyplot.scatter(x_values, y_values, color='black')

        # Graph 2
        pyplot.subplot(nrows, ncols, 2)
        x_values2 = [[x] for x in range(0, len(self.movement_coefficients))]
        y_values2 = [[y] for y in self.movement_coefficients]
        pyplot.xlim(xmin=0, xmax=len(self.movement_coefficients))
        pyplot.ylim(ymin=0, ymax=max(self.movement_coefficients))
        pyplot.scatter(x_values2, y_values2, color='black')

        # Graph 3
        # pyplot.subplot(nrows, ncols, 3)
        # x_values3 = [[x] for x in range(0, len(self.movement_coefficients))]
        # y_values3 = [[y] for y in self.movement_coefficients]
        # pyplot.xlim(xmin=0, xmax=len(self.movement_coefficients))
        # pyplot.ylim(ymin=0, ymax=max(self.movement_coefficients))
        # pyplot.scatter(x_values3, y_values3, color='black')


class LiveSessionGraphs(SleepAnalyzer):
    def add_entry(self, sleep_entry):
        super(LiveSessionGraphs, self).add_entry(sleep_entry)
        pyplot.figure("LiveSessionGraphs")
        pyplot.clf()
        nrows = 2
        ncols = 1

        # Graph 1
        pyplot.subplot(nrows, ncols, 1)
        x_values = [x.index for x in self.last_entries]
        y_values = [x.movement_value for x in self.last_entries]
        pyplot.scatter(x_values, y_values, color='black')

        # Graph 2
        subplot = pyplot.subplot(nrows, ncols, 2)
        subplot.set_title('Movement Coefficients')
        x_values2 = [[x] for x in range(0, len(self.movement_coefficients))]
        y_values2 = [[y] for y in self.movement_coefficients]
        pyplot.xlim(xmin=0, xmax=len(self.movement_coefficients))
        pyplot.ylim(ymin=0, ymax=max(self.movement_coefficients))
        pyplot.scatter(x_values2, y_values2, color='black')


class GraphWithAnalyzer(PostSessionGraphs, LiveSessionGraphs):
    def __init__(self, **kwargs):
        super(GraphWithAnalyzer, self).__init__(**kwargs)
        pyplot.ion()

    def show(self):
        super(GraphWithAnalyzer, self).show()
        pyplot.show()

    def add_entry(self, sleep_entry):
        super(GraphWithAnalyzer, self).add_entry(sleep_entry)
        pyplot.draw()
