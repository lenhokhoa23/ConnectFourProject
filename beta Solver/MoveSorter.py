# move_sorter.py

from Position import Position

class MoveSorter:
    """
    Lớp này hỗ trợ sắp xếp các nước đi tiếp theo dựa theo score.
    Bạn thêm các nước đi cùng với score vào rồi lấy ra theo thứ tự giảm dần score.
    Sử dụng thuật toán chèn (insertion sort) – rất hiệu quả khi số nước đi cần sắp xếp (tối đa là Position.WIDTH)
    và khi thứ tự ban đầu đã tương đối gần với thứ tự mong muốn.
    """
    def __init__(self):
        self.size = 0
        # Sử dụng danh sách cố định với độ dài Position.WIDTH: mỗi phần tử là một dict chứa 'move' và 'score'
        self.entries = [{"move": 0, "score": 0} for _ in range(Position.WIDTH)]
    
    def add(self, move: int, score: int) -> None:
        """Thêm một nước đi cùng với score vào bộ sắp xếp."""
        pos = self.size
        self.size += 1
        # Chèn nước đi theo thứ tự tăng dần của score (để khi lấy ra theo thứ tự ngược, ta có nước đi có score cao nhất trước)
        while pos > 0 and self.entries[pos - 1]["score"] > score:
            self.entries[pos] = self.entries[pos - 1]
            pos -= 1
        self.entries[pos] = {"move": move, "score": score}
    
    def getNext(self) -> int:
        """Lấy nước đi tiếp theo với score cao nhất (và loại bỏ khỏi bộ sắp xếp). Nếu không còn, trả về 0."""
        if self.size:
            self.size -= 1
            return self.entries[self.size]["move"]
        else:
            return 0
    
    def reset(self) -> None:
        """Xóa bộ sắp xếp (reset lại số lượng nước đi lưu)."""
        self.size = 0
