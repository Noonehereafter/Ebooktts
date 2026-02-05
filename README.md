# Ứng dụng Text-to-Speech (TTS) sử dụng Edge TTS

Đây là ứng dụng chuyển đổi văn bản thành giọng nói (Text-to-Speech) có giao diện đồ họa (GUI), sử dụng công cụ Microsoft Edge TTS chất lượng cao. Ứng dụng hỗ trợ đọc văn bản trực tiếp, đọc từ file Text (.txt) và file Ebook (.epub).

## Tính năng chính

*   **Đọc văn bản đa dạng**: Hỗ trợ nhập liệu trực tiếp, file `.txt`, file `.epub`.
*   **Giọng đọc chất lượng cao**: Sử dụng thư viện `edge-tts` để truy cập các giọng đọc tự nhiên của Microsoft Edge (Online).
*   **Tùy chỉnh linh hoạt**:
    *   Lựa chọn giọng đọc (Hỗ trợ tiếng Việt và nhiều ngôn ngữ khác).
    *   Điều chỉnh tốc độ đọc (Rate).
    *   Điều chỉnh âm lượng (Volume).
*   **Điều khiển dễ dàng**: Phát (Play), Dừng (Stop).
*   **Lưu file âm thanh**: Xuất ra file MP3 để nghe offline.
*   **Giao diện tiếng Việt**: Thân thiện và dễ sử dụng.

## Yêu cầu hệ thống

*   Python 3.8 trở lên.
*   Kết nối Internet (để tải giọng đọc từ Edge TTS).

## Hướng dẫn cài đặt

1.  **Clone hoặc tải về mã nguồn dự án**:
    ```bash
    git clone <đường-dẫn-repo-của-bạn>
    cd <tên-thư-mục-dự-án>
    ```

2.  **Cài đặt các thư viện phụ thuộc**:
    Sử dụng `pip` để cài đặt các thư viện được liệt kê trong `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## Hướng dẫn sử dụng

1.  **Chạy ứng dụng**:
    Mở terminal tại thư mục dự án và chạy lệnh:
    ```bash
    python main.py
    ```

2.  **Trên giao diện ứng dụng**:
    *   **Nhập văn bản**: Gõ hoặc dán văn bản vào khung lớn ở giữa.
    *   **Tải file**: Nhấn nút "Chọn File (.txt, .epub)" ở góc trên bên phải để tải nội dung từ file có sẵn.
    *   **Chọn giọng đọc**: Chọn giọng đọc mong muốn từ danh sách (Ứng dụng ưu tiên hiển thị giọng tiếng Việt lên đầu).
    *   **Chỉnh tốc độ/Âm lượng**: Kéo thanh trượt để điều chỉnh theo ý muốn.
    *   **Nghe thử**: Nhấn nút "Phát".
    *   **Lưu file**: Nhấn nút "Lưu MP3" và chọn nơi lưu file âm thanh.

## Lưu ý

*   Do sử dụng dịch vụ online của Microsoft Edge, bạn cần kết nối mạng để lấy danh sách giọng đọc và tạo âm thanh.
*   Quá trình chuyển đổi văn bản dài có thể mất một chút thời gian tùy thuộc vào tốc độ mạng.

## Cấu trúc thư mục

*   `src/`: Mã nguồn chính.
    *   `gui/`: Giao diện người dùng.
    *   `core/`: Xử lý TTS và Audio.
    *   `utils/`: Xử lý file.
*   `tests/`: Các bài test cơ bản.
*   `main.py`: File khởi chạy.
*   `requirements.txt`: Danh sách thư viện.
