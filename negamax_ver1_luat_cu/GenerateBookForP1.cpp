#include "Solver.hpp"
#include "Position.hpp" 
#include <vector>
#include <map>
#include <unordered_map>
#include <queue>
#include <iostream>
#include <algorithm>
#include <limits>
#include <fstream>
#include <string>
#include <chrono>


struct BoardHash {
    size_t operator()(const std::vector<std::vector<int>>& board) const {
        size_t hash = board.size();
        for (const auto& row : board) {
            hash ^= row.size() + 0x9e3779b9 + (hash << 6) + (hash >> 2);
            for (int cell : row) {
                hash ^= std::hash<int>{}(cell) + 0x9e3779b9 + (hash << 6) + (hash >> 2);
            }
        }
        return hash;
    }
};

std::vector<std::vector<int>> positionToVector(const GameSolver::Connect4::Position& pos) {
    std::vector<std::vector<int>> board_vec(GameSolver::Connect4::Position::HEIGHT, std::vector<int>(GameSolver::Connect4::Position::WIDTH));
    const int WIDTH = GameSolver::Connect4::Position::WIDTH;
    const int HEIGHT = GameSolver::Connect4::Position::HEIGHT;
    using position_t = GameSolver::Connect4::Position::position_t;

     position_t current_pos_board = pos.get_current_position(); 
     position_t mask_board = pos.get_mask();               



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

            if ((p1_board & cell_mask) != 0) {
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
    // vertical
    if (((player_board >> 1) & (player_board >> 2) & (player_board >> 3) & player_board) != 0) return true; // shifted up
    // horizontal
    if (((player_board >> (HEIGHT + 1)) & (player_board >> 2 * (HEIGHT + 1)) & (player_board >> 3 * (HEIGHT + 1)) & player_board) != 0) return true; // shifted left
    if (((player_board << (HEIGHT + 1)) & (player_board >> (HEIGHT + 1)) & (player_board >> 2 * (HEIGHT + 1)) & player_board) != 0) return true; // shifted left 1
    if (((player_board << 2 * (HEIGHT + 1)) & (player_board << (HEIGHT + 1)) & (player_board >> (HEIGHT + 1)) & player_board) != 0) return true; // shifted left 2
    if (((player_board << 3 * (HEIGHT + 1)) & (player_board << 2 * (HEIGHT + 1)) & (player_board << (HEIGHT + 1)) & player_board) != 0) return true; // shifted left 3
    // diagonal 1 (bottom-left to top-right)
    if (((player_board >> HEIGHT) & (player_board >> 2 * HEIGHT) & (player_board >> 3 * HEIGHT) & player_board) != 0) return true; // shifted down-left
    if (((player_board << HEIGHT) & (player_board >> HEIGHT) & (player_board >> 2 * HEIGHT) & player_board) != 0) return true; // shifted down-left 1
    if (((player_board << 2 * HEIGHT) & (player_board << HEIGHT) & (player_board >> HEIGHT) & player_board) != 0) return true; // shifted down-left 2
    if (((player_board << 3 * HEIGHT) & (player_board << 2 * HEIGHT) & (player_board << HEIGHT) & player_board) != 0) return true; // shifted down-left 3
    // diagonal 2 (bottom-right to top-left)
    if (((player_board >> (HEIGHT + 2)) & (player_board >> 2 * (HEIGHT + 2)) & (player_board >> 3 * (HEIGHT + 2)) & player_board) != 0) return true; // shifted down-right
    if (((player_board << (HEIGHT + 2)) & (player_board >> (HEIGHT + 2)) & (player_board >> 2 * (HEIGHT + 2)) & player_board) != 0) return true;
    if (((player_board << 2 * (HEIGHT + 2)) & (player_board << (HEIGHT + 2)) & (player_board >> (HEIGHT + 2)) & player_board) != 0) return true;
    if (((player_board << 3 * (HEIGHT + 2)) & (player_board << 2 * (HEIGHT + 2)) & (player_board << (HEIGHT + 2)) & player_board) != 0) return true;

    return false;
}
bool checkWinOrDraw(const GameSolver::Connect4::Position& pos) {
    const int WIDTH = GameSolver::Connect4::Position::WIDTH;
    const int HEIGHT = GameSolver::Connect4::Position::HEIGHT;
    using position_t = GameSolver::Connect4::Position::position_t;

    if (pos.nbMoves() == WIDTH * HEIGHT) {
        return true; 
    }

    if (pos.nbMoves() < 7) return false;

     position_t current_pos_board = pos.get_current_position();
     position_t mask_board = pos.get_mask();                
    position_t previous_player_board = mask_board ^ current_pos_board;

    return check_for_4_in_a_row(previous_player_board);
}

void saveOpeningBookBinary(
    const std::unordered_map<std::vector<std::vector<int>>, int, BoardHash>& book,
    const std::string& filename,
    int width,
    int height)
{
    std::cout << "Saving opening book to " << filename << "..." << std::endl;
    std::ofstream outfile(filename, std::ios::binary);
    if (!outfile.is_open()) {
        std::cerr << "Error: Could not open file for saving book: " << filename << std::endl;
        return;
    }

    size_t num_entries = book.size();
    outfile.write(reinterpret_cast<const char*>(&num_entries), sizeof(num_entries));

    for (const auto& pair : book) {
        const auto& board = pair.first;
        int move = pair.second;

        for (int r = 0; r < height; ++r) {
            outfile.write(reinterpret_cast<const char*>(pair.first[r].data()), width * sizeof(int));
        }

        outfile.write(reinterpret_cast<const char*>(&move), sizeof(move));
    }

    outfile.close();
    std::cout << "Opening book saved successfully to " << filename << "." << std::endl;
}


int main() {
    std::cout << "Program starting: Generating All Valid Opponent Moves Opening Book..." << std::endl;
    auto start_time = std::chrono::high_resolution_clock::now();

    std::unordered_map<std::vector<std::vector<int>>, int, BoardHash> opening_book;
    std::queue<GameSolver::Connect4::Position> states_to_process;

    GameSolver::Connect4::Solver solver;
    solver.reset();
    std::cout << "Solver initialized." << std::endl;

    const std::string existing_book_file = "7x6.book";
    std::cout << "Attempting to load existing book for solver analysis: " << existing_book_file << "..." << std::endl;
    solver.loadBook(existing_book_file);
    std::cout << "Existing book loaded into solver's internal book (if file exists and is valid)." << std::endl;

    const int board_width = GameSolver::Connect4::Position::WIDTH;
    const int board_height = GameSolver::Connect4::Position::HEIGHT;
    std::cout << "Board dimensions: " << board_width << "x" << board_height << std::endl;

    GameSolver::Connect4::Position initial_pos;

    std::cout << "Processing initial empty board (using loaded book if applicable)..." << std::endl;
    std::vector<int> scores_p1_initial = solver.analyze(initial_pos);

    int best_score_p1_initial = std::numeric_limits<int>::min();
    int best_col_p1_initial = -1;

    for (int col = 0; col < board_width; ++col) {
        if (scores_p1_initial[col] != GameSolver::Connect4::Solver::INVALID_MOVE) {
            if (scores_p1_initial[col] > best_score_p1_initial) {
                best_score_p1_initial = scores_p1_initial[col];
                best_col_p1_initial = col;
            }
        }
    }

    if (best_col_p1_initial != -1) {
        opening_book[positionToVector(initial_pos)] = best_col_p1_initial;
        std::cout << "Optimal first move for P1 found: Column " << best_col_p1_initial << " (Score: " << best_score_p1_initial << ")" << std::endl;

        GameSolver::Connect4::Position pos_after_p1_move = initial_pos;
        pos_after_p1_move.playCol(best_col_p1_initial);

        if (!checkWinOrDraw(pos_after_p1_move)) {
            std::vector<int> scores_p2 = solver.analyze(pos_after_p1_move); 

            for (int col_p2 = 0; col_p2 < board_width; ++col_p2) {
                 if (scores_p2[col_p2] != GameSolver::Connect4::Solver::INVALID_MOVE) {
                    GameSolver::Connect4::Position pos_after_p2_move = pos_after_p1_move; 
                    pos_after_p2_move.playCol(col_p2); 

                    if (!checkWinOrDraw(pos_after_p2_move)) {
                         states_to_process.push(pos_after_p2_move);
                    }
                }
            }
        } else {
             std::cout << "Game ended after P1's first move (unlikely)." << std::endl;
        }
    } else {
         std::cerr << "Error: No valid initial move found!" << std::endl;
    }


    unsigned long long processed_count = 0;
    std::cout << "Starting queue processing (" << states_to_process.size() << " states initially in queue)..." << std::endl;
    std::cout << "(Exploring ALL valid opponent responses.)" << std::endl;

    while (!states_to_process.empty()) {
        GameSolver::Connect4::Position current_pos = states_to_process.front();
        states_to_process.pop();

        std::vector<std::vector<int>> current_board_vec = positionToVector(current_pos);

        if (opening_book.count(current_board_vec)) {
            continue;
        }

         if (checkWinOrDraw(current_pos) && current_pos.nbMoves() < board_width * board_height) {
              continue;
         }

        processed_count++;
        if (processed_count % 1000 == 0) {
             std::cout << "Processing state #" << processed_count << ". Queue size: " << states_to_process.size() << ". Book size: " << opening_book.size() << std::endl;
        }

        std::vector<int> scores_p1 = solver.analyze(current_pos); 

        int best_score_p1 = std::numeric_limits<int>::min();
        int best_col_p1 = -1;

        for (int col = 0; col < board_width; ++col) {
             if (scores_p1[col] != GameSolver::Connect4::Solver::INVALID_MOVE) {
                if (scores_p1[col] > best_score_p1) {
                    best_score_p1 = scores_p1[col]; 
                    best_col_p1 = col;
                }
             }
        }

        if (best_col_p1 != -1) {
            opening_book[current_board_vec] = best_col_p1;

            GameSolver::Connect4::Position pos_after_p1_move = current_pos;
            pos_after_p1_move.playCol(best_col_p1);

            if (!checkWinOrDraw(pos_after_p1_move)) {
                std::vector<int> scores_p2 = solver.analyze(pos_after_p1_move); 

                for (int col_p2 = 0; col_p2 < board_width; ++col_p2) {
                     if (scores_p2[col_p2] != GameSolver::Connect4::Solver::INVALID_MOVE) {

                        GameSolver::Connect4::Position pos_after_p2_move = pos_after_p1_move; 
                        pos_after_p2_move.playCol(col_p2); 

                        if (!checkWinOrDraw(pos_after_p2_move)) {
                             states_to_process.push(pos_after_p2_move);
                        }
                    }
                }
            } // else: game was over after P1's move
        } 
    }

    std::cout << "\nGeneration process finished." << std::endl;
    std::cout << "Total unique P1 states saved in book (All Valid Opponent Moves): " << opening_book.size() << std::endl;

    saveOpeningBookBinary(opening_book, "opening_book_all_p2.bin", board_width, board_height); // Lưu tên file khác

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;
    std::cout << "Total generation time (All Valid Opponent Moves): " << elapsed.count() << " seconds." << std::endl;


    std::cout << "Program exiting." << std::endl;
    return 0;
}

