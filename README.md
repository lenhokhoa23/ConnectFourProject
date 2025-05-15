# ConnectFour-AI

Một dự án AI cho trò chơi Connect Four, hướng đến tối ưu hóa khả năng suy luận và hiệu năng tính toán thông qua các thuật toán tìm kiếm tiên tiến và các cấu trúc dữ liệu đặc biệt.

## Mục tiêu chính

- **Tìm kiếm tối ưu**  
  Sử dụng MiniMax/Negamax để đánh giá mọi nước đi có thể xảy ra, đảm bảo AI luôn chọn lựa phương án tốt nhất theo heuristic.

- **Cắt tỉa thông minh**  
  Kết hợp Alpha-Beta pruning để loại bỏ sớm các nhánh không cần thiết, giảm đáng kể số nút phải khám phá mà vẫn giữ được tính chính xác.

- **Biểu diễn hiệu quả**  
  Áp dụng Bitboard encoding — biểu diễn trạng thái bàn cờ dưới dạng bitmask — giúp tiết kiệm bộ nhớ, tăng tốc độ thao tác bitwise và đơn giản hóa việc cập nhật trạng thái.

- **Tái sử dụng kết quả**  
  Sử dụng Transposition Table (bảng chuyển vị) để lưu trữ và tra cứu nhanh các trạng thái đã khám phá, tránh tính toán lặp, tiết kiệm thời gian.

- **Tìm kiếm đa tầng**  
  Kết hợp Iterative Deepening với Null Window Search nhằm điều chỉnh độ sâu tìm kiếm linh hoạt, tăng hiệu quả cắt tỉa và đảm bảo thời gian phản hồi nhất quán.

- **Ngăn chặn thua nhanh**  
  Triển khai cơ chế Anticipate Direct Losing Moves để phát hiện sớm các nước đi dẫn đến thất bại và chủ động chặn đứng, nâng cao khả năng phòng thủ của AI.

- **Cải tiến hiệu năng tổng thể**  
  - Tối ưu hoá cho từng trường hợp cụ thể: Đi trước hay đi sau, đối thủ đi tối ưu hay không.
  - Generate book cho từng trường hợp đến state cuối cùng của bản cờ, đảm bảo luôn có nước đi tối ưu nhất với độ phức tạp O(1).
  - Giảm bộ nhớ lưu trữ và thời gian generate book bằng việc tối ưu lựa chọn trên cây trạng thái.
  

