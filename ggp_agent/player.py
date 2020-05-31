from pyswip import Prolog
from rules import Rules
from random import randrange

"""
    Class that represents a player
"""
class Player:
    """
        Create a new instance of a Player
        @param rules: the path to the gdl file that is used for this player
    """
    def __init__(self,rules):
        self.name = None
        self.rules = Rules(rules)

    """
        Get the associated prolog constant that is used to query this player
    """
    def get_name(self):
        return self.name

    """
        Get the name that is used to display this Player in the terminal
    """
    def get_display_name(self):
        return "[{}] {}".format(self.get_name(),self.get_display_name_())

    """
        Override this method when defining a new Player!!!!
    """    
    def get_display_name_(self):
        raise NotImplementedError()
        
    """
        Set the associated prolog constant that is used to query this player
        @param name: the associated prolog constant to be used in the queries
    """
    def set_name(self,name):
        self.name = name

    """
        Get the next move of the player
        @param state: the current state of the game
    """
    def get_next_move(self,state):
        raise NotImplementedError()

    """
        Destroy this player
    """
    def destroy(self):
        self.rules.destroy()
"""
    Class that represents a human player
"""
class HumanPlayer(Player):

    """
        Get the name that is used to display this Player in the terminal
    """
    def get_display_name_(self):
        return "USER"

    """
        Get the next move of the player
        @param state: the current state of the game
    """
    def get_next_move(self,state):
        return input("Please enter the next move: ")

    """
        Destroy this player
    """
    def destroy(self):
        pass

"""
    Class that represents a player performing random moves
"""
class RandomPlayer(Player):

    """
        Create a new instance of the RandomPlayer
    """
    def __init__(self,rules):
        super(RandomPlayer, self).__init__(rules)
        # we assign a unique id to each random player 
        self.id = str(randrange(0, 3521))

    """
        Get the name that is used to display this Player in the terminal
    """
    def get_display_name_(self):
        return "PLAYER{}".format(self.id,self.get_name()) 

    """
        Get the next move of the player
        @param state: the current state of the game
    """
    def get_next_move(self,state):
        moves = self.rules.get_all_moves(self.get_name(),state)
        return moves[randrange(0,len(moves))]

"""
    Class that represents a player that performs better (but still not very good) than the RandomPlayer
"""
class ExpertPlayer(Player):
    """
        Get the name that is used to display this Player in the terminal
    """
    def get_display_name_(self):
        return "HAROLD" 

    """
        Get the next move of the player
    """
    def get_next_move(self,state):
        best_points = -99999999999999
        best_move = None
        for move in self.rules.get_all_moves(self,state):
            new_state = self.rules.get_next_state(state,[(move,self.get_name())])
            points = self.rules.get_score(self.get_name(),new_state)
            if points == None:
               continue 
            if points > best_points:
                best_points = points
                best_move = move

        if best_move != None:
            return best_move
        else:
            # return a random move because we cannot calculate the best move in the current state
            moves = self.rules.get_all_moves(self,state)
            return moves[randrange(0,len(moves))]
