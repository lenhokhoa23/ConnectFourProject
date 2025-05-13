#ifndef SOLVER_HPP
#define SOLVER_HPP

#include <vector>
#include <string> 
#include <unordered_map> 
#include "Position.hpp" 
#include "TranspositionTable.hpp" 

namespace GameSolver {
namespace Connect4 {

class Solver {
 private:
   static constexpr int TABLE_SIZE = 24; 
   TranspositionTable< uint_t<Position::BOARD_PITCH_SIZE - TABLE_SIZE>, Position::position_t, uint8_t, TABLE_SIZE > transTable;
   unsigned long long nodeCount; 
   int columnOrder[Position::WIDTH];

   int negamax(const Position &P, int alpha, int beta);

 public:
   static const int INVALID_MOVE = -1000; 
   int solve(const Position &P, bool weak = false);

   std::vector<int> analyze(const Position &P, bool weak = false);
  int getColumnOrderAt(int index) const {
       if (index >= 0 && index < Position::WIDTH) {
           return columnOrder[index];
       }
       return -1; 
   }
   unsigned long long getNodeCount() const {
     return nodeCount;
   }

   void reset() {
     nodeCount = 0;
     transTable.reset(); 
   }

   Solver(); 
};

} 
} 
#endif