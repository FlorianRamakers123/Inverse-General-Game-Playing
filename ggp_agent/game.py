import sys
import os
from random import randrange
from pyswip import Prolog
from player import HumanPlayer,RandomPlayer,ExpertPlayer
from rules import Rules

"""
    Class representing a game host
"""
class Game:
    """
        Create a new instance of a Game
        @param game: the name of the game (not a path)
        @param synchronized_moves:
            true: all players choose a move, then the game state changes.
            false: the current player choses a move, the game updates, then the following player choses a move, and so on.
    """
    def __init__(self,game,synchronized_moves=True):
        # create a new Rules object
        path = "../games/{}_pl.pl".format(game)
        self.rules = Rules(path)

        # initialize the game
        self.state = self.rules.get_init_state() 
        self.update_state()

        # intialize the player information
        self.current_player = 0  
        self.players = []
        self.move_info = {}   # key: Player, value:(f,t) with f the amount of wrong moves and t the total moves performed  
        self.synchronized_moves = synchronized_moves

    
    """
        Add a player to this Game
        @param player: the Player to add to this Game
    """
    def add_player(self,player):
        if len(self.players) >= self.rules.get_max_players():
            raise Exception("Maximum number of players reached")
        
        # find the name of the players in the rules
        facts = self.rules.get_all_facts(self.rules.get_clause_name("ROLE")[0])
        name = facts[len(self.players)].split('(')[1].replace(').','')
        player.set_name(name)

        # add the player to list of players and set the move info
        self.players.append(player)
        self.move_info[player] = (0,0)
        
    """
        Start the game
    """
    def start(self):
        # check if the amount of players is valid
        if len(self.players) != self.rules.get_max_players():
            raise Exception("Invalid amount of players")

        # start the initial state
        log("STARTING GAME")
        log("INITIAL STATE:")
        log(self.state.strip())
        log("----------------------")
        # keep processing the rounds until the terminal state is reached
        while not self.rules.is_terminal(self.state):
            if self.synchronized_moves:
                self.process_all_moves()       
            else:
                self.process_next_move()
            log("----------------------")            
            log("NEW STATE:")
            log(self.state.strip())
            log("----------------------")
        
        log("GAME TERMINATED")
        log("*******************************")
        log("STATISTICS:")
        for player in self.players:
            log("-- {}:".format(player.get_display_name()))
            log("\t- score: {}".format(self.rules.get_score(player.get_name(),self.state)))
            log("\t- total moves: {}".format(self.move_info[player][1]))
            log("\t- wrong moves: {}".format(self.move_info[player][0]))
            log("\t- error rate: {}".format(self.move_info[player][0] / self.move_info[player][1]))


    """
        Process all the moves of the players at once
    """
    def process_all_moves(self):
        # get all the moves from the players
        moves = [(self.get_next_move(player),player.get_name()) for player in self.players]
        for i,(move,player) in enumerate(moves):
            log("{}: {}".format(self.players[i].get_display_name(),move))

        # calculate the next state
        self.state = self.rules.get_next_state(self.state,moves)
        self.update_state()


    """
        Get the next move from the player
        @param player: the player to retrieve the move from
    """
    def get_next_move(self,player):
        move = player.get_next_move(self.state)
        (f,t) = self.move_info[player]
        # update the total amount of moves
        new_t = t+1
        new_f = f
        
        # check if the move is legal for that player
        if not self.rules.is_legal_move(player.get_name(),move,self.state):
            # if the player thinks it has no moves then the game will pick a random move for the player
            log("{} ATTEMPTED TO DO ILLEGAL MOVE {}".format(player.get_display_name(),move))
            new_f += 1  # update the total amount of wrong moves
            moves = self.rules.get_all_moves(player.get_name(),self.state)
            if not moves:
                raise Exception("there are no possible moves for player {}".format(player.get_name()))
            move = moves[randrange(0,len(moves))]

        self.move_info[player] = (new_f,new_t)
        return move

    """
        Process the move of the next player
    """
    def process_next_move(self):     
        player = self.players[self.current_player]
        move = self.get_next_move(player)
        log("{}: {}".format(player.get_display_name(),move))
        self.state = self.rules.get_next_state(self.state,[(move,player.get_name())])
        self.update_state()
        self.current_player = (self.current_player + len(moves)) % len(self.players)

    """
        Update the state file
    """
    def update_state(self):
        f = open("state.pl",'w')
        f.write(self.state)
        f.close()

    """
        Clean up all generated files
    """
    def destroy(self):
        os.remove("state.pl")
        for player in self.players:
            player.destroy()
        self.rules.destroy()

# set this to False if you don't want log output
LOG_OUTPUT = True
def log(m):
    global LOG_OUTPUT
    if LOG_OUTPUT:
        print(m)

game_name = sys.argv[1] 
player_config = sys.argv[2]
g = Game(game_name)
if len(sys.argv) > 3 and sys.argv[3] == "-ns":
    g = Game(game_name, False)
path = "../games/{}_pl.pl".format(game_name)
for player in player_config.split(","):
    if player == "H":
        g.add_player(HumanPlayer(path))
    elif player == "R":
        g.add_player(RandomPlayer(path))
    elif player == "E":
        g.add_player(ExpertPlayer(path))
    else:
        raise Exception("player option '{}' is not valid".format(player))
g.start()
g.destroy()
"""
try:
    g.start()
except Exception as e:
    try:
        
        g.destroy()
    except:
        pass

"""    
