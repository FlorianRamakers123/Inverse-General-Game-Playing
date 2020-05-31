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

def run(games,timeout,data_set):
    for game in games:

        mkdir("../data/train/{}/{}/claudien_incremental/".format(game,data_set))

        # create a new copy of the data set so we don't change the original
        copy_targets("../data/train/{}/{}/claudien/".format(game,data_set),"../data/train/{}/{}/claudien_incremental/".format(game,data_set))

        # variables for storing the old results
        # precision and recall
        old_p_and_r = None
        # extra AER info
        old_pred_info = None
        # average error rate (AER)
        old_AER = None

        REPEAT = 15

        for repeat in range(REPEAT):
            print(colored("Calculating average error rate for complete traces (AER), precision, recall...", "white"))
            # run the game_tree to extract AER info
            (p_and_r,avg_err_rate,pred_info) = (None,None,None)
            if game != "fizzbuzz":
                (p_and_r,avg_err_rate, pred_info) = VT.run("claudien",game)
            else:
                (p_and_r,avg_err_rate, pred_info) = VT.run_partly("claudien",game, 97347)
            # print the comparison with old results, if available
            if old_AER == None:
                print("{:30s}│".format(colored("Current AER:","blue")), colored_scale(avg_err_rate * 100, 1 - avg_err_rate))
            else:
                print("{:30s}│".format(colored("Current AER:","blue")), colored_scale(old_AER * 100, 1 - old_AER), \
                       " -> ", colored_scale(avg_err_rate * 100, 1 - avg_err_rate))
            old_AER = avg_err_rate

            # find the precision and recall and generate examples accordingly
            predicates = list(get_subpredicates(game))
            predicates.sort()

            # print the comparison with old results, if available
            if old_p_and_r == None:
                # print the results
                for i,pred in enumerate(predicates):
                    print("{:30s}│".format(colored("{} P|R|C:".format(pred), "blue")), \
                          colored_scale(p_and_r[pred][0], p_and_r[pred][0]) + " | " + colored_scale(p_and_r[pred][1], p_and_r[pred][1]), \
                          "| " + colored_scale(pred_info[pred.split("_")[0]], 1 - pred_info[pred.split("_")[0]]))
            else:
                # print the results
                for i,pred in enumerate(predicates):
                    print("{:30s}│".format(colored("{} P|R|C:".format(pred), "blue")), \
                          colored_scale(old_p_and_r[pred][1], old_p_and_r[pred][1]) + " -> " + colored_scale(p_and_r[pred][1], p_and_r[pred][1]) + \
                          " | " + colored_scale(old_p_and_r[pred][0], old_p_and_r[pred][0]) + " -> " + colored_scale(p_and_r[pred][0], p_and_r[pred][0]), \
                          "| " + colored_scale(old_pred_info[pred.split("_")[0]], 1 - old_pred_info[pred.split("_")[0]]) +\
                          " -> " + colored_scale(pred_info[pred.split("_")[0]], 1 - pred_info[pred.split("_")[0]]))

                """
                # ask if the previous results should be restored
                answer = ""
                while answer.lower() != 'y' and answer.lower() != 'n':
                    answer = input2(colored("Would you like to restore the old results? (y/n): ", "yellow"))
                if answer.lower() == 'y':
                    print(colored("Restoring old results...", "white"))
                    copy_targets("../hypothesis_tmp/claudien/" + game, "../hypothesis/claudien/" + game)
                """
            old_p_and_r = p_and_r
            old_pred_info = pred_info

            """
            # back up the old results
            print(colored("Backing up old results...", "white"))
            copy_targets("../hypothesis/claudien/" + game, "../hypothesis_tmp/claudien/" + game)


            # ask which target should be trained
            print(colored("Which target should be trained?", "yellow"))
            for i,pred in enumerate(predicates):
                print("\t{}) {}".format(i+1, pred))
            print("\t{}) all".format(len(predicates) + 1))
            number = 0
            while number > len(predicates) + 1 or number < 1:
                try:
                    number = int(input2(colored("Enter the number of the target(s): ", "yellow")))
                except ValueError:
                    continue
            """

            # update the input files
            for subtarget in predicates:
                print(colored("START: {}, {} ----- {}".format(game,subtarget,datetime.datetime.now()), "white"))
                dataset_path = module_path + "/../data/train/{0}/{1}/claudien_incremental/{0}_{2}_cwa.dat".format(game,data_set,subtarget)
                f = open(dataset_path, 'a')
                pos_ex_path = "../game_tree/pos_examples/{}/{}.pos".format(game,subtarget)
                if os.path.exists(pos_ex_path):
                    pos_f = open(pos_ex_path)
                    pos_ex = pos_f.read()
                    print(colored("Generated " + str(pos_ex.count("% =====")) + " positive examples", "yellow"))
                    f.write(pos_ex)
                    pos_f.close()
                neg_ex_path = "../game_tree/neg_examples/{}/{}.neg".format(game,subtarget)
                if os.path.exists(neg_ex_path):
                    neg_f = open(neg_ex_path)
                    neg_ex = neg_f.read()
                    print(colored("Generated " + str(neg_ex.count("% =====")) + " negative examples", "yellow"))
                    f.write(neg_ex)
                    neg_f.close()
                f.close()

                train_target_dataset(game,timeout,subtarget,dataset_path)

            """
            f = open("../data/train/{0}/{1}/claudien/incremental/{0}_{2}_train.dat".format(game,data_set,subtarget), 'a')
            pos_ex_path = "../game_tree/pos_examples/{}/{}.pos".format(game,target)
            if os.path.exists(pos_ex_path):
                pos_f = open(pos_ex_path)
                f.write(pos_f.read())
                pos_f.close()
            neg_ex_path = "../game_tree/neg_examples/{}/{}.neg".format(game,target)
            if os.path.exists(neg_ex_path):
                neg_f = open(neg_ex_path)
                f.write(neg_f.read())
                neg_f.close()
            f.close()


            # print the background of progress bar
            bar_length = 50
            print(colored('▒' * bar_length, "white"), end='')
            sys.stdout.flush() # flush because we didn't print a new line
            nb_targets = get_nb_targets(game)
            item_length = int(bar_length / nb_targets) + 1
            progress = 0
            # train yields after every subtarget en returns the trained predicate and whether the training timed out
            for (timed_out, pred) in train_(game,timeout):
                progress += 1
                msg = pred + " timed out" if timed_out else pred + " finished in time"
                curr_length = min(progress * item_length, bar_length)
                print("\r" + "{:75s}".format(colored('▒' * curr_length, "green") + colored('▒' * (bar_length - curr_length), "white")), end='')
                print("{:50s}".format(colored("\t" + msg, "yellow")), end='')
                sys.stdout.flush()
                # convert the output to prolog
                convert(game,pred)
            print("") # print new line

            # inner function for printing the progress bar
            def print_loading_bar(thread):
                bar_length = 50
                counter = 0
                curr_length = 0.0
                print(colored('▒' * bar_length, "white"), end='')
                print("\r" + colored('▒' * (bar_length), "green"), end='')
                sys.stdout.flush()
                while(counter < timeout and thread.is_alive()):
                    sleep(1)
                    counter += 1
                    curr_length += bar_length / timeout
                    print("\r" + colored('▒' * bar_length, "white"), end='')
                    print("\r" + colored('▒' * max(bar_length - int(curr_length),0), "green"), end='')
                    sys.stdout.flush()
                print("") # print new line

            print(colored("Training target '{}'...".format(target), "white"))
            thread1 = Thread(target=train_target, args=(game,timeout,target,))
            thread2 = Thread(target=print_loading_bar, args=(thread1,))
            thread1.start()
            thread2.start()
            thread1.join(timeout+3)
            thread2.join()
            # convert the output of claudien to prolog
            convert(game,target)
            """
            # join all learned hypothesises back to one ruleset
            create_rules("claudien")

        print(colored("Calculating average error rate for complete traces (AER), precision, recall...", "white"))
        # run the game_tree to extract AER info
        (p_and_r,avg_err_rate,pred_info) = (None,None,None)
        if game != "fizzbuzz":
            (p_and_r,avg_err_rate, pred_info) = VT.run("claudien",game)
        else:
            (p_and_r,avg_err_rate, pred_info) = VT.run_partly("claudien",game, 97347)
        # print the comparison with old results, if available
        if old_AER == None:
            print("{:30s}│".format(colored("Current AER:","blue")), colored_scale(avg_err_rate * 100, 1 - avg_err_rate))
        else:
            print("{:30s}│".format(colored("Current AER:","blue")), colored_scale(old_AER * 100, 1 - old_AER), \
                   " -> ", colored_scale(avg_err_rate * 100, 1 - avg_err_rate))
        old_AER = avg_err_rate

        # find the precision and recall and generate examples accordingly
        predicates = list(get_subpredicates(game))
        predicates.sort()

        # print the comparison with old results, if available
        if old_p_and_r == None:
            # print the results
            for i,pred in enumerate(predicates):
                print("{:30s}│".format(colored("{} P|R|C:".format(pred), "blue")), \
                      colored_scale(p_and_r[pred][0], p_and_r[pred][0]) + " | " + colored_scale(p_and_r[pred][1], p_and_r[pred][1]), \
                      "| " + colored_scale(pred_info[pred.split("_")[0]], 1 - pred_info[pred.split("_")[0]]))
        else:
            # print the results
            for i,pred in enumerate(predicates):
                print("{:30s}│".format(colored("{} P|R|C:".format(pred), "blue")), \
                      colored_scale(old_p_and_r[pred][1], old_p_and_r[pred][1]) + " -> " + colored_scale(p_and_r[pred][1], p_and_r[pred][1]) + \
                      " | " + colored_scale(old_p_and_r[pred][0], old_p_and_r[pred][0]) + " -> " + colored_scale(p_and_r[pred][0], p_and_r[pred][0]), \
                      "| " + colored_scale(old_pred_info[pred.split("_")[0]], 1 - old_pred_info[pred.split("_")[0]]) +\
                      " -> " + colored_scale(pred_info[pred.split("_")[0]], 1 - pred_info[pred.split("_")[0]]))


# boolean that indicates whether to use a file as input
USE_FILE = False
# the path of the input file, if used
INPUT_FILE = None
if len(sys.argv) > 1:
    USE_FILE = True
    INPUT_FILE = open(sys.argv[1])

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

run(games,timeout,data_set)
