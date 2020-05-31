import sys
from utils.gamelib import find_hypothesis, find_background, get_game_names, get_subpredicates, mkdir
import os
module_path = os.path.dirname(os.path.abspath(__file__))

def generate(game,neg_ex_path,pos_ex_path):
    for pred in get_subpredicates(game):
        if pred != "":
            _generate(game,pred,neg_ex_path + "/{}/{}.neg".format(game,pred), pos_ex_path + "/{}/{}.pos".format(game,pred))

def generate_target(game,target,neg_ex_path,pos_ex_path):
    _generate(game,target,neg_ex_path + "/{}/{}.neg".format(game,target), pos_ex_path + "/{}/{}.pos".format(game,target))

def _generate(game,predicate,neg_ex_path,pos_ex_path):
    # read in the base file
    content = open(module_path + "/../data/base/{0}/claudien/{0}_{1}_base.dat".format(game,predicate)).read() + "\n"

    # read the positive exmaples
    content += open(pos_ex_path).read()

    # read the negative exmaples
    if os.path.exists(neg_ex_path):
        content += open(neg_ex_path).read()
    else:
        #print("[warning] no negative examples are found on path", neg_ex_path)
        pass
    f = open(module_path + "/input/{}/{}.pl".format(game,predicate),"w")
    f.write(content)
    f.close()


def generate2(game,predicate):
    # find the cores
    content = "% === CORES ===\n"
    gdl = find_hypothesis("gdl",game,predicate)
    heads = {h.split(":-")[0].strip() for h in gdl.split("\n")}
    content += ".\n".join(heads) + ".\n"

    content += "% === BACKGROUND ===\n"
    content += find_background(game)
    content += "\n"
    modes = open(module_path + "/modes/{}/{}.mode".format(game,predicate)).read().strip()
    content += modes
    # find the types
    content += "\n% === TYPES === \n"
    type_decs = open(module_path + "/../types/{}.typ".format(game)).read().replace("\n", "").split(".")
    types = []
    constants = []
    for type_dec in type_decs:
        if "::" in type_dec:
            type_dec_parts = type_dec.split("::")
            lhs = type_dec_parts[0].split(",")
            rhs = type_dec_parts[1].split("->")
            if len(rhs) > 1:
                for lh in lhs:
                    types.append(lh.strip() + "(" + ",".join([p.strip() for p in rhs[:-1]]) + ").")
            else:
                for lh in lhs:
                    if rhs[0].strip() != "bool":
                        constants.append(rhs[0].strip() + "(" + lh.strip() + ").")

    content += "\n".join(types)
    content += "\n% === CONSTANTS ===\n"
    content += "\n".join(constants) + "\n"

    content += "% ==========\n"
    # extract the learning examples
    train_data = open(module_path + "/../data/train/{}_{}_train.dat".format(game,predicate.split("_")[0])).read()
    bk,pos = [],[]

    for x in train_data.split('---'):
        xs = list(map(lambda x: x.strip(), x.strip().split('\n')))
        h,t = xs[0], xs[1:]
        if h == 'background:':
            bk.append(t)
        elif h == 'positives:':
            pos.append(t)
    examples = [".\n".join(bk[i]) + ".\n" + (".\n".join(pos[i]) + ".\n" if len(pos[i]) > 0 else "") for i in range(len(bk))]
    content += "% ==========\n".join(examples)

    f = open(module_path + "/input/{}/{}.pl".format(game,predicate),"w")
    f.write(content)
    f.close()

if __name__ == "__main__":
    for game in get_game_names():
        for pred in get_subpredicates(game):
            print("writing file for game {} and predicate {}".format(game,pred))
            generate(game,pred, "../replay/neg_ex/{}/{}.neg".format(game,pred))
