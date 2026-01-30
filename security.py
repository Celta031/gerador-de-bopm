from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import re
import hashlib
import secrets
from typing import Optional

class SecurityManager:
    def __init__(self, master_key: Optional[str] = None):
        if master_key:
            self.key = self._derive_key(master_key)
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'bopm_salt_2026',
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return ""
    
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_token(length: int = 32) -> str:
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def sanitize_input(text: str, allow_special: bool = True) -> str:
        if not allow_special:
            text = re.sub(r'[<>{}[\]\\]', '', text)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
        return text.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = '*', keep_last: int = 4) -> str:
        if len(data) <= keep_last:
            return mask_char * len(data)
        return mask_char * (len(data) - keep_last) + data[-keep_last:]

security = SecurityManager()
