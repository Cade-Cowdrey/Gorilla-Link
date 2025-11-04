"""
Security Service - 2FA, WebAuthn, Encryption, Audit Logging
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from extensions import db
from models_extended import TwoFactorAuth, WebAuthnCredential, AuditLog, ConsentRecord, SecretVault
import logging

logger = logging.getLogger(__name__)


class SecurityService:
    """Comprehensive security service"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """Initialize with encryption key"""
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    # ============================================================
    # TWO-FACTOR AUTHENTICATION (TOTP)
    # ============================================================
    
    def enable_2fa(self, user_id: int, user_email: str) -> Dict[str, Any]:
        """
        Enable 2FA for a user and generate QR code
        """
        try:
            # Check if already enabled
            existing = TwoFactorAuth.query.filter_by(user_id=user_id).first()
            if existing and existing.is_enabled:
                return {"success": False, "message": "2FA is already enabled"}
            
            # Generate secret
            secret = pyotp.random_base32()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
            
            # Create or update 2FA record
            if existing:
                existing.secret = secret
                existing.backup_codes = backup_codes
                existing.is_enabled = False  # Require verification first
            else:
                two_fa = TwoFactorAuth(
                    user_id=user_id,
                    secret=secret,
                    backup_codes=backup_codes,
                    is_enabled=False
                )
                db.session.add(two_fa)
            
            db.session.commit()
            
            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user_email,
                issuer_name="PittState-Connect"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "secret": secret,
                "qr_code": qr_code_base64,
                "backup_codes": backup_codes
            }
            
        except Exception as e:
            logger.error(f"2FA enable error: {e}")
            db.session.rollback()
            return {"success": False, "message": str(e)}
    
    def verify_2fa_token(self, user_id: int, token: str) -> bool:
        """
        Verify 2FA token
        """
        try:
            two_fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
            if not two_fa:
                return False
            
            # Check backup codes first
            if token.upper() in two_fa.backup_codes:
                # Remove used backup code
                two_fa.backup_codes.remove(token.upper())
                two_fa.last_used = datetime.utcnow()
                db.session.commit()
                return True
            
            # Verify TOTP token
            totp = pyotp.TOTP(two_fa.secret)
            if totp.verify(token, valid_window=1):
                two_fa.last_used = datetime.utcnow()
                if not two_fa.is_enabled:
                    two_fa.is_enabled = True
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"2FA verification error: {e}")
            return False
    
    def disable_2fa(self, user_id: int) -> bool:
        """
        Disable 2FA for a user
        """
        try:
            two_fa = TwoFactorAuth.query.filter_by(user_id=user_id).first()
            if two_fa:
                db.session.delete(two_fa)
                db.session.commit()
                self.log_audit(
                    user_id=user_id,
                    action="2fa_disabled",
                    severity="warning"
                )
                return True
            return False
        except Exception as e:
            logger.error(f"2FA disable error: {e}")
            db.session.rollback()
            return False
    
    # ============================================================
    # WEBAUTHN / FIDO2
    # ============================================================
    
    def register_webauthn_credential(
        self,
        user_id: int,
        credential_id: str,
        public_key: str,
        device_name: Optional[str] = None
    ) -> bool:
        """
        Register WebAuthn credential
        """
        try:
            credential = WebAuthnCredential(
                user_id=user_id,
                credential_id=credential_id,
                public_key=public_key,
                device_name=device_name or "Unknown Device"
            )
            db.session.add(credential)
            db.session.commit()
            
            self.log_audit(
                user_id=user_id,
                action="webauthn_registered",
                details={"device_name": device_name}
            )
            return True
            
        except Exception as e:
            logger.error(f"WebAuthn registration error: {e}")
            db.session.rollback()
            return False
    
    def verify_webauthn_credential(self, user_id: int, credential_id: str) -> bool:
        """
        Verify WebAuthn credential (simplified - full implementation needs webauthn library)
        """
        try:
            credential = WebAuthnCredential.query.filter_by(
                user_id=user_id,
                credential_id=credential_id
            ).first()
            
            if credential:
                credential.sign_count += 1
                credential.last_used = datetime.utcnow()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"WebAuthn verification error: {e}")
            return False
    
    # ============================================================
    # AUDIT LOGGING
    # ============================================================
    
    def log_audit(
        self,
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict] = None,
        severity: str = "info"
    ) -> bool:
        """
        Create comprehensive audit log entry
        """
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details,
                severity=severity
            )
            db.session.add(log_entry)
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")
            db.session.rollback()
            return False
    
    def get_audit_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Query audit logs with filters
        """
        query = AuditLog.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        if action:
            query = query.filter_by(action=action)
        if severity:
            query = query.filter_by(severity=severity)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    # ============================================================
    # CONSENT MANAGEMENT (FERPA/GDPR)
    # ============================================================
    
    def record_consent(
        self,
        user_id: int,
        consent_type: str,
        granted: bool,
        version: str = "1.0",
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Record user consent for compliance
        """
        try:
            consent = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                version=version,
                granted_at=datetime.utcnow() if granted else None,
                revoked_at=datetime.utcnow() if not granted else None,
                ip_address=ip_address
            )
            db.session.add(consent)
            db.session.commit()
            
            self.log_audit(
                user_id=user_id,
                action=f"consent_{consent_type}_{'granted' if granted else 'revoked'}",
                details={"version": version}
            )
            return True
            
        except Exception as e:
            logger.error(f"Consent recording error: {e}")
            db.session.rollback()
            return False
    
    def check_consent(self, user_id: int, consent_type: str) -> bool:
        """
        Check if user has given consent
        """
        consent = ConsentRecord.query.filter_by(
            user_id=user_id,
            consent_type=consent_type
        ).order_by(ConsentRecord.granted_at.desc()).first()
        
        return consent and consent.granted and not consent.revoked_at
    
    def get_user_consents(self, user_id: int) -> List[ConsentRecord]:
        """
        Get all consent records for a user
        """
        return ConsentRecord.query.filter_by(user_id=user_id).all()
    
    # ============================================================
    # SECRET VAULT & ENCRYPTION
    # ============================================================
    
    def store_secret(
        self,
        key_name: str,
        value: str,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """
        Store encrypted secret in vault
        """
        try:
            encrypted_value = self.cipher.encrypt(value.encode()).decode()
            
            # Check if secret exists
            secret = SecretVault.query.filter_by(key_name=key_name).first()
            
            if secret:
                secret.encrypted_value = encrypted_value
                secret.updated_at = datetime.utcnow()
                secret.expires_at = expires_at
            else:
                secret = SecretVault(
                    key_name=key_name,
                    encrypted_value=encrypted_value,
                    expires_at=expires_at
                )
                db.session.add(secret)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Secret storage error: {e}")
            db.session.rollback()
            return False
    
    def retrieve_secret(self, key_name: str) -> Optional[str]:
        """
        Retrieve and decrypt secret from vault
        """
        try:
            secret = SecretVault.query.filter_by(key_name=key_name).first()
            
            if not secret:
                return None
            
            # Check expiration
            if secret.expires_at and secret.expires_at < datetime.utcnow():
                return None
            
            decrypted_value = self.cipher.decrypt(secret.encrypted_value.encode()).decode()
            return decrypted_value
            
        except Exception as e:
            logger.error(f"Secret retrieval error: {e}")
            return None
    
    def rotate_secret(self, key_name: str, new_value: str) -> bool:
        """
        Rotate secret with new value
        """
        try:
            secret = SecretVault.query.filter_by(key_name=key_name).first()
            if not secret:
                return False
            
            secret.encrypted_value = self.cipher.encrypt(new_value.encode()).decode()
            secret.rotation_date = datetime.utcnow()
            secret.updated_at = datetime.utcnow()
            db.session.commit()
            
            self.log_audit(
                action="secret_rotated",
                details={"key_name": key_name},
                severity="info"
            )
            return True
            
        except Exception as e:
            logger.error(f"Secret rotation error: {e}")
            db.session.rollback()
            return False
    
    # ============================================================
    # DATA ENCRYPTION
    # ============================================================
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt arbitrary data
        """
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data
        """
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def hash_data(self, data: str, salt: Optional[str] = None) -> str:
        """
        Create secure hash of data
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        return hashlib.pbkdf2_hmac(
            'sha256',
            data.encode(),
            salt.encode(),
            100000
        ).hex()


# Singleton instance
_security_service_instance = None

def get_security_service(encryption_key: Optional[bytes] = None) -> SecurityService:
    """Get or create security service singleton"""
    global _security_service_instance
    if _security_service_instance is None:
        _security_service_instance = SecurityService(encryption_key)
    return _security_service_instance
