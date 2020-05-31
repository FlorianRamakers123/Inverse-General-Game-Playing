import sys
#import faulthandler
import os
from graphviz import Digraph
from collections import defaultdict
sys.path.insert(1,'../')
from ggp_agent.rules import Rules
from utils.gamelib import get_subpredicates, find_hypothesis, find_background
from pyswip import Prolog
module_path = os.path.dirname(os.path.abspath(__file__))

class Node:
    def __init__(self, next_state, future_state=None, parent_node=None):
        self.child_nodes = []
        self.next_state = next_state
        self.future_state = future_state
        self.parent_node = parent_node
        if not rules.is_terminal(self.next_state):
            self.moves = rules.get_all_moves_perm(self.next_state)
        else:
            self.moves = None
        self.child_moves = []

    def add_node(self,node,moves):
        self.child_nodes.append(node)
        self.child_moves.append(moves)

    def add_nodes(self, node_list):
        self.child_nodes.extend(node_list)

    def get_child_nodes(self):
        return self.child_nodes

    def get_child_and_moves(self):
        return [(self.child_nodes[i],self.child_moves[i]) for i in range(len(self.child_nodes))]

    def get_next_state(self):
        return self.next_state

    def get_future_state(self):
        return self.future_state

    def get_moves(self):
        return self.moves

    def get_goal_example(self):
        return (self.get_next_state(),rules.get_scores_state(self.get_next_state()))

    def get_legal_example(self):
        state = self.get_next_state()
        facts = []
        for moves in self.get_moves():
            facts += [rules.get_clause_name("LEGAL")[0].instantiate([player,move], ".\n") for move,player in moves]
        positives = "".join(set(facts))
        return (state,positives)

    def get_terminal_example(self):
        if rules.is_terminal(self.get_next_state()):
            return (self.get_next_state(), "terminal.")
        else:
            return (self.get_next_state(), "")

    def get_next_example(self, moves):
        (new_state, future) = rules.get_future_state(self.get_next_state(), moves)
        return (new_state, future)

    def __str__(self):
        return self.state.replace("\n",", ")

class Tree:
    def __init__(self, root_node):
        self.root_node = root_node # de init state

    def get_root_node(self):
        return self.root_node


def construct_tree(game, gdl_path):
    global rules, visited, g
    g = Digraph('G', filename='{}_gdl_minimal.gv'.format(game))
    visited = []

    rules = Rules(gdl_path)
    init_state = rules.get_init_state()
    root = Node(init_state, rules.get_all_moves_perm(init_state))
    tree = Tree(root)

    try:
        calculate_next_states(tree, root)
    except KeyboardInterrupt:
        pass

    rules.destroy()

    return tree


def calculate_next_states(tree, node):
    state = node.get_next_state()
    if rules.is_terminal(state):
        return

    moves_perm = rules.get_all_moves_perm(state)
    for moves in moves_perm:
        new_state = rules.get_next_state(state,moves)
        future_state = rules.get_future_state(state,moves)
        if not (state,moves) in visited:
            visited.append((state,moves))
            new_node = Node(new_state,future_state,node)
            node.add_node(new_node,moves)
            calculate_next_states(tree,new_node)


def loop_tree(node, clause, other_clauses):
    perm_moves = node.get_moves()
    if perm_moves != None:
        for moves in perm_moves:
            (valid, example) = process_node(node, clause, other_clauses, moves)
            if valid:
                #print("found valid state for clause", clause, "\n" + node.get_next_state())
                minimal_data[node.get_next_state()].append(clause)
                examples[clause.split(":-")[0].split("(")[0].strip()].append(example)
                return True
    else:
        pred_name = clause.split(":-")[0].strip()
        #print("processing state", node.get_next_state(), "for", clause)
        if not pred_name.startswith("next"):
            (valid, example) = process_node(node, clause, other_clauses, None)
            if valid:
                #print("found valid end state for clause", clause, "\n" + node.get_next_state())
                minimal_data[node.get_next_state()].append(clause)
                examples[clause.split(":-")[0].split("(")[0].strip()].append(example)
                return True
    for i,child in enumerate(node.get_child_nodes()):
        if loop_tree(child, clause, other_clauses):
            return True

    return False


def process_node(node, clause, other_clauses,moves):
    global tmp_example, prolog
    # check if clause is true for this node and other_clauses are all false for this node
    f = open("state.pl", 'w')
    example_bk_base = node.get_next_state()
    example_bk = example_bk_base
    if moves != None:
        for move,player in moves:
            does_pred = rules.get_clause_name("DOES")[0].instantiate([player,move]) + '.\n'
            f.write(does_pred)
            example_bk += does_pred
    f.write(node.get_next_state())
    f.write(clause)
    f.close()
    #prolog = Prolog()
    list(prolog.query("style_check(-discontiguous)"))
    list(prolog.query("style_check(-singleton)"))
    prolog.consult("state.pl")
    #print(node.get_next_state())
    clause_name = clause.split(":-")[0].strip().replace(".", "")
    result = list(prolog.query(clause_name))
    positives = None
    if bool(result):
        list(prolog.query("unload_file(\"state.pl\")"))
        list(prolog.query("unload_file(\"{}/../background/{}_bk.pl\")".format(module_path,game)))
        pred = clause_name.split('(')[0].split("_")[0].strip()
        if pred == "goal":
            positives = node.get_goal_example()[1]
        elif pred == "next":
            positives = node.get_next_example(moves)[1]
            example_bk_base = example_bk # does predicate must be in background
        elif pred == "legal":
            positives = ""
            for r in result:
                positive = clause_name
                for key in r.keys():
                    positive = positive.replace(key,str(r[key]))
                positives += positive + ".\n"
        else:
            positives = node.get_terminal_example()[1]
        prolog.consult(module_path + "/../background/{}_bk.pl".format(game))
        """

        """
    else:
        list(prolog.query("unload_file(\"state.pl\")"))
        return (False, None)
    if tmp_example == None:
        tmp_example = (example_bk_base,positives)

    list(prolog.query("unload_file(\"state.pl\")"))
    for other in other_clauses:
        f = open("state.pl", 'w')
        if moves != None:
            for move,player in moves:
                does_pred = rules.get_clause_name("DOES")[0].instantiate([player,move]) + '.\n'
                f.write(does_pred)
        f.write(node.get_next_state())
        f.write(other)
        f.close()
        prolog.consult("state.pl")
        if bool(list(prolog.query(other.split(":-")[0].strip()))):
            list(prolog.query("unload_file(\"state.pl\")"))
            #print("----\nclause", clause, "was true in state\n" + node.get_next_state().strip() + "\nbut other clause",other, "was also true")
            return (False, None)

    list(prolog.query("unload_file(\"state.pl\")"))
    return (True, (example_bk_base,positives))

def find_trace(state,node,states,moves_list):
    if len(node.get_child_nodes()) == 0:
        states += [node.get_next_state()]
        if state in states:
            for i in range(len(moves_list)):
                if not (states[i],states[i+1],moves_list[i]) in edges:
                    g.edge(states[i], states[i+1], label="".join(["{}: {}\n".format(player,move) for move,player in moves_list[i]]))
                    edges.append((states[i],states[i+1],moves_list[i]))
            return (states,moves_list)
        else:
            return None
    for (child,moves) in node.get_child_and_moves():
        t = find_trace(state,child,states + [node.get_next_state()], moves_list + [moves])
        if t != None:
            return t
    return None

def log(s):
    if LOG_OUTPUT:
        print(s)

# ---------------------------
LOG_OUTPUT = False
visited = []
tmp_example = None
rules = None
edges = []
g = None
k = 0
minimal_data = defaultdict(list)
examples = defaultdict(list)
current_clause = ""
prolog = None
if __name__ == "__main__":
    #faulthandler.enable()
    minimal_data = defaultdict(list)
    examples = defaultdict(list)
    game = sys.argv[1]
    LOG_OUTPUT = True
    t = construct_tree(game, "../games/{}_pl.pl".format(game))
    prolog = Prolog()
    prolog.consult(module_path + "/../background/{}_bk.pl".format(game))
    predicates = list(get_subpredicates(game))
    predicates.sort(reverse=True)
    for predicate in predicates:
        hyp = find_hypothesis("gdl", game, predicate)
        #print(hyp)
        clauses = list(filter(None,hyp.split("\n")))
        for i in range(len(clauses)):
            clause = clauses[i]
            #print("------------------------")
            #print("current clause:", clause)
            other_clauses = clauses[:i] + clauses[i+1:]
            old_len = len(minimal_data)
            tmp_example = None
            if not loop_tree(t.get_root_node(), clause, other_clauses):
                if tmp_example != None:
                    #minimal_data[node.get_next_state()].append(clause)
                    examples[clause.split(":-")[0].split("(")[0].strip()].append(tmp_example)
                    #print("tmp example was used for clause", clause)
                else:
                    raise RuntimeError("no state found for clause " + clause)
    bool(list(prolog.query("unload_file(\"{}/../background/{}_bk.pl\")".format(module_path,game))))

    ### CODE FOR GENERATING THE MINIMAL TREE DATA

    bks_list = [[bk for (bk,pos) in examples[key]] for key in examples.keys()]
    states = [bk for bks in bks_list for bk in bks]
    states = ["\n".join([s for s in state.split("\n") if not s.startswith("does")]) for state in states]
    traces = []
    for state in states:
        trace = find_trace(state,t.get_root_node(),[],[])
        if trace == None:
            raise RuntimeError("this should not happen: no trace found for state\n" + state)
        traces.append(trace)
    #g.view()

    traces_str = []

    for j,(states,moves_list) in enumerate(traces):
        trace_str = ""
        for i in range(len(moves_list)):
            trace_str += states[i].strip() + "\n"
            trace_str += "%%%\n"
            for move,player in moves_list[i]:
                trace_str += "{}:{}\n".format(player,move)
            if i < len(states) - 1:
                trace_str += "---\n"
        trace_str += states[-1]
        traces_str.append(trace_str)
    f = open("../data/validate/{}/minimal/minimal_data.traces".format(game), 'w')
    f.write("######\n".join(set(traces_str)))
    f.close()

    #### CODE FOR GENERATING THE MINIMAL DATA SET

    print("**************************************")
    print("\n------\n".join(set(examples)))
    for subtarget in examples.keys():
        f = open(module_path + "/../data/train/{0}/minimal/claudien/{0}_{1}_train.dat".format(game,subtarget), 'w')
        f.write(open(module_path + "/../data/base/{0}/claudien/{0}_{1}_base.dat".format(game,subtarget)).read().strip() + "\n")
        if subtarget == "terminal":
            examples[subtarget].append((t.get_root_node().get_next_state(),""))
        for (bk,pos) in set(examples[subtarget]):
            f.write("% =========\n")
            f.write(bk.strip() + "\n")
            f.write(pos.strip() + "\n")
        f.close()


    comb_ex = defaultdict(list)
    for key in examples.keys():
        for example in examples[key]:
            comb_ex[key.split('_')[0]].append(example)

    for target in comb_ex.keys():
        f2 = open(module_path + "/../data/train/{0}/minimal/ilasp/{0}_{1}_train.dat".format(game,target), 'w')
        f2.write(open(module_path + "/../data/base/{0}/ilasp/{0}_{1}_base.dat".format(game,target)).read().strip() + "\n\n")
        for (bk,pos) in set(comb_ex[target]):
            f2.write("---\n\nbackground:\n")
            f2.write("\t" + bk.strip().replace(".\n", "\n\t").replace(".","") + "\n\n")
            f2.write("---\n\npositives:\n")
            f2.write("\t" + pos.strip().replace(".\n", "\n\t").replace(".","") + "\n\n")
        f2.write("---")
        f2.close()
