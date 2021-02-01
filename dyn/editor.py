import numpy as np

from util import eq0

# 三维圆 直角坐标
# 该圆是单位球上的小圆
# 圆心为 Vn * t
# Vn 必须为单位向量
def genCircle(Vn : np.ndarray, t, sep = 40):
    assert (0 < t < 1 and f"genCircle(Vn, t) #2 t = {t} out of (0, 1).")
    assert (eq0((Vn ** 2).sum() - 1) and f"genCircle(Vn, t) #1 Vn = {Vn} is not unit vertex.")
    # 获得圆心
    center = Vn * t
    # 获得半径
    radius = (1 - t ** 2) ** 0.5
    # 获得圆的两个方向向量
    tmp = np.cross(Vn, (1, 0, 0))
    if (tmp**2).sum()**0.5 <= 0.08:
        Va = np.cross(Vn, (0, 1, 0))
        Va /= (Va ** 2).sum() ** 0.5
        Vb = np.cross(Vn, Va)
    else:
        Va = np.cross(Vn, (1, 0, 0))
        Va /= (Va ** 2).sum() ** 0.5
        Vb = np.cross(Vn, Va)
    assert (eq0((Vb ** 2).sum() - 1) and f"genCircle(Vn, t) Vb = {Vb} is not unit vertex.")
    # 圆的参数方程
    # V(p) = V(c) + V(r) * V(a) * cos(t) + V(r) * V(b) * sin(t)
    for t in np.linspace(0, 2 * np.pi, sep):
        # 曲线需要闭合
        ret = center + radius * (Va * np.cos(t) + Vb * np.sin(t))
        assert (eq0((ret ** 2).sum() - 1) and f"genCircla(Vn, t) Vret = {ret} is not unit vertex.")
        yield ret

# 直角坐标转球坐标
# (x, y, z)必须为单位向量
# 返回(dec, ra)
def euc2ball(x, y, z):
    r = (x ** 2 + y ** 2 + z ** 2) ** 0.5
    assert (eq0(r - 1) and f"euc2ball(x, y, z)'s param {(x, y, z)} is not unit vertex.")

    #1 dec == pi / 2 or - pi / 2
    if eq0(z - 1):
        return np.pi / 2, 0
    elif eq0(z + 1):
        return -np.pi / 2, 0

    dec = np.arcsin(z / r)
    #2 x or y == 0
    if eq0(y):
        if x > 0:
            return dec, 0
        else:
            return dec, np.pi
    elif eq0(x):
        if y > 0:
            return dec, np.pi / 2
        else:
            return dec, -np.pi / 2

    #3 other
    ra = np.arctan(abs(y) / abs(x))
    if x > 0:
        if y > 0:
            return dec, ra
        else:
            return dec, -ra
    else:
        if y > 0:
            return dec, np.pi - ra
        else:
            return dec, ra - np.pi

# 球坐标转直角坐标
# 返回一个单位向量
def ball2euc(dec, ra):
    z = np.sin(dec)
    xy = np.cos(dec)
    x = xy * np.cos(ra)
    y = xy * np.sin(ra)
    return x, y, z

# ptsGen生成直角坐标的(x, y, z)下的闭合曲线
# 转换为 1~2条 闭合路线, 不进行平面投影
# 返回(dec, ra)的路径
# 目前曲线与180°经线至多允许2个交点
def xyz2DR(ptsGen):
    lastDec, lastRa = None, None
    rets = [[], []]
    now = 0
    for pt in ptsGen:
        dec, ra = euc2ball(*pt)
        if lastDec is not None:
            if ra * lastRa < 0 and abs(ra - lastRa) > 6:
                # 跨越180°经线
                if now == 0:
                    # 首次跨越 无事发生
                    now = 1
                else:
                    # 再次跨越 两端闭合
                    dec0 = rets[0][-1][0]
                    npts = abs(dec0 - dec) / 0.1
                    # part 0
                    tmpRa = np.pi if rets[0][-1][1] > 0 else -np.pi
                    for tmpDec in np.linspace(dec0, dec, int(npts)):
                        rets[0].append((tmpDec, tmpRa))
                    # part 1
                    tmpRa = -tmpRa
                    for tmpDec in np.linspace(dec, dec0, int(npts)):
                        rets[1].append((tmpDec, tmpRa))
                    yield tuple(rets[1])
                    rets[1].clear()
                    now = 0
            else:
                # 不跨越180°经线 无事发生
                pass
        rets[now].append((dec, ra))
        lastDec, lastRa = dec, ra
    if now == 0:
        # 0 or 2 次跨越 回归远处
        assert len(rets[1]) == 0
        yield tuple(rets[0])
    else:
        # 单次跨越 合并返回
        decX = np.pi / 2 if rets[0][-1][0] > 0 else -np.pi / 2
        rets[1].extend(rets[0])
        dec0 = rets[1][-1][0]
        tmpRa = np.pi if rets[1][-1][1] > 0 else -np.pi
        for tmpDec in np.linspace(dec0, decX, int(abs(dec0 - decX) / 0.1)):
            rets[1].append((tmpDec, tmpRa))
        dec1 = rets[1][0][0]
        tmpRa = -tmpRa
        for tmpDec in np.linspace(decX, dec1, int(abs(decX - dec1) / 0.1)):
            rets[1].append((tmpDec, tmpRa))
        yield tuple(rets[1])

# HammerAitoff投影
# (dec, ra)转(x, y)
# dec [-pi/2, pi/2]
# ra [-pi, pi]
# x, y [-1, 1]
def XY2DR(x, y):
    z = (1 - x ** 2 / 2 - y ** 2 / 2) ** 0.5
    dec = np.arcsin(2 ** 0.5 * y * z)
    ra = 2 * np.arctan(2 ** 0.5 * x * z / (2 * z ** 2 - 1))
    return dec, ra

def DR2XY(dec, ra):
    z = (1 + np.cos(dec) * np.cos(ra / 2))
    x = np.cos(dec) * np.sin(ra / 2) / z
    y = np.sin(dec) / z
    return x, y

def ballDist(DR1, DR2):
    dec1, ra1 = DR1
    dec2, ra2 = DR2
    decDiff = dec1 - dec2
    decDiff = min(abs(decDiff - 2 * np.pi), abs(decDiff), abs(decDiff + 2 * np.pi))
    raDiff = abs(ra1 - ra2)
    return (decDiff ** 2 + raDiff ** 2) ** 0.5

# 生成投影中心在 (dec, ra) 投影半径为deg的圆的投影轨迹
def genCircleOnXY(dec, ra, deg):
    center = np.array(ball2euc(dec, ra))
    circleGen = genCircle(center, np.cos(deg))
    ret = []
    for DRs in xyz2DR(circleGen):
        ret.clear()
        for dr in DRs:
            xy = DR2XY(*dr)
            ret.append(xy)
        yield ret

if __name__ == "__main__":
    for pts in genCircleOnXY(0.1, np.pi - 0.05, 0.3):
        for pt in pts:
            print(pt, XY2DR(*pt))
        print("---------------------------------------")
