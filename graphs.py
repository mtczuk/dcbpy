import sys
from matplotlib import pyplot as plt

USE_DOTS = True
xlabel = "mensagens recebidas"
ylabel = "tamanho do rollback resultante da mensagem"


filename = sys.argv[1]


with open(filename) as file:
    print("aa", xlabel, ylabel)
    lines = file.readlines()
    ys = [int(line.strip()) for line in lines]
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if USE_DOTS:
        plt.plot(
            ys,
            linestyle="",
            marker="o",
        )
    else:
        plt.plot(ys)

plt.show()
