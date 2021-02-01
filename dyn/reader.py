import re
import numpy as np

# 返回5组数据 time, (dec, ra)*4
# time为unix时间戳 dec范围-pi/2~pi/2 ra范围-pi~pi
# 数据中dec范围-90~90 ra范围0~360 需要转换
def readFile(absPath):
    with open(absPath, "rt") as f:
        nowTime = 0
        for line in f:
            lineParts = [float(x) for x in re.split(r"\s|\[|\]", line.strip()) if x]
            if len(lineParts) != 9:
                raise ValueError(f"数据格式错误: {line}")
            this_part = []
            if lineParts[0] < nowTime:
                raise ValueError(f"时间不递增: {lineParts[0]} - {nowTime}")
            this_part.append(lineParts[0])
            nowTime = lineParts[0]
            for i in (1, 3, 5, 7):
                ra = lineParts[i]
                dec = lineParts[i + 1]
                if ra < 0 or ra > 360:
                    raise ValueError(f"ra {ra} in line {line} out of [0, 360]")
                if dec < -90 or dec > 90:
                    raise ValueError(f"dec {dec} in line {line} out of [-90, 90]")
                if ra > 180:
                    ra -= 360
                ra *= np.pi / 180
                dec *= np.pi / 180
                this_part.append((dec, ra))
            yield tuple(this_part)

if __name__ == "__main__":
    cnt = 0
    for line in readFile(r"../data.txt"):
        cnt += 1
        print(line)
    print(cnt)
