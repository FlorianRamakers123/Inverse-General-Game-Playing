import sys
sys.path.insert(1,'../')
from utils.printing import colored, colored_scale
from claudien.claudien_runner import train, get_nb_targets, train_target, train_target_dataset
from claudien.claudien_to_prolog import convert
from claudien.generator import generate, generate_target
from learned_rules.generate_rules import create_rules
import game_tree.validation_tree as VT
from utils.gamelib import get_subpredicates,mkdir
from threading import Thread
from time import sleep
import datetime
import os
import shutil
module_path = os.path.dirname(os.path.abspath(__file__))


# read input, fromt stdin or from file
def input2(s):
    if USE_FILE:
        inp = INPUT_FILE.readline().split("//")[0].strip()
        while inp == "":
            inp = INPUT_FILE.readline().split("//")[0].strip()
        print(s, inp)
        return inp
    else:
        return input(s)

# copy the files in src to dst
def copy_targets(src, dst):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            f = open(d,'w')
            f.write(open(s).read())
            f.close()

def write_csv(csv_data,game):
    f = open(module_path + "/results/incremental/{}_incremental_data_no_cwa.csv".format(game), 'w')
    f.write("\"predicate\",\"precision\",\"recall\",\"avg_err_rate\",\"neg examples\",\"pos examples\",\"timeout\"\n")
    for row in csv_data:
        f.write(",".join(["\"" + str(s) + "\"" for s in row]) + "\n")
    f.close()

def run(games,timeout,timeout_ext,data_set):
    for game in games:

        mkdir("../data/train/{}/{}/claudien_incremental_no_cwa/".format(game,data_set))
        csv_data = []

        # train on the initial dataset
        predicates = list(get_subpredicates(game))
        predicates.sort()

        timeouts = {}
        prev_extended = {}
        print(colored("Training on initial dataset", "white"))
        for subtarget in predicates:
            timeouts[subtarget] = timeout
            prev_extended[subtarget] = False
            train_target_dataset(game,timeout,subtarget, module_path + "/../data/train/{0}/{1}/claudien/{0}_{2}_train.dat".format(game,data_set,subtarget))

        create_rules("claudien")

        # create a new copy of the data set so we don't change the original
        copy_targets("../data/train/{}/{}/claudien/".format(game,data_set),"../data/train/{}/{}/claudien_incremental_no_cwa/".format(game,data_set))

        print(colored("Calculating average error rate for complete traces (AER), precision, recall...", "white"))
        # run the game_tree to extract AER info and precision and recall
        (p_and_r,avg_err_rate,pred_info) = (None,None,None)
        if game != "fizzbuzz": # fizzbuzz is too big to run the full tree on
            (p_and_r,avg_err_rate, pred_info) = VT.run("claudien",game)
        else:
            (p_and_r,avg_err_rate, pred_info) = VT.run_partly("claudien",game, 97347)
        # print the results:
        print("{:30s}│".format(colored("Current AER:","blue")), colored_scale(avg_err_rate * 100, 1 - avg_err_rate))

        old_AER = avg_err_rate

        for i,pred in enumerate(predicates):
            print("{:30s}│".format(colored("{} P|R|C:".format(pred), "blue")), \
                  colored_scale(p_and_r[pred][0], p_and_r[pred][0]) + " | " + colored_scale(p_and_r[pred][1], p_and_r[pred][1]), \
                  "| " + colored_scale(pred_info[pred.split("_")[0]], 1 - pred_info[pred.split("_")[0]]))

            _f = open(module_path + "/../data/train/{0}/{1}/claudien_incremental_no_cwa/{0}_{2}_train.dat".format(game,data_set,pred), 'r')
            _content = _f.read()
            _f.close()
            _examples = _content.split("% =========")[1:]
            _pos_examples = [s.strip() for s in _examples if s.strip()[0] != '!']
            _neg_examples = [s.strip()[1:] for s in _examples if s.strip()[0] == '!']

            csv_data.append([pred,p_and_r[pred][0],p_and_r[pred][1],avg_err_rate,len(_pos_examples),len(_neg_examples),timeout])


        old_p_and_r = p_and_r
        old_pred_info = pred_info

        REPEAT = 10
        try:
            for repeat in range(REPEAT):
                print("+===============================================================================+")
                print("ITERATION {} ------- {}".format(repeat,datetime.datetime.now()))
                print("+===============================================================================+")

                new_nb_pos_examples = 0
                new_nb_neg_examples = 0

                old_nb_pos_examples = 0
                old_nb_neg_examples = 0

                pos_ex_count = {}
                neg_ex_count = {}

                # update the input files
                for subtarget in predicates:
                    print(colored("+++++++ {} +++++++".format(subtarget), "blue"))
                    # calculate the current amount of positive en negative examples
                    dataset_path = module_path + "/../data/train/{0}/{1}/claudien_incremental_no_cwa/{0}_{2}_train.dat".format(game,data_set,subtarget)
                    f = open(dataset_path, 'r')
                    content = f.read()
                    f.close()
                    examples = content.split("% =========")[1:]
                    pos_examples = [s.strip() for s in examples if s.strip()[0] != '!']
                    neg_examples = [s.strip()[1:] for s in examples if s.strip()[0] == '!']
                    print(colored("old nb of positive examples for {}: ".format(subtarget) + str(len(pos_examples)), "yellow"))
                    print(colored("old nb of negative examples for {}: ".format(subtarget) + str(len(neg_examples)), "yellow"))
                    old_nb_pos_examples += len(pos_examples)
                    old_nb_neg_examples += len(neg_examples)
                    # calculate the new positive and negative examples
                    new_pos_examples = []
                    new_neg_examples = []

                    pos_ex_path = "../game_tree/pos_examples/{}/{}.pos".format(game,subtarget)
                    if os.path.exists(pos_ex_path):
                        pos_f = open(pos_ex_path)
                        new_pos_examples = [s.strip() for s in pos_f.read().split("% =========") if s.strip() != ""]
                        print(colored("Generated " + str(len(new_pos_examples)) + " positive examples for {}".format(subtarget), "yellow"))
                        pos_f.close()

                    neg_ex_path = "../game_tree/neg_examples/{}/{}.neg".format(game,subtarget)
                    if os.path.exists(neg_ex_path):
                        neg_f = open(neg_ex_path)
                        new_neg_examples = [s.strip() for s in neg_f.read().split("% =========!") if s.strip() != ""]
                        print(colored("Generated " + str(len(new_neg_examples)) + " negative examples for {}".format(subtarget), "yellow"))
                        neg_f.close()

                    new_pos_examples = set(new_pos_examples).difference(pos_examples)
                    new_neg_examples = set(new_neg_examples).difference(neg_examples)
                    print(colored("Adding " + str(len(new_pos_examples)) + " new positive examples for {}".format(subtarget), "white"))
                    print(colored("Adding " + str(len(new_neg_examples)) + " new negative examples for {}".format(subtarget), "white"))

                    new_nb_pos_examples += len(pos_examples) + len(new_pos_examples)
                    new_nb_neg_examples += len(neg_examples) + len(new_neg_examples)

                    pos_ex_count[subtarget] = len(pos_examples) + len(new_pos_examples)
                    neg_ex_count[subtarget] = len(neg_examples) + len(new_neg_examples)

                    f = open(dataset_path, 'a')
                    f.write("\n".join(["\n% =========\n" + s for s in new_pos_examples if s.strip() != ""]))
                    f.write("\n".join(["\n% =========!\n" + s for s in new_neg_examples if s.strip() != ""]))
                    f.close()

                    if old_p_and_r[subtarget][0] != 1 or old_p_and_r[subtarget][1] != 1:
                        if len(new_pos_examples) == 0 and len(new_neg_examples) == 0:
                            if not prev_extended[subtarget]:
                                print(colored("No new examples for predicate " + subtarget, "red"))
                                print("extending timeout for predicate " + subtarget)
                                timeouts[subtarget] += timeout_ext
                                print("new timeout:", timeouts[subtarget])
                                prev_extended[subtarget] = True
                            else:
                                continue
                        print(colored("---- START: {}, {} ----- {}".format(game,subtarget,datetime.datetime.now()), "white"))
                        print("traing", subtarget, "with timeout", timeouts[subtarget])
                        train_target_dataset(game,timeouts[subtarget],subtarget,dataset_path)

                print(colored("Finished training with " + str(new_nb_pos_examples) + " positive examples and " + str(new_nb_neg_examples) + " negative examples","yellow"))
                # join all learned hypothesises back to one ruleset
                create_rules("claudien")

                print(colored("Calculating average error rate for complete traces (AER), precision, recall...", "white"))
                # run the game_tree to extract AER info
                (p_and_r,avg_err_rate,pred_info) = (None,None,None)
                if game != "fizzbuzz":
                    (p_and_r,avg_err_rate, pred_info) = VT.run("claudien",game)
                else:
                    (p_and_r,avg_err_rate, pred_info) = VT.run_partly("claudien",game, 97347)

                # print the comparison with old results
                print("{:30s}│".format(colored("Current AER:","blue")), colored_scale(old_AER * 100, 1 - old_AER), \
                       " -> ", colored_scale(avg_err_rate * 100, 1 - avg_err_rate))
                old_AER = avg_err_rate

                # print the results
                for i,pred in enumerate(predicates):
                    print("{:30s}│".format(colored("{} P|R|C:".format(pred), "blue")), \
                          colored_scale(old_p_and_r[pred][0], old_p_and_r[pred][0]) + " -> " + colored_scale(p_and_r[pred][0], p_and_r[pred][0]) + \
                          " | " + colored_scale(old_p_and_r[pred][1], old_p_and_r[pred][1]) + " -> " + colored_scale(p_and_r[pred][1], p_and_r[pred][1]), \
                          "| " + colored_scale(old_pred_info[pred.split("_")[0]], 1 - old_pred_info[pred.split("_")[0]]) +\
                          " -> " + colored_scale(pred_info[pred.split("_")[0]], 1 - pred_info[pred.split("_")[0]]))

                    csv_data.append([pred,p_and_r[pred][0],p_and_r[pred][1],avg_err_rate,pos_ex_count[pred],neg_ex_count[pred],timeouts[pred]])

                old_p_and_r = p_and_r
                old_pred_info = pred_info
                if avg_err_rate == 0:
                    print(colored("Exiting because maximum score reached.", "green"))
                    print("writing csv file")
                    write_csv(csv_data,game)
                    exit()
                #if old_nb_neg_examples == new_nb_neg_examples and old_nb_pos_examples == old_nb_neg_examples:
                #    print("writing csv file")
                #    write_csv(csv_data,game)
                #    exit()
        except KeyboardInterrupt:
            pass
        print("writing csv file")
        write_csv(csv_data,game)

# boolean that indicates whether to use a file as input
USE_FILE = False
# the path of the input file, if used
INPUT_FILE = None
if len(sys.argv) > 4:
    USE_FILE = True
    INPUT_FILE = open(sys.argv[4])


"""
# ask which game to train
print(colored("Which game(s) should be trained?", "yellow"))
print("\t1) Buttons & Lights")
print("\t2) Fizzbuzz")
print("\t3) Scissors, Paper, Stone")



numbers = [int(s.strip()) for s in input2(colored("Enter the number(s) of the game(s): ", "yellow")).split(",")]

all_games = ["buttons_and_lights", "fizzbuzz", "scissors_paper_stone"]
games = [all_games[i-1] for i in numbers]

# ask which dataset to start from
print(colored("Which data set should be used as start?", "yellow"))
print("\t1) Minimal data set")
print("\t2) Data set of Andrew Cropper")
print("\t3) Maximal data set")

number = 0
while number > 3 or number < 1:
    try:
        number = int(input2(colored("Enter the number of the dataset: ", "yellow")))
    except ValueError:
        continue
data_set = ["minimal","cropper","maximal"][number - 1]

# specify the timeout for the training process
timeout = 0
while timeout <= 0:
    try:
        timeout = int(input2(colored("Enter the timeout value (in seconds): ", "yellow")))
    except ValueError:
        continue

# specify the timeout extension for the training process
timeout_ext = 0
while timeout_ext <= 0:
    try:
        timeout_ext = int(input2(colored("Enter the timeout extension value (in seconds): ", "yellow")))
    except ValueError:
        continue
"""

run([sys.argv[1]],int(sys.argv[2]),int(sys.argv[3]), "minimal")
