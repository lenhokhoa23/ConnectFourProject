import math
from typing import Any, List

def med(min_val: int, max_val: int) -> int:
    return (min_val + max_val) // 2

def has_factor(n: int, min_val: int, max_val: int) -> bool:
    if min_val * min_val > n:
        return False
    if min_val + 1 >= max_val:
        return n % min_val == 0
    return has_factor(n, min_val, med(min_val, max_val)) or has_factor(n, med(min_val, max_val), max_val)

def next_prime(n: int) -> int:
    if has_factor(n, 2, n):
        return next_prime(n + 1)
    return n

def log2_int(n: int) -> int:
    if n <= 1:
        return 0
    return log2_int(n // 2) + 1

class TranspositionTable:
    """
    Bản chuyển đổi của TranspositionTable từ C++ sang Python.
    Các tham số:
      - log_size: lũy thừa của kích thước bảng, bảng có kích thước là số nguyên tố gần nhất với (1 << log_size).
      - key_size: số byte dùng để lưu khóa (partial key) nội bộ.
      - value_size: số byte dùng để lưu giá trị.
    """
    def __init__(self, log_size: int, key_size: int = 1, value_size: int = 1):
        # Tính kích thước của bảng là số nguyên tố gần nhất với 1 << log_size.
        self.size: int = next_prime(1 << log_size)
        self.K: List[int] = [0] * self.size
        self.V: List[Any] = [0] * self.size
        self.key_size: int = key_size
        self.value_size: int = value_size

    def reset(self) -> None:
        self.K = [0] * self.size
        self.V = [0] * self.size

    def _index(self, key: int) -> int:
        return key % self.size

    def put(self, key: int, value: Any) -> None:
        pos = self._index(key)
        self.K[pos] = key  # Ở C++ có thể lưu rút gọn key; ở đây ta lưu nguyên key
        self.V[pos] = value

    def get(self, key: int) -> Any:
        pos = self._index(key)
        if self.K[pos] == key:
            return self.V[pos]
        else:
            return 0

    def getKeySize(self) -> int:
        """Trả về số byte dùng để lưu key."""
        return self.key_size

    def getValueSize(self) -> int:
        """Trả về số byte dùng để lưu value."""
        return self.value_size

    def getSize(self) -> int:
        """Trả về kích thước bảng."""
        return self.size