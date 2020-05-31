import sys
sys.path.insert(1,'../')
from utils.gamelib import find_hypothesis, find_background,get_game_names

for game in get_game_names():
    f = open("{}_bk.pl".format(game), 'w')
    f.write(find_background(game))
    f.close()
