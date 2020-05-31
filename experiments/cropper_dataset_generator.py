import sys
sys.path.insert(1,'../')
from utils.gamelib import get_subpredicates
game = sys.argv[1]

for pred in get_subpredicates(game):
    base_path = "../data/train/{0}/cropper/".format(game)
    train_data = open(base_path + "ilasp/{}_{}_train.dat".format(game,pred.split("_")[0])).read()
    bk,pos = [],[]
    content = "% ==========\n"
    for x in train_data.split('---'):
        xs = list(map(lambda x: x.strip(), x.strip().split('\n')))
        h,t = xs[0], xs[1:]
        if h == 'background:':
            bk.append(t)
        elif h == 'positives:':
            pos.append([ts.replace("terminal()","terminal") for ts in t])
    examples = [".\n".join(bk[i]) + ".\n" + (".\n".join(pos[i]) + ".\n" if len(pos[i]) > 0 else "") for i in range(len(bk))]
    content += "% ==========\n".join(examples)
    f = open(base_path + "claudien/{}_{}_train.dat".format(game,pred),'w')
    f.write(open("../data/base/{0}/claudien/{0}_{1}_base.dat".format(game,pred)).read().strip() + "\n")
    f.write(content)
    f.close()
