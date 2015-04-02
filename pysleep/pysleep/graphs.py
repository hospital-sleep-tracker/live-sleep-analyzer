from matplotlib import pyplot
from utils import SleepAnalyzer


class PostSessionGraphs(SleepAnalyzer):
    def __init__(self, **kwargs):
        super(PostSessionGraphs, self).__init__(**kwargs)
        pyplot.ion()

    def show(self):
        super(PostSessionGraphs, self).show()
        pyplot.figure("PostSessionGraphs %s" % self.session_id)
        pyplot.clf()
        nrows = 0
        ncols = 1

        # Graph 1
        if self.big_movement_entries:
            nrows += 1
            pyplot.subplot(nrows, ncols, nrows)
            x_values = [sleep_entry.index for sleep_entry in self.big_movement_entries]
            y_values = [sleep_entry.movement_value for sleep_entry in self.big_movement_entries]
            pyplot.xlim(xmin=0, xmax=max(x_values))
            pyplot.ylim(ymin=0, ymax=max(y_values))
            pyplot.plot(x_values, y_values, 'ro')

        # Graph 2
        if self.movement_coefficients:
            nrows += 1
            pyplot.subplot(nrows, ncols, nrows)
            x_values2 = range(0, len(self.movement_coefficients))
            y_values2 = self.movement_coefficients
            pyplot.xlim(xmin=0, xmax=len(self.movement_coefficients))
            pyplot.ylim(ymin=0, ymax=max(self.movement_coefficients))
            pyplot.plot(x_values2, y_values2, 'ro')

        # Graph 3
        if self.movement_sums:
            nrows += 1
            pyplot.subplot(nrows, ncols, nrows)
            y_values3 = self.movement_sums
            x_values3 = range(0, len(self.movement_sums))
            pyplot.xlim(xmin=0, xmax=len(self.movement_sums))
            pyplot.ylim(ymin=0, ymax=max(self.movement_sums))
            pyplot.plot(x_values3, y_values3, 'ro')

        if self.deteriorating_movement_sums:
            nrows += 1
            pyplot.subplot(nrows, ncols, nrows)
            y_values4 = self.deteriorating_movement_sums
            x_values4 = range(0, len(self.deteriorating_movement_sums))
            # pyplot.xlim(xmin=0, xmax=len(self.deteriorating_movement_sums))
            # pyplot.ylim(ymin=0, ymax=max(self.deteriorating_movement_sums))
            pyplot.plot(x_values4, y_values4, 'ro')

        if self.deteriorating_movement_sum_coefficients:
            nrows += 1
            pyplot.subplot(nrows, ncols, nrows)
            y_values5 = self.deteriorating_movement_sum_coefficients
            x_values5 = range(0, len(self.deteriorating_movement_sum_coefficients))
            # pyplot.xlim(xmin=0, xmax=len(self.deteriorating_movement_sums))
            # pyplot.ylim(ymin=0, ymax=max(self.deteriorating_movement_sums))
            pyplot.plot(x_values5, y_values5, 'ro')

        pyplot.draw()
        pyplot.show()


class LiveSessionGraphs(SleepAnalyzer):
    def __init__(self, **kwargs):
        super(LiveSessionGraphs, self).__init__(**kwargs)
        pyplot.ion()

    def add_entry(self, sleep_entry):
        super(LiveSessionGraphs, self).add_entry(sleep_entry)
        pyplot.figure("LiveSessionGraphs %s" % self.session_id)
        pyplot.clf()
        nrows = 1
        ncols = 1

        # Graph 1
        subplot = pyplot.subplot(nrows, ncols, nrows)
        subplot.set_title('Raw Movement Values')
        x_values = [x.index for x in self.last_entries]
        y_values = [x.movement_value for x in self.last_entries]
        pyplot.scatter(x_values, y_values, color='black')

        # Graph 2
        if self.movement_coefficients:
            nrows += 1
            subplot = pyplot.subplot(nrows, ncols, nrows)
            subplot.set_title('Movement Coefficients')
            x_values2 = [[x] for x in range(0, len(self.movement_coefficients))]
            y_values2 = [[y] for y in self.movement_coefficients]
            pyplot.xlim(xmin=0, xmax=len(self.movement_coefficients))
            pyplot.ylim(ymin=0, ymax=max(self.movement_coefficients))
            pyplot.scatter(x_values2, y_values2, color='black')

        pyplot.draw()


class GraphWithAnalyzer(PostSessionGraphs):
    pass
