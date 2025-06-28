"""
測試版本管理模組
"""
from utils.version_manager import version_manager

def test_version_manager():
    print("=== 測試版本管理模組 ===")
    
    # 1. 建立新版本
    print("\n1. 建立新版本...")
    new_version = version_manager.create_new_version()
    print(f"新版本ID: {new_version}")
    
    # 2. 取得最新版本
    print("\n2. 取得最新版本...")
    latest_version = version_manager.get_latest_version()
    print(f"最新版本: {latest_version}")
    
    # 3. 取得當前版本
    print("\n3. 取得當前版本...")
    current_version = version_manager.get_current_version()
    print(f"當前版本: {current_version}")
    
    # 4. 列出所有版本
    print("\n4. 列出所有版本...")
    versions = version_manager.list_versions()
    for version in versions:
        print(f"  - {version['version_id']}: {version['description']}")
    
    # 5. 測試路徑取得
    print("\n5. 測試路徑取得...")
    if new_version:
        in_sample_path = version_manager.get_version_path(new_version, "in_sample_params")
        print(f"樣本內參數路徑: {in_sample_path}")
        
        out_sample_path = version_manager.get_version_path(new_version, "out_sample_params")
        print(f"樣本外參數路徑: {out_sample_path}")
    
    print("\n✅ 版本管理模組測試完成！")

if __name__ == "__main__":
    test_version_manager() 