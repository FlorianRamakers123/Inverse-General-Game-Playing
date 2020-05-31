from os import listdir
from os.path import join, isfile
import sys
import os
from utils.gamelib import find_hypothesis, get_subpredicates
from utils.type_inst import instantiate_constants
module_path = os.path.dirname(os.path.abspath(__file__))


def create_rules(system):
    path = module_path + "/../hypothesis/{}/".format(system)
    for game in [f for f in listdir(path) if not isfile(join(path,f))]:
        create_rules_game(system, game)

def create_rules_game(system, game):
        bk = open(module_path + "/../background/{}_bk.pl".format(game)).read().strip() + '\n'
        type_instantiations = instantiate_constants(game)
        total = bk + "\n\n% Type constanst \n" + type_instantiations + "\n\n \n%learned hypotheses: \n"

        for subpred in [p for p in get_subpredicates(game) if p != ""]:
              total += find_hypothesis(system,game,subpred).strip() + "\n"
        f = open(module_path + "/{}/{}_pl.pl".format(system,game), 'w')
        f.write(total)
        f.close()

if __name__ == "__main__":
    create_rules(sys.argv[1])
