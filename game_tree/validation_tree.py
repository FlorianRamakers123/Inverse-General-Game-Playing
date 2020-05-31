import sys
sys.path.insert(1,"../")
from utils.gamelib import *
from utils.prologlib import *
from utils.tokenlib import tokenize_prolog_body
from utils.type_inst import instantiate_constants
from ggp_agent.rules import Rules
from graphviz import Digraph
import os
from collections import defaultdict
import random
from copy import copy
import datetime
module_path = os.path.dirname(os.path.abspath(__file__))

class Node:
    def __init__(self, state,depth=0,parent=None,trace_matrix=defaultdict(list),parent_moves=[]):
        # BASE
        self.state = state
        self.depth = depth
        self.is_terminal = rules.is_terminal(state)
        self.moves_perm = rules.get_all_moves_perm(state)
        self.state_and_moves = {}
        for moves in self.moves_perm:
            self.state_and_moves[tuple(moves)] = rules.get_next_state(state,moves)

        # VALIDATION
        # confusion matrix of the path from the root to the parent (this node not included)
        self.trace_matrix = copy(trace_matrix)
        self.confusion_matrix = None
        # list of tuples (move,new_state)
        self.seen_moves = defaultdict(list)
        # incoming edges (from parent)
        self.used_edges = []

        # AVERAGE ERROR RATE
        self.score = 0
        self.terminal_hyp = hypothesis.is_terminal(state)
        self.scores_gdl = rules.get_all_scores(state)
        self.scores_hyp = hypothesis.get_all_scores(state)
        self.set_parent(parent,parent_moves)
        self.moves_causes = defaultdict(list)
        self.pred_infos = defaultdict(dict)

    def add_edge(self, parent,moves):
        self.used_edges.append((parent,moves))

    def has_performed_moves(self,moves):
        keys = list(self.seen_moves.keys())
        if keys:
            pred = keys[0]
            return self.has_seen_move(pred,moves)
        return False

    def is_used_edge(self,parent,moves):
        return (parent,moves) in self.used_edges

    def get_states_and_moves(self):
        return self.state_and_moves

    def set_confusion_matrix(self,confusion_matrix):
        self.confusion_matrix = copy(confusion_matrix)

    def has_confusion_matrix(self):
        return self.confusion_matrix != None

    def set_trace_matrix(self,trace_matrix):
        self.trace_matrix = copy(trace_matrix)

    def add_new_move(self,next_pred,moves,TP_FP_FN):
        self.seen_moves[(next_pred,tuple(moves))] = TP_FP_FN

    def has_seen_move(self,next_pred,moves):
        return (next_pred,tuple(moves)) in self.seen_moves

    def get_TP_FP_FN(self,next_pred,moves):
        return self.seen_moves[(next_pred,tuple(moves))]

    def calculate_trace_matrix(self,moves):
        new_trace_matrix = defaultdict(list)
        if len(self.trace_matrix) > 0:
            for key in self.trace_matrix.keys():
                if key in self.confusion_matrix:
                    new_trace_matrix[key] =  tuple([x + y for x,y in zip(self.confusion_matrix[key], self.trace_matrix[key])])
                else:
                    new_trace_matrix[key] = tuple([x + y for x,y in zip(self.seen_moves[(key,tuple(moves))], self.trace_matrix[key])])
        else:
            new_trace_matrix = copy(self.confusion_matrix)
            for (next_pred,moves2) in self.seen_moves.keys():
                if moves2 == tuple(moves):
                    new_trace_matrix[next_pred] = self.seen_moves[(next_pred,moves2)]
        return new_trace_matrix

    def get_state(self):
        return self.state

    def is_leaf_node(self):
        return self.is_terminal

    def get_depth(self):
        return self.depth

    def get_score(self):
        return self.score

    def update_score(self,error):
        parent = self.get_parent()
        if parent != None:
            parent_score = parent.get_score()
            if error:
                self.score = (parent_score * (self.depth - 1) + 1) / self.depth
            else:
                self.score = (parent_score * (self.depth - 1)) / self.depth
        else:
            if error:
                self.score = 1
            else:
                self.score = 0

    def get_parent(self):
        return self.parent

    def set_parent(self,parent,parent_moves):
        self.parent = parent
        self.parent_moves = parent_moves
        #for moves in self.moves_perm:
        #    self.pred_infos[tuple(moves)] = defaultdict(int)
        #    if parent != None:
        #        for pred in parent.pred_infos[tuple(parent_moves)].keys():
        #            self.pred_infos[tuple(moves)][pred] = parent.pred_infos[tuple(parent_moves)][pred]

    def evaluate(self,moves):
        causes = []
        if tuple(moves) in self.moves_causes:
            #log("state and move already encountered")
            causes = self.moves_causes[tuple(moves)]
        else:
            #print("new moves")
            #print(self.state)
            #print(moves)
            if set(self.scores_hyp) != set(self.scores_gdl):
                causes.append("goal")

            if self.is_terminal != self.terminal_hyp:
                causes.append("terminal")

            if moves:
                for move,player in moves:
                    if not hypothesis.is_legal_move(player,move,self.state):
                        causes.append("legal")
                        break

                self.new_state_gdl = self.state_and_moves[tuple(moves)]
                self.new_state_hyp = hypothesis.get_next_state(self.state,moves)
                if self.new_state_hyp == None or set(filter(None,self.new_state_hyp.split("\n"))) != set(filter(None,self.new_state_gdl.split("\n"))):
                    causes.append("next")

            self.moves_causes[tuple(moves)] = causes

        if self.parent != None:
            for pred in self.parent.pred_infos[tuple(self.parent_moves)].keys():
                self.pred_infos[tuple(moves)][pred] = self.parent.pred_infos[tuple(self.parent_moves)][pred]
        else:
            self.pred_info = defaultdict(int)


        for cause in causes:
            if cause in self.pred_infos[tuple(moves)]:
                self.pred_infos[tuple(moves)][cause] += 1
            else:
                self.pred_infos[tuple(moves)][cause] = 1


        if causes:
            log("---------------------------")
            log("CURRENT STATE:")
            log(self.state)
            if moves:
                log(moves)
                log("STATE ACCORDING TO GDL:")
                log(self.new_state_gdl.strip())
                for (score,player) in self.scores_gdl:
                    log("{}: {}".format(player,score))
                log("STATE ACCORDING TO HYPOTHESIS:")
                log(self.new_state_hyp)
                for (score,player) in self.scores_hyp:
                    log("{}: {}".format(player,score))
            else:
                log("no moves can be performed in this state")
            log("CAUSES: " + ", ".join(causes))
        else:
            log("---------------------------")
            log("CURRENT STATE:")
            log(self.state)
            if moves:
                log(moves)
                log("STATE ACCORDING TO GDL:")
                log(self.new_state_gdl.strip())
                for (score,player) in self.scores_gdl:
                    log("{}: {}".format(player,score))
                log("STATE ACCORDING TO HYPOTHESIS:")
                log(self.new_state_hyp)
                for (score,player) in self.scores_hyp:
                    log("{}: {}".format(player,score))
            else:
                log("no moves can be performed in this state")
        return not causes

    def __str__(self):
        return self.state.replace("\n",", ")

# return the recall and the precision of the terminal predicate
def validate_terminal(path,system,facts,game):
    TP = 0
    FP = 0
    FN = 0
    gdl_true = bool(perform_query("terminal1",path))
    hyp_true = bool(perform_query("terminal2",path))

    positives = []
    negatives = []
    if gdl_true == hyp_true:
        TP += 1
    elif gdl_true and not hyp_true:
        positives.append("terminal")
        FN += 1
    elif not gdl_true and hyp_true:
        negatives.append("terminal")
        FP += 1


    if system == "claudien":
        write_examples(game,"terminal",facts,positives,negatives)
    return (TP,FP,FN)

def prepare_validation_file(system,game,predicates,facts):
    # create the output folders and files
    folder = module_path + "/output/{}/{}".format(system,game)
    path = module_path + "/output/{0}/{1}/test.pl".format(system,game)
    if not os.path.exists(folder):
        os.makedirs(folder)

    content = ""
    # define the background knowledge
    content += "%%%%%%% BACKGROUND KNOWLEDGE %%%%%%%\n"
    content += find_background(game)

    # define the GDL rule distinct because some hypothesis rely on this predicate and it is not defined by default
    content += "\ndistinct(A,B):-A \== B."

    # define the constants
    content += "\n%%%%%%% CONSTANTS %%%%%%%%\n"
    content += instantiate_constants(game) + "\n"

    content += "%%%%%%% FALSE FACTS %%%%%%%\n"
    pos_list = facts.split("\n")
    pos_list.extend(instantiate_constants(game).split("\n"))
    content += getNegInstances(pos_list,game)
    content += "not(A) :- \+ A.\n"

    # define all needed facts
    content += "\n%%%%%%% FACTS %%%%%%%\n"
    content += facts

    # terminal needs an hardcoded entry because it is validated in another method
    heads = { "terminal" : None}

    for predicate in predicates:
        # define the hypothesises
        content += "\n%%%%%%% HYPOTHESISES {} %%%%%%%\n".format(predicate.upper())


        hyp = find_hypothesis(system,game,predicate)
        gdl = find_hypothesis("gdl",game,predicate)
        if hyp == False:
            raise ValueError("cannot test system {} on game {} for predicate {}".format(system,game,predicate))
            return

        # define the gdl and system hypothesises as two versions of the same hypothesis by appending '1' en '2'
        gdl_new = ".\n".join(suffix(gdl,"1").strip().split("\n")) + ".\n"
        hyp_new = ".\n".join(suffix(hyp,"2").strip().split("\n")) + ".\n"
        content += gdl_new
        content += hyp_new

        # find the most general declaration of the head of the clause
        # bv legal(robot,B) --> legal(A,B)
        head = find_head(game,predicate)
        heads[predicate] = head
        if predicate.startswith("terminal"):
            continue
        # define the base test
        content += "\n%%%%%%% BASE TEST {} %%%%%%%\n".format(predicate.upper())
        head_base = suffix(head,"_base").strip()
        base_clause = "{} :- {}, {}.".format(head_base,suffix(head,"1").strip(),suffix(head,"2").strip())
        content += base_clause + "\n"

        # define the positive test
        content += "\n%%%%%%% POSITIVE TEST {} %%%%%%%\n".format(predicate.upper())
        # for the test predicates we need to call the general declaration of the gdl version
        gdl_new_head = suffix(head,"1").strip()
        gdl_new_hyp = gdl_new.replace(gdl_new.split(":-")[0].strip(),gdl_new_head)

        head_pos = suffix(head,"_pos").strip()
        hyp_pos = "{} :- {}, \\+ {}.\n".format(head_pos, gdl_new_head, suffix(head,"2").strip())
        content += hyp_pos

        # define the negative test
        content += "\n%%%%%%% NEGATIVE TEST {} %%%%%%%\n".format(predicate.upper())
        head_neg = suffix(head,"_neg").strip()
        hyp_neg = "{} :- {}, \\+ {}.\n".format(head_neg,suffix(head,"2").strip(), gdl_new_head)
        content += hyp_neg

    # we need to replace distinct by distinct_gdl because it is a prolog builtin
    content = content.replace("distinct", "distinct_gdl")
    content = content.replace("not", "my_not")
    f = open(path,'w')
    f.write(content)
    f.flush()
    f.close()
    return (path, heads)
# return the recall and the precision
def validate(predicate,path,head,facts,system,game):
    if predicate.startswith("terminal"):
        return validate_terminal(path,system,facts,game)

    #BASE TEST
    # get all the instances where the gdl and the hypothesis are true
    log("performing base query for predicate " + predicate)
    head_base = suffix(head,"_base").strip()
    instances_true = findall(path,head_base)

    # POSITIVE TEST
    #print("instances gdl true: {}".format(instances_gdl_true))
    # get all the instances where the gdl is true and the hypothesis is false
    log("performing postive query for predicate " + predicate)
    head_pos = suffix(head,"_pos").strip()
    instances_hyp_false = findall(path,head_pos)
    #print("instances hyp false: {}".format(instances_hyp_false))
    # NEGATIVE TEST
    # get all the instances where the gdl is false and the hypothesis is true
    log("performing negative query for predicate " + predicate)
    head_neg = suffix(head,"_neg").strip()
    instances_gdl_false = findall(path,head_neg)
    #print("instances gdl false: {}".format(instances_gdl_false))

    # true positives are the instances where the gdl is true and where the hypothesis is true
    TP = len(instances_true)
    # false positives are the instances where the gdl is false and where the hypothesis is true
    FP = len(instances_gdl_false)
    # false negatives are the instances where the gdl is true and where the hypothesis is false
    FN = len(instances_hyp_false)

    positives = []
    negatives = []
    clause = head_pos.replace("_pos(", "(")
    # generate positives
    for unification in instances_hyp_false:
        positive = clause
        for var in unification.keys():
            positive = positive.replace(var, str(unification[var]))
        positives.append(positive)
    # generate negatives
    for unification in instances_gdl_false:
        negative = clause
        for var in unification.keys():
            negative = negative.replace(var, str(unification[var]))
        negatives.append(negative)

    if system == "claudien":
        write_examples(game,predicate,facts,positives,negatives)

    return (TP,FP,FN)

def suffix(pred,suffix):
    preds = [p.replace(".","") for p in pred.split("\n")]
    result = ""
    pred_name = preds[0].split(":-")[0].strip().split('(')[0]
    for p in preds:
        head_and_body = p.split(":-")
        pred_parts = head_and_body[0].strip().split('(')
        if pred_parts[0] != pred_name:
            result += p + "\n"
            continue
        result += pred_parts[0] + suffix + ('(' if '(' in head_and_body[0] else "") + ('('.join(pred_parts[1:]) if '(' in head_and_body[0] else "") + (" :-" + head_and_body[1] if len(head_and_body) > 1 else "") + "\n"
    return result

def validate_all(system,game,full_tree):
    init_state = rules.get_init_state()
    root = Node(init_state)
    state_nodes[root.get_state()] = root

    try:
        if full_tree:
            walk_tree(root,system,game)
        else:
            NB_WALKS = 25
            curr_nb_walks = 0
            while curr_nb_walks < NB_WALKS:
                if walk_tree_randomly(root,system,game,False):
                    print(curr_nb_walks)
                    curr_nb_walks += 1
    except KeyboardInterrupt:
        pass

    rules.destroy()
    hypothesis.destroy()

    p_and_r = defaultdict(list)
    for key in total_confusion_matrix.keys():
        precisions = [(x[0] / (x[0] + x[1]) if x[0] + x[1] > 0 else 1) for x in total_confusion_matrix[key] ]
        recalls = [(x[0] / (x[0] + x[2]) if x[0] + x[2]  > 0 else 1) for x in total_confusion_matrix[key]]
        p_and_r[key] = [sum(precisions) / len(precisions), sum(recalls) / len(recalls)]

    AER = total_score / nb_traces
    print(pred_info)
    print(nb_nodes)
    print(nb_traces)
    total_pred_info = { "goal" : pred_info["goal"] / nb_nodes, \
                        "legal" : pred_info["legal"] / (nb_nodes - nb_traces), \
                        "next" : pred_info["next"] / (nb_nodes - nb_traces), \
                        "terminal" : pred_info["terminal"] / nb_nodes }

    return (p_and_r,AER,total_pred_info)

def validate_minimal(system,game,minimal_tree_data):
    global nb_traces
    init_state = rules.get_init_state()
    root = Node(init_state)

    f = open(minimal_tree_data)
    tree_data = f.read()
    f.close()
    traces = [s.strip() for s in tree_data.split("######")]
    try:
        for i,trace in enumerate(set(traces)):
            nodes = [s.strip() for s in trace.split("---")]
            states = [node.split("%%%")[0].strip() + "\n"  for node in nodes]
            moves_list = [[(moves.split(":")[1],moves.split(':')[0]) for moves in node.split("%%%")[1].strip().split("\n")] for node in nodes if "%%%" in node]
            walk_trace(states,moves_list,game,system)
    except KeyboardInterrupt:
        pass
    #print(total_confusion_matrix)
    rules.destroy()
    p_and_r = defaultdict(list)
    for key in total_confusion_matrix.keys():
        precisions = [(x[0] / (x[0] + x[1]) if x[0] + x[1] > 0 else 1) for x in total_confusion_matrix[key] ]
        recalls = [(x[0] / (x[0] + x[2]) if x[0] + x[2]  > 0 else 1) for x in total_confusion_matrix[key]]
        p_and_r[key] = [sum(precisions) / len(precisions), sum(recalls) / len(recalls)]

    AER = total_score / nb_traces
    total_pred_info = { "goal" : pred_info["goal"] / nb_nodes, \
                        "legal" : pred_info["legal"] / (nb_nodes - nb_traces), \
                        "next" : pred_info["next"] / (nb_nodes - nb_traces), \
                        "terminal" : pred_info["terminal"] / nb_nodes }
    return (p_and_r,AER,total_pred_info)

def calculate_confusion_matrix(state, moves,system,game):
    log("------------------------------------------------")
    log(moves)
    facts = ""
    for move,player in moves:
        facts += rules.get_clause_name("DOES")[0].instantiate([player,move]) + '.\n'
    if len(moves) == 0:
        facts += rules.get_clause_name("DOES")[0].instantiate(['A','B']) + ' :- fail.\n'
    facts += state
    subpredicates = get_subpredicates(game)
    (path, heads) = prepare_validation_file(system,game,subpredicates,facts)
    confusion_matrix = defaultdict(list)
    node = state_nodes[state]

    for predicate in subpredicates:
        if node.has_confusion_matrix():
            if predicate.startswith("next"):
                if not node.has_seen_move(predicate,moves):
                    if len(moves) > 0:
                        (TP,FP,FN) = validate(predicate,path, heads[predicate],facts,system,game)
                        node.add_new_move(predicate,moves,(TP,FP,FN))
                    else:
                        node.add_new_move(predicate,moves,(0,0,0))
        else:
            if not predicate.startswith("next"):
                confusion_matrix[predicate] = validate(predicate,path, heads[predicate],facts, system,game)
            else:
                if not node.has_seen_move(predicate,moves):
                    if len(moves) > 0:
                        (TP,FP,FN) = validate(predicate,path, heads[predicate],facts,system,game)
                        node.add_new_move(predicate,moves,(TP,FP,FN))
                    else:
                        node.add_new_move(predicate,moves,(0,0,0))

    if not node.has_confusion_matrix():
        node.set_confusion_matrix(confusion_matrix)

def write_examples(game,pred,facts,positives,negatives):
    if positives:
        pos_path = module_path + "/pos_examples/{}/".format(game)
        mkdir(pos_path)
        f = open(pos_path + "{}.pos".format(pred), 'a+')
        f.write("% =========\n")
        f.write("".join(facts) + ".\n".join(positives) + ".\n")
        f.close()

    if negatives:
        neg_path = module_path + "/neg_examples/{}/".format(game)
        mkdir(neg_path)
        f = open(neg_path + "{}.neg".format(pred), 'a+')
        f.write("% =========!\n")
        f.write("".join(facts) + ".\n".join(negatives) + ".\n")
        f.close()

# BASE
def walk_tree_randomly(node,system,game,new):
    global total_confusion_matrix, nb_traces, total_score, nb_nodes
    state = node.get_state()
    if node.is_leaf_node():
        if new:
            # BASE
            nb_traces += 1

            # VALIDATION
            calculate_confusion_matrix(state,[],system,game)
            trace_matrix = node.calculate_trace_matrix([])
            log(str(nb_traces) + " TRACES REACHED")
            for key in trace_matrix.keys():
                total_confusion_matrix[key].append(trace_matrix[key])

            # AVERAGE ERROR RATE
            valid = node.evaluate([])
            node.update_score(not valid)
            nb_nodes += node.get_depth() + 1
            for pred in node.pred_infos[tuple([])].keys():
                pred_info[pred] += node.pred_infos[tuple([])][pred]
            if node.get_score() > 0:
                total_score += 1
        return new

    # BASE
    possible_moves = node.get_states_and_moves().keys()
    nb_moves = len(possible_moves)
    indices = [i for i in range(nb_moves)]
    moves = None
    new_state = None
    while len(indices) > 0:
        rnd_nb = random.randrange(0,len(indices))
        idx = indices[rnd_nb]
        del indices[rnd_nb]
        moves_tmp = list(possible_moves)[idx]
        new_state_tmp = node.get_states_and_moves()[moves_tmp]
        if node.has_performed_moves(moves_tmp):
            continue
        else:
            moves = moves_tmp
            new_state = new_state_tmp
            break

    if new_state == None or moves == None:
        idx = random.randrange(0,len(state_moves))
        moves = possible_moves[idx]
        new_state = node.get_states_and_moves()[moves]

    # VALIDATION
    calculate_confusion_matrix(state,moves,system,game)
    trace_matrix = node.calculate_trace_matrix(moves)

    # AVERAGE ERROR RATE
    valid = node.evaluate(list(moves))
    node.update_score(not valid)

    new_node = None

    if new_state in state_nodes:
        new_node = state_nodes[new_state]
        new_node.set_parent(node, moves)
        new_node.set_trace_matrix(trace_matrix)
        new = not new_node.is_used_edge(node,moves) or new
    else:
        new_node = Node(new_state,node.get_depth() + 1,node,trace_matrix,moves)
        state_nodes[new_state] = new_node
        new = True

    new_node.add_edge(node,moves)
    return walk_tree_randomly(new_node,system,game,new)

def walk_tree(node,system,game):
    global total_confusion_matrix, nb_traces, total_score, nb_nodes
    state = node.get_state()
    if node.is_leaf_node():
        # BASE
        nb_traces += 1

        # VALIDATION
        calculate_confusion_matrix(state,[],system,game)
        trace_matrix = node.calculate_trace_matrix([])
        log(str(nb_traces) + " TRACES REACHED")
        for key in trace_matrix.keys():
            total_confusion_matrix[key].append(trace_matrix[key])

        # AVERAGE ERROR RATE
        valid = node.evaluate([])
        node.update_score(not valid)
        nb_nodes += node.get_depth() + 1
        for pred in node.pred_infos[tuple([])].keys():
            pred_info[pred] += node.pred_infos[tuple([])][pred]
        if node.get_score() > 0:
            total_score += 1

        return


    for moves in node.get_states_and_moves().keys():
        # BASE
        new_state = node.get_states_and_moves()[moves]

        # VALIDATION
        calculate_confusion_matrix(state,moves,system,game)
        trace_matrix = node.calculate_trace_matrix(moves)

        # AVERAGE ERROR RATE
        valid = node.evaluate(list(moves))
        node.update_score(not valid)

        new_node = None

        if new_state in state_nodes:
            new_node = state_nodes[new_state]
            new_node.set_trace_matrix(trace_matrix)
            new_node.set_parent(node, moves)
        else:
            new_node = Node(new_state,node.get_depth() + 1,node,trace_matrix, moves)
            state_nodes[new_state] = new_node

        walk_tree(new_node,system,game)

def walk_trace(states,moves_list,system,game):
    global nb_nodes, nb_traces, total_score
    for i in range(len(states)):
        state = states[i]
        prev_moves = []
        curr_moves = []
        if i > 0:
            prev_moves = moves_list[i-1]
            # AVERAGE ERROR RATE
            old_node = state_nodes[states[i-1]]
            valid = old_node.evaluate(list(prev_moves))
            old_node.update_score(not valid)
        if i < len(moves_list):
            curr_moves = moves_list[i]

        node = None
        if state in state_nodes:
            node = state_nodes[state]
            if i > 0:
                # BASE
                old_node = state_nodes[states[i-1]]
                # VALIDATION
                trace_matrix = old_node.calculate_trace_matrix(prev_moves)
                node.set_trace_matrix(trace_matrix)
                # AVERAGE ERROR RATE
                node.set_parent(old_node, prev_moves)
            else:
                node.set_trace_matrix(defaultdict(list))
                node.set_parent(None,[])
        else:
            if i == 0:
                node = Node(state)
            else:
                # BASE
                old_node = state_nodes[states[i-1]]
                # VALIDATION
                trace_matrix = old_node.calculate_trace_matrix(prev_moves)
                node = Node(state,i,old_node,trace_matrix,prev_moves)
            state_nodes[state] = node

        calculate_confusion_matrix(state,curr_moves,game,system)

    # BASE
    node = state_nodes[states[-1]]

    # VALIDATION
    trace_matrix = node.calculate_trace_matrix([])
    log(trace_matrix)
    for key in trace_matrix.keys():
        total_confusion_matrix[key].append(trace_matrix[key])

    # AVERAGE ERROR RATE
    valid = node.evaluate([])
    node.update_score(not valid)
    nb_nodes += node.get_depth() + 1
    for pred in node.pred_infos[tuple([])].keys():
        pred_info[pred] += node.pred_infos[tuple([])][pred]
    nb_traces += 1
    if node.get_score() > 0:
        total_score += 1


def clear_current_examples(game):
    for subtarget in get_subpredicates(game):
        pos_file = module_path + "/pos_examples/{}/{}.pos".format(game,subtarget)
        if os.path.exists(pos_file):
            os.remove(pos_file)
        neg_file = module_path + "/neg_examples/{}/{}.neg".format(game,subtarget)
        if os.path.exists(neg_file):
            os.remove(neg_file)

# ---------------------------
# BASE
LOG_OUTPUT = False
state_nodes = {} # dictionary for associating states to nodes
rules = None
nb_traces = 0

# VALIDATION
total_confusion_matrix = defaultdict(list)
# AVERAGE ERROR RATE
nb_nodes = 0
total_score = 0
pred_info = defaultdict(int)
hypothesis = None
# ---------------------------
# run the full tree
def run(system,game):
    global total_confusion_matrix, total_score, pred_info, state_nodes, nb_traces, nb_nodes, rules, hypothesis
    t = datetime.datetime.now()
    # BASE
    state_nodes = {}
    nb_traces = 0

    # VALIDATIONs, nb_nodes
    t = datetime.datetime.now()
    total_confusion_matrix = defaultdict(list)
    if system == "claudien":
        clear_current_examples(game)

    # AVERAGE ERROR RATE
    pred_info = defaultdict(int)
    total_score = 0
    nb_nodes = 0

    gdl_path = module_path + "/../games/{}_pl.pl".format(game)
    hyp_path = module_path + "/../learned_rules/{}/{}_pl.pl".format(system,game)
    rules = Rules(gdl_path)
    hypothesis = Rules(hyp_path)

    v = validate_all(system,game,True)
    t2 = datetime.datetime.now()
    log("validation took " + str(t2 - t) + "seconds")
    log(str(nb_traces) + " traces validated")
    return v

# run the minimal tree and perform random walks
def run_partly(system,game,seed):
    global total_confusion_matrix, total_score, pred_info, state_nodes, nb_traces, nb_nodes, rules, hypothesis
    t = datetime.datetime.now()
    # BASE
    state_nodes = {}
    nb_traces = 0
    random.seed(seed)

    # VALIDATION
    total_confusion_matrix = defaultdict(list)
    if system == "claudien":
        clear_current_examples(game)

    # AVERAGE ERROR RATE
    pred_info = defaultdict(int)
    total_score = 0
    nb_nodes = 0

    gdl_path = module_path + "/../games/{}_pl.pl".format(game)
    hyp_path = module_path + "/../learned_rules/{}/{}_pl.pl".format(system,game)
    rules = Rules(gdl_path)
    hypothesis = Rules(hyp_path)

    path = module_path + "/../data/validate/{}/minimal/minimal_data.traces".format(game)
    validate_minimal(system,game,path)
    v = validate_all(system,game,False)
    t2 = datetime.datetime.now()
    log("validation took " + str(t2 - t))
    log(str(nb_traces) + " traces validated")
    return v

def log(s):
    if LOG_OUTPUT:
        print(s)

if __name__ == "__main__":
    game = sys.argv[1]
    system = sys.argv[2]
    LOG_OUTPUT = False
    #print(run_partly(system,game, random.randrange(0,239492374)))
    print(run(system,game))
