"""
版本管理模組
負責管理策略參數、訊號、績效的版本控制
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

class VersionManager:
    def __init__(self):
        self.version_metadata_file = "version_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """載入版本元數據"""
        if os.path.exists(self.version_metadata_file):
            with open(self.version_metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"versions": [], "current_version": None}
    
    def _save_metadata(self):
        """儲存版本元數據"""
        with open(self.version_metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def create_new_version(self) -> str:
        """建立新版本"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 建立版本目錄
        version_dirs = [
            f"strategies/in_sample/all_params/{timestamp}",
            f"strategies/in_sample/best/{timestamp}",
            f"strategies/out_sample/param_logs/{timestamp}",
            f"strategies/out_sample/best/{timestamp}",
            f"trading_simulation/signal/{timestamp}",
            f"trading_simulation/performance/{timestamp}"
        ]
        
        for dir_path in version_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        # 更新元數據
        self.metadata["versions"].append({
            "version_id": timestamp,
            "created_at": datetime.now().isoformat(),
            "description": f"Version created at {timestamp}"
        })
        self.metadata["current_version"] = timestamp
        self._save_metadata()
        
        print(f"✅ 新版本已建立: {timestamp}")
        return timestamp
    
    def get_latest_version(self) -> Optional[str]:
        """取得最新版本"""
        if not self.metadata["versions"]:
            return None
        return self.metadata["versions"][-1]["version_id"]
    
    def get_current_version(self) -> Optional[str]:
        """取得當前版本"""
        return self.metadata.get("current_version")
    
    def set_current_version(self, version_id: str):
        """設定當前版本"""
        if version_id in [v["version_id"] for v in self.metadata["versions"]]:
            self.metadata["current_version"] = version_id
            self._save_metadata()
            print(f"✅ 當前版本已設定為: {version_id}")
        else:
            print(f"❌ 版本 {version_id} 不存在")
    
    def list_versions(self) -> List[Dict]:
        """列出所有版本"""
        return self.metadata["versions"]
    
    def get_version_path(self, version_id: str, path_type: str) -> str:
        """取得指定版本的目錄路徑"""
        path_mapping = {
            "in_sample_params": f"strategies/in_sample/all_params/{version_id}",
            "in_sample_best": f"strategies/in_sample/best/{version_id}",
            "out_sample_params": f"strategies/out_sample/param_logs/{version_id}",
            "out_sample_best": f"strategies/out_sample/best/{version_id}",
            "trading_signal": f"trading_simulation/signal/{version_id}",
            "trading_performance": f"trading_simulation/performance/{version_id}"
        }
        return path_mapping.get(path_type, "")

# 全域版本管理器實例
version_manager = VersionManager() 