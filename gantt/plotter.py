from matplotlib import pyplot as plt
from matplotlib import patches
import numpy as np
from datetime import datetime
from PyQt5.QtCore import QDateTime

from util import eps
from gantt.reader import readGanttFile

class GanttPlotterWrapper:
    def __init__(self, fig, ax, data, colorTuple, start = None, step = None):
        self.fig : plt.Figure = fig
        self.ax : plt.Axes = ax
        self.data = data
        self.colorTuple = colorTuple
        self.nlines = 8
        self.start = start
        self.step = step
        self.yheight = 0.1
        self.parse()
    def parse(self):
        print("parsing ...")
        # parse self.data as gantt's format
        # if self.start or self.stop is none, set to data first / last time
        self.plottedData = [[] for _ in range(self.nlines)]
        if self.start is None:
            self.start = self.data[0][0]
        if self.step is None:
            self.step = 86400
        self.stop = self.start + self.step * self.nlines
        # sep [start, stop] into 8 intervals
        curStartTime = self.start
        curStopTime = self.start + self.step
        curID = 0
        for d in self.data:
            lastTime, time, status = d
            if time < self.start:
                continue
            if lastTime > self.stop:
                break
            if lastTime < self.start:
                lastTime = self.start
            if time > self.stop:
                time = self.stop
            if time <= curStopTime:
                left = (lastTime - curStartTime) / self.step
                right = (time - curStartTime) / self.step
                self.plottedData[curID].append((left, right, status))
            else:
                left = (lastTime - curStartTime) / self.step
                self.plottedData[curID].append((left, 1, status))
                curID += 1
                if curID < self.nlines:
                    curStartTime += self.step
                    curStopTime += self.step
                    right = (time - curStartTime) / self.step
                    self.plottedData[curID].append((0, right, status))
                else:
                    # all rested data is useless
                    break
        print("parse OK !")
    def plot(self):
        self.ax.clear()
        nth = 0
        ydiff = 1 / self.nlines # 0.125
        curY = 0
        print("plotting ...")
        cnt = 0
        for plottedInfos in self.plottedData:
            for info in plottedInfos:
                left, right, lblID = info
                col = self.colorTuple[int(lblID) - 1]
                rect = patches.Rectangle((left, curY), right - left, self.yheight, color = col)
                self.ax.add_patch(rect)
                cnt += 1
            curY += ydiff
            nth += 1
        print(f"{cnt} rects plotted.")
        # set yaxis' label
        self.ax.yaxis.set_label("Time")
        self.ax.yaxis.set_ticks(np.linspace(0, 1, self.nlines + 1))
        lbl = []
        t = self.start
        diff = (self.stop - self.start) / self.nlines
        for i in range(self.nlines + 1):
            tm = datetime.fromtimestamp(t)
            lbl.append(tm.strftime("%Y-%m-%d %H:%M:%S"))
            t += diff
        self.ax.yaxis.set_ticklabels(lbl)
        print(lbl)
        # self.ax.invert_yaxis()

        # legend : ignore
        '''
        legends = []
        for i in range(len(self.colorTuple)):
            pch = patches.Patch(color = self.colorTuple[i], label = f"label {i + 1}")
            legends.append(pch)
        self.ax.legend(handles = legends, loc = "upper left")
        '''

        # plot range
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_xticklabels([])
        self.ax.invert_yaxis()
        print("plot OK")


if __name__ == "__main__":
    data, totalLabel = readGanttFile("../ganttData.txt")
    print(totalLabel)
    fig, ax = plt.subplots()
    colorTuple = ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0), (0, 1, 1))
    wrapper = GanttPlotterWrapper(fig, ax, data, colorTuple)
    wrapper.plot()
    wrapper.ax.yaxis.set_inverted(True)
    plt.show()

