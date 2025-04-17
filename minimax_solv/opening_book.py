# -*- coding: utf-8 -*-
# Equivalent of OpeningBook.hpp from Connect4 Game Solver

import sys
import os
import struct
import math
from typing import Optional, Tuple

# Assumes position.py and transposition_table.py are in the same package
# Use relative imports if part of a package structure
try:
    from .position import Position
    from .transposition_table import TranspositionTable
except ImportError:
    # Fallback for running standalone (if files are in the same directory)
    from position import Position
    from transposition_table import TranspositionTable


class OpeningBook:
    """
    Manages an opening book for Connect 4, stored in a binary file.
    Uses a TranspositionTable internally to store positions and results.
    Positions are queried using their symmetric key (key3).
    """

    # Define format strings for struct packing/unpacking based on key bytes
    _KEY_FORMAT = {
        1: '<B', # 1 byte unsigned char
        2: '<H', # 2 bytes unsigned short (little-endian)
        4: '<I', # 4 bytes unsigned int (little-endian)
        8: '<Q'  # 8 bytes unsigned long long (little-endian)
        # Add more if needed, e.g., for partial_key_bytes=3? Unlikely.
    }
    _VALUE_FORMAT = '<B' # Always 1 byte unsigned char for value

    def __init__(self, width: int = Position.WIDTH, height: int = Position.HEIGHT):
        """
        Initializes an empty OpeningBook for a given board size.

        Args:
            width: Board width.
            height: Board height.
        """
        self.width: int = width
        self.height: int = height
        self.T: Optional[TranspositionTable] = None
        self.depth: int = -1
        self._log_size: int = -1 # Store the log_size used when loading
        self._partial_key_bytes: int = -1 # Store key bytes used when loading

    def load(self, filename: str) -> bool:
        """
        Loads the opening book data from a binary file.

        File Format:
        - 1 byte: board width
        - 1 byte: board height
        - 1 byte: max stored position depth
        - 1 byte: partial key size in bytes (1, 2, 4, or 8)
        - 1 byte: value size in bytes (must be 1)
        - 1 byte: log_size = log2(approx table size).
        - size * partial_key_bytes: key data
        - size * value_bytes: value data

        Args:
            filename: Path to the opening book file.

        Returns:
            True if loading was successful, False otherwise.
        """
        self.depth = -1 # Reset depth in case of failure
        self.T = None   # Reset table
        self._log_size = -1
        self._partial_key_bytes = -1

        if not os.path.exists(filename):
             print(f"Error: Opening book file not found: {filename}", file=sys.stderr)
             return False

        try:
            with open(filename, 'rb') as ifs:
                print(f"Loading opening book from file: {filename}. ", file=sys.stderr, end="")

                # --- Read Header ---
                try:
                    header_fmt = '<BBBBBB' # width, height, depth, key_bytes, val_bytes, log_size
                    header_size = struct.calcsize(header_fmt)
                    header_data = ifs.read(header_size)
                    if len(header_data) < header_size:
                        raise IOError("Unexpected EOF reading header.")

                    file_width, file_height, file_depth, partial_key_bytes, value_bytes, log_size = \
                        struct.unpack(header_fmt, header_data)

                except struct.error as e:
                    raise IOError(f"Error unpacking header: {e}")

                # --- Validate Header ---
                if file_width != self.width:
                    raise ValueError(f"Invalid width (found: {file_width}, expected: {self.width})")
                if file_height != self.height:
                    raise ValueError(f"Invalid height (found: {file_height}, expected: {self.height})")
                if not (0 <= file_depth <= self.width * self.height):
                     raise ValueError(f"Invalid depth (found: {file_depth})")
                if partial_key_bytes not in self._KEY_FORMAT:
                    raise ValueError(f"Invalid internal key size (found: {partial_key_bytes} bytes)")
                if value_bytes != 1:
                    raise ValueError(f"Invalid value size (found: {value_bytes}, expected: 1)")
                if not (0 <= log_size <= 40): # Reasonable limit for log_size
                    raise ValueError(f"Invalid log2(size) (found: {log_size})")

                # --- Initialize Transposition Table ---
                partial_key_bits = partial_key_bytes * 8
                try:
                    self.T = TranspositionTable(log_size=log_size, partial_key_bits=partial_key_bits)
                except Exception as e:
                     raise RuntimeError(f"Failed to initialize TranspositionTable: {e}")

                table_size = self.T.size
                key_read_size = table_size * partial_key_bytes
                value_read_size = table_size * value_bytes # Should be table_size

                # --- Read Key Data ---
                key_data = ifs.read(key_read_size)
                if len(key_data) < key_read_size:
                    raise IOError("Unexpected EOF reading key data.")

                # --- Read Value Data ---
                value_data = ifs.read(value_read_size)
                if len(value_data) < value_read_size:
                     raise IOError("Unexpected EOF reading value data.")

                # --- Populate Table ---
                key_fmt = self._KEY_FORMAT[partial_key_bytes]
                try:
                    unpacked_keys = struct.iter_unpack(key_fmt, key_data)
                    for i, (key_val,) in enumerate(unpacked_keys):
                        # Store the raw partial key bytes interpretation
                        # Handle potential 0 value if it was written for None
                        self.T.keys[i] = key_val if key_val != 0 else None # Assume 0 means empty slot if loaded
                        # A better approach might be needed if 0 is a valid partial key
                        # but given C++ memset(0), this seems plausible.

                except struct.error as e:
                    raise IOError(f"Error unpacking key data: {e}")

                try:
                    unpacked_values = struct.iter_unpack(self._VALUE_FORMAT, value_data)
                    for i, (val,) in enumerate(unpacked_values):
                         self.T.values[i] = val
                except struct.error as e:
                     raise IOError(f"Error unpacking value data: {e}")

                # Success - Update state
                self.depth = file_depth
                self._log_size = log_size
                self._partial_key_bytes = partial_key_bytes
                print("done", file=sys.stderr)
                return True

        except (IOError, ValueError, RuntimeError, FileNotFoundError) as e:
            print(f"\nError loading opening book '{filename}': {e}", file=sys.stderr)
            self.T = None
            self.depth = -1
            self._log_size = -1
            self._partial_key_bytes = -1
            return False

    def save(self, output_file: str) -> bool:
        """
        Saves the current opening book data to a binary file.

        Args:
            output_file: Path to the file where the book will be saved.

        Returns:
            True if saving was successful, False otherwise.
        """
        if self.T is None or self.depth < 0:
            print("Error: Cannot save empty or unloaded opening book.", file=sys.stderr)
            return False

        if self._log_size < 0 or self._partial_key_bytes <= 0:
             print("Error: Book metadata (log_size/key_bytes) missing. Load book before saving.", file=sys.stderr)
             return False

        try:
            with open(output_file, 'wb') as ofs:
                # --- Write Header ---
                value_bytes = 1 # Fixed
                header_fmt = '<BBBBBB' # width, height, depth, key_bytes, val_bytes, log_size
                header_data = struct.pack(header_fmt,
                                          self.width,
                                          self.height,
                                          self.depth,
                                          self._partial_key_bytes,
                                          value_bytes,
                                          self._log_size)
                ofs.write(header_data)

                # --- Write Key Data ---
                key_fmt = self._KEY_FORMAT[self._partial_key_bytes]
                packed_keys = bytearray()
                for key_val in self.T.keys:
                    # Pack 0 if key is None (empty slot)
                    packed_keys.extend(struct.pack(key_fmt, key_val if key_val is not None else 0))
                ofs.write(packed_keys)

                # --- Write Value Data ---
                packed_values = bytearray()
                for val in self.T.values:
                    packed_values.extend(struct.pack(self._VALUE_FORMAT, val))
                ofs.write(packed_values)

            print(f"Opening book successfully saved to: {output_file}", file=sys.stderr)
            return True

        except (IOError, struct.error) as e:
            print(f"Error saving opening book to '{output_file}': {e}", file=sys.stderr)
            return False


    def get(self, p: Position) -> int:
        """
        Queries the opening book for a given position.

        Args:
            p: The Position object to query.

        Returns:
            The stored value (typically a score or result indicator, 0-255)
            if the position is found within the book's depth limit,
            otherwise 0.
        """
        if self.T is None or p.nb_moves() > self.depth:
            return 0 # Not loaded or position is too deep

        # Query using the symmetric key (key3)
        key = p.key3()
        # The get method of TranspositionTable already handles lookup and returns 0 on miss
        return self.T.get(key)

    @property
    def is_loaded(self) -> bool:
        """Returns True if an opening book is currently loaded."""
        return self.T is not None and self.depth >= 0


# Example Usage:
if __name__ == "__main__":
    # Create a dummy opening book file for testing load
    TEST_FILENAME = "dummy_book.bin"
    width, height = 7, 6
    depth = 10
    partial_key_bytes = 4 # uint32_t
    value_bytes = 1 # uint8_t
    log_size = 5 # Target 32, next prime is 37
    table_size = 37
    key_bits = partial_key_bytes * 8

    try:
        with open(TEST_FILENAME, 'wb') as ofs:
            print(f"Creating dummy book file: {TEST_FILENAME}")
            # Header
            header_fmt = '<BBBBBB'
            header = struct.pack(header_fmt, width, height, depth, partial_key_bytes, value_bytes, log_size)
            ofs.write(header)
            # Dummy Keys (write 0s for empty slots, maybe one real key)
            key_fmt = OpeningBook._KEY_FORMAT[partial_key_bytes]
            dummy_key = 123456789 & ((1 << key_bits) - 1) # Example partial key
            keys_written = 0
            for i in range(table_size):
                 # Put dummy key at index matching dummy_key % table_size
                 if i == dummy_key % table_size:
                     ofs.write(struct.pack(key_fmt, dummy_key))
                     keys_written +=1
                 else:
                     ofs.write(struct.pack(key_fmt, 0)) # Write 0 for empty/None
            assert keys_written == 1 # Ensure we wrote the key
            # Dummy Values (write 0s, maybe one real value matching the key)
            val_fmt = OpeningBook._VALUE_FORMAT
            vals_written = 0
            for i in range(table_size):
                  if i == dummy_key % table_size:
                      ofs.write(struct.pack(val_fmt, 99)) # Example value
                      vals_written += 1
                  else:
                      ofs.write(struct.pack(val_fmt, 0))
            assert vals_written == 1

    except Exception as e:
        print(f"Failed to create dummy file: {e}")

    # Test Loading
    print("-" * 20)
    book = OpeningBook(width=width, height=height)
    success = book.load(TEST_FILENAME)
    print(f"Load successful: {success}")
    print(f"Book loaded: {book.is_loaded}")
    if book.is_loaded:
        print(f"Book depth: {book.depth}")
        print(f"Table size: {len(book.T)}")
        print(f"Log size: {book._log_size}")
        print(f"Partial key bytes: {book._partial_key_bytes}")

        # Test Get (needs a Position object and key3 calculation)
        # Create a dummy position that *might* hash to the stored key
        # This part is hard without running the actual Position logic
        class DummyPosition:
            _moves = 5
            def nb_moves(self): return self._moves
            def key3(self): return 123456789 # The key we stored

        class DummyPositionMiss:
             _moves = 5
             def nb_moves(self): return self._moves
             def key3(self): return 987654321 # A different key

        class DummyPositionDeep:
             _moves = 15
             def nb_moves(self): return self._moves
             def key3(self): return 123456789

        print("\nTesting get():")
        pos_hit = DummyPosition()
        print(f"Get(pos_hit): {book.get(pos_hit)}") # Should be 99

        pos_miss = DummyPositionMiss()
        print(f"Get(pos_miss): {book.get(pos_miss)}") # Should be 0

        pos_deep = DummyPositionDeep()
        print(f"Get(pos_deep): {book.get(pos_deep)}") # Should be 0 (too deep)


    # Test Saving
    print("-" * 20)
    SAVE_FILENAME = "saved_book.bin"
    if book.is_loaded:
        save_success = book.save(SAVE_FILENAME)
        print(f"Save successful: {save_success}")

        # Optional: Compare dummy_book.bin and saved_book.bin (should be identical if load/save correct)
        if save_success and os.path.exists(SAVE_FILENAME):
            with open(TEST_FILENAME, 'rb') as f1, open(SAVE_FILENAME, 'rb') as f2:
                print(f"Comparing original and saved files... Same: {f1.read() == f2.read()}")

    # Clean up test files
    if os.path.exists(TEST_FILENAME): os.remove(TEST_FILENAME)
    if os.path.exists(SAVE_FILENAME): os.remove(SAVE_FILENAME)