import os
import sys
from datetime import datetime
from collections import defaultdict
module_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, '../')

from claudien.claudien_runner import train_target_dataset
from specialised_ILASP.ilasp_runner import run_ilasp
from utils.gamelib import get_subpredicates, write_csv
import game_tree.validation_tree as VT
import game_tree.game_tree as GA
from copy import copy
from learned_rules.generate_rules import create_rules_game


systems = ["ilasp"]
datasets = ["cwa_cropper", "cwa_maximal"]#, "cwa_minimal", "cwa_cropper"]
games = ["buttons_and_lights"]#, "fizzbuzz", "scissors_paper_stone"]

timeout = 10 * 60
seed = 97347


def get_data_path(system, game, subtarget, dataset_name):
    target = subtarget
    if system == "ilasp":
        target = subtarget.split("_")[0]

    if dataset_name.startswith("cwa_"):
        if system == "claudien":
            return module_path + "/../data/train/{}/{}/{}/{}_{}_cwa.dat".format(game, dataset_name[4:], system, game, target)
        else:
            return "/../data/train/{}/{}/{}/{}_{}_train.dat".format(game, dataset_name[4:], system, game, target)
    else:
        if system == "claudien":
            return module_path + "/../data/train/{}/{}/{}/{}_{}_train.dat".format(game, dataset_name, system, game, target)
        else:
            return "/../data/train/{}/{}/{}/{}_{}_train.dat".format(game, dataset_name, system, game, target)

def run_system_data_target(system, game, subtarget, dataset_name):
    #global timeout
    target = subtarget.split("_")[0]
    print("--- START [{}, {}, {}, {}]".format(system, game, subtarget, dataset_name))
    dataset_path = get_data_path(system, game, subtarget, dataset_name)

    #Run System on given dataset -------------------------------------------------------------------------
    if system == "claudien":
        train_target_dataset(game, timeout, subtarget, dataset_path)


    elif system == "ilasp":
        if dataset_path != None:
            outfile = "/../hypothesis/{}/{}/{}.pl".format(system, game, subtarget)
            run_ilasp(outfile, game, subtarget, dataset_path, timeout)

    else:
        print("Error invalid system name", system)


    #------------------------------------------------------------------------------------------------------
    print("--- DONE [{}, {}, {}]".format(system, game, subtarget), datetime.now())

def run_system_data(system, game, dataset_name):
    for p in get_subpredicates(game):
        run_system_data_target(system, game, p, dataset_name)

    # combines all learned hypothesises to game rules -----------------------------------------------------
    create_rules_game(system, game)



    #COLLECT RESULTS
    p_and_r = None
    info = None
    AER = None
    if game == "fizzbuzz": # fizzbuzz is too large to run the full tree
        (p_and_r, AER, info) = VT.run_partly(system,game,seed)
    else:
        (p_and_r, AER, info) = VT.run(system, game)
    print("PRECISION AND RECALL")
    for pred in p_and_r.keys():
        print("\t{}: {}, {}".format(pred,p_and_r[pred][0],p_and_r[pred][1]))
    print("AVERAGE ERROR RATE (AER)")
    print("\tAER = {}".format(AER))

    print("ERROR BLAME")
    for pred in info.keys():
        print("\t{}: {}".format(pred,info[pred]))

     #precision = info[pred][0]) ,recall= info[pred][1]

    saveCSV_per_predicate(system, game, dataset_name, p_and_r)
    saveCSV_global(system, game, dataset_name, p_and_r, AER)
    print("**************", system.upper(), "FINISHED | GAME:" , game + ", DATA:", dataset_name , "*************", datetime.now())

def saveCSV_per_predicate(system, game, dataset_name, info):
    new_dict = defaultdict(list)
    for subpred in info.keys():
        pred = subpred.split("_")[0]
        new_dict[pred].append(info[subpred])

    #transform list with subtredicates as key, to a list with (normal) predicate keys
    for p in new_dict.keys():
        new2 = [0, 0]
        for item in new_dict[p]:
            new2[0] += item[0]
            new2[1] += item[1]
        new2[0]  = new2[0] / len(new_dict[p])
        new2[1]  = new2[1] / len(new_dict[p])
        new_dict[p] = new2

    for p in new_dict:
        currRow = [dataset_name, p, "{:.4f}".format(new_dict[p][0]), "{:.4f}".format(new_dict[p][1])]
        csv_per_p_output.append(currRow)

def saveCSV_global(system, game, dataset_name, info, avg_err_rate):
    #calculate global average of all precision and recalls of each predicate
    overalPR = [0,0]
    for p in info.keys():
        overalPR[0] += info[p][0]
        overalPR[1] += info[p][1]

    csv_global_output.append([dataset_name, "{:.4f}".format(overalPR[0] / len(info.keys())), "{:.4f}".format(overalPR[1] / len(info.keys())), "{:.4f}".format(avg_err_rate)])


#-------init global csv lists
csv_per_p_headers = ["dataset", "predicate", "precision", "recall"]
csv_per_p_output = [csv_per_p_headers]

csv_global_headers = ["dataset",  "total_precision", "total_recall", "kans_op_fout"]
csv_global_output = [csv_global_headers]

def run(systems1,games1,datasets1,exp_name="base_experiment"):
    global csv_per_p_output, csv_global_output
    for system in systems1:
        for game in games1:
            for data_name in datasets1:
                #if not data_name.startswith("cwa") or system == "claudien":
                run_system_data(system, game, data_name)

            write_csv("results/" + exp_name + "/" + game + "_" + system + "_pred_overview.csv", csv_per_p_output)
            write_csv("results/" + exp_name + "/" + game + "_" + system + "_global_overview.csv", csv_global_output)
            csv_per_p_output = [csv_per_p_headers]
            csv_global_output = [csv_global_headers]

if __name__ == "__main__":
    run(systems,games,datasets)
