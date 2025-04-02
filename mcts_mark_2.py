import random
import time
import math
from copy import deepcopy
from queue import Queue
from random import choice
from meta import GameMeta, MCTSMeta
from ConnectState import ConnectState


class Node:
    """
    Node for the MCTS. Stores the move applied to reach this node from its parent,
    stats for the associated game position, children, parent and outcome
    (outcome==none unless the position ends the game).
    Args:
        move:
        parent:
        N (int): times this position was visited
        Q (int): average reward (wins-losses) from this position
        Q_RAVE (int): times this move has been critical in a rollout
        N_RAVE (int): times this move has appeared in a rollout
        children (dict): dictionary of successive nodes
        outcome (int): If node is a leaf, then outcome indicates
                       the winner, else None
    """

    def __init__(self, move: tuple = None, parent: object = None):
        """
        Initialize a new node with optional move and parent and initially empty
        children list and rollout statistics and unspecified outcome.
        """
        self.move = move
        self.parent = parent
        self.N = 0  # times this position was visited
        self.Q = 0  # average reward (wins-losses) from this position
        self.Q_RAVE = 0  # times this move has been critical in a rollout
        self.N_RAVE = 0  # times this move has appeared in a rollout
        self.children = {}
        self.outcome = GameMeta.PLAYERS['none']

    def add_children(self, children: dict) -> None:
        """
        Add a list of nodes to the children of this node.
        """
        for child in children:
            self.children[child.move] = child

    @property
    def value(self, explore: float = MCTSMeta.EXPLORATION):
        """
        Calculate the UCT value of this node relative to its parent, the parameter
        "explore" specifies how much the value should favor nodes that have
        yet to be thoroughly explored versus nodes that seem to have a high win
        rate.
        """
        # if the node is not visited, set the value as infinity. Nodes with no visits are on priority
        if self.N == 0:
            return 0 if explore == 0 else GameMeta.INF
        else:
            # exploitation + exploration (UCT)
            return self.Q / self.N + explore * math.sqrt(2 * math.log(self.parent.N) / self.N)


class Connect4MCTSAgent:
    """
    MCTS for Connect Four
    Attributes:
        root_state (ConnectState): Game simulator that helps us to understand the game situation
        root (Node): Root of the tree search
        run_time (int): time per each run
        node_count (int): the whole nodes in tree
        num_rollouts (int): The number of rollouts for each search
        EXPLORATION (int): specifies how much the value should favor
                           nodes that have yet to be thoroughly explored versus nodes
                           that seem to have a high win rate.
    """

    def __init__(self, state=ConnectState()):
        self.root_state = deepcopy(state)
        self.root = Node()
        self.run_time = 0
        self.node_count = 0
        self.num_rollouts = 0

    def search(self, time_budget: int) -> None:
        """
        Search and update the search tree for a specified amount of time in seconds.
        """
        start_time = time.time()
        num_rollouts = 0

        # do until we exceed our time budget
        while time.time() - start_time < time_budget:
            node, state = self.select_node()
            outcome = self.roll_out(state)
            self.backup(node, state.to_play, outcome)
            num_rollouts += 1
        run_time = time.time() - start_time
        node_count = self.tree_size()
        self.run_time = run_time
        self.node_count = node_count
        self.num_rollouts = num_rollouts

    def select_node(self) -> tuple:
        """
        Select a node in the tree to perform a single simulation from.
        """
        node = self.root
        state = deepcopy(self.root_state)

        # stop if we find reach a leaf node
        while len(node.children) != 0:
            # descend to the maximum value node, break ties at random
            children = node.children.values()
            max_value = max(children, key=lambda n: n.value).value
            max_nodes = [n for n in node.children.values()
                         if n.value == max_value]
            node = choice(max_nodes)
            state.move(node.move)

            # if some child node has not been explored select it before expanding
            if node.N == 0:
                return node, state

        # if we reach a leaf node generate its children and return one of them
        if self.expand(node, state):
            node = choice(list(node.children.values()))
            state.move(node.move)
        return node, state

    @staticmethod
    def expand(parent: Node, state: ConnectState) -> bool:
        """
        Generate the children of the passed "parent" node based on the available
        moves in the passed game state and add them to the tree.

        Returns:
            bool: returns false if node is leaf (the game has ended).
        """
        children = []
        if state.game_over():
            return False

        children = [Node(move, parent) for move in state.get_legal_moves()]
        parent.add_children(children)
        return True

    @staticmethod
    def roll_out(state: ConnectState) -> int:
        """
        Simulate an entirely random game from the passed state and return the winning player.

        Args:
            state: game state

        Returns:
            int: winner of the game
        """
        while not state.game_over():
            state.move(random.choice(state.get_legal_moves()))

        return state.get_outcome()

    @staticmethod
    def backup(node: Node, turn: int, outcome: int) -> None:
        """
        Update the node statistics on the path from the passed node to root to reflect
        the outcome of a randomly simulated playout.

        Args:
            node:
            turn: winner turn
            outcome: outcome of the rollout
        """
        reward = 0 if outcome == turn else 1

        while node is not None:
            node.N += 1
            node.Q += reward
            node = node.parent
            if outcome == GameMeta.OUTCOMES['draw']:
                reward = 0
            else:
                reward = 1 - reward

    def best_move(self) -> tuple:
        """
        Return the best move according to the current tree.
        Returns:
            best move in terms of the most simulations number unless the game is over
        """
        if self.root_state.game_over():
            return -1

        # choose the move of the most simulated node breaking ties randomly
        max_value = max(self.root.children.values(), key=lambda n: n.N).N
        max_nodes = [n for n in self.root.children.values() if n.N == max_value]
        bestchild = choice(max_nodes)
        return bestchild.move

    def move(self, move: tuple) -> None:
        """
        Make the passed move and update the tree appropriately. It is designed to let the player choose an action manually.
        """
        if move in self.root.children:
            child = self.root.children[move]
            child.parent = None
            self.root = child
            self.root_state.move(child.move)
            return

        # if for whatever reason the move is not in the children of the root just throw out the tree and start over
        self.root_state.move(move)
        self.root = Node()

    def set_ConnectState(self, state: ConnectState) -> None:
        """
        Set the root_state of the tree to the passed ConnectState, this clears all the information stored in the tree since none of it applies to the new state.
        """
        self.root_state = deepcopy(state)
        self.root = Node()

    def statistics(self) -> tuple:
        return self.num_rollouts, self.node_count, self.run_time

    def tree_size(self) -> int:
        """
        Count nodes in tree by BFS.
        """
        Q = Queue()
        count = 0
        Q.put(self.root)
        while not Q.empty():
            node = Q.get()
            count += 1
            for child in node.children.values():
                Q.put(child)
        return count
