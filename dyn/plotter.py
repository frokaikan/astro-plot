from itertools import chain

import numpy as np
from matplotlib import pyplot as plt
from matplotlib import patches
from matplotlib.animation import FuncAnimation
from matplotlib.image import AxesImage
from time import time, sleep

from dyn.editor import genCircleOnXY, DR2XY, ballDist
from util import search, getSatellite

# 把data打包为字典格式
def wrapData(data):
    ret = {}
    l = zip(*data)
    ret["timestamp"] = next(l)
    ret["satellite"] = next(l)
    ret["solar"] = next(l)
    ret["lunar"] = next(l)
    ret["view"] = next(l)
    return ret, len(ret["timestamp"])

# 获取卫星的填充区域
def getSatelliteExt(dec, ra, ext = 0.05):
    x, y = DR2XY(dec, ra)
    return x - ext, x + ext, y - ext, y + ext

class PlotterWrapper:
    def __init__(self, fig : plt.Figure, ax : plt.Axes, canvas, data):
        self.fig = fig
        self.ax = ax
        self.canvas = canvas

        print("wrapping...")
        self.data, self.dataCnt = wrapData(data)
        print("wrap OK")

        self.cfg = type("", (), {})
        self.config()

        self.solar : list = []
        self.lunar : list = []
        self.viewX : list = []
        self.view  : list = []

        self.rawImg = np.flipud(getSatellite())
        self.satelliteIMG : AxesImage = self.ax.imshow(self.rawImg, origin = "lower")
        self.satelliteIMG.set_visible(False)
        self.ax.set_aspect("auto")
        self.ax.set_xlim(-1.2, 1.2)
        self.ax.set_ylim(-1.2, 1.2)
        self.ax.xaxis.set_ticks([])
        self.ax.yaxis.set_ticks([])

        self.background()
        self.init_anim()

        self.curTime = None
        self.idx = None

        self.plotAtIndex(0)

    def config(self):
        self.cfg.solarRadius = 50 * np.pi / 180,
        self.cfg.solarColor = (1, 0, 0, 0.5)
        self.cfg.lunarRadius = 40 * np.pi / 180,
        self.cfg.lunarColor = (1, 1, 0, 0.3)
        self.cfg.viewRadius = 0.5 * np.pi / 180,
        self.cfg.viewRadiusOnXY = 0.003
        self.cfg.viewColor = (0.3, 0.3, 0.3, 0.7)
        self.cfg.viewColorSpecial = (1, 0, 0, 0.7)
        self.cfg.viewXRadius = 2 * np.pi / 180
        self.cfg.viewXColor = (0, 0, 0.3, 1)
        self.cfg.viewXColorSpecial = (1, 0, 0, 0)

    @classmethod
    def ifSpecialView(self, dec, ra):
        specialDec = [36, 2 * 36, 3 * 36, 4 * 36, 5 * 36, 6 * 36, 7 * 36, 8 * 36, 9 * 36, 359]
        specialRa = [35, -45, 55, -65, 75, -70, 60, -50, 40, -30]
        # dec = dec * 180 / np.pi
        # ra = ra * 180 / np.pi
        for sDec, sRa in zip(specialDec, specialRa):
            if sDec > 180:
                sDec -= 360
            sDec = sDec / 180 * np.pi
            sRa = sRa / 180 * np.pi
            diff = ballDist((dec, ra), (sDec, sRa))
            diff = diff / np.pi * 180
            if diff < 3:
                return True
        return False

    def background(self):
        # 经度
        for dec in np.linspace(-np.pi / 2, np.pi / 2, 7):
            arr = np.array([DR2XY(dec, l) for l in np.linspace(-np.pi, np.pi, 500)])
            self.ax.plot(arr[:, 0], arr[:, 1], "-.k", linewidth=0.3)
        # 纬度
        for ra in np.linspace(-np.pi, np.pi, 9):
            arr = np.array([DR2XY(l, ra) for l in np.linspace(-np.pi / 2, np.pi / 2, 250)])
            self.ax.plot(arr[:, 0], arr[:, 1], "-.k", linewidth=0.3)
        # 背景
        self.canvas.draw()
        # 储存原始背景
        self.bkg = self.canvas.copy_from_bbox(self.ax.bbox)

    def init_anim(self):
        pch : patches.Patch
        for dec, ra in self.data["view"]:
            color = self.cfg.viewColorSpecial if self.ifSpecialView(dec, ra) else self.cfg.viewColor
            pch = patches.Circle(DR2XY(dec, ra), self.cfg.viewRadiusOnXY)
            pch.set_color(color)
            self.ax.add_patch(pch)
            self.view.append(pch)

    def plotAtIndex(self, idx):
        # 这个函数不应该直接调用 应该通过plotAtTime()调用
        assert (idx < self.dataCnt)

        pch : patches.Patch
        # 清空画布
        self.canvas.restore_region(self.bkg)

        # 之前的观测点
        for _id in range(idx - 1):
            pch = self.view[_id]
            self.ax.draw_artist(pch)

        # 储存背景 以供后面使用
        # self.canvas.blit()
        self.lastFrame = self.canvas.copy_from_bbox(self.ax.bbox)

        # 当前点
        ext = getSatelliteExt(*self.data["satellite"][idx])
        self.satelliteIMG.set_extent(ext)
        self.satelliteIMG.set_visible(True)
        self.ax.draw_artist(self.satelliteIMG)
        for pts in genCircleOnXY(*self.data["solar"][idx], self.cfg.solarRadius):
            pch = patches.Polygon(pts)
            pch.set_color(self.cfg.solarColor)
            self.solar.append(pch)
            self.ax.add_patch(pch)
            self.ax.draw_artist(pch)
        for pts in genCircleOnXY(*self.data["lunar"][idx], self.cfg.lunarRadius):
            pch = patches.Polygon(pts)
            pch.set_color(self.cfg.lunarColor)
            self.lunar.append(pch)
            self.ax.add_patch(pch)
            self.ax.draw_artist(pch)
        for pts in genCircleOnXY(*self.data["view"][idx], self.cfg.viewXRadius):
            pch = patches.Polygon(pts)
            pch.set_color(self.cfg.viewXColor)
            self.viewX.append(pch)
            self.ax.add_patch(pch)
            self.ax.draw_artist(pch)

        self.idx = idx
        self.canvas.blit(self.ax.bbox)

    def plotNextIndex(self, dIndex):
        # 应该通过addCurTime()函数调用 而非直接调用
        # 增量式绘图
        assert (self.idx + dIndex < self.dataCnt)

        # 形状计算
        pch : patches.Patch
        for pch in self.solar:
            pch.remove()
        for pch in self.lunar:
            pch.remove()
        for pch in self.viewX:
            pch.remove()
        self.solar.clear()
        self.lunar.clear()
        self.viewX.clear()

        ext = getSatelliteExt(*self.data["satellite"][self.idx + dIndex])
        self.satelliteIMG.set_extent(ext)
        for pts in genCircleOnXY(*self.data["solar"][self.idx + dIndex], self.cfg.solarRadius):
            pch = patches.Polygon(pts)
            pch.set_color(self.cfg.solarColor)
            self.solar.append(pch)
            self.ax.add_patch(pch)
        for pts in genCircleOnXY(*self.data["lunar"][self.idx + dIndex], self.cfg.lunarRadius):
            pch = patches.Polygon(pts)
            pch.set_color(self.cfg.lunarColor)
            self.lunar.append(pch)
            self.ax.add_patch(pch)
        for pts in genCircleOnXY(*self.data["view"][self.idx + dIndex], self.cfg.viewXRadius):
            pch = patches.Polygon(pts)
            pch.set_color(self.cfg.viewXColor)
            self.viewX.append(pch)
            self.ax.add_patch(pch)

        # if self.lastFrame is not None:
        self.canvas.restore_region(self.lastFrame)

        # 观察点
        for idx in range(dIndex):
            pch = self.view[self.idx + idx]
            self.ax.draw_artist(pch)

        # 储存背景
        # self.canvas.blit(self.ax.bbox)
        self.lastFrame = self.canvas.copy_from_bbox(self.ax.bbox)

        # 当前点
        self.ax.draw_artist(self.satelliteIMG)
        for pch in chain(self.solar, self.lunar, self.viewX):
            self.ax.draw_artist(pch)

        self.canvas.blit(self.ax.bbox)

    def plotAtTime(self, curTime):
        # 同plotAtIndex() 该函数不应该频繁调用
        self.curTime = curTime
        idx = search(self.data["timestamp"], curTime)
        self.plotAtIndex(idx)

    def addCurTime(self, dTime):
        # 这个函数不会调用plotAtTime() 只会调用plotNextIndex()
        finalTime = self.curTime + dTime
        self.curTime = finalTime
        allTimes = self.data["timestamp"]
        dIndex = 0
        while True:
            if self.idx + dIndex == self.dataCnt - 1:
                # the last viewpoint
                break
            else:
                nxtTime = allTimes[self.idx + dIndex + 1]
                if nxtTime > finalTime:
                    break
                else:
                    dIndex += 1
        if dIndex:
            self.plotNextIndex(dIndex)
            self.idx += dIndex

    def cache(self):
        self.cached_bkg = self.canvas.copy_from_bbox(self.ax.bbox)
        self.cached_time = self.curTime
        self.cached_idx = self.idx
        self.lastFrame = None

    def restore(self):
        self.curTime = self.cached_time
        self.idx = self.cached_idx
        self.canvas.restore_region(self.cached_bkg)
        self.canvas.blit()

if __name__ == "__main__":
    from dyn.reader import readFile
    rawData = readFile("../data.txt")
    ax : plt.Axes
    fig, ax = plt.subplots()
    canvas = fig.canvas
    ax.invert_yaxis()
    pltWrapper = PlotterWrapper(fig, ax, canvas, rawData)
    plt.show()
