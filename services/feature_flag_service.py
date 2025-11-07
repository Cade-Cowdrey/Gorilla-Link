"""
Feature Flags Service
A/B testing, feature rollouts, and configuration management
"""

from typing import Dict, Any, Optional, List
from extensions import db, cache
from models_admin import FeatureFlag
from models_extended import ABTest, ABTestAssignment
from datetime import datetime
import logging
import hashlib

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """Feature flag and A/B testing management"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    # ============================================================
    # FEATURE FLAGS
    # ============================================================
    
    @cache.memoize(timeout=300)
    def is_enabled(self, flag_name: str, user_id: Optional[int] = None, role: Optional[str] = None) -> bool:
        """
        Check if a feature flag is enabled for a user
        """
        try:
            flag = FeatureFlag.query.filter_by(name=flag_name).first()
            
            if not flag:
                logger.warning(f"Feature flag '{flag_name}' not found")
                return False
            
            # If flag is globally disabled
            if not flag.enabled:
                return False
            
            # If flag is globally enabled with no targeting
            if flag.rollout_percentage == 100.0 and not flag.target_users and not flag.target_roles:
                return True
            
            # Check user targeting
            if user_id and flag.target_users:
                if user_id in flag.target_users:
                    return True
            
            # Check role targeting
            if role and flag.target_roles:
                if role in flag.target_roles:
                    return True
            
            # Check rollout percentage
            if flag.rollout_percentage > 0 and user_id:
                # Use consistent hashing for stable rollout
                user_hash = hashlib.md5(f"{flag_name}:{user_id}".encode()).hexdigest()
                hash_value = int(user_hash, 16) % 100
                
                if hash_value < flag.rollout_percentage:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Feature flag check error: {e}")
            return False
    
    def create_flag(
        self,
        name: str,
        description: str,
        enabled: bool = False,
        rollout_percentage: float = 0.0,
        target_users: Optional[List[int]] = None,
        target_roles: Optional[List[str]] = None
    ) -> bool:
        """
        Create a new feature flag
        """
        try:
            # Check if flag exists
            existing = FeatureFlag.query.filter_by(name=name).first()
            if existing:
                logger.warning(f"Feature flag '{name}' already exists")
                return False
            
            flag = FeatureFlag(
                name=name,
                description=description,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                target_users=target_users or [],
                target_roles=target_roles or []
            )
            
            db.session.add(flag)
            db.session.commit()
            
            # Clear cache
            cache.delete_memoized(self.is_enabled, flag_name=name)
            
            logger.info(f"Feature flag '{name}' created")
            return True
            
        except Exception as e:
            logger.error(f"Feature flag creation error: {e}")
            db.session.rollback()
            return False
    
    def update_flag(
        self,
        name: str,
        enabled: Optional[bool] = None,
        rollout_percentage: Optional[float] = None,
        target_users: Optional[List[int]] = None,
        target_roles: Optional[List[str]] = None
    ) -> bool:
        """
        Update an existing feature flag
        """
        try:
            flag = FeatureFlag.query.filter_by(name=name).first()
            if not flag:
                return False
            
            if enabled is not None:
                flag.enabled = enabled
            if rollout_percentage is not None:
                flag.rollout_percentage = rollout_percentage
            if target_users is not None:
                flag.target_users = target_users
            if target_roles is not None:
                flag.target_roles = target_roles
            
            flag.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Clear cache
            cache.delete_memoized(self.is_enabled, flag_name=name)
            
            logger.info(f"Feature flag '{name}' updated")
            return True
            
        except Exception as e:
            logger.error(f"Feature flag update error: {e}")
            db.session.rollback()
            return False
    
    def delete_flag(self, name: str) -> bool:
        """Delete a feature flag"""
        try:
            flag = FeatureFlag.query.filter_by(name=name).first()
            if not flag:
                return False
            
            db.session.delete(flag)
            db.session.commit()
            
            cache.delete_memoized(self.is_enabled, flag_name=name)
            
            logger.info(f"Feature flag '{name}' deleted")
            return True
            
        except Exception as e:
            logger.error(f"Feature flag deletion error: {e}")
            db.session.rollback()
            return False
    
    def get_all_flags(self) -> List[FeatureFlag]:
        """Get all feature flags"""
        return FeatureFlag.query.order_by(FeatureFlag.name).all()
    
    def get_user_flags(self, user_id: int, role: Optional[str] = None) -> Dict[str, bool]:
        """
        Get all feature flags and their status for a specific user
        """
        flags = {}
        all_flags = self.get_all_flags()
        
        for flag in all_flags:
            flags[flag.name] = self.is_enabled(flag.name, user_id, role)
        
        return flags
    
    # ============================================================
    # A/B TESTING
    # ============================================================
    
    def create_ab_test(
        self,
        name: str,
        description: str,
        variant_a: Dict,
        variant_b: Dict,
        traffic_split: float = 0.5
    ) -> bool:
        """
        Create a new A/B test
        """
        try:
            test = ABTest(
                name=name,
                description=description,
                variant_a=variant_a,
                variant_b=variant_b,
                traffic_split=traffic_split,
                status='draft'
            )
            
            db.session.add(test)
            db.session.commit()
            
            logger.info(f"A/B test '{name}' created")
            return True
            
        except Exception as e:
            logger.error(f"A/B test creation error: {e}")
            db.session.rollback()
            return False
    
    def start_ab_test(self, test_id: int) -> bool:
        """Start an A/B test"""
        try:
            test = ABTest.query.get(test_id)
            if not test:
                return False
            
            test.status = 'running'
            test.started_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"A/B test {test_id} started")
            return True
            
        except Exception as e:
            logger.error(f"A/B test start error: {e}")
            db.session.rollback()
            return False
    
    def stop_ab_test(self, test_id: int, winner: Optional[str] = None) -> bool:
        """Stop an A/B test and optionally declare winner"""
        try:
            test = ABTest.query.get(test_id)
            if not test:
                return False
            
            test.status = 'completed'
            test.ended_at = datetime.utcnow()
            if winner:
                test.winner = winner
            
            db.session.commit()
            
            logger.info(f"A/B test {test_id} stopped, winner: {winner}")
            return True
            
        except Exception as e:
            logger.error(f"A/B test stop error: {e}")
            db.session.rollback()
            return False
    
    def get_ab_variant(self, test_id: int, user_id: int) -> Optional[str]:
        """
        Get the A/B test variant for a user
        Returns 'A' or 'B'
        """
        try:
            # Check existing assignment
            assignment = ABTestAssignment.query.filter_by(
                test_id=test_id,
                user_id=user_id
            ).first()
            
            if assignment:
                return assignment.variant
            
            # Get test
            test = ABTest.query.get(test_id)
            if not test or test.status != 'running':
                return None
            
            # Assign variant using consistent hashing
            user_hash = hashlib.md5(f"{test_id}:{user_id}".encode()).hexdigest()
            hash_value = int(user_hash, 16) % 100
            
            variant = 'A' if hash_value < (test.traffic_split * 100) else 'B'
            
            # Save assignment
            assignment = ABTestAssignment(
                test_id=test_id,
                user_id=user_id,
                variant=variant
            )
            db.session.add(assignment)
            db.session.commit()
            
            return variant
            
        except Exception as e:
            logger.error(f"A/B variant assignment error: {e}")
            db.session.rollback()
            return None
    
    def get_ab_test_results(self, test_id: int) -> Dict[str, Any]:
        """
        Get results/analytics for an A/B test
        """
        try:
            test = ABTest.query.get(test_id)
            if not test:
                return {"error": "Test not found"}
            
            # Count assignments
            total_assignments = ABTestAssignment.query.filter_by(test_id=test_id).count()
            variant_a_count = ABTestAssignment.query.filter_by(test_id=test_id, variant='A').count()
            variant_b_count = ABTestAssignment.query.filter_by(test_id=test_id, variant='B').count()
            
            return {
                "test_id": test_id,
                "name": test.name,
                "status": test.status,
                "started_at": test.started_at.isoformat() if test.started_at else None,
                "ended_at": test.ended_at.isoformat() if test.ended_at else None,
                "winner": test.winner,
                "total_participants": total_assignments,
                "variant_a": {
                    "participants": variant_a_count,
                    "percentage": (variant_a_count / total_assignments * 100) if total_assignments > 0 else 0
                },
                "variant_b": {
                    "participants": variant_b_count,
                    "percentage": (variant_b_count / total_assignments * 100) if total_assignments > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"A/B test results error: {e}")
            return {"error": str(e)}
    
    def get_all_ab_tests(self, status: Optional[str] = None) -> List[ABTest]:
        """Get all A/B tests, optionally filtered by status"""
        query = ABTest.query
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(ABTest.created_at.desc()).all()
    
    # ============================================================
    # CONFIGURATION MANAGEMENT
    # ============================================================
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with caching
        Similar to feature flags but for configuration
        """
        cache_key = f"config:{key}"
        cached_value = cache.get(cache_key)
        
        if cached_value is not None:
            return cached_value
        
        # In production, would load from database or external config service
        # For now, return default
        return default
    
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        try:
            cache_key = f"config:{key}"
            cache.set(cache_key, value, timeout=3600)
            
            # In production, would persist to database
            logger.info(f"Config '{key}' set to {value}")
            return True
            
        except Exception as e:
            logger.error(f"Config set error: {e}")
            return False


# ============================================================
# PREDEFINED FEATURE FLAGS
# ============================================================

FEATURE_FLAGS = {
    # Core features
    "ai_assistant": "Enable GorillaGPT AI assistant",
    "scholarships_v2": "Enable Scholarship Hub Phase 2",
    "advanced_analytics": "Enable advanced analytics dashboards",
    "alumni_portal": "Enable alumni engagement portal",
    "employer_portal": "Enable employer analytics portal",
    
    # Communication features
    "unified_inbox": "Enable unified inbox",
    "forums": "Enable community forums",
    "webinars": "Enable webinar hub",
    "calendar_sync": "Enable calendar synchronization",
    
    # Integration features
    "canvas_sync": "Enable Canvas LMS sync",
    "linkedin_integration": "Enable LinkedIn integration",
    "stripe_payments": "Enable Stripe payments",
    "twilio_sms": "Enable Twilio SMS notifications",
    
    # Security features
    "two_factor_auth": "Enable 2FA",
    "webauthn": "Enable WebAuthn/FIDO2",
    "audit_logs": "Enable comprehensive audit logging",
    
    # Advanced features
    "ar_campus": "Enable AR Campus Explorer",
    "voice_assistant": "Enable Hey Gorilla voice assistant",
    "blockchain_credentials": "Enable blockchain credentials",
    
    # Experimental
    "experimental_ui": "Enable experimental UI components",
    "beta_features": "Enable beta features",
}


def initialize_feature_flags():
    """
    Initialize default feature flags
    Should be called during app setup
    """
    service = get_feature_flag_service()
    
    for flag_name, description in FEATURE_FLAGS.items():
        # Check if flag exists
        existing = FeatureFlag.query.filter_by(name=flag_name).first()
        if not existing:
            service.create_flag(
                name=flag_name,
                description=description,
                enabled=True,  # Enable by default in production
                rollout_percentage=100.0
            )
            logger.info(f"Initialized feature flag: {flag_name}")


# Singleton
_feature_flag_service = None

def get_feature_flag_service() -> FeatureFlagService:
    global _feature_flag_service
    if _feature_flag_service is None:
        _feature_flag_service = FeatureFlagService()
    return _feature_flag_service
