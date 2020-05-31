import sys
import os
module_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1,module_path + "/../utils")

from gamelib import get_game_names, get_subpredicates



def convert(game,pred):
    hyp = open(module_path + "/output/{0}/{0}_{1}.pl".format(game,pred)).read()
    lines = list(filter(None,hyp.split("\n")))
    content = ""
    for line in lines:
        line = line.replace(" /\\", ",")
        parts = [p.strip() for p in line.split("->")]
        if parts[-1] == "false" or "\\/" in line:
            continue
        if len(parts) < 2:
            content += line + ".\n"
        else:
            content += parts[1] + " :- " + parts[0] + ".\n"

    f = open(module_path + "/../hypothesis/claudien/{}/{}.pl".format(game,pred), "w")
    f.write(content)
    f.close()
