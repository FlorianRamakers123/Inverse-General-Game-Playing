from collections import defaultdict
import itertools
from pyswip import Prolog
from pyswip.prolog import PrologError
import os

module_path = os.path.dirname(os.path.abspath(__file__))

"""
    Class that represents the rules for a game competitions
    Different users may use different rules
"""
class Rules:
    """
        Create new instance of the Rules class
        @param gdl_file: the path to the prolog rules
    """
    def __init__(self,gdl_file):
        # create the prolog environment
        self.p = Prolog()
        self.gdl_file = gdl_file
        self.gdl = list(filter(None,open(gdl_file).read().split("\n")))
        # read in the info_file
        info_file = module_path + "/rule_info/{}.info".format(gdl_file.split('/')[-1].split('.')[0][:-3])
        info_lines = open(info_file).readlines()
        self.info = {}
        for info_line in info_lines:
            parts = info_line.split("=")
            preds = parts[1].split(";")
            self.info[parts[0].strip()] = [Predicate.from_str(pred.strip()) for pred in preds]

        self.max_player_count = len(self.get_all_facts(str(self.get_clause_name("ROLE")[0])))

    """
        Get the maximum amount of players allowed
    """
    def get_max_players(self):
        return self.max_player_count

    """
        Get the clause name for a specific GDL predicate
        @param name: the name of the GDL predicate
            Options are: LEGAL, DOES, NEXT, INIT, ROLE
    """
    def get_clause_name(self,name):
        return self.info[name]

    """
        Retrieve all the facts of the predicate with the given name
        @param pred: the name of the predicate to retrieve all facts from
    """
    def get_all_facts(self,pred):
        return [line for line in self.gdl if line.startswith(str(pred)) and not ':-' in line]

    """
        Get the initial state of the game
    """
    def get_init_state(self):
        state = ""
        for predicate in self.get_clause_name("INIT"):
            state += '\n'.join(["true" + s[4:] for s in self.get_all_facts(str(predicate))]) + '\n'
        return state

    """
        Check whether the given move is valid for the given player in the given state
        @param player: the player to check
        @param move: the move to check
        @param state: the states in which the moves is checked to be valid
    """
    def is_legal_move(self,player,move,state):
        return self.query(self.get_clause_name("LEGAL")[0].instantiate([player, move]),state)

    """
        Calculate the score of the given player in the given state
        @param player: the player to calculate the score from
        @param state: the state to calculate the score in
    """
    def get_score(self,player,state, load_background=True):
        result = self.query("goal({},A)".format(player),state,load_background)
        # result may be empty because the calculation of the goal predicate might rely on the the move of others
        # if these moves are not yet known then the predicate fails to query
        points = [int(r['A']) for r in result]
        if points:
            return max(points)
        else:
            return None

    """
        Calculate the score of all the players in the given state
        @param state: the state to calculate the scores in
    """
    def get_all_scores(self,state,load_background=True):
        return [(self.get_score(player,state,load_background), player) for player in self.get_all_player_names()]


    """
        Get the scores in the given state, expressed with the goal/2 predicate
        @param state: the state to calculate the scores in
    """
    def get_scores_state(self,state,load_background=True):
        ret_state = ""
        scores = self.get_all_scores(state,load_background)
        for score,player in scores:
            ret_state += Predicate.from_str("goal/2").instantiate([player,str(score)]) + '.\n'
        return ret_state

    """
        Calculate all the legal moves for the given player in the given state
        @param player: the player to retrieve all legal moves from
        @param state: the state to query in
    """
    def get_all_moves(self,player,state):
        result = self.query(self.get_clause_name("LEGAL")[0].instantiate([player]),state)
        return [str(r['A']) for r in result]

    def get_all_player_names(self):
        player_names = []
        facts = self.get_all_facts(self.get_clause_name("ROLE")[0])
        for fact in facts:
            player_names.append(fact.split('(')[1].replace(').',''))
        return player_names

    """
        Calculate all the permutation of the legal moves for all players
        @param state: the state to query in
    """
    def get_all_moves_perm(self,state):
        moves = []
        player_names = self.get_all_player_names()
        for player_name in player_names:
            result = [(str(r['A']), player_name) for r in self.query(self.get_clause_name("LEGAL")[0].instantiate([player_name]),state)]
            moves.append(result)
        return [list(a) for a in itertools.product(*moves)]

    """
        Check if the given state is the terminal state
        @param the state to check
    """
    def is_terminal(self,state,load_background=True):
        return bool(self.query("terminal",state,load_background))

    """
        Query the given predicate in the given state
    """
    def query(self,query,state,load_background=True):
        # write the state to a temporary file
        # we use the id of the Rules object so we can differentatiate the temp file from the other files
        tmp_file = str(id(self)) + ".pl"
        f = open(tmp_file,'w')
        f.write(state)
        f.close()
        list(self.p.query("style_check(-discontiguous)"))
        list(self.p.query("style_check(-singleton)"))
        if load_background:
            self.p.consult(self.gdl_file)
        self.p.consult(tmp_file)
        result = []
        try:
            result = list(self.p.query(query))
        except PrologError as e:
            pass
        bool(list(self.p.query("unload_file(\"{}\")".format(tmp_file))))
        if load_background:
            bool(list(self.p.query("unload_file(\"{}\")".format(self.gdl_file))))
        return result

    """
        Generate an example, based on the state and moves
        @param state: the current state
        @param future_state: the future state, predicted by another Rules object
        @param moves: a list of tuples (move,player)
        @param scores: the scores in the current state, as stated by another Rules object
        @return: a positive example if the future state, calculated by this Rules object, matches the future new_state
                 a negative example otherwise
    """
    def generate_example(self, state, moves, future_state, scores):
        examples = []

        (state,this_future_state) = self.get_future_state(state,moves)
        if future_state == None and this_future_state != None:
            examples.append(("terminal", state, "terminal.\n"))

        for move,player in moves:
            if not self.is_legal_move(player,move,state):
                examples.append(("legal", state, self.get_clause_name("LEGAL")[0].instantiate([player,move]) + '.\n'))


        new_state = self.get_next_state(state,moves)
        for score,player in set(scores).difference(set(self.get_all_scores(new_state))):
            examples.append(("goal", new_state, Predicate.from_str("goal/2").instantiate([player,str(score)]) + '.\n'))

        tfs_parts = this_future_state.split("\n")
        fs_parts = list(filter(None,future_state.split("\n")))

        if not fs_parts:
            examples.append(("next",state,"\n".join(tfs_parts)))

        for tfs_part in tfs_parts:
            if tfs_part in fs_parts:
                fs_parts.remove(tfs_part)

        if fs_parts:
            examples.append(("next", state,"\n".join(fs_parts)))


        return examples

    """
        Get the future state, based on the given moves
        @param state: the state to calculate the futurue state from
        @param moves: a list of tuples (move,player)
    """
    def get_future_state(self,state,moves,load_background=True):
        if self.is_terminal(state,load_background):
            return (state,None)
        for move,player in moves:
            state += self.get_clause_name("DOES")[0].instantiate([player,move]) + '.\n'

        new_state = ""
        for next in self.get_clause_name("NEXT"):
            # we assume here that if the arity is 1, the player variable is not needed
            # when the arity is higher then we assume the player is the first argument
            if next.get_arity() == 1:
                result = self.query(next.instantiate(),state, load_background)
                line = '\n'.join(set([str(next) + "({}).".format(r['A']) for r in result if not '_' in str(r['A'])])) + '\n'
                if not line in new_state:
                    new_state += line
            else:
                for _,player in moves:
                    result = self.query(next.instantiate([player]),state, load_background)
                    line = '\n'.join(set([str(next) + "({},{}).".format(player,r['A']) for r in result if not '_' in str(r['A'])])) + '\n'
                    if not line in new_state:
                        new_state += line
        return (state,new_state)


    """
        Get the next state, based on the given moves
        @param state: the state to calculate the next state from
        @param moves: a list of tuples (move,player)
    """
    def get_next_state(self,state,moves):
        if self.is_terminal(state):
            return None

        for move,player in moves:
            state += self.get_clause_name("DOES")[0].instantiate([player,move]) + '.\n'

        new_state = ""
        for next in self.get_clause_name("NEXT"):
            # we assume here that if the arity is 1, the player variable is not needed
            # when the arity is higher then we assume the player is the first argument
            if next.get_arity() == 1:
                result = self.query(next.instantiate(),state)
                line = '\n'.join(set(["true" + str(next)[4:] + "({}).".format(r['A']) for r in result])) + '\n'
                if not line in new_state:
                    new_state += line
            else:
                for _,player in moves:
                    result = self.query(next.instantiate([player]),state)
                    line = '\n'.join(set(["true" + str(next)[4:] + "({},{}).".format(player,r['A']) for r in result])) + '\n'
                    if not line in new_state:
                        new_state += line
        return new_state

    """
        Check if, given a start state and some moves, new_state is reached according to this Rules instance
        @param state: the state to start from
        @param moves: the moves to perform in the start state
        @param new_state: the state that has been reached by performing the specified moves in the given start state
        @param future_scores: the scores of the players in the next state
        @param terminal: boolean indicating whether state is an end state according to the hypothesis
    """
    def check_state(self,state,moves,new_state,future_scores,terminal):
        new_state2 = self.get_next_state(state,moves)
        causes = []
        terminal2 = self.is_terminal(state)
        if terminal != terminal2:
            causes.append("terminal")





        if set(self.get_all_scores(new_state2)) != set(future_scores):
            causes.append("goal")

        return causes


    """
        Clean up the generated files
    """
    def destroy(self):
        try:
            os.remove(str(id(self)) + ".pl")
        except:
            pass


"""
    Class that represents a predicate
"""
class Predicate:
    """
        Create a new instance of the Predicate class
        @param name: the name of the predicate
        @param arity: the arity of the predicate
    """
    def __init__(self,name,arity):
        self.name = name
        self.arity = arity

    """
        Create a Predicate object from a string 'pred/arity'
    """
    @staticmethod
    def from_str(s):
        parts = s.split('/')
        return Predicate(parts[0],int(parts[1]))

    """
        Define the string representation of this Predicate
    """
    def __str__(self):
        return self.name

    """
        Get the arity of this Predicate
    """
    def get_arity(self):
        return self.arity

    """
        Instantiate this predicate with arguments
        @param args: the arguments to instantiate this Predicate with
        @param ext: the extension to add after the instantiation (ex. '.' for prolog)
    """
    def instantiate(self,args=[],ext=''):
        if len(args) > self.arity:
            raise Exception("{}: argument count ({}) did not match arity ({}): {}".format(self.name,len(args),self.arity,args))
        if len(args) < self.arity:
            args += [chr(i+65) for i in range(0,self.arity - len(args))]

        return "{}({}){}".format(self.name,','.join(args),ext)
