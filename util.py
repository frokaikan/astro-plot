from PIL import Image

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

def getSatellite(path = r"D:\src\HammerAitof\HammerAitoff\dyn\satellite.png"):
    return Image.open(path)
