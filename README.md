# Ứng dụng Text-to-Speech (TTS) sử dụng Edge TTS

Đây là ứng dụng chuyển đổi văn bản thành giọng nói (Text-to-Speech) có giao diện đồ họa (GUI), sử dụng công cụ Microsoft Edge TTS chất lượng cao. Ứng dụng hỗ trợ đọc văn bản trực tiếp, đọc từ file Text (.txt), file Ebook (.epub) và file Phụ đề (.srt, .vtt).

## Tính năng chính

*   **Đọc văn bản đa dạng**: Hỗ trợ nhập liệu trực tiếp, file `.txt`, file `.epub`, file `.srt/.vtt`.
*   **Tách chương (Ebook)**: Hỗ trợ tự động tách và lưu file âm thanh theo từng chương đối với file `.epub`.
*   **Đồng bộ Audio với Phụ đề**: Tạo file audio từ file phụ đề (`.srt`, `.vtt`...), tự động chèn khoảng lặng (silence) để khớp thời gian với các mốc thời gian trong phụ đề.
*   **Giọng đọc chất lượng cao**: Sử dụng thư viện `edge-tts` để truy cập các giọng đọc tự nhiên của Microsoft Edge (Online).
*   **Tùy chỉnh linh hoạt**:
    *   Lựa chọn giọng đọc (Hỗ trợ tiếng Việt và nhiều ngôn ngữ khác).
    *   Điều chỉnh tốc độ đọc (Rate).
    *   Điều chỉnh âm lượng (Volume).
    *   **Tự động lưu cấu hình**: Ứng dụng tự động ghi nhớ các thiết lập của bạn cho lần mở sau.
*   **Điều khiển dễ dàng**:
    *   Phát (Play) - Phím tắt **F5**.
    *   Dừng (Stop) - Phím tắt **F6**.
    *   Lưu file (Save) - Phím tắt **Ctrl+S**.
*   **Lưu file âm thanh**:
    *   Lưu 1 file duy nhất cho toàn bộ nội dung.
    *   Lưu hàng loạt file (mỗi chương 1 file) cho Ebook.
    *   Lưu file audio đã đồng bộ thời gian cho Phụ đề.
*   **Giao diện hiện đại**: Sử dụng theme mới, có thanh tiến trình (Progress Bar) khi xử lý tác vụ nặng.

## Yêu cầu hệ thống

*   Python 3.8 trở lên.
*   Kết nối Internet (để tải giọng đọc từ Edge TTS).
*   **FFmpeg**: Cần cài đặt FFmpeg và thêm vào PATH để tính năng đồng bộ audio phụ đề hoạt động (do thư viện `pydub` yêu cầu).

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
3.  **Cài đặt FFmpeg**:
    *   Tải FFmpeg từ trang chủ.
    *   Giải nén và thêm thư mục `bin` vào biến môi trường PATH của hệ thống.

## Hướng dẫn sử dụng

1.  **Chạy ứng dụng**:
    Mở terminal tại thư mục dự án và chạy lệnh:
    ```bash
    python main.py
    ```

2.  **Trên giao diện ứng dụng**:
    *   **Nhập văn bản**: Gõ hoặc dán văn bản vào khung lớn ở giữa.
    *   **Tải file**: Nhấn nút "Chọn File" để tải nội dung từ file `.txt`, `.epub` hoặc `.srt/.vtt`.
    *   **Xử lý Phụ đề**:
        *   Tải file phụ đề (.srt, .vtt).
        *   Nội dung và mốc thời gian sẽ hiển thị để xem trước.
        *   Nhấn "Lưu MP3" -> Chọn "Lưu Audio Đồng Bộ Subtitle".
        *   Ứng dụng sẽ tạo ra 1 file MP3 duy nhất, trong đó các câu thoại khớp đúng thời điểm hiển thị trong file phụ đề.
    *   **Tách chương (Ebook)**:
        *   Tích chọn checkbox "Tách chương (EPUB)".
        *   Sau khi tải file, danh sách chương sẽ hiện ra để bạn chọn xem.
        *   Khi nhấn "Lưu MP3", ứng dụng sẽ yêu cầu chọn thư mục để lưu toàn bộ các chương thành các file riêng biệt.
    *   **Chọn giọng đọc/Tốc độ/Âm lượng**: Điều chỉnh tùy ý.
    *   **Nghe thử**: Nhấn nút "Phát" (F5).
    *   **Lưu file**: Nhấn nút "Lưu MP3" (Ctrl+S).

## Lưu ý

*   Tính năng đồng bộ phụ đề yêu cầu kết nối mạng ổn định vì phải tạo nhiều file audio nhỏ liên tục.
*   Quá trình xử lý file phụ đề dài có thể mất nhiều thời gian.

## Cấu trúc thư mục

*   `src/`: Mã nguồn chính.
    *   `gui/`: Giao diện người dùng.
    *   `core/`: Xử lý TTS và Audio.
    *   `utils/`: Xử lý file, cấu hình.
*   `tests/`: Các bài test cơ bản.
*   `main.py`: File khởi chạy.
*   `requirements.txt`: Danh sách thư viện.
