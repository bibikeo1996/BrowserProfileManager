import os
import subprocess
import logging
from pathlib import Path
from .Config.Settings import AUTOMATION_PROFILES_DIR, EXECUTABLE_PATHS

logger = logging.getLogger(__name__)

def setup_automation_profile(profile_name: str, browser_name: str = "Chrome"):
    """
    Mở trình duyệt có UI trỏ vào thư mục profile độc lập để người dùng đăng nhập bằng tay lần đầu.
    Hệ thống sẽ chờ cho đến khi người dùng tự đóng trình duyệt mới kết thúc.
    """
    # 1. Tạo thư mục profile nếu chưa có
    profile_dir = Path(AUTOMATION_PROFILES_DIR) / profile_name
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Lấy đường dẫn file thực thi
    exec_path = EXECUTABLE_PATHS.get(browser_name)
    if not exec_path or not os.path.exists(exec_path):
        raise FileNotFoundError(f"Không tìm thấy file thực thi của trình duyệt: {exec_path}")
        
    # 3. Tham số khởi chạy (Anti-bot + Bypass Keychain)
    args = [
        exec_path,
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--password-store=basic",  # Rất quan trọng để bypass macOS Keychain
        "--disable-blink-features=AutomationControlled",
        "--test-type"  # Ẩn cảnh báo "unsupported command-line flag"
    ]
    
    print("\n" + "="*80)
    print(f"🚨 CẢNH BÁO: Đang mở {browser_name} cho Profile độc lập '{profile_name}'")
    print(f"📂 Lưu trữ tại: {profile_dir}")
    print("👉 HƯỚNG DẪN: Hãy đăng nhập tài khoản và cài đặt các Extension cần thiết.")
    print("👉 QUAN TRỌNG: Sau khi xong, hãy ĐÓNG TRÌNH DUYỆT BẰNG TAY (Bấm dấu X) để hoàn tất!")
    print("="*80 + "\n")
    
    try:
        process = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        process.wait()  # Dừng script cho đến khi user đóng cửa sổ
        print(f"\n✅ Setup Profile '{profile_name}' hoàn tất! Cookie và phiên đăng nhập đã được lưu.\n")
    except KeyboardInterrupt:
        print("\n⚠️ Đã hủy bỏ quá trình setup.\n")
        process.terminate()
