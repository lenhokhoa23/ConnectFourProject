import time
import random
from copy import deepcopy
import sys

from meta import GameMeta, MCTSMeta
from ConnectState import ConnectState

class Connect4Interface:
    """
    A GTP-like interface for Connect Four, wrapping an MCTS-based agent + ConnectState.
    It provides:
      - gtp_time([movetime])
      - gtp_boardsize([size]) (mostly unused for standard Connect Four)
      - gtp_clear([])
      - gtp_winner([])
      - gtp_genmove([color])
      - gtp_play([color, move_str])
      - (Optional) gtp_show([])
    """
    def __init__(self, agent_class, movetime=1.0):
        """
        agent_class: e.g. Connect4MCTSAgent, RaveMctsAgent, etc.
        movetime: default time for each move (can be used by agent if the agent is time-based).
        """
        self.game = ConnectState()  # The Connect Four board
        self.AgentClass = agent_class
        self.agent = agent_class(deepcopy(self.game))  # An instance of the agent
        self.movetime = float(movetime)

    def gtp_time(self, args):
        """
        E.g. interface.gtp_time([movetime])
        We'll store this as self.movetime. 
        """
        if args:
            self.movetime = float(args[0])

    def gtp_boardsize(self, args):
        """
        For Connect Four, the standard board is 6x7. 
        The snippet calls gtp_boardsize([size]) – we can ignore or store if needed.
        """
        pass

    def gtp_clear(self, args):
        """
        Clear the board and re-initialize the agent.
        """
        self.game = ConnectState()
        self.agent = self.AgentClass(deepcopy(self.game))

    def gtp_winner(self, args):
        """
        Return e.g. [True, "b"] if black (player one) has won, 
                    [True, "w"] if white (player two) has won,
                    [True, "draw"] if draw,
                    [False, "none"] if game not over.
        The snippet checks interface.gtp_winner([])[1].
        We'll interpret 'b' as Player One, 'w' as Player Two for consistency with the snippet's usage.
        """
        outcome = self.game.get_outcome()
        if outcome == GameMeta.OUTCOMES['none']:  # Game is ongoing
            return [False, "none"]
        elif outcome == GameMeta.OUTCOMES['one']:  # Player one (b)
            return [True, "b"]
        elif outcome == GameMeta.OUTCOMES['two']:  # Player two (w)
            return [True, "w"]
        else:
            return [True, "draw"]  # e.g. a tie or something else

    def gtp_genmove(self, args):
        """
        The snippet does:
            move = interface.gtp_genmove([color])  # color is 'b' or 'w'
        We return (bool, move_str, rollouts_count)
          - bool: True if a valid move, False if pass/no move
          - move_str: The chosen column as string
          - rollouts_count: how many rollouts used (optional)
        We'll do the agent search -> best_move -> apply it in agent & self.game
        """
        if not args:
            return (False, "", 0)
        color = args[0]  # 'b' or 'w', but in Connect4, we typically track current player in self.agent

        # Let the agent search with the self.movetime as an integer or float 
        # (depending if your agent interprets it as #rollouts or #seconds).
        before_rollouts, _, _ = self.agent.statistics()  # check stats prior
        self.agent.search(int(self.movetime))
        after_rollouts, _, _ = self.agent.statistics()
        used_rollouts = after_rollouts - before_rollouts

        mv = self.agent.best_move()
        if mv == -1:
            # No legal move or game is over
            return (False, "", used_rollouts)

        # Apply move to agent and board
        self.agent.move(mv)
        self.game.move(mv)

        return (True, str(mv), used_rollouts)

    def gtp_play(self, args):
        """
        The snippet does interface.gtp_play([color, move_str]).
        We parse move_str -> int column, apply it in agent & game.
        """
        if len(args) < 2:
            return
        # color = args[0] # 'b' or 'w'
        move_str = args[1]
        try:
            col = int(move_str)
        except:
            return

        self.agent.move(col)
        self.game.move(col)

    def gtp_show(self, args):
        """
        Optional. Return [False, board_str] for debugging.
        """
        board_str = ""
        for row in range(GameMeta.ROWS):
            for col in range(GameMeta.COLS):
                val = self.game.board[row][col]
                if val == GameMeta.PLAYERS['one']:
                    board_str += "b"
                elif val == GameMeta.PLAYERS['two']:
                    board_str += "w"
                else:
                    board_str += "."
            board_str += "\n"
        return [False, board_str]
