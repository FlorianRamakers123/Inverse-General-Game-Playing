def colored(s,color):
    if color == "red":
        return '\x1b[1;31;48m' + str(s) + '\x1b[0m'
    elif color == "green":
        return '\x1b[1;32;48m' + str(s) + '\x1b[0m'
    elif color == "yellow":
        return '\x1b[1;33;48m' + str(s) + '\x1b[0m'
    elif color == "blue":
        return '\x1b[1;37;44m' + str(s) + '\x1b[0m'
    elif color == "white":
        return '\x1b[7;30;47m' + str(s) + '\x1b[0m'
def colored_scale(s,scale):
    if scale < 0.25:
        return '\x1b[1;31;48m' + "{:.3f}".format(s) + '\x1b[0m'
    elif 0.25 <= scale < 0.75:
        return '\x1b[1;33;48m' + "{:.3f}".format(s) + '\x1b[0m'
    else:
        return '\x1b[1;32;48m' + "{:.3f}".format(s) + '\x1b[0m'
