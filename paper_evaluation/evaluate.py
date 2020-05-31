import claudien
import metagol
import specialised_ilasp

import os
import multiprocessing
import signal
import numpy as np
from os import listdir
from os.path import isfile, join
from multiprocessing import Pool
import config as cfg
import sys

sys.path.insert(1, '../utils')
from gamelib import *

def game_names(path):
    # return ['minimal_decay']
   return sorted(set('_'.join(f.split('_')[:-2]) for f in listdir(path) if isfile(join(path, f)) and f.endswith('.dat')))

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def pred(atom):
    xs=atom.split('(')
    return (xs[0],xs[1].count(',')+1)

def targets(inpath):
    a= list(set(f.split('.')[0] for f in listdir(inpath) if isfile(join(inpath, f))))
    a.sort() # in place function
    return a

def parmap(func,jobs):
    p=Pool(cfg.map_size)
    return p.map(func,jobs)

def parse_(args):
    (system,game) = args
   
    outpath='exp/{}/{}/{}/'.format(system.name,"test",game)
    mkdir(outpath)
    for target in ['goal','legal','next','terminal']:
        datafile='../data/{0}/{1}_{2}_{0}.dat'.format("test",game,target)
  
        system.parse_test(datafile,outpath,game,target)

def parse(system):
    parmap(parse_,list((system,game) for game in game_names('../data/train')))


def do_test_(args):
    (system,game)=args
    inpath='exp/{}/test/{}/'.format(system.name,game)
    outpath='results/{}/{}/'.format(system.name,game)
    mkdir(outpath)
    for target in targets(inpath):
        print("evaluation game: " + game +" target:", target)
        dataf='exp/{}/test/{}/{}.pl'.format(system.name,game,target)
        programf='../hypothesis/{}/{}/{}.pl'.format(system.name,game,target)
        resultsf=outpath+'{}.pl'.format(target)
        system.do_test(dataf,programf,resultsf)

def do_test(system):
    parmap(do_test_,list((system,game) for game in sorted(game_names('../data/train'))))

# results is a list of (predication,label) pairs
# seems a bit cumbersome
def balanced_acc(results):
    tp,tn,num_p,num_n=0.0,0.0,0.0,0.0

    for prediction,label in results:
        if label == 1:
            num_p+=1
        if label == 0:
            num_n +=1
        if prediction == 1 and label == 1:
            tp+=1
        if prediction == 0 and label == 0:
            tn+=1
    #print("  tp", tp, "tn", tn, " num_p", num_p, "num_n", num_n)
    """if (tp == num_p):
        print("  --cava--")
    else:
         print("  --NOT cava--")"""

    if num_p == 0 and num_n == 0:
        return -1
    elif num_p > 0 and num_n > 0:
        return ((tp / num_p) + (tn / num_n))/2
    elif num_p == 0:
        return (tn / num_n)
    elif num_n == 0:
        return (tp / num_p)

def res_parser(resultsf):
    with open(resultsf) as f:
        for line in f:
            xs=line.strip().split(',')
            if len(xs)>1:
                yield (int(xs[0]),int(xs[1]))

#xs is list of balanced accuracies with range in [0,1]
def perfectly_correct(xs):
    return sum(1 for x in xs if int(x) == 1)


def print_results_(args):
    (system, game) = args

    inpath='exp/{}/test/{}/'.format(system.name, game) 
    sub_targets=targets(inpath)
    scores = []
    for target in ['goal','legal','next','terminal']:
        target_scores=[]
        for sub_target in sub_targets:
            if sub_target.startswith(target):
                resultsf='results/{}/{}/{}.pl'.format(system.name,game,sub_target)
                target_scores += res_parser(resultsf)

        #print(game,target, ":")
        b = balanced_acc(target_scores)
        print(game,target, ":   " , int(b*100)) #, "   perfect:", perfectly_correct( [b] ))
        scores.append(b)
    return scores

#NOTE: perfectly solved metric can be misleading because of incomplete test data!!!
def print_results(system):
    args = [(system, game) for game in game_names('../data/test')]
    scores = [score for scores in parmap(print_results_, args) for score in scores]
    mean = int(np.mean(scores)*100)
    p = perfectly_correct(scores)
    print(system.name, mean, p)
    return (system.name, mean, p)

#systems = [metagol.Metagol(), specialised_ilasp.SPECIALISED_ILASP()]


def args_(arg, game):
    if arg == "parse":
        print("creating parse data for game: " + game +" in system: " + system.name)
        parse_((system,game))

    elif arg == "evaluate":
        print("evaluation game: " + game +" in system: " + system.name)
        do_test_((system,game))
        print_results_((system,game))

    elif arg == "results":
        print("results game: " + game +" in system: " + system.name)
        print_results_((system,game))
    else:
        print("invalid arg", arg)


######################
#system = specialised_ilasp.SPECIALISED_ILASP() #claudien.Claudien()
system = claudien.Claudien()

"""
arg = sys.argv[1]
if arg == 'parse':
    parse( system)
if arg == 'test':
    do_test(system)
if arg == 'results':
    print_results(system)
"""

# system are in column of cvs
if len(sys.argv) == 2 and sys.argv[1] == "saveresults":
    systems = [metagol.Metagol(), specialised_ilasp.SPECIALISED_ILASP(), claudien.Claudien()]
    csvHeaders = ["system", "balanced acc", "perfectly solved"]
    csv_output = [csvHeaders]

    for s in systems:
        (name, mean, p) = print_results(s)
        csv_output.append([name, mean, p])
    
    write_csv("all_results/paper_eval_output.csv", csv_output)

"""
if len(sys.argv) == 2 and sys.argv[1] == "saveresults":
    systems = [metagol.Metagol(), specialised_ilasp.SPECIALISED_ILASP(), claudien.Claudien()]
    csvHeaders = [s.name for s in systems]
    csv_output = [csvHeaders]

    res = []
    for s in systems:
        (name, mean, p) = print_results(s)
        res.append([name, mean, p])

    for r in res:
    
    write_csv("all_results/paper_eval_output.csv", csv_output)
"""

#for all games
#command create parse data: python3 evaluate.py parse
#command evaulate data: python3 evaluate.py evaluate
if len(sys.argv) == 2 and sys.argv[1] != "saveresults":
    arg = sys.argv[1]
    for game in sorted(game_names('../data/train')):
        args_(arg, game)
   

#for a given game
#command create parse data: python3 evaluate.py parse game
#command evaulate data: python3 evaluate.py evaluate game
if len(sys.argv) == 3:
    arg = sys.argv[1]
    game = sys.argv[2]
    args_(arg, game)

