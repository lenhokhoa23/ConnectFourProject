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
#include <utility>
#include <functional>
#include <cassert>


namespace GameSolver {
namespace Connect4 {

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

    std::vector<std::vector<int>> positionToVector(const Position& pos) {
        std::vector<std::vector<int>> board_vec(Position::HEIGHT, std::vector<int>(Position::WIDTH));
        const int WIDTH = Position::WIDTH;
        const int HEIGHT = Position::HEIGHT;
        using position_t = Position::position_t;

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

    bool check_for_4_in_a_row(Position::position_t player_board) {
        const int HEIGHT = Position::HEIGHT;
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

    bool checkWinOrDraw(const Position& pos) {
        const int WIDTH = Position::WIDTH;
        const int HEIGHT = Position::HEIGHT;
        using position_t = Position::position_t;

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
    const std::unordered_map<std::vector<std::vector<int>>, int, GameSolver::Connect4::BoardHash>& book,
    const std::string& filename,
    int width,
    int height);

}
}


void GameSolver::Connect4::saveOpeningBookBinary(
const std::unordered_map<std::vector<std::vector<int>>, int, GameSolver::Connect4::BoardHash>& book,
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

        outfile.write(reinterpret_cast<const char*>(&move), sizeof(int));
    }

    outfile.close();
    std::cout << "Opening book saved successfully to " << filename << "." << std::endl;
}

int main() {
    std::cout << "Program starting: Generating P2 vs. All Valid P1 Book (P2 First Optimal Move) after P1's initial optimal move..." << std::endl;
    auto start_time = std::chrono::high_resolution_clock::now();

    std::unordered_map<std::vector<std::vector<int>>, int, GameSolver::Connect4::BoardHash> opening_book;

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

    GameSolver::Connect4::Position initial_pos_p1_turn;

    std::cout << "Processing initial empty board (P1's turn) to seed P2 queue with state after P1's first optimal move..." << std::endl;
    std::vector<int> scores_p1_initial = solver.analyze(initial_pos_p1_turn);

    int best_score_p1_initial = std::numeric_limits<int>::min();
    int p1_first_optimal_col = -1;

    for (int col = 0; col < board_width; ++col) {
        if (scores_p1_initial[col] != GameSolver::Connect4::Solver::INVALID_MOVE) {
            if (scores_p1_initial[col] > best_score_p1_initial) {
                best_score_p1_initial = scores_p1_initial[col];
            }
        }
    }
     for(int col=0; col < board_width; ++col) {
         if (scores_p1_initial[col] != GameSolver::Connect4::Solver::INVALID_MOVE && scores_p1_initial[col] == best_score_p1_initial) {
             p1_first_optimal_col = col;
             break;
         }
     }

    if (p1_first_optimal_col == -1) {
        std::cerr << "Error: Could not determine P1's first optimal move from empty board. Exiting." << std::endl;
        return 1;
    }

    std::cout << "P1's first optimal move identified as Column " << p1_first_optimal_col << ". Starting book generation from state after this move." << std::endl;
    GameSolver::Connect4::Position start_pos_after_p1_optimal = initial_pos_p1_turn;
    start_pos_after_p1_optimal.playCol(p1_first_optimal_col);

    if (GameSolver::Connect4::checkWinOrDraw(start_pos_after_p1_optimal)) {
        std::cerr << "Error: Game ended immediately after P1's first optimal move (unlikely). Cannot generate book." << std::endl;
        return 1;
    }
    states_to_process.push(start_pos_after_p1_optimal);
    std::cout << "Initial P2 state pushed to queue." << std::endl;

    unsigned long long processed_p2_states_count = 0;
    std::cout << "\nStarting queue processing (P2 states)..." << std::endl;
    std::cout << "(Solver will use the loaded book for analysis whenever possible.)" << std::endl;

    while (!states_to_process.empty()) {
        GameSolver::Connect4::Position current_pos_p2_turn = states_to_process.front();
        states_to_process.pop();

        std::vector<std::vector<int>> current_board_vec = GameSolver::Connect4::positionToVector(current_pos_p2_turn);

        if (opening_book.count(current_board_vec)) {
            continue;
        }

        if (GameSolver::Connect4::checkWinOrDraw(current_pos_p2_turn)) {
             continue;
        }

        processed_p2_states_count++;
        if (processed_p2_states_count % 1000 == 0) {
             std::cout << "Processing P2 state #" << processed_p2_states_count << ". Queue size: " << states_to_process.size() << ". Book size: " << opening_book.size() << std::endl;
        }

        std::vector<int> scores_p2 = solver.analyze(current_pos_p2_turn);

        int best_score_p2 = std::numeric_limits<int>::min();
        int first_optimal_col_p2 = -1;

        for (int col = 0; col < board_width; ++col) {
             if (scores_p2[col] != GameSolver::Connect4::Solver::INVALID_MOVE) {
                 if (scores_p2[col] > best_score_p2) {
                     best_score_p2 = scores_p2[col];
                 }
             }
        }

        for (int col = 0; col < board_width; ++col) {
             if (scores_p2[col] != GameSolver::Connect4::Solver::INVALID_MOVE && scores_p2[col] == best_score_p2) {
                 first_optimal_col_p2 = col;
                 break;
             }
        }

        if (first_optimal_col_p2 != -1) {
            opening_book[current_board_vec] = first_optimal_col_p2;

            GameSolver::Connect4::Position pos_after_p2_move = current_pos_p2_turn;
            pos_after_p2_move.playCol(first_optimal_col_p2);

            if (GameSolver::Connect4::checkWinOrDraw(pos_after_p2_move)) {
                 continue;
            }

            for (int col_p1_response = 0; col_p1_response < board_width; ++col_p1_response) {
                 if (pos_after_p2_move.canPlay(col_p1_response)) {
                     GameSolver::Connect4::Position pos_after_p1_response = pos_after_p2_move;
                     pos_after_p1_response.playCol(col_p1_response);

                     if (!GameSolver::Connect4::checkWinOrDraw(pos_after_p1_response)) {
                         states_to_process.push(pos_after_p1_response);
                     }
                 }
            }
        }
    }

    std::cout << "\nGeneration process finished." << std::endl;
    std::cout << "Total unique P2 states saved in book (vs. All Valid P1, P2 First Optimal, after P1 initial optimal): " << opening_book.size() << std::endl;

    GameSolver::Connect4::saveOpeningBookBinary(opening_book, "p2_vs_all_valid_p1_book_after_p1_initial_optimal.bin", board_width, board_height);

    auto end_time = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsed = end_time - start_time;
    std::cout << "Total generation time: " << elapsed.count() << " seconds." << std::endl;

    std::cout << "Program exiting." << std::endl;
    return 0;
}