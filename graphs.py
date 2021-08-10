import sys
from matplotlib import pyplot as plt

filename = sys.argv[1]

with open(filename) as file:
    lines = file.readlines()
    ys = [int(line.strip()) for line in lines]
    print(ys)
    plt.plot(ys)
    plt.show()
