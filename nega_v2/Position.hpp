

#ifndef POSITION_HPP
#define POSITION_HPP

#include <string>
#include <cstdint>
#include <cassert>
#include <iostream> 
#include <vector>
#include <cmath> 
#include <algorithm> 

namespace GameSolver {
namespace Connect4 {

class Position {
public:
    static constexpr int WIDTH = 7;
    static constexpr int HEIGHT = 6;
    static constexpr int BOARD_PITCH_SIZE = WIDTH * (HEIGHT + 1); 
    using position_t = uint64_t;

    static constexpr int MIN_SCORE = -(WIDTH*HEIGHT)/2 + 3; 
    static constexpr int MAX_SCORE = (WIDTH*HEIGHT+1)/2 - 3;

    static_assert(WIDTH < 10, "Board's width must be less than 10");
    static_assert(BOARD_PITCH_SIZE <= sizeof(position_t)*8, "Board does not fit into position_t bitmask");

    Position();
    Position(int row1_arg, int col1_arg, int row2_arg, int col2_arg); 
    Position(position_t current_bb, position_t mask_bb, position_t blocked_bb);

    position_t get_current_position() const { return current_position; }
    position_t get_mask() const { return mask; }
    position_t get_blocked_cells() const { return blocked_cells; }
    int nbMoves() const { return moves_; }

    bool canPlay(int col) const;
    void playCol(int col);
    bool isWinningMove(int col) const; 
    bool canWinNext() const; 
    position_t key() const; 
    void reconstructBoardState(const std::vector<std::vector<int>>& board_gui, int player_id_whose_turn_it_is);

    int moveScore(position_t move_landing_mask) const; 
    
    void play(position_t move_mask); 
    position_t winning_position() const; 
    position_t opponent_winning_position() const; 

    static unsigned int popcount(position_t m); 
    static position_t compute_winning_position(position_t position, position_t mask_of_all_pieces); 
    
    std::vector<int> getNonLosingPlayableCols() const; 
    int getLowestAvailableBitIndex(int col) const; 

private:
    position_t current_position;
    position_t mask;
    position_t blocked_cells;
    unsigned int moves_;

    static constexpr position_t bottom_mask = UINT64_C(0x41041041041041);
    static constexpr position_t actual_board_cells_mask = bottom_mask * ((position_t(1) << HEIGHT) - 1);

public: 
    static constexpr position_t top_mask_col_static(int col) {
      return position_t(1) << ((HEIGHT - 1) + col * (HEIGHT + 1));
    }
    static constexpr position_t bottom_mask_col_static(int col) {
      return position_t(1) << col * (HEIGHT + 1);
    }
   static constexpr position_t column_mask_static(int col) {
     return ((position_t(1) << (HEIGHT + 1)) - 1) << col * (HEIGHT + 1);
   }
};


inline Position::Position() :
    current_position{0}, mask{0}, blocked_cells{0}, moves_{0} {}

inline Position::Position(int row1_arg, int col1_arg, int row2_arg, int col2_arg) :
    current_position{0}, mask{0}, blocked_cells{0}, moves_{0} {
    const int Eff_WIDTH = Position::WIDTH; 
    const int Eff_HEIGHT = Position::HEIGHT;
    if (col1_arg >= 0 && col1_arg < Eff_WIDTH && row1_arg >= 0 && row1_arg < Eff_HEIGHT) {
        int bitboard_row1 = Eff_HEIGHT - 1 - row1_arg; 
        int bit_index1 = col1_arg * (Eff_HEIGHT + 1) + bitboard_row1;
        blocked_cells |= (position_t(1) << bit_index1);
    } else {
        std::cerr << "Warning: Invalid removed cell 1 coordinates (row=" << row1_arg << ", col=" << col1_arg << "). Ignoring.\n" << std::flush;
    }
    if (col2_arg >= 0 && col2_arg < Eff_WIDTH && row2_arg >= 0 && row2_arg < Eff_HEIGHT) {
        int bitboard_row2 = Eff_HEIGHT - 1 - row2_arg; 
        int bit_index2 = col2_arg * (Eff_HEIGHT + 1) + bitboard_row2;
        bool cell1_was_valid_and_is_identical_to_cell2 = (row1_arg == row2_arg) && (col1_arg == col2_arg) && (col1_arg >= 0 && col1_arg < Eff_WIDTH && row1_arg >= 0 && row1_arg < Eff_HEIGHT);
        if (!cell1_was_valid_and_is_identical_to_cell2) { 
             blocked_cells |= (position_t(1) << bit_index2);
        }
    } else {
        std::cerr << "Warning: Invalid removed cell 2 coordinates (row=" << row2_arg << ", col=" << col2_arg << "). Ignoring.\n" << std::flush;
    }
}

inline Position::Position(position_t current_bb, position_t mask_bb, position_t blocked_bb) :
    current_position(current_bb), mask(mask_bb), blocked_cells(blocked_bb) {
    moves_ = popcount(mask);
}

inline int Position::getLowestAvailableBitIndex(int col) const {
    const int intHeight = Position::HEIGHT;
    if (col < 0 || col >= WIDTH) { return -1; }
    for (int row_board = 0; row_board < intHeight; ++row_board) {
        int bit_idx = col * (intHeight + 1) + row_board;
        if ((blocked_cells & (position_t(1) << bit_idx)) == 0) {
            if ((mask & (position_t(1) << bit_idx)) == 0) {
                return bit_idx;
            }
        }
    }
    return -1;
}

inline bool Position::canPlay(int col) const {
    return getLowestAvailableBitIndex(col) != -1;
}

inline void Position::playCol(int col) {
    int drop_bit_idx = getLowestAvailableBitIndex(col);
    assert(drop_bit_idx != -1 && "playCol called on a non-playable column");
    position_t move_mask = position_t(1) << drop_bit_idx;
    play(move_mask);
}

inline void Position::play(position_t move_mask) {
    current_position ^= mask; 
    mask |= move_mask;        
    moves_++;                 
}

inline bool Position::isWinningMove(int col) const {
  if (!canPlay(col)) { return false; }
  int drop_bit_idx = getLowestAvailableBitIndex(col);
  if (drop_bit_idx == -1) { return false; }
  position_t move_landing_mask = position_t(1) << drop_bit_idx;
  position_t current_player_winning_spots = compute_winning_position(this->current_position, this->mask);
  return (current_player_winning_spots & move_landing_mask) != 0;
}
inline void Position::reconstructBoardState(
    const std::vector<std::vector<int>>& board_gui, 
    int player_id_whose_turn_it_is 
) {
    
    this->current_position = 0;
    this->mask = 0;
    this->moves_ = 0;
    
    int piece_count = 0;

    for (int r_gui = 0; r_gui < HEIGHT; ++r_gui) {
        for (int c_gui = 0; c_gui < WIDTH; ++c_gui) {
            int piece_in_cell = board_gui[r_gui][c_gui];
            if (piece_in_cell == 1 || piece_in_cell == 2) {
                piece_count++;
                int bitboard_row = (HEIGHT - 1) - r_gui; 
                position_t stone_mask = position_t(1) << (c_gui * (HEIGHT + 1) + bitboard_row);
                
                this->mask |= stone_mask; 
                
                if (piece_in_cell == player_id_whose_turn_it_is) {
                    this->current_position |= stone_mask;
                }
            }
        }
    }
    this->moves_ = piece_count;

    bool p1_should_play_logically = (this->moves_ % 2 == 0); // Player 1 (X) đi khi tổng số quân là chẵn
    bool p1_is_designated_player = (player_id_whose_turn_it_is == 1);

    if (p1_should_play_logically != p1_is_designated_player) {
        std::cerr << "Position::reconstructBoardState Warning: Mismatch between calculated number of moves (" 
                  << this->moves_ << ") and designated player_id_whose_turn_it_is (" 
                  << player_id_whose_turn_it_is << "). "
                  << "The current_position bitmask might not correctly reflect the player whose turn it actually is according to move count. "
                  << "This can happen if the board state from Python is inconsistent." << std::endl;
    }
}
inline std::vector<int> Position::getNonLosingPlayableCols() const {
    std::vector<int> non_losing_cols;
    std::vector<int> all_playable_cols; 
    for (int col = 0; col < WIDTH; ++col) {
        if (canPlay(col)) {
            all_playable_cols.push_back(col); 
            Position P2_after_move(*this);    
            P2_after_move.playCol(col);       
            if (!P2_after_move.canWinNext()) { 
                non_losing_cols.push_back(col); 
            }
        }
    }
    if (non_losing_cols.empty() && !all_playable_cols.empty()) {
        return all_playable_cols;
    }
    return non_losing_cols; 
}

inline int Position::moveScore(position_t move_landing_mask) const {
    const int SCORE_MY_IMMEDIATE_WIN = 20000;                 
    const int PENALTY_LEADS_TO_MY_IMMEDIATE_LOSS = -19000;    
    const int SCORE_BLOCK_OPPONENT_IMMEDIATE_WIN = 18000;  
    const int SCORE_CREATE_MY_DOUBLE_THREAT = 1500;         
    const int SCORE_CREATE_MY_SINGLE_THREAT = 500;          
    const int CENTRALITY_MAX_BONUS_PER_COL_STEP = 3;                                             
    const int CENTRALITY_WEIGHT = 5;                


    if (move_landing_mask == 0) {
        return -100000; 
    }

    int landing_col = -1;
    unsigned int bit_pos_for_col = 0;
    #ifdef __GNUC__
    bit_pos_for_col = __builtin_ctzll(move_landing_mask);
    #else
    for (unsigned int k = 0; k < sizeof(position_t) * 8; ++k) {
        if ((move_landing_mask >> k) & 1) {
            bit_pos_for_col = k;
            break;
        }
    }
    #endif
    if (!((position_t(1) << bit_pos_for_col) == move_landing_mask)) {
        landing_col = -1; 
    } else {
        landing_col = bit_pos_for_col / (HEIGHT + 1);
    }


    position_t my_winning_spots_now = compute_winning_position(this->current_position, this->mask);
    if ((my_winning_spots_now & move_landing_mask) != 0) {
        return SCORE_MY_IMMEDIATE_WIN; 
    }

    Position P_after_my_move(*this);
    P_after_my_move.play(move_landing_mask); 

    if (P_after_my_move.canWinNext()) { 
        return PENALTY_LEADS_TO_MY_IMMEDIATE_LOSS; 
    }

    int tactical_score = 0;

    position_t opponent_board_before_my_move = this->current_position ^ this->mask;
    position_t opponent_winning_spots_before_my_move = compute_winning_position(opponent_board_before_my_move, this->mask);
    if ((opponent_winning_spots_before_my_move & move_landing_mask) != 0) {
        tactical_score += SCORE_BLOCK_OPPONENT_IMMEDIATE_WIN; 
    }
    

    position_t my_board_after_my_move = P_after_my_move.mask ^ P_after_my_move.current_position;
    position_t my_threat_spots_for_next_turn = compute_winning_position(my_board_after_my_move, P_after_my_move.mask);
    unsigned int num_my_threats = popcount(my_threat_spots_for_next_turn);

    if (num_my_threats >= 2) { 
        tactical_score += SCORE_CREATE_MY_DOUBLE_THREAT; 
    } else if (num_my_threats == 1) { 
        tactical_score += SCORE_CREATE_MY_SINGLE_THREAT;
    }

    int positional_score = 0;
    if (landing_col != -1) {
        int centrality_value = (Position::WIDTH / 2 - std::abs(landing_col - Position::WIDTH / 2)); 
        positional_score += centrality_value * CENTRALITY_WEIGHT; 
    }
    
    return tactical_score + positional_score; 
}


inline bool Position::canWinNext() const {
    position_t winning_spots = winning_position(); 
    position_t possible_moves_mask = 0;
    for(int col=0; col<WIDTH; ++col) {
        int drop_bit_idx = getLowestAvailableBitIndex(col);
        if (drop_bit_idx != -1) {
            possible_moves_mask |= (position_t(1) << drop_bit_idx);
        }
    }
    return (winning_spots & possible_moves_mask) != 0;
}

inline GameSolver::Connect4::Position::position_t Position::key() const {
    return current_position ^ mask ^ blocked_cells;
}

inline unsigned int Position::popcount(position_t m) {
    #ifdef __GNUC__
    if (sizeof(position_t) == sizeof(uint64_t)) {
        return __builtin_popcountll(m);
    }
    #endif
    unsigned int c = 0;
    while(m) {
        m &= m - 1;
        c++;
    }
    return c;
}

inline Position::position_t Position::compute_winning_position(position_t P, position_t M) {
    const int H = Position::HEIGHT;       
    const int H1 = H + 1;   
    const int H_diag_fwd = H;                            
    const int H_diag_bwd = H + 2;
    position_t r = 0;
    position_t p_temp; // Biến tạm để tránh nhầm lẫn với tham số P

    // Dọc
    r |= (P << 1) & (P << 2) & (P << 3); 
    r |= (P >> 1) & (P << 1) & (P << 2); 
    r |= (P >> 2) & (P >> 1) & (P << 1); 
    r |= (P >> 3) & (P >> 2) & (P >> 1); 

    // Ngang
    p_temp = (P << H1) & (P << 2*H1); 
    r |= p_temp & (P << 3*H1); 
    r |= p_temp & (P >> H1);   
    p_temp = (P >> H1) & (P >> 2*H1); 
    r |= p_temp & (P << H1);   
    r |= p_temp & (P >> 3*H1); 

    // Chéo /
    p_temp = (P << H_diag_fwd) & (P << 2*H_diag_fwd);
    r |= p_temp & (P << 3*H_diag_fwd);
    r |= p_temp & (P >> H_diag_fwd);
    p_temp = (P >> H_diag_fwd) & (P >> 2*H_diag_fwd);
    r |= p_temp & (P << H_diag_fwd);
    r |= p_temp & (P >> 3*H_diag_fwd);
    
    // Chéo \
    p_temp = (P << H_diag_bwd) & (P << 2*H_diag_bwd);
    r |= p_temp & (P << 3*H_diag_bwd);
    r |= p_temp & (P >> H_diag_bwd);
    p_temp = (P >> H_diag_bwd) & (P >> 2*H_diag_bwd);
    r |= p_temp & (P << H_diag_bwd);
    r |= p_temp & (P >> 3*H_diag_bwd);

    return r & (actual_board_cells_mask ^ M); // Chỉ lấy các ô trống hợp lệ
}


inline Position::position_t Position::winning_position() const {
    return compute_winning_position(current_position, mask);
}

inline Position::position_t Position::opponent_winning_position() const {
    return compute_winning_position(current_position ^ mask, mask);
}

} 
} 
#endif 