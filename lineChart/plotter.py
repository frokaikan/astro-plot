from datetime import datetime
import numpy as np
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

from lineChart.reader import readLCFile

class LCPlotterWrapper:
    def __init__(self, fig : plt.Figure, ax : plt.Axes, data):
        self.fig = fig
        self.ax = ax
        self.rawData = data
        self.minX = data[0]
        self.maxX = data[-1]
        self.doInterp()
        self.plot()
    def doInterp(self):
        dataY = []
        for i in range(1, len(self.rawData) + 1):
            dataY.append(i / 30)
        f = interp1d(self.rawData, dataY, 2)
        self.dataX = self.rawData
        self.dataY = f(self.dataX)
        '''
        self.dataX = self.rawData
        self.dataY = dataY
        '''
    def plot(self):
        self.ax.set_xlim(self.minX - 1, self.maxX + 1)
        xticks = np.linspace(self.minX, self.maxX, 5)
        self.ax.set_xticks(xticks)
        xlabel = []
        fmt = "%Y-%m-%d %H:%M:%S"
        for x in xticks:
            d = datetime.fromtimestamp(x)
            xlabel.append(d.strftime(fmt))
        self.ax.set_xticklabels(xlabel)
        self.ax.plot(self.dataX, self.dataY)

if __name__ == "__main__":
    fig, ax = plt.subplots()
    data = readLCFile("../data1736086396.txt")
    wrapper = LCPlotterWrapper(fig, ax, data)
    plt.show()
