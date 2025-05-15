// interactive_solver_only_main.cpp
#include "Position.hpp" 
#include "Solver.hpp"   
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <limits>   
#include <algorithm>

using namespace GameSolver::Connect4;


int main() {
    std::ios_base::sync_with_stdio(false); 
    std::cin.tie(NULL);

    Solver solver_instance; 

    std::cerr << "C++ Solver Backend (No Book): Initialized and ready." << std::endl;
    std::cerr << "READY" << std::endl; 

    std::string command_line;
    while (std::getline(std::cin, command_line)) { 
        if (command_line == "QUIT") {
            std::cerr << "C++ Solver Backend: Received QUIT. Exiting." << std::endl;
            break;
        } else if (command_line == "GET_MOVE") { 
            int r1_removed, c1_removed, r2_removed, c2_removed;
            int player_id_to_move; 
            std::vector<std::vector<int>> board_gui(Position::HEIGHT, std::vector<int>(Position::WIDTH));
            bool input_error = false;

            if (!(std::cin >> r1_removed >> c1_removed >> r2_removed >> c2_removed)) { input_error = true; }
            if (!input_error) std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); 

            if (!input_error && !(std::cin >> player_id_to_move)) { input_error = true; }
            if (!input_error) std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');

            if (!input_error) {
                for (int r = 0; r < Position::HEIGHT; ++r) {
                    std::string row_str;
                    if (!std::getline(std::cin, row_str)) { input_error = true; break; }
                    std::istringstream iss_row(row_str);
                    for (int c_idx = 0; c_idx < Position::WIDTH; ++c_idx) {
                        if (!(iss_row >> board_gui[r][c_idx])) { input_error = true; break; }
                    }
                    if (input_error) break;
                }
            }

            if (input_error) {
                std::cerr << "C++ Solver Backend: Error reading input for GET_MOVE." << std::endl;
                std::cout << "ERROR: Malformed input for GET_MOVE" << std::endl;
                continue; 
            }
            
            Position current_game_pos(r1_removed, c1_removed, r2_removed, c2_removed); 
            current_game_pos.reconstructBoardState(board_gui, player_id_to_move);
            
            bool use_weak_solve = false; 
            std::vector<int> scores = solver_instance.analyze(current_game_pos, use_weak_solve);

            int best_col = -1;
            int best_score = std::numeric_limits<int>::min();
            
            for (int i = 0; i < Position::WIDTH; ++i) {
                int col_to_check = solver_instance.getColumnOrderAt(i);
                if (col_to_check == -1 || col_to_check < 0 || col_to_check >= Position::WIDTH) continue;

                if (current_game_pos.canPlay(col_to_check) && scores[col_to_check] != Solver::INVALID_MOVE) {
                    if (scores[col_to_check] > best_score) {
                        best_score = scores[col_to_check];
                        best_col = col_to_check;
                    }
                }
            }
            
            if (best_col != -1) {
                std::cout << "MOVE " << best_col << std::endl;
            } else {
                bool found_fallback = false;
                for(int col_idx_fb = 0; col_idx_fb < Position::WIDTH; ++col_idx_fb) { // Đổi tên biến lặp
                    if(current_game_pos.canPlay(col_idx_fb)) {
                        std::cout << "MOVE " << col_idx_fb << std::endl;
                        found_fallback = true;
                        break;
                    }
                }
                if(!found_fallback) {
                    std::cout << "ERROR: No valid moves found by C++ solver (fallback)." << std::endl;
                }
            }

        } else {
            std::cerr << "C++ Solver Backend: Unknown command: " << command_line << std::endl;
            std::cout << "ERROR: Unknown command" << std::endl;
        }
    } 

    std::cerr << "C++ Solver Backend: Shutting down." << std::endl;
    return 0;
}