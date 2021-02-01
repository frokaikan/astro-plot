import re

def readGanttFile(absPath):
    '''
    [startTime, status]
    :param absPath:
    :return:
    '''
    print("reading ... ")
    ret = []
    lastLabel = None
    lastTime = None
    totalLabel = 0
    with open(absPath, "rt") as f:
        cont = f.read()
        patt = re.compile(r"\[(.*?)\]")
        m = re.finditer(patt, cont)
        timeStamp = (float(x.strip()) for x in next(m).group(1).split(","))
        label = (int(x.strip()) for x in next(m).group(1).split(","))
        ret = []
        for d in zip(timeStamp, label):
            if lastTime:
                ret.append((lastTime, d[0], lastLabel))
            lastTime = d[0]
            lastLabel = d[1]
            totalLabel = max(totalLabel, lastLabel)
    print("read OK !")
    return ret, totalLabel
