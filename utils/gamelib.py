from utils.tokenlib import tokenize_prolog_body,tokenize_arguments
from os import listdir
from os.path import isfile, join
import os
import csv
module_path = os.path.dirname(os.path.abspath(__file__))

# returns a the hypothesis for the specified game and predicate
def find_hypothesis(system,game,predicate):
    if system == "metagol":
        return find_hypothesis_metagol(game,predicate)
    elif system == "ilasp":
        return find_hypothesis_ilasp(game,predicate)
    elif system == "gdl":
        return find_hypothesis_gdl(game,predicate)
    elif system == "claudien":
        return find_hypothesis_claudien(game,predicate)
    else:
        raise Exception("unable to retrieve hypothesis for predicate {} in game {} for system {}".format(predicate,game,system))

def get_game_names():
    return [s[0:-6] for s in listdir(module_path + "/../games")]

# get all the predicates
def get_subpredicates(game):
    gdl = open(module_path + "/../games/{}_pl.pl".format(game)).readlines()
    preds = []
    bk_found = False
    for i in range(len(gdl)):
        if bk_found:
            preds.append(gdl[i].split(':-')[0].strip().split('(')[0])
        else:
            if gdl[i].startswith("%%%%"):
                bk_found = True
    subpreds = list([p for p in set(preds) if p != ""])
    subpreds.sort()
    return subpreds

def get_target_subpredicates(game, pred):
	return [s for s in get_subpredicates(game) if s.startswith(pred)]

def find_hypothesis_gdl(game,predicate):
    path = module_path + "/../games/{}_pl.pl".format(game)
    gdl = open(path).readlines()
    result = ""
    for line in gdl:
        if line.split(":-")[0].split('(')[0].strip() == predicate:
            result += line
    return result.strip()

def find_hypothesis_metagol(game,predicate):
    path = module_path + '/../hypothesis/metagol/{}/{}.pl'.format(game, predicate)
    result = ""
    content = open(path).readlines()
    predicate = predicate.replace("my_", "")

    # starts with some empty lines and a 'true' in the first 3 lines, then some lines that start with %, and then the hypothesis
    for i in range(3,len(content)):
        if (content[i].startswith("%")):
            continue
        else:
            result += content[i]

    # metagol didn't learn any hypothesis
    if result == "":
        return find_head(game,predicate) + " :- false."

    # delete all the metagol redundancy
    result =  result.replace("my_", "").replace("A,", "").replace("(A)", "")

    # unground not
    return unground_not(result)

def find_hypothesis_ilasp(game,predicate):
    path = module_path + '/../hypothesis/ilasp/{}/{}.pl'.format(game, predicate)
    content = open(path).readlines()
    result = ""
    #usually, the first line is empty and the rest of the file contains the hypothese
    for i in range(len(content)):
        if (content[i].strip() == ""):
            continue
        else:
            result += content[i]

    if result == "":
        gdl = find_hypothesis_gdl(game,predicate)
        if gdl == "":
            # predicate not found in gdl
            return False
        return find_head(game,predicate) + " :- false."

    return result.strip()

def find_hypothesis_claudien(game,predicate):
    path = module_path + '/../hypothesis/claudien/{}/{}.pl'.format(game, predicate)
    content = list(filter(None,open(path).readlines()))

    # claudien didn't learn any hypothesis
    if len(content) == 0:
        return find_head(game,predicate) + " :- false."
    return "\n".join(list(map(unground_not, content))) + "\n"
    # unground not
    #return unground_not(content) #.replace("succ1","succ")

def unground_not(result):
    hyps = result.split("\n")
    for i in range(len(hyps)):
        parts = hyps[i].split(":-")
        if len(parts) < 2:
            continue
        body = parts[1].strip().replace(".", "")
        if "not_" in body:
            body_parts = tokenize_prolog_body(body)
            for j in range(len(body_parts)):
                if body_parts[j].strip().startswith("not_"):
                    body_parts[j] = body_parts[j].replace("not_", "not(") + ")"
            hyps[i] = parts[0] + " :-" + ", ".join(body_parts) + "."

    return "\n".join(hyps).strip()

def has_empty_hypothesis(system,game,predicate):
    if system == "metagol":
        return has_empty_hyp_metagol(game,predicate)
    else:
        return has_empty_hyp_ilasp(game,predicate)

def has_empty_hyp_metagol(game,predicate):
    path = module_path + '/../hypothesis/metagol/{}/{}.pl'.format(game, predicate)
    result = ""
    content = open(path).readlines()
    predicate = predicate.replace("my_", "")

    # starts with some empty lines and a 'true' in the first 3 lines, then some lines that start with %, and then the hypothesis
    for i in range(3,len(content)):
        if (content[i].startswith("%")):
            continue
        else:
            result += content[i]

    # metagol didn't learn any hypothesis
    if result == "":
        return True
    return False


def has_empty_hyp_ilasp(game,predicate):
    path = module_path + '/../hypothesis/ilasp/{}/{}.pl'.format(game, predicate)
    content = open(path).readlines()
    result = ""
    #usually, the first line is empty and the rest of the file contains the hypothese
    for i in range(len(content)):
        if (content[i].strip() == ""):
            continue
        else:
            result += content[i]

    if result == "":
        return True
    return False

# extract the background knowledge
def find_background(game):
    path = module_path + '/../games/{}_pl.pl'.format(game)
    index = 0 #index of the line with the separator
    content = open(path).readlines()

    for i in range(len(content)):
        if (content[i].startswith("%%%%")):
            index = i

    content[index-1] = content[index-1].replace("\n", "") #remove last new line, so if we do later on a split, we don't get an empty last line
    return "".join(content [:index])


def find_instances(game):
    return open(module_path + '/../instances/{}.inst'.format(game)).read()

def getNegInstances(pos_list, game):
    #print(pos_list)
    total = open(module_path + '/../instances/{}.inst'.format(game)).read().split("\n")

    excl_list = ["not(" + e.replace(".", "") + ")" for e in total if e != "" and e not in pos_list]

    return ".\n" . join(excl_list) + ".\n"

def get_neg_instances_no_not(pos_list,game,pred):
    new_pos_list = []
    for p in pos_list:
        new_pos_list.append(p.replace(", ", ","))

    total = open(module_path + '/../instances/{}.inst'.format(game)).read().split("\n")
    excl_list = [e for e in total if e != "" and e.replace(".", "").replace(", ", ",") not in new_pos_list and e.startswith(pred)]
    return "\n" . join(excl_list) + "\n"

def find_head(game,predicate):
    hyp = find_hypothesis_gdl(game,predicate)
    head = hyp.split(":-")[0].strip()
    if not '(' in head:
        return head.strip()
    n = len(tokenize_arguments(head))
    args = ",".join([chr(ord('A') + i) for i in range(n)])
    return head.split('(')[0].strip() + '(' + args + ')'

# find the atoms of the given game and given predicate (goal, legal, next, terminal)
# @param game: the name of the game (without extension)
# @param
def find_atoms(game, predicate):
    path = module_path + "/../data/train/{}_{}_train.dat".format(game, predicate)
    parts = open(path, "r+").read().split("---")
    atoms = parts[0].strip().replace("atoms:", "").replace("\t", "")
    return atoms.split("\n")

# write the specified list to a csv file
# @param mylist: the list to write to a csv file
def write_csv(path, mylist):
    s = getDirectoryOfFile(path)
    mkdir(s)
    with open(path, 'w', newline='') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerows(mylist)

def writeOutput1(content, path):
    s = getDirectoryOfFile(path)
    mkdir(s)
    output_file = open(path, "w+") #create file is it doesn't exists
    output_file.write(content)
    output_file.close()

# given a path of a file, returns the parent directory of the file
# @param path: the path to retrieve the parent directory from
def getDirectoryOfFile(path):
    return  ('/').join( path.split('/')[:-1]) + '/'

# create the current directory if it does not exist already
# @param path: the directory to create
def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
