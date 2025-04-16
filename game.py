from ConnectState import ConnectState
from mcts import MCTS
from mcts_mark_2 import Connect4MCTSAgent
from rave_mcts import *


def play():
    state = ConnectState()
    mcts = Connect4MCTSAgent(state)
    rave_mcts = RaveMctsAgent(state)
    deci_rave_mcts = DecisiveMoveMctsAgent(state)
    agent = mcts

    while not state.game_over():
        print("Current state:")
        state.print()

        user_move = int(input("Enter a move: "))
        while user_move not in state.get_legal_moves():
            print("Illegal move")
            user_move = int(input("Enter a move: "))

        state.move(user_move)
        agent.move(user_move)

        state.print()

        if state.game_over():
            print("Player one won!")
            break

        print("Thinking...")

        agent.search(30)
        num_rollouts, node_count, run_time = agent.statistics()
        print("Statistics: ", num_rollouts, "rollouts in", run_time, "seconds")
        move = agent.best_move()

        print("MCTS chose move: ", move)

        state.move(move)
        agent.move(move)

        if state.game_over():
            print("Player two won!")
            break

def play_match(agent1, agent2, num_games=1):
    wins = {1: 0, 2: 0, 'draw': 0}
    for _ in range(num_games):
        state = ConnectState()
        agents = {GameMeta.PLAYERS['one']: agent1, GameMeta.PLAYERS['two']: agent2}
        turn = GameMeta.PLAYERS['one']
        while not state.game_over():
            agent = agents[turn]
            agent.set_ConnectState(state)
            agent.search(5)  # Shorter time for testing
            move = agent.best_move()
            state.move(move)
            turn = GameMeta.PLAYERS['two'] if turn == GameMeta.PLAYERS['one'] else GameMeta.PLAYERS['one']
        outcome = state.get_outcome()
        if outcome == GameMeta.OUTCOMES['one']:
            wins[1] += 1
        elif outcome == GameMeta.OUTCOMES['two']:
            wins[2] += 1
        else:
            wins['draw'] += 1
    return wins

mcts = Connect4MCTSAgent(ConnectState())
rave_mcts = RaveMctsAgent(ConnectState())
results = play_match(mcts, rave_mcts)
print(f"Base MCTS vs RAVE MCTS: {results}")
