import sys

from PyQt5.QtCore import QRegExp, Qt, QTime, QDateTime, QTimer
from PyQt5.QtGui import QRegExpValidator, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QDialog, QHBoxLayout, QLayout, \
    QLabel, QDateTimeEdit, QLineEdit, QSlider, QFileDialog, QMessageBox, QColorDialog, QComboBox
from matplotlib import pyplot as plt

from util import doInThread

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
plt.ioff()
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
import numpy as np
from time import time

from dyn.plotter import PlotterWrapper
from dyn.reader import readFile

from gantt.reader import readGanttFile
from gantt.plotter import GanttPlotterWrapper

from lineChart.reader import readLCFile
from lineChart.plotter import LCPlotterWrapper

def RBindWidgets(*widgetsOrLayouts):
    layout = QHBoxLayout()
    for wl in widgetsOrLayouts:
        if isinstance(wl, QWidget):
            layout.addWidget(wl)
        elif isinstance(wl, QLayout):
            layout.addLayout(wl)
        elif isinstance(wl, int):
            layout.addStretch(wl)
        else:
            raise ValueError(f"{wl} is not {QWidget} nor {QLayout}")
    return layout


def CBindWidgets(*widgetsOrLayouts):
    layout = QVBoxLayout()
    for wl in widgetsOrLayouts:
        if isinstance(wl, QWidget):
            layout.addWidget(wl)
        elif isinstance(wl, QLayout):
            layout.addLayout(wl)
        elif isinstance(wl, int):
            layout.addStretch(wl)
        else:
            raise ValueError(f"{wl} is not {QWidget} nor {QLayout}")
    return layout


def layout2widget(parent, layout):
    ret = QWidget(parent)
    ret.setLayout(layout)
    return ret


class UI:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.initUI()
        sys.exit(self.app.exec_())

    def initUI(self):
        self.mainWidget = QWidget()
        self.mainWidget.setWindowTitle("巡天结果展示软件")

        lbl1 = QLabel("欢迎使用\t有问题请联系: 541240857@qq.com", self.mainWidget)
        lbl2 = QLabel(self.mainWidget)
        pix = QPixmap("main.jpg")
        lbl2.setPixmap(pix)

        btn1 = QPushButton("动态巡天结果展示", self.mainWidget)
        btn2 = QPushButton("巡天规划甘特图", self.mainWidget)
        btn3 = QPushButton("巡天覆盖曲线展示", self.mainWidget)

        layout = CBindWidgets(lbl1, lbl2, RBindWidgets(btn1, btn3, btn2))
        self.mainWidget.setLayout(layout)

        btn1.clicked.connect(self.showDyn)
        btn2.clicked.connect(self.showGantt)
        btn3.clicked.connect(self.showLC)

        self.mainWidget.setFixedSize(self.mainWidget.width(), self.mainWidget.height())
        self.mainWidget.show()

    def showDyn(self):
        self.dyn = type("", (), {})

        self.dyn.dialog = QDialog(self.mainWidget)
        self.dyn.dialog.setWindowTitle("动态巡天结果")
        self.dyn.dialog.setAttribute(Qt.WA_DeleteOnClose)

        self.dyn.fig: plt.Figure
        self.dyn.ax: plt.Axes
        self.dyn.fig = plt.figure()
        self.dyn.ax = self.dyn.fig.add_subplot()
        self.dyn.ax.set_xlabel("黄道坐标")
        self.dyn.ax.xaxis.set_ticklabels([])
        self.dyn.ax.yaxis.set_ticklabels([])

        self.dyn.canvas = FigureCanvasQTAgg(self.dyn.fig)
        self.dyn.canvas.setParent(self.dyn.dialog)
        # self.dyn.toolbar = NavigationToolbar2QT(self.dyn.canvas, self.dyn.dialog)

        self.dyn.dialog.setFixedSize(1024, 768)

        # 布局
        self.dyn.btnImport = QPushButton("导入数据", self.dyn.dialog)

        self.dyn.btnExport = QPushButton("生成动画", self.dyn.dialog)
        self.dyn.btnExport.setEnabled(False)

        self.dyn.startEditor = QDateTimeEdit(self.dyn.dialog)
        self.dyn.startEditor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dyn.startEditor.setEnabled(False)

        self.dyn.stopEditor = QDateTimeEdit(self.dyn.dialog)
        self.dyn.stopEditor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dyn.stopEditor.setEnabled(False)

        self.dyn.curTime = QDateTimeEdit(self.dyn.dialog)
        self.dyn.curTime.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.dyn.curTime.setEnabled(False) # 当前时间始终不可编辑

        # slider以秒为单位进行控制
        self.dyn.slider = QSlider(Qt.Horizontal, self.dyn.dialog)
        self.dyn.slider.setSingleStep(1)
        self.dyn.slider.setPageStep(86400)
        self.dyn.slider.setEnabled(False)

        self.dyn.pauseOrRecoverBtn = QPushButton("播放", self.dyn.dialog)
        self.dyn.pauseOrRecoverBtn.setCheckable(True)
        self.dyn.pauseOrRecoverBtn.setEnabled(False)

        self.dyn.stopBtn = QPushButton("结束", self.dyn.dialog)
        self.dyn.stopBtn.setEnabled(False)

        self.dyn.animSpeedEditor = QLineEdit(self.dyn.dialog)
        self.dyn.animSpeedEditor.setText("1000")
        validator = QRegExpValidator(QRegExp(r"[1-9]\d*"))
        self.dyn.animSpeedEditor.setValidator(validator)
        self.dyn.animSpeedEditor.setEnabled(False)

        layoutDown = QVBoxLayout()
        layoutDown.addLayout(RBindWidgets(1, self.dyn.btnImport, self.dyn.btnExport, 1))
        layoutDown.addLayout(RBindWidgets(
            QLabel("开始时间", self.dyn.dialog), self.dyn.startEditor, 1,
            QLabel("结束时间", self.dyn.dialog), self.dyn.stopEditor
        ))
        layoutDown.addWidget(self.dyn.slider)
        layoutDown.addLayout(RBindWidgets(
            1, QLabel("当前时间", self.dyn.dialog), self.dyn.curTime, 1
        ))
        layoutDown.addLayout(RBindWidgets(self.dyn.pauseOrRecoverBtn, self.dyn.stopBtn))
        layoutDown.addLayout(RBindWidgets(
            QLabel("动画速度 __s/200ms", self.dyn.dialog), self.dyn.animSpeedEditor
        ))

        widgetDown = layout2widget(self.dyn.dialog, layoutDown)
        widgetDown.setMaximumHeight(300)
        widgetUp = layout2widget(self.dyn.dialog, CBindWidgets(self.dyn.canvas))
        dialogLayout = CBindWidgets(widgetUp, widgetDown)
        self.dyn.dialog.setLayout(CBindWidgets(widgetUp, widgetDown))

        # 控制

        # 控件是否可用
        def staticMotion():
            self.dyn.btnImport.setEnabled(True)
            self.dyn.btnExport.setEnabled(True)
            self.dyn.startEditor.setEnabled(True)
            self.dyn.stopEditor.setEnabled(True)
            self.dyn.slider.setEnabled(True)
            self.dyn.pauseOrRecoverBtn.setEnabled(False)
            self.dyn.stopBtn.setEnabled(False)
            self.dyn.animSpeedEditor.setEnabled(False)

        def animWaitMotion():
            self.dyn.btnImport.setEnabled(False)
            self.dyn.btnExport.setEnabled(False)
            self.dyn.startEditor.setEnabled(False)
            self.dyn.stopEditor.setEnabled(False)
            self.dyn.slider.setEnabled(True)
            self.dyn.pauseOrRecoverBtn.setEnabled(True)
            self.dyn.stopBtn.setEnabled(True)
            self.dyn.animSpeedEditor.setEnabled(True)

        def animRunMotion():
            self.dyn.btnImport.setEnabled(False)
            self.dyn.btnExport.setEnabled(False)
            self.dyn.startEditor.setEnabled(False)
            self.dyn.stopEditor.setEnabled(False)
            self.dyn.slider.setEnabled(False)
            self.dyn.pauseOrRecoverBtn.setEnabled(True)
            self.dyn.stopBtn.setEnabled(False)
            self.dyn.animSpeedEditor.setEnabled(False)

        # 生成动画相关
        self.dyn.rawData = None
        self.dyn.plotterWrapper: PlotterWrapper = None

        # 导入数据
        def readData():
            fileName = QFileDialog.getOpenFileName(self.dyn.dialog, "Select data", ".")
            if fileName[0]:
                try:
                    self.dyn.rawData = readFile(fileName[0])
                    staticMotion()
                    self.dyn.ax.clear()
                    '''
                    tempMsg = QMessageBox(self.dyn.dialog)
                    tempMsg.setIcon(QMessageBox.Information)
                    tempMsg.setWindowTitle("正在载入")
                    tempMsg.setText("由于数据量较大, 请耐心等待...")
                    tempBtn = QPushButton("确定", self.dyn.dialog)
                    tempBtn.setEnabled(False)
                    tempMsg.addButton(tempBtn, QMessageBox.YesRole)
                    tempMsg.open()
                    # 
                    tempBtn.setEnabled(True)
                    tempMsg.setText("数据载入完毕")
                    '''
                    self.dyn.plotterWrapper = doInThread(self.dyn.dialog,
                        PlotterWrapper,
                        self.dyn.fig, self.dyn.ax, self.dyn.canvas, self.dyn.rawData
                    )
                    startTime = int(np.floor(self.dyn.plotterWrapper.data["timestamp"][0]))
                    stopTime = int(np.ceil(self.dyn.plotterWrapper.data["timestamp"][-1]))
                    self.dyn.startEditor.setDateTime(QDateTime.fromTime_t(startTime))
                    self.dyn.stopEditor.setDateTime(QDateTime.fromTime_t(stopTime))
                    self.dyn.slider.setMinimum(startTime)
                    self.dyn.slider.setMaximum(stopTime)
                except Exception as e:
                    print(f"exception {e} raised")
        self.dyn.btnImport.clicked.connect(readData)

        self.dyn.timer = QTimer(self.dyn.dialog)
        self.dyn.timer.setInterval(200)
        startTime, stopTime, dTime = None, None, None
        curTime = None

        def nextFrame():
            nonlocal startTime, stopTime, dTime, curTime
            assert (dTime is not None)
            nxtTime = curTime + dTime
            if nxtTime >= stopTime:
                '''
                nxtTime = startTime
                self.dyn.plotterWrapper.restore()
                self.dyn.slider.setValue(startTime)
                '''
                # 时间到 什么都不做
                pass
            else:
                self.dyn.plotterWrapper.addCurTime(dTime)
                self.dyn.slider.setValue(nxtTime)
            curTime = nxtTime
        self.dyn.timer.timeout.connect(nextFrame)

        # 生成动画
        def genAnim():
            nonlocal startTime, stopTime
            startTime = self.dyn.startEditor.dateTime().toSecsSinceEpoch()
            stopTime = self.dyn.stopEditor.dateTime().toSecsSinceEpoch()
            if startTime >= stopTime:
                QMessageBox.information(
                    self.dyn.dialog,
                    "错误的时间区间",
                    "动画开始时间必须早于结束时间",
                    QMessageBox.Ok
                )
            else:
                self.dyn.plotterWrapper.plotAtTime(startTime)
                # self.dyn.plotterWrapper.cache()
                self.dyn.slider.setValue(startTime)
                animWaitMotion()
        self.dyn.btnExport.clicked.connect(genAnim)

        # 暂停动画
        def pauseOrRecoverAnim(pressed):
            if pressed:
                text = self.dyn.animSpeedEditor.text()
                if text == "":
                    QMessageBox.information(self.dyn.dialog, "请设置动画步长", "动画步长不能为空", QMessageBox.Ok)
                    return
                else:
                    nonlocal dTime
                    dTime = int(text)
                    animRunMotion()
                    self.dyn.pauseOrRecoverBtn.setText("暂停")
                    self.dyn.timer.start()
            else:
                animWaitMotion()
                self.dyn.pauseOrRecoverBtn.setText("播放")
                self.dyn.timer.stop()
        self.dyn.pauseOrRecoverBtn.clicked[bool].connect(pauseOrRecoverAnim)

        # 拖动滚动条
        def sliderMove():
            nonlocal curTime
            curTime = self.dyn.slider.value()
            self.dyn.curTime.setDateTime(QDateTime.fromSecsSinceEpoch(curTime))
        self.dyn.slider.valueChanged.connect(sliderMove)
        def sliderRelease():
            nonlocal curTime, startTime, stopTime
            curTime = self.dyn.slider.value()
            if startTime is not None:
                if curTime < startTime:
                    curTime = startTime
                if curTime > stopTime:
                    curTime = stopTime
            self.dyn.curTime.setDateTime(QDateTime.fromSecsSinceEpoch(curTime))
            self.dyn.slider.setValue(curTime)
            self.dyn.plotterWrapper.plotAtTime(curTime)
        self.dyn.slider.sliderReleased.connect(sliderRelease)

        # 结束动画
        def stopAnim():
            nonlocal startTime, stopTime, dTime, curTime
            staticMotion()
            startTime, stopTime, dTime = None, None, None
            curTime = None
        self.dyn.stopBtn.clicked.connect(stopAnim)

        self.dyn.dialog.exec_()

    def showGantt(self):
        self.gantt = type("", (), {})

        self.gantt.dialog = QDialog(self.mainWidget)
        self.gantt.dialog.setWindowTitle("巡天状态甘特图")
        self.gantt.dialog.setAttribute(Qt.WA_DeleteOnClose)

        self.gantt.fig: plt.Figure
        self.gantt.ax: plt.Axes

        self.gantt.fig, self.gantt.ax = plt.subplots()
        self.gantt.ax.xaxis.set_ticklabels([])
        self.gantt.ax.yaxis.set_ticklabels([])
        self.gantt.canvas = FigureCanvasQTAgg(self.gantt.fig)
        self.gantt.canvas.setParent(self.gantt.dialog)
        # self.gantt.navigator = NavigationToolbar2QT(self.gantt.canvas, self.gantt.dialog)

        # 布局

        # 左侧
        self.gantt.btnImport = QPushButton("导入数据", self.gantt.dialog)
        self.gantt.btnPlot = QPushButton("绘图", self.gantt.dialog)
        self.gantt.btnPlot.setEnabled(False)

        # 时间
        self.gantt.startTimeEditor = QDateTimeEdit(self.gantt.dialog)
        self.gantt.startTimeEditor.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.gantt.stepEditor = QComboBox(self.gantt.dialog)
        self.gantt.stepEditor.addItem("1小时")
        self.gantt.stepEditor.addItem("3小时")
        self.gantt.stepEditor.addItem("12小时")
        self.gantt.stepEditor.addItem("1天")

        layoutLeft = CBindWidgets(
            RBindWidgets(self.gantt.btnImport),
            RBindWidgets(QLabel("开始时间", self.gantt.dialog), self.gantt.startTimeEditor),
            RBindWidgets(QLabel("步长", self.gantt.dialog), self.gantt.stepEditor),
            RBindWidgets(self.gantt.btnPlot)
        )

        # 右侧

        # 颜色说明
        layoutRight = QVBoxLayout()
        name_color = (
            ("巡天观测",      0x86ff6b),
            ("南大西洋异常区", 0xff2111),
            ("非巡天时段",    0xffd694),
            ("轨道维持",      0xff7e57),
            ("空间站对接",    0xffa1c2),
            ("空闲时段",     0xffffff)
        )
        colorTuple = []
        for idx in range(len(name_color)):
            l = QLabel(f"{idx + 1} : {name_color[idx][0]}", self.gantt.dialog)
            c = QLabel(self.gantt.dialog)
            chex = name_color[idx][1]
            c.setStyleSheet(f"QLabel{{background-color:rgb({chex // 65536},{chex // 256 % 256},{chex % 256});}}")
            colorTuple.append(f"#{chex:06x}")
            layoutRight.addLayout(RBindWidgets(c, l))
        colorTuple = tuple(colorTuple)

        self.gantt.dialog.setFixedSize(2000, 1500)
        widgetUp = CBindWidgets(self.gantt.canvas)
        widgetDown = layout2widget(self.gantt.dialog, RBindWidgets(layoutLeft, layoutRight))
        widgetDown.setMaximumHeight(300)

        self.gantt.dialog.setLayout(CBindWidgets(widgetUp, widgetDown))

        # 控制

        # 读入数据
        def readSlot():
            fileName = QFileDialog.getOpenFileName(self.gantt.dialog, "Select data", ".")
            if fileName[0]:
                try:
                    self.gantt.rawData, self.gantt.totalLabel = readGanttFile(fileName[0])
                    if self.gantt.totalLabel > len(name_color):
                        QMessageBox.information(self.gantt.dialog, "label错误", f"label取值范围必须为1 - {len(name_color)}",
                                                QMessageBox.Ok)
                        return
                    self.gantt.startTimeEditor.setDateTime(QDateTime.fromSecsSinceEpoch(self.gantt.rawData[0][0]))
                    self.gantt.stepEditor.setCurrentIndex(3)
                    self.gantt.btnPlot.setEnabled(True)
                except Exception as e:
                    print(f"exception {e} raised")

        self.gantt.btnImport.clicked.connect(readSlot)

        # 绘图
        def plot():
            startTime = self.gantt.startTimeEditor.dateTime().toSecsSinceEpoch()
            stepIndices = [3600 * x for x in (1, 3, 12, 24)]
            stepTime = stepIndices[self.gantt.stepEditor.currentIndex()]
            wrapper = GanttPlotterWrapper(
                self.gantt.fig, self.gantt.ax,
                self.gantt.rawData, colorTuple,
                startTime, stepTime
            )
            self.gantt.ax.clear()
            wrapper.plot()
            self.gantt.canvas.draw()

        self.gantt.btnPlot.clicked.connect(plot)

        self.gantt.dialog.exec_()

    def showLC(self):
        self.lc = type("", (), {})

        self.lc.dialog = QDialog(self.mainWidget)
        self.lc.dialog.setWindowTitle("巡天覆盖曲线")
        self.lc.dialog.setAttribute(Qt.WA_DeleteOnClose)

        self.lc.fig : plt.Figure
        self.lc.ax : plt.Axes

        self.lc.fig, self.lc.ax = plt.subplots()
        self.lc.ax.xaxis.set_ticklabels([])
        self.lc.ax.yaxis.set_ticklabels([])
        self.lc.canvas = FigureCanvasQTAgg(self.lc.fig)
        self.lc.canvas.setParent(self.lc.dialog)
        # self.lc.toolbar = NavigationToolbar2QT(self.lc.canvas, self.lc.dialog)

        # 布局
        self.lc.modeSelect = QComboBox(self.lc.dialog)
        self.lc.modeSelect.addItem("巡天面积随时间变化曲线")
        self.lc.btnImport = QPushButton("确定", self.lc.dialog)

        self.lc.dialog.setFixedSize(2000, 1500)
        self.lc.widgetUp = layout2widget(self.lc.dialog, CBindWidgets(self.lc.canvas))
        self.lc.widgetDown = layout2widget(self.lc.dialog, RBindWidgets(1, self.lc.modeSelect, self.lc.btnImport, 1))
        self.lc.widgetDown.setMaximumHeight(100)

        self.lc.dialog.setLayout(CBindWidgets(self.lc.widgetUp, self.lc.widgetDown))

        # 控制
        def plot():
            fileName = QFileDialog.getOpenFileName(self.lc.dialog, "Select data", ".")
            if fileName[0]:
                try:
                    self.lc.rawData = readLCFile(fileName[0])
                    wrapper = LCPlotterWrapper(self.lc.fig, self.lc.ax, self.lc.rawData)
                    self.lc.ax.clear()
                    wrapper.plot()
                    self.lc.canvas.draw()
                except Exception as e:
                    print(f"exception {e} raised")
        self.lc.btnImport.clicked.connect(plot)

        self.lc.dialog.exec_()


if __name__ == "__main__":
    UI()
