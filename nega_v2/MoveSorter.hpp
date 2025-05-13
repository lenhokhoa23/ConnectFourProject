#ifndef MOVE_SORTER_HPP
#define MOVE_SORTER_HPP

#include "Position.hpp"

namespace GameSolver {
namespace Connect4 {


class MoveSorter {
 public:

  void add(const Position::position_t move, const int score) {
    int pos = size++;
    for(; pos && entries[pos - 1].score > score; --pos) entries[pos] = entries[pos - 1];
    entries[pos].move = move;
    entries[pos].score = score;
  }

  Position::position_t getNext() {
    if(size)
      return entries[--size].move;
    else
      return 0;
  }

  void reset() {
    size = 0;
  }

  MoveSorter(): size{0} {
  }

 private:
  unsigned int size;

  struct {
    Position::position_t move;
    int score;
  } entries[Position::WIDTH];
};

} 
} 
#endif
