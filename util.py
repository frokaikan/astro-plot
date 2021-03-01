from types import MethodType

from PIL import Image
from PyQt5.QtWidgets import QMessageBox, QPushButton
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread
from time import sleep

eps = 1e-9



def eq0(x):
    return abs(x) < eps


def search(lis, elem):
    # found the last x which x <= elem
    def keyAt(idx):
        return lis[idx][0] if isinstance(lis[idx], (tuple, list)) else lis[idx]
    beg, end = 0, len(lis)
    mid = (beg + end) // 2
    ans = None
    while beg < end:
        if keyAt(mid) <= elem:
            beg = mid + 1
            ans = mid
        else:
            end = mid
        mid = (beg + end) // 2
    return ans

def getSatellite(path = r".\dyn\satellite.png"):
    return Image.open(path)


def doInThread(parent, func, *args, **kw):
    # 准备线程
    newThread = QThread()
    # 半模态对话框
    info = QMessageBox(parent)
    info.setIcon(QMessageBox.Information)
    info.setWindowTitle("请等待")
    info.setText("由于数据量较大, 请耐心等待。请不要关闭本对话框。")
    btn = QPushButton("确认")
    btn.setEnabled(False)
    info.addButton(btn, QMessageBox.YesRole)

    ret = None
    def onReturn(obj):
        nonlocal ret
        ret = obj
        info.setText("数据已经加载完毕")
        btn.setEnabled(True)
        newThread.quit()
    # 子线程
    class WorkingThread(QObject):
        sig = pyqtSignal(object)
        def __init__(self):
            super().__init__()
            self.sig.connect(onReturn)
        def work(self):
            ret = func(*args, **kw)
            self.sig.emit(ret)
    # 新的线程
    work = WorkingThread()
    work.moveToThread(newThread)

    newThread.started.connect(work.work)
    newThread.start()

    # 打开模态对话框
    info.exec_()

    return ret
