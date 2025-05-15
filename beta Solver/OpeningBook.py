import os
import math
import struct
from typing import Any, Optional
from Position import Position
# Giả sử bạn đã có module position với lớp Position đã được chuyển đổi.
# from position import Position
# Giả sử bạn đã có module transposition_table với lớp TranspositionTable đã được chuyển đổi.
# from transposition_table import TranspositionTable

# Nếu chưa có, bạn có thể dùng phiên bản đơn giản của TranspositionTable như dưới đây:
class TranspositionTable:
    """
    Một cài đặt đơn giản của transposition table.
    Các trường:
      - size: kích thước bảng (số nguyên tố gần nhất với 1 << log_size)
      - K: danh sách lưu các khóa (dạng int)
      - V: danh sách lưu các giá trị (ở đây giả sử giá trị là số nguyên 1 byte)
      - key_size: số byte dùng để lưu khóa nội bộ
      - value_size: số byte dùng để lưu giá trị
    """
    def __init__(self, log_size: int):
        self.size: int = self._next_prime(1 << log_size)
        # Khởi tạo bảng với giá trị 0
        self.K: list[int] = [0] * self.size
        self.V: list[int] = [0] * self.size
        # Mặc định; chúng ta sẽ set lại sau theo thông tin từ file
        self.key_size: int = 1  
        self.value_size: int = 1

    @staticmethod
    def _next_prime(n: int) -> int:
        def is_prime(x: int) -> bool:
            if x < 2:
                return False
            for i in range(2, int(math.sqrt(x)) + 1):
                if x % i == 0:
                    return False
            return True

        while not is_prime(n):
            n += 1
        return n

    def getKeys(self) -> list[int]:
        return self.K

    def getValues(self) -> list[int]:
        return self.V

    def getSize(self) -> int:
        return self.size

    def getKeySize(self) -> int:
        return self.key_size

    def getValueSize(self) -> int:
        return self.value_size

    def put(self, key: int, value: Any) -> None:
        pos = key % self.size
        self.K[pos] = key  # Ở phiên bản C++ có thể dùng key rút gọn; ở đây ta lưu nguyên key.
        self.V[pos] = value

    def get(self, key: int) -> int:
        pos = key % self.size
        if self.K[pos] == key:
            return self.V[pos]
        else:
            return 0

    def reset(self) -> None:
        self.K = [0] * self.size
        self.V = [0] * self.size


# Hàm log2 sử dụng math.log2 (sẽ trả về float nên ép về int)
def log2_int(n: int) -> int:
    return int(math.log2(n))


def init_transposition_table(partial_key_bytes: int, log_size: int) -> Optional[TranspositionTable]:
    """
    Khởi tạo transposition table dựa trên kích thước của partial key (1, 2 hoặc 4 byte)
    và log_size (số log2 của kích thước bảng).
    Nếu partial_key_bytes không hợp lệ, in ra lỗi và trả về None.
    """
    if partial_key_bytes in (1, 2, 4):
        table = TranspositionTable(log_size)
        table.key_size = partial_key_bytes
        table.value_size = 1  # theo định dạng file, giá trị luôn chiếm 1 byte.
        return table
    else:
        print("Invalid internal key size:", partial_key_bytes)
        return None


class OpeningBook:
    """
    Lớp OpeningBook dùng để lưu và truy xuất thông tin mở đầu (opening book).
    
    Định dạng file opening book (nhị phân):
      - 1 byte: board width
      - 1 byte: board height
      - 1 byte: max stored position depth
      - 1 byte: internal key size (số byte)
      - 1 byte: value size (số byte, phải bằng 1)
      - 1 byte: log_size = log2(size); số phần tử được lưu: size là số nguyên tố nhỏ nhất > 2^(log_size)
      - Sau đó là các phần tử của key (size * key_size bytes)
      - Sau đó là các phần tử của value (size * value_size bytes)
    """
    def __init__(self, width: int, height: int, depth: int = -1, T: Optional[TranspositionTable] = None):
        self.T = T  # Transposition table
        self.width: int = width
        self.height: int = height
        self.depth: int = depth  # Nếu -1 thì book đang trống

    def load(self, filename: str) -> None:
        self.depth = -1  # reset depth
        self.T = None    # giải phóng transposition table cũ (Python sẽ dọn dẹp)
        try:
            with open(filename, "rb") as f:
                print(f"Loading opening book from file: {filename}. ", end="")
                # Đọc 6 byte đầu tiên
                header = f.read(6)
                if len(header) < 6:
                    print("Failed reading header")
                    return
                _width, _height, _depth, partial_key_bytes, value_bytes, log_size = struct.unpack("6B", header)
                if _width != self.width:
                    print(f"Unable to load opening book: invalid width (found: {_width}, expected: {self.width})")
                    return
                if _height != self.height:
                    print(f"Unable to load opening book: invalid height (found: {_height}, expected: {self.height})")
                    return
                if _depth > self.width * self.height:
                    print(f"Unable to load opening book: invalid depth (found: {_depth})")
                    return
                if partial_key_bytes > 8:
                    print(f"Unable to load opening book: invalid internal key size (found: {partial_key_bytes})")
                    return
                if value_bytes != 1:
                    print(f"Unable to load opening book: invalid value size (found: {value_bytes}, expected: 1)")
                    return
                if log_size > 40:
                    print(f"Unable to load opening book: invalid log2(size) (found: {log_size})")
                    return

                self.T = init_transposition_table(partial_key_bytes, log_size)
                if self.T is None:
                    print("Unable to initialize opening book")
                    return

                num_entries = self.T.getSize()
                # Đọc keys: tổng số byte = num_entries * partial_key_bytes
                keys_data = f.read(num_entries * partial_key_bytes)
                # Đọc values: tổng số byte = num_entries * value_bytes
                values_data = f.read(num_entries * value_bytes)
                if (len(keys_data) < num_entries * partial_key_bytes or
                        len(values_data) < num_entries * value_bytes):
                    print("Unable to load data from opening book")
                    return

                # Giải mã dữ liệu keys: nếu partial_key_bytes == 1 thì danh sách các số 0..255
                if partial_key_bytes == 1:
                    self.T.K = list(keys_data)
                else:
                    self.T.K = [int.from_bytes(keys_data[i * partial_key_bytes:(i + 1) * partial_key_bytes], byteorder="little")
                                for i in range(num_entries)]
                # Với values, vì mỗi value là 1 byte:
                self.T.V = list(values_data)
                self.depth = _depth
                print("done")
        except IOError:
            print("Unable to load opening book:", filename)

    def save(self, output_file: str) -> None:
        try:
            with open(output_file, "wb") as f:
                # Ghi header: width, height, depth, key size, value size, log_size
                f.write(struct.pack("B", self.width))
                f.write(struct.pack("B", self.height))
                f.write(struct.pack("B", self.depth))
                f.write(struct.pack("B", self.T.getKeySize()))
                f.write(struct.pack("B", self.T.getValueSize()))
                f.write(struct.pack("B", log2_int(self.T.getSize())))
                # Ghi keys
                for key in self.T.K:
                    f.write(key.to_bytes(self.T.getKeySize(), byteorder="little"))
                # Ghi values
                for value in self.T.V:
                    f.write(value.to_bytes(self.T.getValueSize(), byteorder="little"))
        except IOError:
            print("Unable to save opening book to file:", output_file)

    def get(self, P: "Position") -> int:
        """
        Nếu số nước đi của vị trí P lớn hơn depth của book thì không có dữ liệu (trả về 0),
        ngược lại truy xuất dữ liệu từ transposition table bằng key3 của P.
        """
        if P.nb_moves() > self.depth:
            return 0
        else:
            return self.T.get(P.key3())

    # Trong Python không cần định nghĩa destructor (__del__) cho việc giải phóng T vì GC lo.
