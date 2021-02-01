def readLCFile(absPath):
    ret = []
    with open(absPath, "rt") as f:
        for line in f:
            line = line.strip()
            if line:
                tm = float(line.split()[0])
                ret.append(tm)
    return ret

if __name__ == "__main__":
    ret = readLCFile("../data1736086396.txt")
    print(ret)
