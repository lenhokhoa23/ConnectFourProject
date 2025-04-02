import random
import time
import math
from copy import deepcopy
from queue import Queue
from random import choice
from meta import GameMeta, MCTSMeta
from ConnectState import ConnectState

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


class RaveMctsAgent(UctMctsAgent):

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
            outcome, black_rave_pts, white_rave_pts = self.roll_out(state)
            self.backup(node, state.to_play, outcome, black_rave_pts, white_rave_pts)
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

        # Descend to the maximum value node, breaking ties randomly
        while len(node.children) != 0:
            max_value = max(node.children.values(), key=lambda n: n.value).value
            max_nodes = [n for n in node.children.values() if n.value == max_value]
            node = choice(max_nodes)
            state.move(node.move)

            # If the node hasn't been visited, return it
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
        moves = state.get_legal_moves()
        while not state.game_over():
            state.move(random.choice(moves))
            moves.remove(state.last_played[1])

        black_rave_pts = []
        white_rave_pts = []

        # Record positions of critical cells
        for x in range(GameMeta.ROWS):
            for y in range(GameMeta.COLS):
                if state.board[x][y] == GameMeta.PLAYERS['one']:
                    black_rave_pts.append((x, y))
                elif state.board[x][y] == GameMeta.PLAYERS['two']:
                    white_rave_pts.append((x, y))

        return state.get_outcome(), black_rave_pts, white_rave_pts

    def backup(self, node: RaveNode, turn: int, outcome: int, black_rave_pts: list, white_rave_pts: list) -> None:
        """
        Update the statistics of nodes along the path from the leaf to the root to reflect the outcome.
        """
        reward = 0 if outcome == turn else 1

        while node is not None:
            # Update RAVE statistics for the current player
            if turn == GameMeta.PLAYERS['one']:
                for point in black_rave_pts:
                    if point in node.children:
                        node.children[point].Q_RAVE += -reward
                        node.children[point].N_RAVE += 1
            else:
                for point in white_rave_pts:
                    if point in node.children:
                        node.children[point].Q_RAVE += -reward
                        node.children[point].N_RAVE += 1

            node.N += 1
            node.Q += reward
            turn = GameMeta.PLAYERS['two'] if turn == GameMeta.PLAYERS['one'] else GameMeta.PLAYERS['one']
            reward = -reward
            node = node.parent
    
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
        moves = state.get_legal_moves()
        good_moves = moves.copy()
        good_opponent_moves = moves.copy()
        to_play = state.to_play

        while state.game_over() == False:
            done = False
            while len(good_moves) > 0 and not done:
                move = choice(good_moves)
                good_moves.remove(move)
                if not state.would_lose(move, to_play):
                    state.move(move)
                    moves.remove(move)
                    if move in good_opponent_moves:
                        good_opponent_moves.remove(move)
                    done = True

            if not done:
                move = choice(moves)
                state.move(move)
                moves.remove(move)
                if move in good_opponent_moves:
                    good_opponent_moves.remove(move)

            good_moves, good_opponent_moves = good_opponent_moves, good_moves

        black_rave_pts = []
        white_rave_pts = []

        for x in range(GameMeta.ROWS):
            for y in range(GameMeta.COLS):
                if state.board[x][y] == GameMeta.PLAYERS["one"]:
                    black_rave_pts.append((x, y))
                elif state.board[x][y] == GameMeta.PLAYERS["two"]:
                    white_rave_pts.append((x, y))

        return state.get_outcome(), black_rave_pts, white_rave_pts


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
        moves = state.get_legal_moves()
        first = state.to_play
        if first == GameMeta.PLAYERS["one"]:
            current_reply = self.black_reply
            other_reply = self.white_reply
        else:
            current_reply = self.white_reply
            other_reply = self.black_reply
        black_moves = []
        white_moves = []
        last_move = None

        while state.game_over() == False:
            if last_move in current_reply:
                move = current_reply[last_move]
                if move not in moves or random() > MCTSMeta.RANDOMNESS:
                    move = choice(moves)
            else:
                move = choice(moves)
            if state.to_play == GameMeta.PLAYERS["one"]:
                black_moves.append(move)
            else:
                white_moves.append(move)

            current_reply, other_reply = other_reply, current_reply
            state.move(move)
            moves.remove(move)
            last_move = move

        black_rave_pts = []
        white_rave_pts = []

        for x in range(GameMeta.ROWS):
            for y in range(GameMeta.COLS):
                if state.board[x][y] == GameMeta.PLAYERS["one"]:
                    black_rave_pts.append((x, y))
                elif state.board[x][y] == GameMeta.PLAYERS["two"]:
                    white_rave_pts.append((x, y))

        offset = 0
        skip = 0
        if state.get_outcome() == GameMeta.PLAYERS["one"]:
            if first == GameMeta.PLAYERS["one"]:
                offset = 1
            if state.to_play == GameMeta.PLAYERS["one"]:
                skip = 1
            for i in range(len(white_moves) - skip):
                self.black_reply[white_moves[i]] = black_moves[i + offset]
        else:
            if first == GameMeta.PLAYERS["two"]:
                offset = 1
            if state.to_play == GameMeta.PLAYERS["two"]:
                skip = 1
            for i in range(len(black_moves) - skip):
                self.white_reply[black_moves[i]] = white_moves[i + offset]

        return state.get_outcome(), black_rave_pts, white_rave_pts


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
        moves = state.get_legal_moves()
        black_rave_moves = sorted(self.black_rave.keys(), key=lambda cell: self.black_rave[cell])
        white_rave_moves = sorted(self.white_rave.keys(), key=lambda cell: self.white_rave[cell])
        black_pool = []
        white_pool = []

        # Fill the pool with high-impact moves
        i = 0
        while len(black_pool) < MCTSMeta.POOLRAVE_CAPACITY and i < len(black_rave_moves):
            if black_rave_moves[i] in moves:
                black_pool.append(black_rave_moves[i])
            i += 1
        i = 0
        while len(white_pool) < MCTSMeta.POOLRAVE_CAPACITY and i < len(white_rave_moves):
            if white_rave_moves[i] in moves:
                white_pool.append(white_rave_moves[i])
            i += 1

        while state.game_over() == False:
            move = None
            if len(black_pool) > 0 and state.to_play == GameMeta.PLAYERS["one"]:
                move = choice(black_pool)
            elif len(white_pool) > 0:
                move = choice(white_pool)

            if random() > MCTSMeta.RANDOMNESS or not move or move not in moves:
                move = choice(moves)

            state.move(move)
            moves.remove(move)

        black_rave_pts = []
        white_rave_pts = []

        for x in range(GameMeta.ROWS):
            for y in range(GameMeta.COLS):
                if state.board[x][y] == GameMeta.PLAYERS["one"]:
                    black_rave_pts.append((x, y))
                    if state.get_outcome() == GameMeta.PLAYERS["one"]:
                        if (x, y) in self.black_rave:
                            self.black_rave[(x, y)] += 1
                        else:
                            self.black_rave[(x, y)] = 1
                    else:
                        if (x, y) in self.black_rave:
                            self.black_rave[(x, y)] -= 1
                        else:
                            self.black_rave[(x, y)] = -1
                elif state.board[x][y] == GameMeta.PLAYERS["two"]:
                    white_rave_pts.append((x, y))
                    if state.get_outcome() == GameMeta.PLAYERS["two"]:
                        if (x, y) in self.white_rave:
                            self.white_rave[(x, y)] += 1
                        else:
                            self.white_rave[(x, y)] = 1
                    else:
                        if (x, y) in self.white_rave:
                            self.white_rave[(x, y)] -= 1
                        else:
                            self.white_rave[(x, y)] = -1

        return state.get_outcome(), black_rave_pts, white_rave_pts
