import sys

import os
from collections import defaultdict
sys.path.insert(1,'../')
from ggp_agent.rules import Rules
from utils.gamelib import get_subpredicates
module_path = os.path.dirname(os.path.abspath(__file__))

class Node:
    def __init__(self, state, future_state=None, parent_node=None):
        self.child_nodes = []
        self.state = state
        self.future_state = future_state
        self.parent_node = parent_node
        if not rules.is_terminal(self.state):
            self.moves = rules.get_all_moves_perm(self.state)
        else:
            self.moves = None

    def add_node(self, node):
        self.child_nodes.append(node)

    def add_nodes(self, node_list):
        self.child_nodes.extend(node_list)

    def get_child_nodes(self):
        return self.child_nodes

    def get_state(self):
        return self.state

    def get_future_state(self):
        return self.future_state

    def get_moves(self):
        return self.moves

    def get_goal_example(self):
        return (self.get_state(),rules.get_scores_state(self.get_state()))

    def get_legal_example(self):
        state = self.get_state()
        facts = []
        for moves in self.get_moves():
            facts += [rules.get_clause_name("LEGAL")[0].instantiate([player,move], ".\n") for move,player in moves]
        positives = "".join(set(facts))
        return (state,positives)

    def get_terminal_example(self):
        if rules.is_terminal(self.get_state()):
            return (self.get_state(), "terminal.")
        else:
            return (self.get_state(), "")

    def get_next_example(self, moves):
        (new_state, future) = rules.get_future_state(self.get_state(), moves)
        return (new_state, future)

    def is_leaf(self):
        return len(self.child_nodes) == 0

    def __str__(self):
        return self.state.replace("\n",", ")

class Tree:
    def __init__(self, root_node):
        self.root_node = root_node # de init state

    def get_root_node(self):
        return self.root_node


def construct_tree(game, gdl_path):
    global rules, visited
    visited = []

    rules = Rules(gdl_path)
    init_state = rules.get_init_state()
    root = Node(init_state)
    tree = Tree(root)

    try:
        calculate_next_states(tree, root)
    except KeyboardInterrupt:
        pass

    rules.destroy()

    return tree


def calculate_next_states(tree, node):
    state = node.get_state()
    if rules.is_terminal(state):
        return

    moves_perm = rules.get_all_moves_perm(state)
    for moves in moves_perm:
        new_state = rules.get_next_state(state,moves)
        future_state = rules.get_future_state(state,moves)[1]
        if not (state,moves) in visited:
            visited.append((state,moves))
            new_node = Node(new_state,future_state,node)
            node.add_node(new_node)
            calculate_next_states(tree,new_node)


def loop_tree(node):
    examples["terminal"].append(node.get_terminal_example())
    examples["goal"].append(node.get_goal_example())
    if not node.is_leaf():
        examples["legal"].append(node.get_legal_example())
        for moves in node.get_moves():
            examples["next"].append(node.get_next_example(moves))

    for child in node.get_child_nodes():
        loop_tree(child)




# ---------------------------
LOG_OUTPUT = False
visited = []
rules = None
examples = defaultdict(list)
if __name__ == "__main__":
    game = sys.argv[1]
    t = construct_tree(game, "../games/{}_pl.pl".format(game))
    loop_tree(t.get_root_node())
    print("**************************************")
    print("\n------\n".join(set(examples)))
    for target in examples.keys():
        f2 = open(module_path + "/../data/train/{0}/maximal/ilasp/{0}_{1}_train.dat".format(game,target), 'w')
        f2.write(open(module_path + "/../data/base/{0}/ilasp/{0}_{1}_base.dat".format(game,target)).read().strip() + "\n\n")
        for (bk,pos) in set(examples[target]):
            f2.write("---\n\nbackground:\n")
            f2.write(bk.strip().replace(".", "") + "\n\n")
            f2.write("---\n\npositives:\n")
            f2.write(pos.strip().replace(".", "") + "\n")
        f2.write("---")
        f2.close()

    for subtarget in get_subpredicates(game):
        target = subtarget.split('_')[0]
        f = open(module_path + "/../data/train/{0}/maximal/claudien/{0}_{1}_train.dat".format(game,subtarget), 'w')
        f.write(open(module_path + "/../data/base/{0}/claudien/{0}_{1}_base.dat".format(game,subtarget)).read().strip() + "\n")
        for (bk,pos) in set(examples[target]):
            f.write("% =========\n")
            f.write(bk.strip() + "\n")
            f.write(pos.strip() + "\n")
        f.close()
