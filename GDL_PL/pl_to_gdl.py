import sys
sys.path.insert(1, '../utils')

from gamelib import *
from tokenlib import *


#from gamelib: unground_not ToDo?-----------------------

def main(game):
    print("starting ", game)
    result = ""
    path = "../games/" + game + "_pl.pl"
    rules = open(path, "r+").read().replace("\n", "").split(".")


    for r in rules:
        result += changePart(r) + "\n"

    pathout = "../games_gdl/" + game + ".kif" 
    mkdir("../games_gdl/")
    output_file = open(pathout, "w+") #create file is it doesn't exists
    output_file.write(result)
    output_file.close()


def changePart(r):
    # a comment in prolog is %, and in gdl a ;
    if r[:1] == "%":
        #first character of r is a %
        return ";" + r

    if isPrologFact(r):
        #print("r", r)
        if "(" in r:
            lis = r.split("(")

            t = "(" + lis[0]
            if len(lis) != 1:
                #ex. not(true(p))
                #print("r", r)
                for e in tokenize_arguments(r):
                    #print("e  ", e)
                    t += " " + changePart(e)

            t += ")"
            #print("t", t)
            return t
        else:
            if r[:1].isupper():
                r = "?" + r.lower()
            return r
    else:
        h = r.split(":-")[0].strip()
        b = r.split(":-")[1].strip()

        mlist = []
        for e in tokenize_clause(b): # ex. does(1, 2), succ(3, 4) -> [does(1, 2), succ(3, 4)]
            mlist.append( changePart(e) )
    
        return "(<= " + changePart(h) + " " + " ".join(mlist) + ")"
    

def isPrologFact(clause):
    return not (":-" in clause)

# returns the arguments of this clause as a list
# @param clause: the clause to retrieve the arguments from
def tokenize_arguments(clause):
    if not "(" in clause:
        return [clause]
    if clause.endswith("."):
        clause = clause[0:-1]
    parent_index = clause.find("(")
    args = []
    args_str = clause[parent_index+1:-1]
    
    curr_arg = ""
    inFunction = False

    for c in args_str:
        if c == '(':
            inFunction = True
        elif c == ')':
            inFunction = False
        elif c == ',' and not inFunction:
            args.append(curr_arg.strip())
           # print("new args", args)
            curr_arg = ""
            continue
        
       # if not inFunction:
            #print("safe")
        curr_arg += c 

        #print("curr_arg = ", curr_arg)

    if curr_arg != "": 
        #print("extra add", curr_arg)
        args.append(curr_arg.strip())
    return args


def tokenize_clause(clause):
    clauses = []
    curr_clause = ""
    inFunction = False

    for c in clause:
        if c == '(':
            inFunction = True
        elif c == ')':
            inFunction = False
        elif c == ',' and not inFunction:
            clauses.append(curr_clause.strip())
            #print("new clauses", clauses)
            curr_clause = ""
            continue
        curr_clause += c 
        #print("curr_clause = ", curr_clause)

    if curr_clause != "":
  
        clauses.append(curr_clause.strip())
    return clauses

"""
#uit def ground_prolog_fact(prolog_fact):
def lala(prolog_fact):
# search the first parenthesis
    first_parenth = prolog_fact.find('(')

    # extract the predicate name
    pred_name = prolog_fact[0:first_parenth]

    # get the arguments
    # arguments can be variables or predicates
    pred_args = tokenize_prolog_body(prolog_fact[first_parenth + 1: -1])
    i = 0
    while i < len(pred_args):      
        arg = pred_args[i]
        # we found a predicate with arity > 0
        if '(' in arg and not "()" in arg:
            first_parenth_arg = arg.find('(')
            pred_name_arg = arg[0:first_parenth_arg]
            pred_arg_args = tokenize_prolog_body(arg[first_parenth_arg + 1: -1])
            pred_args[i] = pred_arg_args[0]
            merge(pred_arg_args[1:], pred_args, i+1)
            pred_name += "_" + pred_name_arg
        # we found a predicate with arity = 0
        # WARNING: (next (gameOver) (gameOver2) x) will not be grounded correctly
        elif "()" in arg:
            pred_name += "_" + arg.replace("()", "")
            pred_args.remove(arg)
        i += 1

    return "{}({})".format(pred_name,", ".join(pred_args))
"""

games_selection = ["buttons_and_lights", "fizzbuzz", "scissors_paper_stone"]
    #["buttons_and_lights", "fizzbuzz", "scissors_paper_stone"]

len_args = len(sys.argv)

if len_args ==1: #geen argumenten opgegeven
    for g in games_selection:
        main(g) 
        
if len_args ==2: #1 argumenten opgegeven
    g = sys.argv[1]
    main(g) 




