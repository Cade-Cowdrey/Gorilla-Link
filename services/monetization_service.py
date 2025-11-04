"""
Monetization Service for PittState-Connect
Handles employer subscriptions, event sponsorships, and payment processing.
"""

import stripe
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from extensions import db
from models import User, Event
from models_extended import (
    Subscription, PaymentTransaction, SponsorshipTier,
    EmployerProfile, EventSponsor
)

# Stripe configuration (set in environment)
stripe.api_key = None  # Will be set from config

# ================================================================
# SPONSORSHIP TIER DEFINITIONS
# ================================================================

SPONSORSHIP_TIERS = {
    "free": {
        "name": "Free",
        "annual_cost": 0.00,
        "monthly_cost": 0.00,
        "benefits": {
            "max_job_postings": 2,
            "posting_duration_days": 30,
            "analytics_access": False,
            "featured_placement": False,
            "event_sponsorship": False,
            "priority_support": False,
            "logo_on_career_page": False,
            "direct_student_messaging": False,
            "resume_database_access": False,
            "custom_branding": False
        }
    },
    "bronze": {
        "name": "Bronze Partner",
        "annual_cost": 499.00,
        "monthly_cost": 49.00,
        "benefits": {
            "max_job_postings": 10,
            "posting_duration_days": 60,
            "analytics_access": True,
            "featured_placement": False,
            "event_sponsorship": True,
            "priority_support": False,
            "logo_on_career_page": True,
            "direct_student_messaging": False,
            "resume_database_access": False,
            "custom_branding": False
        }
    },
    "silver": {
        "name": "Silver Partner",
        "annual_cost": 1499.00,
        "monthly_cost": 149.00,
        "benefits": {
            "max_job_postings": 25,
            "posting_duration_days": 90,
            "analytics_access": True,
            "featured_placement": True,
            "event_sponsorship": True,
            "priority_support": True,
            "logo_on_career_page": True,
            "direct_student_messaging": True,
            "resume_database_access": True,
            "custom_branding": False
        }
    },
    "gold": {
        "name": "Gold Partner",
        "annual_cost": 2999.00,
        "monthly_cost": 299.00,
        "benefits": {
            "max_job_postings": 50,
            "posting_duration_days": 120,
            "analytics_access": True,
            "featured_placement": True,
            "event_sponsorship": True,
            "priority_support": True,
            "logo_on_career_page": True,
            "direct_student_messaging": True,
            "resume_database_access": True,
            "custom_branding": True,
            "dedicated_account_manager": False,
            "custom_virtual_booth": False
        }
    },
    "platinum": {
        "name": "Platinum Partner",
        "annual_cost": 5999.00,
        "monthly_cost": 599.00,
        "benefits": {
            "max_job_postings": -1,  # Unlimited
            "posting_duration_days": 180,
            "analytics_access": True,
            "featured_placement": True,
            "event_sponsorship": True,
            "priority_support": True,
            "logo_on_career_page": True,
            "direct_student_messaging": True,
            "resume_database_access": True,
            "custom_branding": True,
            "dedicated_account_manager": True,
            "custom_virtual_booth": True,
            "exclusive_networking_events": True,
            "priority_candidate_access": True
        }
    }
}

# ================================================================
# EVENT SPONSORSHIP PACKAGES
# ================================================================

EVENT_SPONSORSHIP_PACKAGES = {
    "presenting": {
        "name": "Presenting Sponsor",
        "cost": 5000.00,
        "benefits": {
            "logo_on_all_materials": True,
            "booth_space": "Premium",
            "speaking_opportunity": True,
            "social_media_mentions": 10,
            "email_blast": True,
            "vip_access": True,
            "exclusive_reception": True
        }
    },
    "platinum": {
        "name": "Platinum Sponsor",
        "cost": 2500.00,
        "benefits": {
            "logo_on_all_materials": True,
            "booth_space": "Premium",
            "speaking_opportunity": False,
            "social_media_mentions": 5,
            "email_blast": True,
            "vip_access": True,
            "exclusive_reception": False
        }
    },
    "gold": {
        "name": "Gold Sponsor",
        "cost": 1500.00,
        "benefits": {
            "logo_on_select_materials": True,
            "booth_space": "Standard",
            "speaking_opportunity": False,
            "social_media_mentions": 3,
            "email_blast": False,
            "vip_access": True,
            "exclusive_reception": False
        }
    },
    "silver": {
        "name": "Silver Sponsor",
        "cost": 750.00,
        "benefits": {
            "logo_on_select_materials": True,
            "booth_space": "Standard",
            "speaking_opportunity": False,
            "social_media_mentions": 1,
            "email_blast": False,
            "vip_access": False,
            "exclusive_reception": False
        }
    },
    "bronze": {
        "name": "Bronze Sponsor",
        "cost": 350.00,
        "benefits": {
            "logo_on_website": True,
            "booth_space": "Small",
            "speaking_opportunity": False,
            "social_media_mentions": 1,
            "email_blast": False,
            "vip_access": False,
            "exclusive_reception": False
        }
    }
}


class MonetizationService:
    """Service for handling payments, subscriptions, and sponsorships"""
    
    def __init__(self, stripe_api_key: Optional[str] = None):
        if stripe_api_key:
            stripe.api_key = stripe_api_key
    
    # ================================================================
    # TIER MANAGEMENT
    # ================================================================
    
    def initialize_sponsorship_tiers(self) -> bool:
        """Initialize sponsorship tiers in database"""
        try:
            for tier_key, tier_data in SPONSORSHIP_TIERS.items():
                existing = SponsorshipTier.query.filter_by(name=tier_key).first()
                if not existing:
                    tier = SponsorshipTier(
                        name=tier_key,
                        annual_cost=tier_data["annual_cost"],
                        benefits=tier_data["benefits"],
                        max_job_postings=tier_data["benefits"]["max_job_postings"],
                        analytics_access=tier_data["benefits"]["analytics_access"],
                        featured_placement=tier_data["benefits"]["featured_placement"],
                        priority_support=tier_data["benefits"]["priority_support"]
                    )
                    db.session.add(tier)
            
            db.session.commit()
            logger.info("✅ Sponsorship tiers initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize tiers: {e}")
            db.session.rollback()
            return False
    
    def get_tier_info(self, tier_name: str) -> Optional[Dict]:
        """Get information about a specific tier"""
        return SPONSORSHIP_TIERS.get(tier_name)
    
    def get_all_tiers(self) -> Dict:
        """Get all available tiers"""
        return SPONSORSHIP_TIERS
    
    def compare_tiers(self) -> List[Dict]:
        """Get tier comparison for pricing page"""
        comparison = []
        for tier_key, tier_data in SPONSORSHIP_TIERS.items():
            comparison.append({
                "key": tier_key,
                "name": tier_data["name"],
                "annual_cost": tier_data["annual_cost"],
                "monthly_cost": tier_data.get("monthly_cost", tier_data["annual_cost"] / 12),
                "benefits": tier_data["benefits"],
                "recommended": tier_key == "silver"
            })
        return comparison
    
    # ================================================================
    # SUBSCRIPTION MANAGEMENT
    # ================================================================
    
    def create_subscription(
        self,
        user_id: int,
        tier_name: str,
        billing_cycle: str = "annually",
        payment_method_id: Optional[str] = None
    ) -> Tuple[Optional[Subscription], Optional[str]]:
        """Create a new employer subscription"""
        
        try:
            tier = SPONSORSHIP_TIERS.get(tier_name)
            if not tier:
                return None, f"Invalid tier: {tier_name}"
            
            # Calculate amount based on billing cycle
            if billing_cycle == "monthly":
                amount = tier.get("monthly_cost", tier["annual_cost"] / 12)
            else:
                amount = tier["annual_cost"]
            
            # Free tier doesn't require payment
            if tier_name == "free":
                subscription = Subscription(
                    user_id=user_id,
                    plan_name=tier_name,
                    billing_cycle=billing_cycle,
                    amount=amount,
                    status="active",
                    current_period_start=datetime.utcnow(),
                    current_period_end=datetime.utcnow() + timedelta(days=365 if billing_cycle == "annually" else 30)
                )
                db.session.add(subscription)
                db.session.commit()
                
                logger.info(f"Created free subscription for user {user_id}")
                return subscription, None
            
            # For paid tiers, create Stripe subscription
            if not payment_method_id:
                return None, "Payment method required for paid tiers"
            
            user = User.query.get(user_id)
            if not user:
                return None, "User not found"
            
            # Create Stripe customer if doesn't exist
            if not hasattr(user, 'stripe_customer_id') or not user.stripe_customer_id:
                stripe_customer = stripe.Customer.create(
                    email=user.email,
                    payment_method=payment_method_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )
                user.stripe_customer_id = stripe_customer.id
            
            # Create Stripe subscription
            stripe_sub = stripe.Subscription.create(
                customer=user.stripe_customer_id,
                items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'PittState-Connect {tier["name"]}',
                            'description': f'{tier_name.title()} employer partnership'
                        },
                        'unit_amount': int(amount * 100),  # Convert to cents
                        'recurring': {
                            'interval': 'month' if billing_cycle == 'monthly' else 'year'
                        }
                    }
                }],
                expand=['latest_invoice.payment_intent']
            )
            
            # Create subscription record
            subscription = Subscription(
                user_id=user_id,
                plan_name=tier_name,
                billing_cycle=billing_cycle,
                amount=amount,
                status="active",
                stripe_subscription_id=stripe_sub.id,
                current_period_start=datetime.fromtimestamp(stripe_sub.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end)
            )
            db.session.add(subscription)
            
            # Update employer profile tier
            employer = EmployerProfile.query.filter_by(user_id=user_id).first()
            if employer:
                employer.sponsorship_tier = tier_name
            
            # Record transaction
            transaction = PaymentTransaction(
                user_id=user_id,
                amount=amount,
                currency="USD",
                status="completed",
                payment_method="stripe",
                purpose=f"{tier_name}_subscription",
                metadata={"stripe_subscription_id": stripe_sub.id, "billing_cycle": billing_cycle}
            )
            db.session.add(transaction)
            
            db.session.commit()
            logger.info(f"Created {tier_name} subscription for user {user_id}")
            return subscription, None
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            db.session.rollback()
            return None, str(e)
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            db.session.rollback()
            return None, str(e)
    
    def upgrade_subscription(self, subscription_id: int, new_tier: str) -> Tuple[bool, Optional[str]]:
        """Upgrade employer to higher tier"""
        
        try:
            subscription = Subscription.query.get(subscription_id)
            if not subscription:
                return False, "Subscription not found"
            
            tier = SPONSORSHIP_TIERS.get(new_tier)
            if not tier:
                return False, f"Invalid tier: {new_tier}"
            
            old_tier = subscription.plan_name
            
            # Update Stripe subscription if exists
            if subscription.stripe_subscription_id:
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe_sub['items']['data'][0].id,
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f'PittState-Connect {tier["name"]}'
                            },
                            'unit_amount': int(tier["annual_cost"] * 100),
                            'recurring': {'interval': 'year'}
                        }
                    }],
                    proration_behavior='create_prorations'
                )
            
            # Update subscription
            subscription.plan_name = new_tier
            subscription.amount = tier["annual_cost"]
            
            # Update employer profile
            employer = EmployerProfile.query.filter_by(user_id=subscription.user_id).first()
            if employer:
                employer.sponsorship_tier = new_tier
            
            db.session.commit()
            logger.info(f"Upgraded subscription {subscription_id} from {old_tier} to {new_tier}")
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to upgrade subscription: {e}")
            db.session.rollback()
            return False, str(e)
    
    def cancel_subscription(self, subscription_id: int, immediate: bool = False) -> Tuple[bool, Optional[str]]:
        """Cancel employer subscription"""
        
        try:
            subscription = Subscription.query.get(subscription_id)
            if not subscription:
                return False, "Subscription not found"
            
            # Cancel Stripe subscription
            if subscription.stripe_subscription_id:
                stripe.Subscription.delete(
                    subscription.stripe_subscription_id,
                    prorate=True if immediate else False
                )
            
            subscription.status = "cancelled"
            
            # Downgrade employer to free tier
            employer = EmployerProfile.query.filter_by(user_id=subscription.user_id).first()
            if employer:
                employer.sponsorship_tier = "free"
            
            db.session.commit()
            logger.info(f"Cancelled subscription {subscription_id}")
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            db.session.rollback()
            return False, str(e)
    
    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get active subscription for user"""
        return Subscription.query.filter_by(
            user_id=user_id,
            status="active"
        ).order_by(Subscription.created_at.desc()).first()
    
    def check_tier_benefits(self, user_id: int, benefit: str) -> bool:
        """Check if user's tier includes a specific benefit"""
        
        subscription = self.get_user_subscription(user_id)
        if not subscription:
            # Default to free tier
            tier = SPONSORSHIP_TIERS["free"]
        else:
            tier = SPONSORSHIP_TIERS.get(subscription.plan_name, SPONSORSHIP_TIERS["free"])
        
        return tier["benefits"].get(benefit, False)
    
    # ================================================================
    # EVENT SPONSORSHIP
    # ================================================================
    
    def sponsor_event(
        self,
        event_id: int,
        user_id: int,
        package_name: str,
        payment_method_id: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[str]]:
        """Create event sponsorship"""
        
        try:
            event = Event.query.get(event_id)
            if not event:
                return None, "Event not found"
            
            package = EVENT_SPONSORSHIP_PACKAGES.get(package_name)
            if not package:
                return None, f"Invalid sponsorship package: {package_name}"
            
            # Check if user has active subscription with event sponsorship benefit
            if not self.check_tier_benefits(user_id, "event_sponsorship"):
                return None, "Your tier does not include event sponsorship. Please upgrade."
            
            # Process payment if required
            if package["cost"] > 0 and payment_method_id:
                user = User.query.get(user_id)
                
                # Create payment intent
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(package["cost"] * 100),
                    currency='usd',
                    customer=user.stripe_customer_id if hasattr(user, 'stripe_customer_id') else None,
                    payment_method=payment_method_id,
                    confirm=True,
                    description=f'{package["name"]} - {event.name}'
                )
                
                # Record transaction
                transaction = PaymentTransaction(
                    user_id=user_id,
                    amount=package["cost"],
                    currency="USD",
                    status="completed",
                    payment_method="stripe",
                    purpose="event_sponsorship",
                    metadata={
                        "event_id": event_id,
                        "package": package_name,
                        "payment_intent_id": payment_intent.id
                    }
                )
                db.session.add(transaction)
            
            # Create sponsorship record
            sponsor = EventSponsor(
                event_id=event_id,
                sponsor_user_id=user_id,
                sponsorship_level=package_name,
                amount_paid=package["cost"],
                benefits=package["benefits"],
                active=True
            )
            db.session.add(sponsor)
            db.session.commit()
            
            logger.info(f"Created {package_name} sponsorship for event {event_id} by user {user_id}")
            return sponsor.id, None
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating sponsorship: {e}")
            db.session.rollback()
            return None, str(e)
        except Exception as e:
            logger.error(f"Failed to create event sponsorship: {e}")
            db.session.rollback()
            return None, str(e)
    
    def get_event_sponsors(self, event_id: int) -> List[Dict]:
        """Get all sponsors for an event"""
        
        sponsors = EventSponsor.query.filter_by(event_id=event_id, active=True).all()
        result = []
        
        for sponsor in sponsors:
            user = User.query.get(sponsor.sponsor_user_id)
            employer = EmployerProfile.query.filter_by(user_id=sponsor.sponsor_user_id).first()
            
            result.append({
                "id": sponsor.id,
                "level": sponsor.sponsorship_level,
                "amount": sponsor.amount_paid,
                "benefits": sponsor.benefits,
                "company_name": employer.company_name if employer else user.username,
                "logo_url": employer.logo_url if employer else None,
                "created_at": sponsor.created_at
            })
        
        return result
    
    def get_sponsorship_packages(self) -> Dict:
        """Get all event sponsorship packages"""
        return EVENT_SPONSORSHIP_PACKAGES
    
    # ================================================================
    # ANALYTICS & REPORTING
    # ================================================================
    
    def get_revenue_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """Generate revenue report for date range"""
        
        transactions = PaymentTransaction.query.filter(
            PaymentTransaction.created_at.between(start_date, end_date),
            PaymentTransaction.status == "completed"
        ).all()
        
        total_revenue = sum(t.amount for t in transactions)
        
        by_purpose = {}
        for t in transactions:
            purpose = t.purpose or "other"
            by_purpose[purpose] = by_purpose.get(purpose, 0) + t.amount
        
        subscriptions_count = Subscription.query.filter(
            Subscription.created_at.between(start_date, end_date),
            Subscription.status == "active"
        ).count()
        
        return {
            "total_revenue": total_revenue,
            "transaction_count": len(transactions),
            "by_purpose": by_purpose,
            "new_subscriptions": subscriptions_count,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    
    def get_subscription_stats(self) -> Dict:
        """Get subscription statistics"""
        
        active_subs = Subscription.query.filter_by(status="active").all()
        
        by_tier = {}
        for sub in active_subs:
            tier = sub.plan_name
            by_tier[tier] = by_tier.get(tier, 0) + 1
        
        monthly_recurring = sum(
            sub.amount / 12 if sub.billing_cycle == "annually" else sub.amount
            for sub in active_subs
        )
        
        return {
            "active_subscriptions": len(active_subs),
            "by_tier": by_tier,
            "monthly_recurring_revenue": monthly_recurring,
            "annual_recurring_revenue": monthly_recurring * 12
        }


# ================================================================
# SINGLETON INSTANCE
# ================================================================

_monetization_service = None

def get_monetization_service(stripe_api_key: Optional[str] = None) -> MonetizationService:
    """Get or create MonetizationService singleton"""
    global _monetization_service
    if _monetization_service is None:
        _monetization_service = MonetizationService(stripe_api_key)
    return _monetization_service
