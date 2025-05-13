#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <limits>
#include <algorithm>
#include <functional>

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

bool check_for_4_in_a_row(GameSolver::Connect4::Position::position_t player_board) {
    const int HEIGHT = GameSolver::Connect4::Position::HEIGHT;
    if (((player_board >> 1) & (player_board >> 2) & (player_board >> 3) & player_board) != 0) return true;
    if (((player_board >> (HEIGHT + 1)) & (player_board >> 2 * (HEIGHT + 1)) & (player_board >> 3 * (HEIGHT + 1)) & player_board) != 0) return true;
    if (((player_board << (HEIGHT + 1)) & (player_board >> (HEIGHT + 1)) & (player_board >> 2 * (HEIGHT + 1)) & player_board) != 0) return true;
    if (((player_board << 2 * (HEIGHT + 1)) & (player_board << (HEIGHT + 1)) & (player_board >> (HEIGHT + 1)) & player_board) != 0) return true;
    if (((player_board << 3 * (HEIGHT + 1)) & (player_board << 2 * (HEIGHT + 1)) & (player_board << (HEIGHT + 1)) & player_board) != 0) return true;
    if (((player_board >> HEIGHT) & (player_board >> 2 * HEIGHT) & (player_board >> 3 * HEIGHT) & player_board) != 0) return true;
    if (((player_board << HEIGHT) & (player_board >> HEIGHT) & (player_board >> 2 * HEIGHT) & player_board) != 0) return true;
    if (((player_board << 2 * HEIGHT) & (player_board << HEIGHT) & (player_board >> HEIGHT) & player_board) != 0) return true;
    if (((player_board << 3 * HEIGHT) & (player_board << 2 * HEIGHT) & (player_board << HEIGHT) & player_board) != 0) return true;
    if (((player_board >> (HEIGHT + 2)) & (player_board >> 2 * (HEIGHT + 2)) & (player_board >> 3 * (HEIGHT + 2)) & player_board) != 0) return true;
    if (((player_board << (HEIGHT + 2)) & (player_board >> (HEIGHT + 2)) & (player_board >> 2 * (HEIGHT + 2)) & player_board) != 0) return true;
    if (((player_board << 2 * (HEIGHT + 2)) & (player_board << (HEIGHT + 2)) & (player_board >> (HEIGHT + 2)) & player_board) != 0) return true;
    if (((player_board << 3 * (HEIGHT + 2)) & (player_board << 2 * (HEIGHT + 2)) & (player_board << (HEIGHT + 2)) & player_board) != 0) return true;
    return false;
}

bool checkWinOrDraw(const GameSolver::Connect4::Position& pos) {
    const int WIDTH = GameSolver::Connect4::Position::WIDTH;
    const int HEIGHT = GameSolver::Connect4::Position::HEIGHT;
    const int TOTAL_PLAYABLE_CELLS = WIDTH * HEIGHT - 2;

    if (pos.nbMoves() == TOTAL_PLAYABLE_CELLS) {
        return true;
    }

    if (pos.nbMoves() < 7) return false;

    GameSolver::Connect4::Position::position_t current_pos_board = pos.get_current_position();
    GameSolver::Connect4::Position::position_t mask_board = pos.get_mask();
    GameSolver::Connect4::Position::position_t previous_player_board = mask_board ^ current_pos_board;
    return check_for_4_in_a_row(previous_player_board);
}

void printBoard(const GameSolver::Connect4::Position& pos) {
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
    std::cout << "Moves played: " << pos.nbMoves() << std::endl;
    if (pos.nbMoves() % 2 == 0) {
        std::cout << "Current Turn: Player 1 (X) - Human Opponent" << std::endl;
    } else {
        std::cout << "Current Turn: Player 2 (O) - Solver Player" << std::endl;
    }
    std::cout << "-----------------------------\n";
}

int main() {
    std::cout << "Program start.\n" << std::flush;

    const int board_width = GameSolver::Connect4::Position::WIDTH;
    const int board_height = GameSolver::Connect4::Position::HEIGHT;

    const int REMOVED_COL1 = 1;
    const int REMOVED_ROW1 = 0;
    const int REMOVED_COL2 = 5;
    const int REMOVED_ROW2 = 5;
    std::cout << "Removed cells configured at (" << REMOVED_COL1 << ", " << REMOVED_ROW1 << ") and (" << REMOVED_COL2 << ", " << REMOVED_ROW2 << ").\n" << std::flush;

    GameSolver::Connect4::Solver solver;
    solver.reset();
    std::cout << "Solver initialized.\n" << std::flush;

    std::cout << "\n--- Starting Connect Four Game ---" << std::flush;
    GameSolver::Connect4::Position current_pos(REMOVED_COL1, REMOVED_ROW1, REMOVED_COL2, REMOVED_ROW2);

    std::cin.clear();
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    std::cout << "DEBUG: Initial cin state cleared.\n" << std::flush;

    printBoard(current_pos);
    std::cout << "DEBUG: After first printBoard.\n" << std::flush;

    while (true) {
        std::cout << "DEBUG: Start of loop, nbMoves=" << current_pos.nbMoves() << ".\n" << std::flush;

        if (current_pos.nbMoves() > 0) {
            std::cout << "DEBUG: Checking win/draw for nbMoves > 0.\n" << std::flush;
            if (checkWinOrDraw(current_pos)) {
                std::cout << "DEBUG: Game over condition met.\n" << std::flush;
                printBoard(current_pos);
                if (current_pos.nbMoves() % 2 != 0) {
                    const int TOTAL_PLAYABLE_CELLS = GameSolver::Connect4::Position::WIDTH * GameSolver::Connect4::Position::HEIGHT - 2;
                    if (current_pos.nbMoves() == TOTAL_PLAYABLE_CELLS) {
                        std::cout << "--- Game Over: It's a Draw! ---" << std::endl;
                    } else {
                        std::cout << "--- Game Over: Player 1 (X) Wins! ---" << std::endl;
                    }
                } else {
                    const int TOTAL_PLAYABLE_CELLS = GameSolver::Connect4::Position::WIDTH * GameSolver::Connect4::Position::HEIGHT - 2;
                    if (current_pos.nbMoves() == TOTAL_PLAYABLE_CELLS) {
                        std::cout << "--- Game Over: It's a Draw! ---" << std::endl;
                    } else {
                        std::cout << "--- Game Over: Player 2 (O) Wins! ---" << std::endl;
                    }
                }
                std::cout << "\n--- Game Session Ended ---\n" << std::endl;
                return 0;
            }
            std::cout << "DEBUG: Win/draw check passed.\n" << std::flush;
        }

        std::vector<int> valid_cols_for_turn;
        for(int col=0; col < board_width; ++col) {
            if (current_pos.canPlay(col)) {
                valid_cols_for_turn.push_back(col);
            }
        }

        if (valid_cols_for_turn.empty()) {
            if (current_pos.nbMoves() < board_width * board_height - 2) {
                std::cerr << "Fatal Error: Game not over, but no valid moves found!\n";
                return 1;
            }
            continue;
        }

        if (current_pos.nbMoves() % 2 == 0) {
            std::cout << "DEBUG: P1 turn logic.\n" << std::flush;
            int human_col = -1;

            while (true) {
                std::cout << "\nPlayer 1 (X)'s turn (Human). Please enter column (0-" << board_width - 1 << "): " << std::flush;
                std::cin >> human_col;
                std::cout << "DEBUG: Attempted to read P1 input: " << human_col << ".\n" << std::flush;

                if (std::cin.fail()) {
                    std::cout << "DEBUG: cin failed for P1 input! Clearing error, ignoring buffer.\n" << std::flush;
                    std::cin.clear();
                    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
                    std::cout << "Invalid input. Please enter a number.\n" << std::flush;
                    continue;
                }

                bool is_playable_input = false;
                for(int valid_col : valid_cols_for_turn) {
                    if (human_col == valid_col) {
                        is_playable_input = true;
                        break;
                    }
                }

                if (is_playable_input) {
                    std::cout << "DEBUG: Valid and playable P1 input: " << human_col << ".\n" << std::flush;
                    break;
                } else {
                    std::cout << "DEBUG: Invalid P1 column (" << human_col << ") or column full (or blocked).\n" << std::flush;
                    std::cout << "Invalid input or column full (or blocked). Enter a valid column (0-" << board_width - 1 << "): " << std::flush;
                }
            }

            std::cout << "DEBUG: Before playCol P1 with column " << human_col << ".\n" << std::flush;
            current_pos.playCol(human_col);
            std::cout << "DEBUG: After playCol P1.\n" << std::flush;
            printBoard(current_pos);
            std::cout << "DEBUG: After printBoard P1.\n" << std::flush;

        } else {
            std::cout << "DEBUG: P2 turn logic.\n" << std::flush;
            int chosen_col = -1;

            std::cout << "Player 2 (O)'s turn (Solver Player). Thinking...\n" << std::flush;

            auto start_time = std::chrono::high_resolution_clock::now();
            std::vector<int> scores_p2 = solver.analyze(current_pos, false);
            auto end_time = std::chrono::high_resolution_clock::now();
            std::chrono::duration<double> elapsed = end_time - start_time;
            std::cout << "DEBUG: Solver analyze finished in " << elapsed.count() << " seconds.\n" << std::flush;

            int best_score_p2 = std::numeric_limits<int>::min();
            int best_col_p2 = -1;

            for(int col = 0; col < board_width; ++col) {
                if (scores_p2[col] != GameSolver::Connect4::Solver::INVALID_MOVE) {
                    if (scores_p2[col] > best_score_p2) {
                        best_score_p2 = scores_p2[col];
                        best_col_p2 = col;
                    }
                }
            }

            if (best_col_p2 != -1) {
                chosen_col = best_col_p2;
                std::cout << "DEBUG: Solver chose column " << chosen_col << " with score " << best_score_p2 << ".\n" << std::flush;
            } else {
                std::cerr << "Fatal Error: Solver failed to find any valid move score!\n";
                return 1;
            }

            std::cout << "Player 2 decided on column " << chosen_col << " (Solver Player).\n" << std::flush;

            std::cout << "DEBUG: Before playCol P2 with column " << chosen_col << ".\n" << std::flush;
            current_pos.playCol(chosen_col);
            std::cout << "DEBUG: After playCol P2.\n" << std::flush;
            printBoard(current_pos);
            std::cout << "DEBUG: After printBoard P2.\n" << std::flush;
        }
    }
    return 0;
}