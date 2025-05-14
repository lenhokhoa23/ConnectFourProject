

#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <limits>
#include <algorithm>
#include <functional> 
#include <thread>     
#include <iomanip>    

#include "Position.hpp" 
#include "Solver.hpp"   

std::vector<std::vector<int>> positionToVector(const GameSolver::Connect4::Position& pos) {
    std::vector<std::vector<int>> board_vec(GameSolver::Connect4::Position::HEIGHT, std::vector<int>(GameSolver::Connect4::Position::WIDTH));
    const int WIDTH = GameSolver::Connect4::Position::WIDTH;
    const int HEIGHT = GameSolver::Connect4::Position::HEIGHT;
    using position_t = GameSolver::Connect4::Position::position_t;

    position_t current_pos_board = pos.get_current_position();
    position_t mask_board = pos.get_mask();
    position_t blocked_board = pos.get_blocked_cells(); 

    position_t p1_board, p2_board;

    if (pos.nbMoves() % 2 == 0) { 
        p1_board = current_pos_board;
        p2_board = mask_board ^ current_pos_board;
    } else { 
        p1_board = mask_board ^ current_pos_board;
        p2_board = current_pos_board;
    }

    for (int r = 0; r < HEIGHT; ++r) { 
        for (int c = 0; c < WIDTH; ++c) { 
            int bitboard_row = HEIGHT - 1 - r; 
            int bit_index = c * (HEIGHT + 1) + bitboard_row; 
            position_t cell_mask = position_t(1) << bit_index;

            if ((blocked_board & cell_mask) != 0) {
                board_vec[r][c] = -1; 
            } else if ((p1_board & cell_mask) != 0) {
                board_vec[r][c] = 1; 
            } else if ((p2_board & cell_mask) != 0) {
                board_vec[r][c] = 2; 
            } else {
                board_vec[r][c] = 0; 
            }
        }
    }
    return board_vec;
}

void printBoard(const GameSolver::Connect4::Position& pos, bool print_turn_info = true) {
    std::vector<std::vector<int>> board_vec = positionToVector(pos);
    const int WIDTH = GameSolver::Connect4::Position::WIDTH;
    const int HEIGHT = GameSolver::Connect4::Position::HEIGHT;

    std::cout << "\n-----------------------------\n";
    std::cout << " ";
    for(int c=0; c<WIDTH; ++c) std::cout << c << " ";
    std::cout << "\n";

    for (int r = 0; r < HEIGHT; ++r) {
        std::cout << "|";
        for (int c = 0; c < WIDTH; ++c) {
            if (board_vec[r][c] == 0) std::cout << ".";
            else if (board_vec[r][c] == 1) std::cout << "X"; 
            else if (board_vec[r][c] == 2) std::cout << "O"; 
            else if (board_vec[r][c] == -1) std::cout << "#"; 
            std::cout << "|";
        }
        std::cout << "\n";
    }
    std::cout << "-----------------------------\n";
    if (print_turn_info) {
        std::cout << "Moves played: " << pos.nbMoves() << std::endl;
        if (pos.nbMoves() % 2 == 0) {
            std::cout << "Current Turn: Player 1 (X) - Solver" << std::endl;
        } else {
            std::cout << "Current Turn: Player 2 (O) - Solver" << std::endl; 
        }
        std::cout << "-----------------------------\n";
    }
}

bool check_player_has_won(GameSolver::Connect4::Position::position_t player_board) {
    const int H = GameSolver::Connect4::Position::HEIGHT; 
    const int H1 = H + 1; 
    const int H_diag_fwd = H;                        
    const int H_diag_bwd = H + 2;

    GameSolver::Connect4::Position::position_t y;
    y = player_board & (player_board >> 1);   y = y & (y >> 2);   if (y != 0) return true; 
    y = player_board & (player_board >> H1);  y = y & (y >> (2*H1));if (y != 0) return true; 
    y = player_board & (player_board >> H_diag_fwd); y = y & (y >> (2*H_diag_fwd)); if (y != 0) return true; 
    y = player_board & (player_board >> H_diag_bwd); y = y & (y >> (2*H_diag_bwd)); if (y != 0) return true; 
    return false;
}


int main() {
    std::cout << "Program start.\n" << std::flush; 

    const int REMOVED_ROW1 = 2; 
    const int REMOVED_COL1 = 2;
    const int REMOVED_ROW2 = 3; 
    const int REMOVED_COL2 = 4;
    std::cout << "Playing with fixed removed cells for book testing: (row=" << REMOVED_ROW1 << ",col=" << REMOVED_COL1 
              << ") (effectively one cell removed if both are identical and valid).\n" << std::flush;

    GameSolver::Connect4::Solver shared_solver; 
    shared_solver.reset(); 

    std::cout << "Solver initialized (attempted to load opening book).\n" << std::flush;

    std::cout << "\n--- Starting Connect Four: Solver (X) vs Solver (O) ---" << std::flush;
    GameSolver::Connect4::Position current_pos(REMOVED_ROW1, REMOVED_COL1, REMOVED_ROW2, REMOVED_COL2);

    printBoard(current_pos); 

    bool use_weak_solve_p1 = false; 
    bool use_weak_solve_p2 = false; 

    const int TOTAL_PLAYABLE_CELLS = GameSolver::Connect4::Position::WIDTH * GameSolver::Connect4::Position::HEIGHT - 2; // Thực tế là -1 nếu 2 ô trùng nhau
                                                                                                                      // Hoặc bạn có thể tính chính xác số ô bị chặn từ current_pos.get_blocked_cells() nếu cần.
                                                                                                                      // Hiện tại, TOTAL_PLAYABLE_CELLS = 40 vẫn dùng cho công thức điểm, nhưng khi bàn đầy sẽ là 41 quân.
    const int ACTUAL_PLAYABLE_CELLS = GameSolver::Connect4::Position::WIDTH * GameSolver::Connect4::Position::HEIGHT - GameSolver::Connect4::Position::popcount(current_pos.get_blocked_cells());


    while (true) {
        if (current_pos.nbMoves() > 0) {
            GameSolver::Connect4::Position::position_t board_mask = current_pos.get_mask();
            GameSolver::Connect4::Position::position_t current_player_pieces_in_pos_obj = current_pos.get_current_position();
            GameSolver::Connect4::Position::position_t last_player_pieces = board_mask ^ current_player_pieces_in_pos_obj;

            bool won = check_player_has_won(last_player_pieces);
            bool draw_full_board = (current_pos.nbMoves() >= ACTUAL_PLAYABLE_CELLS); 

            if (won || draw_full_board) {
                std::cout << "DEBUG: Game over condition met.\n" << std::flush;
                if(!won && draw_full_board) {
                     std::cout << "--- Game Over: It's a Draw! (Board Full) ---" << std::endl;
                } else if (current_pos.nbMoves() % 2 != 0) { 
                    std::cout << "--- Game Over: Player 1 (X) Wins! ---" << std::endl;
                } else { 
                    std::cout << "--- Game Over: Player 2 (O) Wins! ---" << std::endl;
                }
                printBoard(current_pos, false); 
                std::cout << "\n--- Game Session Ended ---\n" << std::endl; 
                return 0; 
            }
        }
        
        std::vector<int> valid_cols_for_turn;
        for(int col_idx = 0; col_idx < GameSolver::Connect4::Position::WIDTH; ++col_idx) {
            if (current_pos.canPlay(col_idx)) {
                valid_cols_for_turn.push_back(col_idx);
            }
        }

        if (valid_cols_for_turn.empty()) { 
             std::cout << "--- Game Over: Draw (No valid moves left, board not full) ---" << std::endl;
             printBoard(current_pos, false);
             std::cout << "\n--- Game Session Ended ---\n" << std::endl; 
            return 0;
        }

        int chosen_col = -1;
        bool current_weak_solve_flag;
        std::string player_name_str;
        
        if (current_pos.nbMoves() % 2 == 0) { 
            player_name_str = "Player 1 (X)";
            current_weak_solve_flag = use_weak_solve_p1;
        } else { 
            player_name_str = "Player 2 (O)";
            current_weak_solve_flag = use_weak_solve_p2;
        }
        
        std::cout << "\n" << player_name_str << " - Solver's turn (nbMoves=" << current_pos.nbMoves() << "). Thinking..." << std::endl;

        auto start_time = std::chrono::high_resolution_clock::now();
        std::vector<int> scores_ai = shared_solver.analyze(current_pos, current_weak_solve_flag); 
        auto end_time = std::chrono::high_resolution_clock::now();
        std::chrono::duration<double, std::milli> elapsed_ms = end_time - start_time;
        std::cout << "DEBUG: " << player_name_str << " analyze finished in " << elapsed_ms.count() << " ms." << std::endl;

        std::cout << "Scores for " << player_name_str << " [Col 0-6]: ";
        for (size_t i = 0; i < scores_ai.size(); ++i) {
            if (scores_ai[i] == GameSolver::Connect4::Solver::INVALID_MOVE) {
                std::cout << "INV "; 
            } else {
                std::cout << scores_ai[i] << " ";
            }
        }
        std::cout << std::endl;

        int best_score_ai = std::numeric_limits<int>::min();
        for(int i = 0; i < GameSolver::Connect4::Position::WIDTH; ++i) {
            int col_to_check = shared_solver.getColumnOrderAt(i); 
            if (col_to_check == -1) continue; 

            bool is_playable_col = false;
            for(int valid_col : valid_cols_for_turn) { if (col_to_check == valid_col) {is_playable_col = true; break;} }
            
            if (is_playable_col && scores_ai[col_to_check] != GameSolver::Connect4::Solver::INVALID_MOVE) {
                if (scores_ai[col_to_check] > best_score_ai) {
                    best_score_ai = scores_ai[col_to_check];
                    chosen_col = col_to_check; 
                }
            }
        }
        
        if (chosen_col == -1 ) { 
             if (!valid_cols_for_turn.empty()){
                chosen_col = valid_cols_for_turn[0]; 
                std::cout << "DEBUG: " << player_name_str << " picking first valid move as fallback: " << chosen_col << std::endl;
             } else { 
                std::cerr << "CRITICAL ERROR: " << player_name_str << " no valid moves to pick from fallback!" << std::endl;
                return 1;
             }
        }
        
        std::cout << player_name_str << " chose column " << chosen_col << " with score " << best_score_ai << "." << std::endl;
        current_pos.playCol(chosen_col); 
        printBoard(current_pos); 

    } 
    return 0; 
}