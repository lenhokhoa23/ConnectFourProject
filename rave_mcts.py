import random
import time
import math
from copy import deepcopy
from queue import Queue
from random import choice
from meta import GameMeta, MCTSMeta
from ConnectState import ConnectState
from mcts_mark_2 import Node, Connect4MCTSAgent

class RaveNode(Node):
    """
    Node for the MCTS with RAVE (Rapid Action Value Estimation). This node stores
    statistics for the associated game position, including UCT (Upper Confidence Bound)
    and AMAF (All Moves Are Fair) for better decision-making.
    """

    def __init__(self, move: tuple = None, parent: object = None):
        super(RaveNode, self).__init__(move, parent)

    @property
    def value(self, explore: float = MCTSMeta.EXPLORATION, rave_const: float = MCTSMeta.RAVE_CONST) -> float:
        """
        Calculate the UCT value of this node relative to its parent, incorporating the RAVE statistics.
        """
        # If the node is unvisited, set its value as infinity unless explore is 0
        if self.N == 0:
            return 0 if explore == 0 else GameMeta.INF
        else:
            # RAVE valuation: combining UCT and AMAF (All Moves Are Fair)
            alpha = max(0, (rave_const - self.N) / rave_const)
            UCT = self.Q / self.N + explore * math.sqrt(2 * math.log(self.parent.N) / self.N)
            AMAF = self.Q_RAVE / self.N_RAVE if self.N_RAVE != 0 else 0
            return (1 - alpha) * UCT + alpha * AMAF


class RaveMctsAgent(Connect4MCTSAgent):

    def __init__(self, state=ConnectState()):
        self.root_state = deepcopy(state)
        self.root = RaveNode()
        self.run_time = 0
        self.node_count = 0
        self.num_rollouts = 0

    def set_gamestate(self, state: ConnectState) -> None:
        """
        Set the root_state of the tree to the passed gamestate, this clears all
        the information stored in the tree since none of it applies to the new
        state.
        """
        self.root_state = deepcopy(state)
        self.root = RaveNode()

    def move(self, move: tuple) -> None:
        """
        Make the passed move and update the tree accordingly.
        """
        if move in self.root.children:
            child = self.root.children[move]
            child.parent = None
            self.root = child
            self.root_state.move(child.move)
            return

        self.root_state.move(move)
        self.root = RaveNode()

    def search(self, time_budget: int) -> None:
        """
        Perform MCTS search for a specified amount of time in seconds.
        """
        start_time = time.time()
        num_rollouts = 0

        while time.time() - start_time < time_budget:
            node, state = self.select_node()
            outcome, black_cols, white_cols = self.roll_out(state)  # <-- FIXED
            self.backup(node, state.to_play, outcome, black_cols, white_cols)  # <-- FIXED
            num_rollouts += 1

        self.run_time = time.time() - start_time
        self.node_count = self.tree_size()
        self.num_rollouts = num_rollouts

    def select_node(self) -> tuple:
        """
        Select a node in the tree to perform a single simulation from.
        """
        node = self.root
        state = deepcopy(self.root_state)

        while len(node.children) != 0:
            max_value = max(node.children.values(), key=lambda n: n.value).value
            max_nodes = [n for n in node.children.values() if n.value == max_value]
            node = choice(max_nodes)
            state.move(node.move)

            if node.N == 0:
                return node, state

        if self.expand(node, state):
            node = choice(list(node.children.values()))
            state.move(node.move)

        return node, state
    
    @staticmethod
    def expand(parent: RaveNode, state: ConnectState) -> bool:
        """
        Generate children for the given node based on legal moves and add them to the tree.
        """
        children = []
        if state.game_over():
            return False

        for move in state.get_legal_moves():
            children.append(RaveNode(move, parent))

        parent.add_children(children)
        return True
    
    @staticmethod
    def roll_out(state: ConnectState) -> tuple:
        """
        Simulate a random game except for the critical cells, then return the winner.
        Also returns the critical points for each player.
        """
        black_cols = [] 
        white_cols = [] 
        moves = state.get_legal_moves()
        while not state.game_over():
            if not moves:
                break
            move = random.choice(moves)
            state.move(move)
            if state.height[move] < 0:
                moves.remove(move)            
            current_player = state.to_play
            if current_player == GameMeta.PLAYERS['one']:
                black_cols.append(move)
            else:
                white_cols.append(move)

        return state.get_outcome(), black_cols, white_cols

    def backup(self, node: RaveNode, turn: int, outcome: int, black_cols: list, white_cols: list) -> None:
        """
        Update the statistics of nodes along the path from the leaf to the root to reflect the outcome.
        """
        reward = 0 if outcome == turn else 1
        while node is not None:
            if turn == GameMeta.PLAYERS['one']:
                for col in black_cols:
                    if col in node.children:
                        node.children[col].Q_RAVE += (1 - reward)
                        node.children[col].N_RAVE += 1
            else:
                for col in white_cols:
                    if col in node.children:
                        node.children[col].Q_RAVE += (1 - reward)
                        node.children[col].N_RAVE += 1
            node.N += 1
            node.Q += reward
            node = node.parent
            if outcome == GameMeta.OUTCOMES['draw']:
                reward = 0
            else:
                reward = 1 - reward
            turn = (GameMeta.PLAYERS['two'] if turn == GameMeta.PLAYERS['one'] else GameMeta.PLAYERS['one'])
        
    def best_move(self) -> tuple:
        """
        Return the best move according to the most simulations, breaking ties randomly.
        """
        if self.root_state.game_over():
            return -1  # Indicate that the game is over

        max_value = max(self.root.children.values(), key=lambda n: n.N).N
        max_nodes = [n for n in self.root.children.values() if n.N == max_value]
        bestchild = choice(max_nodes)
        return bestchild.move
    

class DecisiveMoveMctsAgent(RaveMctsAgent):
    """
    Decisive Move MCTS Agent for Connect Four. Prioritizes playing critical moves first.
    """
    def roll_out(self, state: ConnectState) -> tuple:
        black_cols = []
        white_cols = []

        # Single call to get_legal_moves
        moves = state.get_legal_moves()

        # We track "good_moves" for the current player, and "good_opponent" for the other
        # but we also need a 'done' flag in each iteration
        while not state.game_over() and moves:
            done = False
            to_play = state.to_play

            # Build a list of "safe moves"
            safe_moves = [m for m in moves if not state.would_lose(m, to_play)]

            if safe_moves:
                chosen_move = random.choice(safe_moves)
                done = True
            else:
                # If no safe moves exist, pick random
                chosen_move = random.choice(moves)

            current_player = state.to_play
            state.move(chosen_move)

            if state.height[chosen_move] < 0:
                moves.remove(chosen_move)

            # Record the column for RAVE
            if current_player == GameMeta.PLAYERS['one']:
                black_cols.append(chosen_move)
            else:
                white_cols.append(chosen_move)

        outcome = state.get_outcome()
        return outcome, black_cols, white_cols

class LGRMctsAgent(RaveMctsAgent):
    """
    LGR (Last Game Reply) MCTS Agent for Connect Four. Uses previous replies to guide moves.
    """
    def __init__(self, state: ConnectState = ConnectState()):
        super().__init__(state)
        self.black_reply = {}
        self.white_reply = {}

    def set_gamestate(self, state: ConnectState) -> None:
        super().set_gamestate(state)
        self.white_reply = {}
        self.black_reply = {}

    def roll_out(self, state: ConnectState) -> tuple:
        black_cols = []
        white_cols = []

        moves = state.get_legal_moves()

        first_player = state.to_play
        if first_player == GameMeta.PLAYERS['one']:
            current_reply = self.black_reply
            other_reply = self.white_reply
        else:
            current_reply = self.white_reply
            other_reply = self.black_reply

        last_move = None

        while not state.game_over() and moves:
            # If we have a "last good reply" to the opponent's last move:
            if last_move in current_reply:
                chosen_move = current_reply[last_move]
                # If that chosen move is no longer legal, or random fails, pick random
                if (chosen_move not in moves) or (random.random() > MCTSMeta.RANDOMNESS):
                    chosen_move = random.choice(moves)
            else:
                chosen_move = random.choice(moves)

            current_player = state.to_play
            state.move(chosen_move)
            if state.height[chosen_move] < 0:
                moves.remove(chosen_move)

            # Record columns
            if current_player == GameMeta.PLAYERS['one']:
                black_cols.append(chosen_move)
            else:
                white_cols.append(chosen_move)

            # Swap which reply table is "current" vs "other"
            current_reply, other_reply = other_reply, current_reply
            last_move = chosen_move

        outcome = state.get_outcome()

        # If black (player one) wins, we store "last good replies" for black
        if outcome == GameMeta.PLAYERS["one"]:
            # If black started, black_moves were black_cols
            # We'll pair each white_cols[i] with black_cols[i+offset] if possible
            offset = (1 if first_player == GameMeta.PLAYERS["one"] else 0)
            skip = (1 if state.to_play == GameMeta.PLAYERS["one"] else 0)
            for i in range(len(white_cols) - skip):
                w_move = white_cols[i]
                # black_cols[i + offset] might exist
                if i + offset < len(black_cols):
                    self.black_reply[w_move] = black_cols[i + offset]
        elif outcome == GameMeta.PLAYERS["two"]:
            offset = (1 if first_player == GameMeta.PLAYERS["two"] else 0)
            skip = (1 if state.to_play == GameMeta.PLAYERS["two"] else 0)
            for i in range(len(black_cols) - skip):
                b_move = black_cols[i]
                if i + offset < len(white_cols):
                    self.white_reply[b_move] = white_cols[i + offset]

        return outcome, black_cols, white_cols

class PoolRaveMctsAgent(RaveMctsAgent):
    """
    Pool RAVE MCTS Agent for Connect Four. Uses a pool of high-impact moves for each player.
    """
    def __init__(self, state: ConnectState = ConnectState()):
        super().__init__(state)
        self.black_rave = {}
        self.white_rave = {}

    def set_gamestate(self, state: ConnectState) -> None:
        super().set_gamestate(state)
        self.black_rave = {}
        self.white_rave = {}

    def roll_out(self, state: ConnectState) -> tuple:
        black_cols = []
        white_cols = []

        moves = state.get_legal_moves()

        def black_score(col): return self.black_rave.get(col, 0)
        def white_score(col): return self.white_rave.get(col, 0)

        black_sorted = sorted(moves, key=black_score, reverse=True)
        white_sorted = sorted(moves, key=white_score, reverse=True)
        black_pool = black_sorted[:MCTSMeta.POOLRAVE_CAPACITY]
        white_pool = white_sorted[:MCTSMeta.POOLRAVE_CAPACITY]

        while not state.game_over() and moves:
            current_player = state.to_play
            if current_player == GameMeta.PLAYERS["one"]:
                col = None
                if black_pool:
                    col = random.choice(black_pool)
                if (not col) or (col not in moves) or (random.random() > MCTSMeta.RANDOMNESS):
                    col = random.choice(moves)
            else:
                col = None
                if white_pool:
                    col = random.choice(white_pool)
                if (not col) or (col not in moves) or (random.random() > MCTSMeta.RANDOMNESS):
                    col = random.choice(moves)

            state.move(col)
            if state.height[col] < 0:
                moves.remove(col)

            if current_player == GameMeta.PLAYERS["one"]:
                black_cols.append(col)
            else:
                white_cols.append(col)

        outcome = state.get_outcome()

        if outcome == GameMeta.PLAYERS["one"]:
            for col in black_cols:
                self.black_rave[col] = self.black_rave.get(col, 0) + 1
            for col in white_cols:
                self.white_rave[col] = self.white_rave.get(col, 0) - 1
        elif outcome == GameMeta.PLAYERS["two"]:
            for col in white_cols:
                self.white_rave[col] = self.white_rave.get(col, 0) + 1
            for col in black_cols:
                self.black_rave[col] = self.black_rave.get(col, 0) - 1
        else:
            pass

        return outcome, black_cols, white_cols