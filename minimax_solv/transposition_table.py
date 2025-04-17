import math
from typing import Optional, List

def _is_prime(n: int) -> bool:
    """Basic primality test."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def _next_prime(n: int) -> int:
    """Find the smallest prime number greater than or equal to n."""
    if n <= 2:
        return 2
    prime = n
    # Ensure starting point is odd if n > 2
    if prime % 2 == 0:
        prime += 1
    while True:
        if _is_prime(prime):
            return prime
        prime += 2 # Check only odd numbers

# --- Transposition Table Class ---
class TranspositionTable:
    """
    A simple fixed-size hash map implementing a transposition table.

    Uses modulo hashing and overwrites entries on collision.
    Stores partial keys to potentially save memory, matching C++ behavior.
    Values of 0 are treated as cache misses.
    """

    def __init__(self, log_size: int, partial_key_bits: int = 32):
        """
        Initializes the Transposition Table.

        Args:
            log_size: Base-2 logarithm of the desired table size.
                      The actual size will be the next prime >= 2^log_size.
            partial_key_bits: Number of bits to store for the key (truncation).
                              Must be positive.
        """
        if not isinstance(log_size, int) or log_size < 0:
            raise ValueError("log_size must be a non-negative integer")
        if not isinstance(partial_key_bits, int) or partial_key_bits <= 0:
            raise ValueError("partial_key_bits must be a positive integer")

        target_size = 1 << log_size
        self.size: int = _next_prime(target_size)
        self.partial_key_bits: int = partial_key_bits
        self.partial_key_mask: int = (1 << partial_key_bits) - 1

        # Use None in keys list to indicate an empty slot, distinguishing from key 0.
        self.keys: List[Optional[int]] = [None] * self.size
        # Use 0 in values list to indicate a cache miss, matching C++ get logic.
        self.values: List[int] = [0] * self.size
        # print(f"TT Initialized: log_size={log_size}, target={target_size}, prime_size={self.size}, key_bits={partial_key_bits}") # Debug

    def _index(self, key: int) -> int:
        """Calculates the hash index for a given key."""
        # Ensure key is non-negative before modulo if necessary, though Position.key() should be positive.
        # return abs(key) % self.size
        return key % self.size # Position.key() seems positive based on addition

    def reset(self):
        """Clears the transposition table, filling entries with default values."""
        # print("TT Resetting...") # Debug
        self.keys = [None] * self.size
        self.values = [0] * self.size

    def put(self, key: int, value: int):

        if value == 0:
            # Optional: Warn or raise error if trying to store 0, as it means 'miss' on get.
            # print(f"Warning: Attempting to store value 0 for key {key} in TT.")
            # return # Or proceed, knowing get will return 0 anyway.
            pass

        pos = self._index(key)
        # Store only the truncated (partial) key
        self.keys[pos] = key & self.partial_key_mask
        self.values[pos] = value
        # print(f"TT Put: key={key}, value={value}, pos={pos}, stored_key={self.keys[pos]}") # Debug


    def get(self, key: int) -> int:

        pos = self._index(key)
        stored_partial_key = self.keys[pos]

        # Calculate the partial key of the input key for comparison
        input_partial_key = key & self.partial_key_mask

        # Check if the slot has been used (key is not None) AND
        # if the stored partial key matches the input's partial key.
        if stored_partial_key is not None and stored_partial_key == input_partial_key:
            # print(f"TT Hit: key={key}, pos={pos}, value={self.values[pos]}") # Debug
            return self.values[pos]
        else:
            # print(f"TT Miss: key={key}, pos={pos}, stored_key={stored_partial_key}") # Debug
            return 0 # Cache miss

    def __len__(self) -> int:
        """Returns the allocated size (number of slots) of the table."""
        return self.size

# Example Usage
if __name__ == "__main__":
    tt = TranspositionTable(log_size=4, partial_key_bits=8)
    print(f"Table size: {len(tt)}")

    key1 = 0b1111000010101010
    partial1 = key1 & 0xFF
    index1 = key1 % 17

    key2 = 0b0000111110101010
    partial2 = key2 & 0xFF
    index2 = key2 % 17

    key3 = 0b1111000001010101
    partial3 = key3 & 0xFF

    print(f"Key1: {key1}, Partial1: {partial1}, Index1: {index1}")
    print(f"Key2: {key2}, Partial2: {partial2}, Index2: {index2}")

    tt.put(key1, 100)
    print(f"\nGet Key1: {tt.get(key1)}")
    print(f"Get Key2: {tt.get(key2)}")
    print(f"Get Key3: {tt.get(key3)}")

    tt.put(key2, 200)
    print(f"\nPut Key2 (Value 200)")
    print(f"Get Key1: {tt.get(key1)}")
    print(f"Get Key2: {tt.get(key2)}")

    tt.reset()
    print(f"\nAfter Reset:")
    print(f"Get Key1: {tt.get(key1)}")
    print(f"Get Key2: {tt.get(key2)}")