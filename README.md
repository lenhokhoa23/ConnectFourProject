# ConnectFour-AI

Một dự án AI cho trò chơi Connect Four thiết kế chuyên để thi đấu đối kháng với các AI khác.

---

## 📑 Mục lục

1. [🎯 Mục tiêu chính](#-mục-tiêu-chính)  
2. [🚀 Phiên bản game](#-phiên-bản-game)  
3. [🧠 Giải thuật và chiến lược](#-giải-thuật-và-chiến-lược)  

---

## 🎯 Mục tiêu chính
Mục tiêu của dự án là xây dựng một hệ thống trí tuệ nhân tạo chất lượng cao, có khả năng tự động phân tích mọi thế trận, dự đoán kết quả, và đưa ra quyết định tối ưu nhằm giành chiến thắng. Hệ thống phải duy trì hiệu suất xử lý nhanh, sử dụng cấu trúc dữ liệu hiệu quả để tiết kiệm bộ nhớ và thời gian tính toán, đồng thời luôn cập nhật, học hỏi từ kinh nghiệm để cải thiện khả năng chơi theo thời gian. Bên cạnh đó, AI cần có cơ chế tự điều chỉnh chiến thuật, linh hoạt ứng phó với mọi nước đi bất ngờ của đối thủ, đồng thời hỗ trợ tạo sẵn các tình huống mở đầu và kết thúc ván cờ để đảm bảo luôn luôn có sẵn lựa chọn tốt nhất. 


## 🚀 Phiên bản game

| Phiên bản | Tính năng chính | 
|----------|-----------------|
| `v1.0: MiniMax` | Sử dụng Minimax + Alphabeta Pruning. |
| `v1.1: MCTS` | Sử dụng giải thuật MCTS. |
| `v2.0: Beta Solver` | Triển khai thuật toán Solver được giải. | 
| `v2.1: nega v1` | Cải tiến opening book của solver cho từng trường hợp. | 
| `v2.2: nega v2` | Cải tiến thuật toán sử dụng cho luật chơi mới. | 

---

## 🧠 Giải thuật và chiến lược

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
