
#include <cassert>
#include <vector>
#include <algorithm> 
#include <limits>
#include <iostream> 

#include "Solver.hpp"         
#include "Position.hpp"       
#include "TranspositionTable.hpp" 
#include "MoveSorter.hpp" 

namespace GameSolver {
namespace Connect4 {

using position_t = Position::position_t;

Solver::Solver() : nodeCount{0} {
    for(int i = 0; i < Position::WIDTH; i++)
        columnOrder[i] = Position::WIDTH / 2 + (1 - 2 * (i % 2)) * (i + 1) / 2;
    
}


int Solver::negamax(const Position &P_current, int alpha, int beta) {
    assert(alpha < beta); 
    assert(!P_current.canWinNext()); 

    nodeCount++; 
    const GameSolver::Connect4::Position::position_t key = P_current.key();

    if(P_current.nbMoves() >= Position::WIDTH * Position::HEIGHT - 2) {
        return 0; 
    }

    int min_score_possible_at_depth = -(Position::WIDTH * Position::HEIGHT - 2 - P_current.nbMoves()) / 2;
    int max_score_possible_at_depth = (Position::WIDTH * Position::HEIGHT - 2 + 1 - P_current.nbMoves()) / 2;

	if(alpha < min_score_possible_at_depth) {
		alpha = min_score_possible_at_depth;
		if(alpha >= beta) return alpha;
	}
    if(beta > max_score_possible_at_depth) {
		beta = max_score_possible_at_depth;
		if(alpha >= beta) return beta;
	}

    if(int val = transTable.get(key)) {
        // Đảm bảo dùng đúng tên hằng số MIN_SCORE/MAX_SCORE từ Position.hpp
        if(val > Position::MAX_SCORE - Position::MIN_SCORE + 1) { 
            int tt_min_bound = val + 2 * Position::MIN_SCORE - Position::MAX_SCORE - 2;
            if(alpha < tt_min_bound) { alpha = tt_min_bound; if(alpha >= beta) return alpha; }
        } else { 
            int tt_max_bound = val + Position::MIN_SCORE - 1;
            if(beta > tt_max_bound) { beta = tt_max_bound; if(alpha >= beta) return beta; }
        }
    }

    MoveSorter moves; 
    std::vector<int> potential_cols = P_current.getNonLosingPlayableCols();

    for (int i = 0; i < Position::WIDTH; ++i) {
        int ordered_col = columnOrder[i];
        bool is_potential = false;
        for (int p_col : potential_cols) { if (p_col == ordered_col) {is_potential = true; break;} }

        if (is_potential) { 
            int drop_bit_idx = P_current.getLowestAvailableBitIndex(ordered_col);
            if (drop_bit_idx != -1) { 
                Position::position_t move_landing_mask = Position::position_t(1) << drop_bit_idx;
                int heuristic_score = P_current.moveScore(move_landing_mask); 
                moves.add(move_landing_mask, heuristic_score);
            }
        }
    }
    
    int found_moves_count = 0; 
    int best_value_found = std::numeric_limits<int>::min(); 

    while(Position::position_t next_move_landing_mask = moves.getNext()) {
        found_moves_count++;
        Position P2_next_state(P_current); 
        P2_next_state.play(next_move_landing_mask); 

        int score_eval_for_move; 

        if (P2_next_state.canWinNext()) {
            score_eval_for_move = -((Position::WIDTH * Position::HEIGHT - 2 + 1 - P2_next_state.nbMoves()) / 2);
        } else {
            score_eval_for_move = -negamax(P2_next_state, -beta, -alpha);
        }

        if (best_value_found == std::numeric_limits<int>::min() || score_eval_for_move > best_value_found) {
            best_value_found = score_eval_for_move;
        }

        if(score_eval_for_move >= beta) { 
            transTable.put(key, best_value_found + Position::MAX_SCORE - 2 * Position::MIN_SCORE + 2); 
            return best_value_found; 
        }
        if(score_eval_for_move > alpha) { 
            alpha = score_eval_for_move;   
        }
    }

    if (found_moves_count == 0) { 
        return min_score_possible_at_depth; 
    }

    transTable.put(key, best_value_found - Position::MIN_SCORE + 1); 
    return best_value_found; 
}

int Solver::solve(const Position &P, bool weak) {

    if (P.canWinNext()) {
        return (Position::WIDTH * Position::HEIGHT - 2 + 1 - P.nbMoves()) / 2; 
    }

    int min_s, max_s; 
    if (weak) {
        min_s = -1; max_s = 1;  
    } else {
        max_s = (Position::WIDTH * Position::HEIGHT - 2 + 1 - P.nbMoves()) / 2;
        min_s = -(Position::WIDTH * Position::HEIGHT - 2 - P.nbMoves()) / 2; 
    }

    int current_alpha = min_s;
    int current_beta = max_s;

    while (current_alpha < current_beta) {
        int med = current_alpha + (current_beta - current_alpha) / 2;
        if (med <= 0) { 
            if (med > current_alpha / 2 && current_alpha != 0 && current_alpha != -1 ) med = current_alpha / 2;
            if (med == current_alpha) med++; 
        } else { 
            if (med < current_beta / 2 && current_beta != 0 && current_beta != 1) med = current_beta / 2;
            if (med == current_beta) med--;
        }
        if (med <= current_alpha) med = current_alpha + 1;
        if (med >= current_beta) med = current_beta - 1;
        if (current_alpha >= current_beta || med >= current_beta) break; 

        int r = negamax(P, med, med + 1); 

        if (r <= med) { current_beta = r; } 
        else { current_alpha = r; }
    }
    return current_alpha; 
}

std::vector<int> Solver::analyze(const Position &P, bool weak) {
    std::vector<int> scores(Position::WIDTH, Solver::INVALID_MOVE);
    for (int col = 0; col < Position::WIDTH; col++) {
        if (P.canPlay(col)) {
            if(P.isWinningMove(col)) { 
                scores[col] = (Position::WIDTH * Position::HEIGHT - 2 + 1 - P.nbMoves()) / 2;
            }
            else { 
                Position P2(P); 
                P2.playCol(col); 
                scores[col] = -solve(P2, weak); 
            }
        }
    }
    return scores;
}

} 
}