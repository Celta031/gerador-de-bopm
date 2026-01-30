import json
import os
from typing import Any, Dict
from pathlib import Path

class UserSettings:
    DEFAULT_SETTINGS = {
        "appearance": {
            "theme": "dark",
            "color_theme": "blue",
            "font_family": "Segoe UI",
            "font_size": 13
        },
        "ai": {
            "model": "gemini-2.0-flash-exp",
            "temperature": 0.7,
            "custom_prompt": ""
        },
        "editor": {
            "auto_save": True,
            "auto_save_interval": 30,
            "show_line_numbers": False,
            "wrap_text": True
        },
        "search": {
            "case_sensitive": False,
            "regex_enabled": False,
            "max_results": 100
        },
        "security": {
            "encrypt_sensitive_data": False,
            "auto_logout": False,
            "session_timeout": 30
        },
        "backup": {
            "enabled": False,
            "interval_hours": 24,
            "max_backups": 7
        }
    }
    
    def __init__(self, settings_file: str = "user_settings.json"):
        self.settings_path = Path(settings_file)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    return {**self.DEFAULT_SETTINGS, **json.load(f)}
            except Exception:
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self) -> bool:
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get(self, category: str, key: str, default: Any = None) -> Any:
        return self.settings.get(category, {}).get(key, default)
    
    def set(self, category: str, key: str, value: Any) -> None:
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value
    
    def reset_to_defaults(self) -> None:
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()
    
    def get_all(self) -> Dict[str, Any]:
        return self.settings.copy()
    
    def update_category(self, category: str, values: Dict[str, Any]) -> None:
        if category in self.settings:
            self.settings[category].update(values)

settings = UserSettings()
