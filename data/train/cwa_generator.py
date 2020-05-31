import sys
from os import listdir
sys.path.insert(1,'../../')
from utils.gamelib import get_neg_instances_no_not,get_subpredicates

game = sys.argv[1]
datasets = ["minimal","maximal","cropper","dataset1_1","dataset1_2","dataset1_3", "dataset1_4","dataset2_1","dataset2_2","dataset2_3", "dataset2_4","dataset3_1","dataset3_2","dataset3_3", "dataset3_4","dataset4_1","dataset4_2","dataset4_3", "dataset4_4","dataset5_1","dataset5_2","dataset5_3", "dataset5_4"]

for dataset in datasets:
    print("converting dataset",dataset)
    for subpredicate in get_subpredicates(game):
        print("\t converting predicate",subpredicate)
        pred = subpredicate.split("_")[0]
        f = open("{0}/{1}/ilasp/{0}_{2}_train.dat".format(game,dataset,pred))
        content = f.read()
        f.close()
        bk,pos = [],[]
        for x in content.split('---'):
            xs = list(map(lambda x: x.strip(), x.strip().split('\n')))
            h,t = xs[0], xs[1:]
            if h == 'background:':
                bk.append(t)
            elif h == 'positives:':
                pos.append([ts.replace("terminal()","terminal") for ts in t])
        cwa_examples = []
        for i in range(len(bk)):
            neg_inst = get_neg_instances_no_not(pos[i],game,subpredicate)
            if neg_inst.strip() != "":
                cwa_examples.append(".\n".join(bk[i]) + ".\n" + neg_inst)

        new_content = ""
        if len(cwa_examples) > 0:
            new_content = "% =========!\n"
            new_content += "% =========!\n".join(cwa_examples)
        f = open("{0}/{1}/claudien/{0}_{2}_cwa.dat".format(game,dataset,subpredicate), "w")
        f2 = open("{0}/{1}/claudien/{0}_{2}_train.dat".format(game,dataset,subpredicate))
        f.write(f2.read())
        f2.close()
        if pred != "terminal":
            f.write(new_content)
        f.close()
