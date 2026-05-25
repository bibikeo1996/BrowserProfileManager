# Phiên bản v0.4.0 (Isolated Multi-Profile Architecture)

## 🔄 Cập Nhật Kiến Trúc (Architecture Update)
- **LOẠI BỎ:** Cơ chế quét (`BrowserScanner`) và tìm kiếm thư mục Profile mặc định của hệ thống bị gỡ bỏ để tránh xung đột cấu hình.
- **TÍNH NĂNG MỚI:** Thay thế bằng cơ chế **Isolated Profiles**. Tất cả Profiles tự động hóa giờ đây được lưu trữ hoàn toàn độc lập tại thư mục `.automation_profiles/` nhằm ngăn chặn 100% lỗi File Lock của SQLite và lỗi Safe Storage của macOS Keychain.
- **SỬA LỖI:** Vô hiệu hóa thanh cảnh báo vàng "Unsupported command-line flag" trên Chrome (bằng cờ `--test-type`).
- **SỬA LỖI:** Ẩn toàn bộ log rác nội bộ từ `GoogleUpdater` và `Crashpad` để giữ cho Terminal luôn gọn gàng.

## 🚀 Hướng Dẫn Sử Dụng Nhanh (Quick Start)

Vì hệ thống không còn dùng Profile gốc của Chrome, bạn cần thiết lập Profile và đăng nhập lần đầu tiên (Chỉ 1 lần duy nhất).

### Bước 1: Setup Profile (Khởi tạo và đăng nhập thủ công)
```python
from BrowserProfileManager import setup_automation_profile

# Gọi lệnh này để mở trình duyệt.
# Tự tay đăng nhập tài khoản. Xong thì bấm nút X đóng trình duyệt lại.
setup_automation_profile("Profile_Upload_TikTok")
```

### Bước 2: Chạy Tự Động Hóa (Automation)
Sau khi setup xong, Profile này đã có sẵn Cookie. Ở các lần sau, bạn chỉ cần gọi `BrowserSession` như bình thường:
```python
from BrowserProfileManager import BrowserSession
from playwright.sync_api import sync_playwright

with BrowserSession("Profile_Upload_TikTok") as endpoint:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint)
        page = browser.contexts[0].pages[0]
        
        # Mở web (Đã đăng nhập sẵn)
        page.goto("https://tiktok.com/creator")
```
