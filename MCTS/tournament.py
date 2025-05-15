import sys
import time
from meta import GameMeta

def tournament(interface1, interface2, game_number=10, movetime=1, size=8, opening_moves=[]):
    """
    Adapted from your snippet. We run some # of games between interface1 (agent 1) and interface2 (agent 2),
    alternating who moves first. We'll treat 'b' as Player 1, 'w' as Player 2, though in Connect Four
    it's typically 'one' and 'two'.
    We'll measure how many wins agent1 gets vs agent2. 
    The snippet references time.clock(); in Python 3.8+ you might use time.process_time or time.perf_counter.
    """
    begin = time.process_time()
    p1_score = 0  # player1 score
    p2_score = 0  # player2 score

    # set the time / boardsize for each interface
    interface1.gtp_time([movetime])
    interface2.gtp_time([movetime])
    interface1.gtp_boardsize([size])
    interface2.gtp_boardsize([size])

    rollouts_1 = 0
    genmove_calls_1 = 0
    list_of_rollouts = []

    print('Tournament Started ...')
    print(f"{game_number} games will be running between agents ...")

    for i in range(game_number):
        # Clear boards
        interface1.gtp_clear([])
        interface2.gtp_clear([])

        # The snippet checks 'turn = interface1.game.turn()'
        turn = interface1.game.to_play  # who is to_play in ConnectState? 
        # We'll interpret 'turn' => if it's 1 => 'b', if it's 2 => 'w'
        c1 = 'w' if turn == GameMeta.PLAYERS["one"] else 'b'
        c2 = 'b' if turn == GameMeta.PLAYERS["two"] else 'w'

        game = []
        
        # If i % 2 == 0 => interface1 is "Player 1"
        if i % 2 == 0:
            while interface1.gtp_winner([])[1] == "none":
                # interface1 moves as c1 => player1
                move = interface1.gtp_genmove([c1])
                rollouts_1 += move[2]
                genmove_calls_1 += 1
                list_of_rollouts.append(move[2])
                if move[0]:
                    interface2.gtp_play([c1, move[1]])
                    game.append(move[1])

                # interface2 moves as c2 => player2
                w_info = interface1.gtp_winner([])
                if w_info[1] != "none":
                    break
                move = interface2.gtp_genmove([c2])
                rollouts_1 += move[2]
                genmove_calls_1 += 1
                list_of_rollouts.append(move[2])
                if move[0]:
                    interface1.gtp_play([c2, move[1]])
                    game.append(move[1])

            # Once out of loop, we see who won
            winner = interface1.gtp_winner([])[1]
            if winner.startswith(c1):
                p1_score += 1
                print(f"GAME OVER, WINNER : PLAYER 1 ({c1})\n")
            elif winner == "draw":
                print("GAME OVER, DRAW.\n")
            else:
                p2_score += 1
                print(f"GAME OVER, WINNER : PLAYER 2 ({c2})\n")

            print(f"Games played =  [ {i+1} / {game_number} ]")
            print(f"Wins   |  Player 1 =  [{p1_score}]  |  Player 2 = [{p2_score}]")
        else:
            # interface2 is "Player 1"
            while interface1.gtp_winner([])[1] == "none":
                # interface2 as player1
                move = interface2.gtp_genmove([c1])
                rollouts_1 += move[2]
                genmove_calls_1 += 1
                list_of_rollouts.append(move[2])
                if move[0]:
                    interface1.gtp_play([c1, move[1]])
                    game.append(move[1])

                # interface1 as player2
                w_info = interface1.gtp_winner([])
                if w_info[1] != "none":
                    break
                move = interface1.gtp_genmove([c2])
                rollouts_1 += move[2]
                genmove_calls_1 += 1
                list_of_rollouts.append(move[2])
                if move[0]:
                    interface2.gtp_play([c2, move[1]])
                    game.append(move[1])

            winner = interface1.gtp_winner([])[1]
            if winner.startswith(c2):
                # Means agent1 is player2 => p1_score
                p1_score += 1
                print(f"GAME OVER, WINNER : PLAYER 1 (interface2 as {c1})\n")
            elif winner == "draw":
                print("GAME OVER, DRAW.\n")
            else:
                p2_score += 1
                print(f"GAME OVER, WINNER : PLAYER 2 (interface1 as {c2})\n")

            print(f"Games played =  [ {i+1} / {game_number} ]")
            print(f"Wins   |  Player 1 =  [{p1_score}]  |  Player 2 = [{p2_score}]")

        sys.stdout.flush()

    list_of_rollouts = list(filter(lambda a: a != 0, list_of_rollouts))
    p1 = (p1_score / game_number) * 100
    p2 = (p2_score / game_number) * 100
    if len(list_of_rollouts) > 0:
        rollouts_info = (
            round(sum(list_of_rollouts) / len(list_of_rollouts)),
            max(list_of_rollouts),
            min(list_of_rollouts),
        )
    else:
        rollouts_info = (0, 0, 0)

    print("\n\n\n")
    print("player 1 wins = ", p1, " %")
    print("player 2 wins = ", p2, " %")
    if genmove_calls_1 != 0:
        avg_sims = (rollouts_1 / genmove_calls_1)
    else:
        avg_sims = 0
    print("Average Simulations = [ %a ] " % (avg_sims))

    finish_time = time.process_time() - begin
    print("Finished in %i seconds" % finish_time)
    return p1_score, p2_score, rollouts_info, finish_time


if __name__ == "__main__":
    # Suppose you have these classes defined:
    # - Connect4MCTSAgent
    # - RaveMctsAgent
    # - DecisiveMoveMctsAgent
    # - LGRMctsAgent
    # - PoolRaveMctsAgent

    from rave_mcts import RaveMctsAgent, DecisiveMoveMctsAgent, LGRMctsAgent, PoolRaveMctsAgent
    from mcts_mark_2 import Connect4MCTSAgent
    from Connect4Interface import Connect4Interface

    # Create the two interfaces
    interface1 = Connect4Interface(Connect4MCTSAgent, movetime=5)
    interface2 = Connect4Interface(DecisiveMoveMctsAgent, movetime=5)

    # Run the tournament
    p1_score, p2_score, rollouts_info, finish_time = tournament(
        interface1, interface2, 
        game_number=100, 
        movetime=5,  # seconds or rollouts, depending on agent
        size=8
    )
    print("Tournament done. p1_score=", p1_score, "p2_score=", p2_score)
    print("Rollouts info:", rollouts_info)
    print("Finished in:", finish_time, "seconds")