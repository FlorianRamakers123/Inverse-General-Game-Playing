import re
import sys
import itertools
from utils.tokenlib import ground_prolog,strip
from utils.gamelib import get_game_names, find_background, find_atoms
import os
module_path = os.path.dirname(os.path.abspath(__file__))
def instantiate(game):
    type_file = open(module_path + "/../types/{}.typ".format(game)).read()
    type_decs = [s for s in type_file.replace("\n", "").split(".")]
    instances = []
    bk = find_background(game)
    for type_dec in type_decs:
        instances += instantiate_rule(type_dec,type_decs,bk)
    output_file = open(module_path + "/../instances/{}.inst".format(game), 'w')
    #output_file.write(".\n".join(map(ground_prolog, instances)).replace(" ", "") + ".")
    output_file.write(".\n".join(map(ground_prolog, instances)) + ".")

def instantiate_constants(game):
    type_file = open(module_path + "/../types/{}.typ".format(game)).read()
    type_decs = [s for s in type_file.replace("\n", "").split(".")]
    instances = []
    bk = find_background(game)
    for type_dec in type_decs:
        if not '->' in type_dec: 
            instances += instantiate_rule(type_dec,type_decs,bk)
    return ".\n".join(map(ground_prolog, instances)).replace(" ", "") + "."

def instantiate_constants_not(game):
    type_file = open(module_path + "/../types/{}.typ".format(game)).read()
    type_decs = [s for s in type_file.replace("\n", "").split(".")]
    instances = []
    bk = find_background(game)
    for type_dec in type_decs:
        if not '->' in type_dec: 
            instances += instantiate_rule(type_dec,type_decs,bk)
    return ".\n".join(["not_" + p for p in list(map(ground_prolog, instances))]).replace(" ", "") + "."

def is_in_bk(bk, predicate):
    for bk_rule in bk.split("\n"):
        if bk_rule.split('(')[0] == predicate:
            return True
    return False

def instantiate_rule(type_dec, rules, bk):
    instances = []
    match = re.search('(.*[^ ]) *:: *([^ ].*)', type_dec, re.MULTILINE | re.DOTALL)
    if match:
        lhs = match.group(1).split(",")
        rhs = match.group(2).split(" -> ")
        # A1, A2, ..., An :: B
        if len(rhs) == 1:
            if rhs[-1] != "bool" and not is_in_bk(bk,rhs[0]):
           #     for pred in lhs:
           #         instances.append(pred.strip())
           # else:    
                for pred in lhs:
                    instances.append(rhs[0] + '(' + pred.strip() + ")")
        # A1, A2, ..., An :: B1 -> B2 -> ... -> Bm
        elif len(rhs) > 1:
            if rhs[-1] != "bool":
                return []
            args = []
            for i in range(0,len(rhs) - 1):
                args.append(instantiate_type(rhs[i], bk, rules))
            for lh in lhs: 
                if not is_in_bk(bk,lh.strip()):                  
                    for arg in itertools.product(*args):
                        instances.append(lh.strip() + '(' + ", ".join(map(strip,list(arg))) + ')')

    # A1, A2, ..., An :> B
    else:
        match = re.search('(.*[^ ]) *:> *([^ ].*)', type_dec, re.MULTILINE | re.DOTALL)
        if match:
            lhs = match.group(1).split(", ")
            rhs = match.group(2)
            for pred in lhs:
                instances.append(rhs + '(X) :- ' + pred + '(X)')
    return instances    

def instantiate_type(typ, bk, rules):
    instances = []
    for type_dec in rules:
        match = re.search('(.*[^ ]) *:: *([^ ].*)', type_dec, re.MULTILINE | re.DOTALL)
        if match:
            lhs = match.group(1).split(",")
            rhs = match.group(2).split(" -> ")
            if rhs[-1] == typ:
                # A1, A2, ..., An :: B
                if len(rhs) == 1:
                    for pred in lhs:
                        instances.append(pred.strip())
                # A1, A2, ..., An :: B1 -> B2 -> ... -> Bm
                elif len(rhs) > 1 and rhs[-1] == typ:
                    args = []
                    for i in range(0,len(rhs) - 1):
                        args.append(instantiate_type(rhs[i], bk, rules))
                    for lh in lhs: 
                        if not is_in_bk(bk,lh.strip()):                  
                            for arg in itertools.product(*args):
                                instances.append(lh.strip() + '(' + ", ".join(map(strip,list(arg))) + ')')
                    
        """        
        # A1, A2, ..., An :> B
        else:
            match = re.search('(.*[^ ]) *:> *([^ ].*)', type_dec, re.MULTILINE | re.DOTALL)
            if match:
                lhs = match.group(1).split(", ")
                rhs = match.group(2)
                for pred in lhs:
                    instances.append(rhs + '(X) :- ' + pred + '(X).\n')
        """
    return instances
       
"""
if len(sys.argv) == 2:
    game = sys.argv[1]
    if game == "all":
        for g in get_game_names():
            instantiate(g)
    else:
        instantiate(game)
"""
