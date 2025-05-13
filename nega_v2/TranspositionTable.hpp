
#ifndef TRANSPOSITION_TABLE_HPP
#define TRANSPOSITION_TABLE_HPP

#include <cstring>

namespace GameSolver {
namespace Connect4 {


constexpr uint64_t med(uint64_t min, uint64_t max) {
  return (min + max) / 2;
}

constexpr bool has_factor(uint64_t n, uint64_t min, uint64_t max) {
  return min * min > n ? false : 
         min + 1 >= max ? n % min == 0 :
         has_factor(n, min, med(min, max)) || has_factor(n, med(min, max), max);
}


constexpr uint64_t next_prime(uint64_t n) {
  return has_factor(n, 2, n) ? next_prime(n + 1) : n;
}

constexpr unsigned int log2(unsigned int n) {
  return n <= 1 ? 0 : log2(n / 2) + 1;
}


template<class key_t, class value_t>
class TableGetter {
 private:
  virtual void* getKeys() = 0;
  virtual void* getValues() = 0;
  virtual size_t getSize() = 0;
  virtual int getKeySize() = 0;
  virtual int getValueSize() = 0;

 public:
  virtual value_t get(key_t key) const = 0;
  virtual ~TableGetter() {};

 friend class OpeningBook;
};

template<int S> using uint_t =
  typename std::conditional < S <= 8, uint_least8_t,
  typename std::conditional < S <= 16, uint_least16_t,
  typename std::conditional<S <= 32, uint_least32_t,
  uint_least64_t>::type>::type >::type;

template<class partial_key_t, class key_t, class value_t, int log_size>
class TranspositionTable : public TableGetter<key_t, value_t> {
 private:
  static const size_t size = next_prime(1 << log_size); 
  partial_key_t *K;    
  value_t *V; 

  void* getKeys()    override {return K;}
  void* getValues()  override {return V;}
  size_t getSize()   override {return size;}
  int getKeySize()   override {return sizeof(partial_key_t);}
  int getValueSize() override {return sizeof(value_t);}

  size_t index(key_t key) const {
    return key % size;
  }

 public:
  TranspositionTable() {
    K = new partial_key_t[size];
    V = new value_t[size];
    reset();
  }

  ~TranspositionTable() {
    delete[] K;
    delete[] V;
  }

  void reset() { 
    memset(K, 0, size * sizeof(partial_key_t));
    memset(V, 0, size * sizeof(value_t));
  }

  void put(key_t key, value_t value) {
    size_t pos = index(key);
    K[pos] = key; 
    V[pos] = value;
  }

  value_t get(key_t key) const override {
    size_t pos = index(key);
    if(K[pos] == (partial_key_t)key) return V[pos]; 
    else return 0;
  }
};

} 
} 
#endif
