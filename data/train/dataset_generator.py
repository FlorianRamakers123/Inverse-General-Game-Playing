import sys
sys.path.insert(1,'../../')
from utils.gamelib import mkdir, get_subpredicates
from random import randrange

def parse_target(datafile):
    with open(datafile,'r') as f:
        episode = 0
        bk,pos = [],[]
        for x in f.read().split('---'):
            xs = list(map(lambda x: x.strip(), x.strip().split('\n')))
            h,t = xs[0], xs[1:]
            if h == 'background:':
                episode+=1
                bk.append(t)
            elif h == 'positives:':
                pos.append(t)
        return (bk, pos)

def find_subtargets(target,game):
    subtargets = get_subpredicates(game)
    return [subtarget for subtarget in subtargets if subtarget.startswith(target)]


game = sys.argv[1]
REPEAT = 5
DIVISION = 5
base_path = "{}/".format(game)
for predicate in ["goal", "legal", "next", "terminal"]:
    subtargets_c = find_subtargets(predicate,game)

    (bk_max,pos_max) = parse_target(base_path + "maximal/ilasp/{}_{}_train.dat".format(game,predicate))
    max_examples_i = [(list(filter(None,bk_max[q])),list(filter(None,pos_max[q]))) for q in range(len(bk_max))]
    increase = int((1/DIVISION) * len(max_examples_i))
    for i in range(REPEAT):
        max_examples_copy = max_examples_i.copy()
        curr_dataset_i = []
        curr_dataset_c = []
        for j in range(DIVISION - 1):
            ext_c = []
            ext_i = []

            for k in range(increase):
                idx = randrange(0,len(max_examples_copy))
                (bk,pos) = max_examples_copy[idx]
                max_examples_copy.remove((bk,pos))
                ext_c.append("% =========\n" + ".\n".join(bk) + ".\n" + "".join([p + ".\n" for p in pos]))
                ext_i.append("---\n\nbackground:\n\t{}\n\n---\n\npositives:\n\t{}\n\n".format( ("\n\t".join(bk) ), ("\n\t".join(pos)) ))
            curr_dataset_c += ext_c
            curr_dataset_i += ext_i
            print("----")
            print("nb of examples in dataset{}_{} for claudien:".format(i+1,j+1), len(curr_dataset_c))
            print("nb of examples in dataset{}_{} for ilasp:".format(i+1,j+1), len(curr_dataset_i))
            dataset_path = base_path + "dataset{}_{}".format(i+1,j+1)
            mkdir(dataset_path + "/claudien")
            for subtarget in subtargets_c:
                f = open(dataset_path + "/claudien/{}_{}_train.dat".format(game,subtarget), 'w')
                f.write(open("../base/{0}/claudien/{0}_{1}_base.dat".format(game,subtarget)).read().strip() + "\n")
                f.write("".join(curr_dataset_c))
                f.close()
            mkdir(dataset_path + "/ilasp")
            f = open(dataset_path + "/ilasp/{}_{}_train.dat".format(game,predicate.split('_')[0]), 'w')
            f.write(open("../base/{0}/ilasp/{0}_{1}_base.dat".format(game,predicate.split('_')[0])).read().strip() + "\n\n")
            f.write("".join(curr_dataset_i) + "---")
            f.close()
