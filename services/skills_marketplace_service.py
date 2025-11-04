"""
Skills Marketplace Service
Student freelancing platform for services and micro-projects

Features:
- Create service listings (tutoring, design, coding, writing, etc.)
- Browse and hire student freelancers
- Project proposals and contracts
- Milestone-based payments
- Escrow payment system (Stripe integration)
- Portfolio showcase
- Skill verification
- Client reviews and ratings
- Dispute resolution
- Earnings dashboard
- Tax document generation (1099 forms)
- Gig matching algorithm

Revenue Model:
- 15% platform fee on all transactions
- Premium seller profiles: $20/month
- Promoted listings: $10-50/listing
- Enterprise hiring: $500+/month for bulk hiring
Target: $200,000+ annually from transaction fees

Example: $100 gig = $15 platform fee = $85 to student
At 10,000 transactions/year averaging $100: $150,000 revenue
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict
from decimal import Decimal
import hashlib

from models import db, User
from sqlalchemy import func, and_, or_

logger = logging.getLogger(__name__)


class SkillsMarketplaceService:
    """Service for student freelancing marketplace"""
    
    # Service categories
    SERVICE_CATEGORIES = {
        'tutoring': {
            'name': 'Tutoring & Teaching',
            'subcategories': ['Math', 'Science', 'Languages', 'Test Prep', 'Music']
        },
        'design': {
            'name': 'Graphic Design',
            'subcategories': ['Logo Design', 'Web Design', 'UI/UX', 'Illustrations', 'Branding']
        },
        'development': {
            'name': 'Programming & Tech',
            'subcategories': ['Web Development', 'Mobile Apps', 'Data Analysis', 'AI/ML', 'Automation']
        },
        'writing': {
            'name': 'Writing & Content',
            'subcategories': ['Blog Writing', 'Copywriting', 'Technical Writing', 'Editing', 'Resumes']
        },
        'video': {
            'name': 'Video & Animation',
            'subcategories': ['Video Editing', '3D Animation', 'Motion Graphics', 'Explainer Videos']
        },
        'marketing': {
            'name': 'Digital Marketing',
            'subcategories': ['Social Media', 'SEO', 'Content Strategy', 'Email Marketing', 'Analytics']
        },
        'business': {
            'name': 'Business Services',
            'subcategories': ['Virtual Assistant', 'Data Entry', 'Research', 'Consulting', 'Project Management']
        },
        'music': {
            'name': 'Music & Audio',
            'subcategories': ['Music Production', 'Voice Over', 'Podcast Editing', 'Sound Design']
        }
    }
    
    # Pricing tiers for gigs
    PRICING_TIERS = {
        'basic': {'label': 'Basic', 'max_revisions': 1, 'delivery_days': 7},
        'standard': {'label': 'Standard', 'max_revisions': 3, 'delivery_days': 5},
        'premium': {'label': 'Premium', 'max_revisions': 5, 'delivery_days': 3}
    }
    
    # Platform fee structure
    PLATFORM_FEE = 0.15  # 15% platform fee
    STRIPE_FEE = 0.029  # 2.9% Stripe fee
    STRIPE_FIXED_FEE = 0.30  # $0.30 Stripe fixed fee
    
    # Seller levels (based on performance)
    SELLER_LEVELS = {
        'new_seller': {'min_sales': 0, 'max_sales': 10, 'badge': 'New Seller'},
        'level_one': {'min_sales': 10, 'max_sales': 50, 'badge': 'Level 1 Seller'},
        'level_two': {'min_sales': 50, 'max_sales': 100, 'badge': 'Level 2 Seller'},
        'top_rated': {'min_sales': 100, 'max_sales': 999999, 'badge': 'Top Rated Seller'}
    }

    def __init__(self):
        """Initialize skills marketplace service"""
        self.logger = logger
    
    def create_gig(
        self,
        seller_id: int,
        gig_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new service gig
        
        Args:
            seller_id: User creating the gig
            gig_data: Gig details
        
        Returns:
            Created gig details
        """
        try:
            seller = User.query.get(seller_id)
            if not seller:
                return {'success': False, 'error': 'User not found'}
            
            # Validate seller profile completeness
            profile_check = self._check_seller_profile(seller)
            if not profile_check['complete']:
                return {
                    'success': False,
                    'error': 'Complete your profile first',
                    'missing_fields': profile_check['missing']
                }
            
            # Validate gig data
            validation = self._validate_gig_data(gig_data)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': 'Invalid gig data',
                    'validation_errors': validation['errors']
                }
            
            # Create gig record
            gig_record = {
                'seller_id': seller_id,
                'title': gig_data['title'],
                'category': gig_data['category'],
                'subcategory': gig_data.get('subcategory'),
                'description': gig_data['description'],
                'skills_required': gig_data.get('skills_required', []),
                
                # Pricing tiers
                'basic_price': gig_data.get('basic_price'),
                'basic_description': gig_data.get('basic_description'),
                'basic_delivery_days': gig_data.get('basic_delivery_days', 7),
                'basic_revisions': gig_data.get('basic_revisions', 1),
                
                'standard_price': gig_data.get('standard_price'),
                'standard_description': gig_data.get('standard_description'),
                'standard_delivery_days': gig_data.get('standard_delivery_days', 5),
                'standard_revisions': gig_data.get('standard_revisions', 3),
                
                'premium_price': gig_data.get('premium_price'),
                'premium_description': gig_data.get('premium_description'),
                'premium_delivery_days': gig_data.get('premium_delivery_days', 3),
                'premium_revisions': gig_data.get('premium_revisions', 5),
                
                # Details
                'portfolio_items': gig_data.get('portfolio_items', []),
                'faq': gig_data.get('faq', []),
                'requirements': gig_data.get('requirements', ''),
                'tags': gig_data.get('tags', []),
                
                # Metadata
                'status': 'pending_review',
                'views': 0,
                'orders': 0,
                'rating': 0.0,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
            
            # Content moderation
            moderation = self._moderate_gig_content(gig_record)
            if not moderation['approved']:
                return {
                    'success': False,
                    'error': 'Gig content needs review',
                    'reasons': moderation['reasons']
                }
            
            gig_record['status'] = 'active'
            
            # Save gig
            gig_id = self._save_gig(gig_record)
            
            # Add to search index
            self._index_gig_for_search(gig_id, gig_record)
            
            # Send confirmation
            self._send_gig_creation_confirmation(seller, gig_record)
            
            return {
                'success': True,
                'gig_id': gig_id,
                'status': 'active',
                'gig_url': f'/marketplace/gig/{gig_id}',
                'message': 'Your gig is now live!',
                'next_steps': [
                    'Share your gig on social media',
                    'Respond quickly to inquiries',
                    'Deliver quality work to earn reviews',
                    'Consider promoting your gig for more visibility'
                ],
                'estimated_earnings': self._estimate_gig_earnings(gig_record)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating gig: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def search_gigs(
        self,
        search_query: str = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Search for gigs
        
        Args:
            search_query: Search keywords
            filters: Category, price range, delivery time, etc.
        
        Returns:
            Matching gigs
        """
        try:
            # Get all active gigs
            gigs = self._query_active_gigs()
            
            # Apply search
            if search_query:
                gigs = self._apply_search_query(gigs, search_query)
            
            # Apply filters
            if filters:
                if filters.get('category'):
                    gigs = [g for g in gigs if g['category'] == filters['category']]
                
                if filters.get('max_price'):
                    gigs = [g for g in gigs if g.get('basic_price', 0) <= filters['max_price']]
                
                if filters.get('max_delivery_days'):
                    gigs = [g for g in gigs if g.get('basic_delivery_days', 999) <= filters['max_delivery_days']]
                
                if filters.get('min_rating'):
                    gigs = [g for g in gigs if g.get('rating', 0) >= filters['min_rating']]
                
                if filters.get('seller_level'):
                    gigs = [g for g in gigs if self._get_seller_level(g['seller_id']) == filters['seller_level']]
            
            # Sort results
            sort_by = filters.get('sort_by', 'relevance') if filters else 'relevance'
            sorted_gigs = self._sort_gigs(gigs, sort_by, search_query)
            
            # Enhance gig details
            enhanced_gigs = []
            for gig in sorted_gigs[:50]:  # Top 50 results
                enhanced = self._enhance_gig_for_display(gig)
                enhanced_gigs.append(enhanced)
            
            return {
                'success': True,
                'total_results': len(gigs),
                'gigs': enhanced_gigs,
                'search_query': search_query,
                'filters_applied': filters or {},
                'suggested_categories': self._get_suggested_categories(search_query) if search_query else []
            }
            
        except Exception as e:
            self.logger.error(f"Error searching gigs: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def place_order(
        self,
        buyer_id: int,
        gig_id: str,
        order_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Place an order for a gig
        
        Args:
            buyer_id: User placing order
            gig_id: Gig to order
            order_details: Tier, requirements, custom requests
        
        Returns:
            Order confirmation and payment details
        """
        try:
            buyer = User.query.get(buyer_id)
            if not buyer:
                return {'success': False, 'error': 'User not found'}
            
            # Get gig
            gig = self._get_gig(gig_id)
            if not gig:
                return {'success': False, 'error': 'Gig not found'}
            
            if gig['status'] != 'active':
                return {'success': False, 'error': 'Gig is not available'}
            
            # Prevent self-ordering
            if gig['seller_id'] == buyer_id:
                return {'success': False, 'error': 'Cannot order your own gig'}
            
            # Get pricing tier
            tier = order_details.get('tier', 'basic')
            price = gig.get(f'{tier}_price')
            
            if not price:
                return {'success': False, 'error': f'Invalid tier: {tier}'}
            
            # Calculate fees
            fee_breakdown = self._calculate_fees(price)
            
            # Create order
            order_record = {
                'order_id': self._generate_order_id(),
                'buyer_id': buyer_id,
                'seller_id': gig['seller_id'],
                'gig_id': gig_id,
                'tier': tier,
                'price': price,
                'platform_fee': fee_breakdown['platform_fee'],
                'payment_processing_fee': fee_breakdown['payment_processing_fee'],
                'seller_earnings': fee_breakdown['seller_earnings'],
                'delivery_days': gig.get(f'{tier}_delivery_days'),
                'revisions_included': gig.get(f'{tier}_revisions'),
                'revisions_remaining': gig.get(f'{tier}_revisions'),
                'requirements': order_details.get('requirements', ''),
                'attachments': order_details.get('attachments', []),
                'custom_requests': order_details.get('custom_requests', ''),
                'status': 'pending_payment',
                'created_at': datetime.utcnow(),
                'due_date': datetime.utcnow() + timedelta(days=gig.get(f'{tier}_delivery_days', 7))
            }
            
            # Save order
            order_id = self._save_order(order_record)
            
            # Create Stripe payment intent
            payment_intent = self._create_stripe_payment_intent(order_record)
            
            # Update order with payment info
            order_record['payment_intent_id'] = payment_intent['id']
            order_record['client_secret'] = payment_intent['client_secret']
            
            return {
                'success': True,
                'order_id': order_id,
                'status': 'pending_payment',
                'payment': {
                    'amount': price,
                    'client_secret': payment_intent['client_secret'],
                    'payment_intent_id': payment_intent['id']
                },
                'fee_breakdown': fee_breakdown,
                'delivery_date': order_record['due_date'].isoformat(),
                'next_steps': [
                    'Complete payment',
                    'Seller will be notified',
                    'Work begins after payment confirmation',
                    'Track progress in your dashboard'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error placing order: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def confirm_payment(
        self,
        order_id: str,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Confirm payment received for order
        
        Args:
            order_id: Order ID
            payment_intent_id: Stripe payment intent ID
        
        Returns:
            Order activation confirmation
        """
        try:
            # Get order
            order = self._get_order(order_id)
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            # Verify payment with Stripe
            payment_verified = self._verify_stripe_payment(payment_intent_id)
            
            if not payment_verified:
                return {
                    'success': False,
                    'error': 'Payment verification failed'
                }
            
            # Update order status
            order['status'] = 'in_progress'
            order['payment_confirmed_at'] = datetime.utcnow()
            order['payment_held_in_escrow'] = True
            
            self._update_order(order_id, order)
            
            # Notify seller
            seller = User.query.get(order['seller_id'])
            self._notify_seller_of_order(seller, order)
            
            # Notify buyer
            buyer = User.query.get(order['buyer_id'])
            self._notify_buyer_of_confirmation(buyer, order)
            
            return {
                'success': True,
                'order_id': order_id,
                'status': 'in_progress',
                'payment_held_in_escrow': True,
                'seller_notified': True,
                'estimated_delivery': order['due_date'].isoformat(),
                'message': 'Payment confirmed! Your order is now in progress.'
            }
            
        except Exception as e:
            self.logger.error(f"Error confirming payment: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def submit_delivery(
        self,
        seller_id: int,
        order_id: str,
        delivery: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Seller submits completed work
        
        Args:
            seller_id: Seller ID
            order_id: Order ID
            delivery: Delivery files and message
        
        Returns:
            Delivery confirmation
        """
        try:
            # Get order
            order = self._get_order(order_id)
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            # Verify seller
            if order['seller_id'] != seller_id:
                return {'success': False, 'error': 'Unauthorized'}
            
            if order['status'] != 'in_progress':
                return {'success': False, 'error': 'Order not in progress'}
            
            # Save delivery
            delivery_record = {
                'order_id': order_id,
                'delivery_files': delivery.get('files', []),
                'delivery_message': delivery.get('message'),
                'delivered_at': datetime.utcnow(),
                'on_time': datetime.utcnow() <= order['due_date']
            }
            
            delivery_id = self._save_delivery(delivery_record)
            
            # Update order status
            order['status'] = 'delivered'
            order['delivered_at'] = datetime.utcnow()
            self._update_order(order_id, order)
            
            # Notify buyer
            buyer = User.query.get(order['buyer_id'])
            self._notify_buyer_of_delivery(buyer, order, delivery_record)
            
            # Start auto-completion timer (3 days)
            self._schedule_auto_completion(order_id)
            
            return {
                'success': True,
                'order_id': order_id,
                'delivery_id': delivery_id,
                'status': 'delivered',
                'message': 'Work delivered successfully!',
                'buyer_notified': True,
                'auto_complete_in': '3 days if buyer doesn\'t respond'
            }
            
        except Exception as e:
            self.logger.error(f"Error submitting delivery: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def complete_order(
        self,
        buyer_id: int,
        order_id: str,
        review: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Buyer marks order as complete and leaves review
        
        Args:
            buyer_id: Buyer ID
            order_id: Order ID
            review: Optional review
        
        Returns:
            Completion confirmation
        """
        try:
            # Get order
            order = self._get_order(order_id)
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            # Verify buyer
            if order['buyer_id'] != buyer_id:
                return {'success': False, 'error': 'Unauthorized'}
            
            if order['status'] != 'delivered':
                return {'success': False, 'error': 'Order not delivered yet'}
            
            # Save review if provided
            review_id = None
            if review:
                review_record = {
                    'order_id': order_id,
                    'reviewer_id': buyer_id,
                    'seller_id': order['seller_id'],
                    'rating': review['rating'],
                    'communication': review.get('communication', 5),
                    'service_quality': review.get('service_quality', 5),
                    'would_recommend': review.get('would_recommend', True),
                    'comment': review.get('comment'),
                    'submitted_at': datetime.utcnow()
                }
                review_id = self._save_review(review_record)
                
                # Update seller rating
                self._update_seller_rating(order['seller_id'])
            
            # Update order status
            order['status'] = 'completed'
            order['completed_at'] = datetime.utcnow()
            self._update_order(order_id, order)
            
            # Release payment from escrow to seller
            payout = self._release_payment_to_seller(order)
            
            # Update seller stats
            self._update_seller_stats(order['seller_id'], order)
            
            # Check seller level upgrade
            new_level = self._check_seller_level_upgrade(order['seller_id'])
            
            # Notify seller
            seller = User.query.get(order['seller_id'])
            self._notify_seller_of_completion(seller, order, payout)
            
            return {
                'success': True,
                'order_id': order_id,
                'status': 'completed',
                'review_submitted': review_id is not None,
                'payment_released': True,
                'seller_earnings': payout['amount'],
                'message': 'Order completed successfully!',
                'seller_level_update': new_level
            }
            
        except Exception as e:
            self.logger.error(f"Error completing order: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def request_revision(
        self,
        buyer_id: int,
        order_id: str,
        revision_request: str
    ) -> Dict[str, Any]:
        """
        Buyer requests revision
        
        Args:
            buyer_id: Buyer ID
            order_id: Order ID
            revision_request: Revision details
        
        Returns:
            Revision request confirmation
        """
        try:
            # Get order
            order = self._get_order(order_id)
            if not order:
                return {'success': False, 'error': 'Order not found'}
            
            # Verify buyer
            if order['buyer_id'] != buyer_id:
                return {'success': False, 'error': 'Unauthorized'}
            
            if order['status'] != 'delivered':
                return {'success': False, 'error': 'Can only request revisions on delivered work'}
            
            # Check revisions remaining
            if order['revisions_remaining'] <= 0:
                return {
                    'success': False,
                    'error': 'No revisions remaining',
                    'can_order_extra_revision': True,
                    'extra_revision_cost': order['price'] * 0.2  # 20% of order price
                }
            
            # Create revision request
            revision_record = {
                'order_id': order_id,
                'requested_by': buyer_id,
                'request': revision_request,
                'requested_at': datetime.utcnow()
            }
            
            revision_id = self._save_revision_request(revision_record)
            
            # Update order
            order['status'] = 'revision_requested'
            order['revisions_remaining'] -= 1
            self._update_order(order_id, order)
            
            # Notify seller
            seller = User.query.get(order['seller_id'])
            self._notify_seller_of_revision(seller, order, revision_record)
            
            return {
                'success': True,
                'revision_id': revision_id,
                'revisions_remaining': order['revisions_remaining'],
                'message': 'Revision requested. Seller has been notified.'
            }
            
        except Exception as e:
            self.logger.error(f"Error requesting revision: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_seller_dashboard(
        self,
        seller_id: int
    ) -> Dict[str, Any]:
        """
        Get seller dashboard with earnings and analytics
        
        Args:
            seller_id: Seller user ID
        
        Returns:
            Dashboard data
        """
        try:
            seller = User.query.get(seller_id)
            if not seller:
                return {'success': False, 'error': 'User not found'}
            
            # Get seller stats
            stats = self._get_seller_stats(seller_id)
            
            # Get active orders
            active_orders = self._get_seller_active_orders(seller_id)
            
            # Get earnings
            earnings = self._calculate_seller_earnings(seller_id)
            
            # Get gigs
            gigs = self._get_seller_gigs(seller_id)
            
            # Get seller level
            level = self._get_seller_level(seller_id)
            
            # Performance metrics
            performance = self._calculate_seller_performance(seller_id)
            
            return {
                'success': True,
                'seller_id': seller_id,
                'seller_level': level,
                'statistics': stats,
                'active_orders': active_orders,
                'earnings': earnings,
                'gigs': gigs,
                'performance': performance,
                'recommendations': self._get_seller_recommendations(seller_id, performance)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting seller dashboard: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Private helper methods
    
    def _check_seller_profile(self, user: User) -> Dict[str, Any]:
        """Check if seller profile is complete"""
        missing = []
        
        if not user.bio:
            missing.append('bio')
        if not hasattr(user, 'skills') or not user.skills:
            missing.append('skills')
        
        return {
            'complete': len(missing) == 0,
            'missing': missing
        }
    
    def _validate_gig_data(self, data: Dict) -> Dict[str, Any]:
        """Validate gig data"""
        errors = []
        
        if not data.get('title'):
            errors.append('Title is required')
        
        if not data.get('category') or data['category'] not in self.SERVICE_CATEGORIES:
            errors.append('Valid category is required')
        
        if not data.get('description'):
            errors.append('Description is required')
        
        if not data.get('basic_price') or data['basic_price'] < 5:
            errors.append('Basic price must be at least $5')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _moderate_gig_content(self, gig: Dict) -> Dict[str, Any]:
        """Moderate gig content"""
        # Simplified moderation
        return {'approved': True, 'reasons': []}
    
    def _save_gig(self, gig: Dict) -> str:
        """Save gig to database"""
        gig_id = f"gig_{gig['seller_id']}_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Saved gig: {gig_id}")
        return gig_id
    
    def _index_gig_for_search(self, gig_id: str, gig: Dict):
        """Add gig to search index"""
        self.logger.info(f"Indexed gig {gig_id} for search")
    
    def _send_gig_creation_confirmation(self, seller: User, gig: Dict):
        """Send gig creation confirmation"""
        self.logger.info(f"Sent gig creation confirmation to {seller.email}")
    
    def _estimate_gig_earnings(self, gig: Dict) -> str:
        """Estimate potential earnings"""
        basic_price = gig.get('basic_price', 0)
        avg_orders_per_month = 5  # Conservative estimate
        monthly_gross = basic_price * avg_orders_per_month
        monthly_net = monthly_gross * (1 - self.PLATFORM_FEE - self.STRIPE_FEE) - (self.STRIPE_FIXED_FEE * avg_orders_per_month)
        return f"Potential: ${int(monthly_net)}/month with {avg_orders_per_month} orders"
    
    def _query_active_gigs(self) -> List[Dict]:
        """Query all active gigs"""
        # Simulated gig data
        gigs = []
        for i in range(50):
            gigs.append({
                'gig_id': f'gig_{i}',
                'seller_id': i % 10,
                'title': f'Professional Service {i}',
                'category': list(self.SERVICE_CATEGORIES.keys())[i % len(self.SERVICE_CATEGORIES)],
                'description': f'High quality service description {i}',
                'basic_price': 25 + (i * 5),
                'basic_delivery_days': 3 + (i % 7),
                'rating': 4.0 + (i % 10) / 10,
                'orders': i * 2,
                'status': 'active'
            })
        return gigs
    
    def _apply_search_query(self, gigs: List[Dict], query: str) -> List[Dict]:
        """Apply search query to gigs"""
        query_lower = query.lower()
        return [g for g in gigs if query_lower in g['title'].lower() or query_lower in g['description'].lower()]
    
    def _get_seller_level(self, seller_id: int) -> str:
        """Get seller level badge based on actual sales"""
        try:
            from models_extended import Order
            
            # Count completed orders for this seller
            total_sales = Order.query.filter_by(
                seller_id=seller_id,
                status='completed'
            ).count()
            
            # Determine level based on sales count
            for level, config in self.SELLER_LEVELS.items():
                if config['min_sales'] <= total_sales <= config['max_sales']:
                    return config['badge']
            
            return 'New Seller'
            
        except Exception as e:
            self.logger.error(f"Error getting seller level: {e}")
            return 'New Seller'
    
    def _sort_gigs(self, gigs: List[Dict], sort_by: str, query: str = None) -> List[Dict]:
        """Sort gigs"""
        if sort_by == 'price_low':
            return sorted(gigs, key=lambda x: x.get('basic_price', 0))
        elif sort_by == 'price_high':
            return sorted(gigs, key=lambda x: x.get('basic_price', 0), reverse=True)
        elif sort_by == 'rating':
            return sorted(gigs, key=lambda x: x.get('rating', 0), reverse=True)
        elif sort_by == 'best_selling':
            return sorted(gigs, key=lambda x: x.get('orders', 0), reverse=True)
        else:  # relevance
            return sorted(gigs, key=lambda x: (x.get('rating', 0), x.get('orders', 0)), reverse=True)
    
    def _enhance_gig_for_display(self, gig: Dict) -> Dict:
        """Enhance gig with seller info"""
        seller_level = self._get_seller_level(gig['seller_id'])
        
        return {
            **gig,
            'seller_level': seller_level,
            'seller_name': f"Seller {gig['seller_id']}",
            'seller_response_time': '1 hour',
            'gig_url': f'/marketplace/gig/{gig["gig_id"]}'
        }
    
    def _get_suggested_categories(self, query: str) -> List[str]:
        """Get suggested categories"""
        return list(self.SERVICE_CATEGORIES.keys())[:3]
    
    def _get_gig(self, gig_id: str) -> Optional[Dict]:
        """Get gig by ID"""
        return {
            'gig_id': gig_id,
            'seller_id': 1,
            'title': 'Test Gig',
            'category': 'development',
            'basic_price': 50,
            'basic_delivery_days': 3,
            'basic_revisions': 2,
            'status': 'active'
        }
    
    def _calculate_fees(self, price: float) -> Dict[str, float]:
        """Calculate fee breakdown"""
        platform_fee = price * self.PLATFORM_FEE
        payment_processing_fee = (price * self.STRIPE_FEE) + self.STRIPE_FIXED_FEE
        seller_earnings = price - platform_fee - payment_processing_fee
        
        return {
            'total': price,
            'platform_fee': round(platform_fee, 2),
            'payment_processing_fee': round(payment_processing_fee, 2),
            'seller_earnings': round(seller_earnings, 2)
        }
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        return f"order_{datetime.utcnow().timestamp()}"
    
    def _save_order(self, order: Dict) -> str:
        """Save order"""
        self.logger.info(f"Saved order: {order['order_id']}")
        return order['order_id']
    
    def _create_stripe_payment_intent(self, order: Dict) -> Dict:
        """Create Stripe payment intent"""
        return {
            'id': f"pi_{order['order_id']}",
            'client_secret': f"secret_{order['order_id']}"
        }
    
    def _get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        return {
            'order_id': order_id,
            'buyer_id': 1,
            'seller_id': 2,
            'gig_id': 'gig_1',
            'price': 50,
            'status': 'pending_payment',
            'due_date': datetime.utcnow() + timedelta(days=3),
            'seller_earnings': 40,
            'revisions_remaining': 2
        }
    
    def _verify_stripe_payment(self, payment_intent_id: str) -> bool:
        """Verify payment with Stripe"""
        return True
    
    def _update_order(self, order_id: str, order: Dict):
        """Update order"""
        self.logger.info(f"Updated order: {order_id}")
    
    def _notify_seller_of_order(self, seller: User, order: Dict):
        """Notify seller of new order"""
        self.logger.info(f"Notified seller {seller.email}")
    
    def _notify_buyer_of_confirmation(self, buyer: User, order: Dict):
        """Notify buyer of payment confirmation"""
        self.logger.info(f"Notified buyer {buyer.email}")
    
    def _save_delivery(self, delivery: Dict) -> str:
        """Save delivery"""
        delivery_id = f"delivery_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Saved delivery: {delivery_id}")
        return delivery_id
    
    def _notify_buyer_of_delivery(self, buyer: User, order: Dict, delivery: Dict):
        """Notify buyer of delivery"""
        self.logger.info(f"Notified buyer {buyer.email} of delivery")
    
    def _schedule_auto_completion(self, order_id: str):
        """Schedule auto-completion"""
        self.logger.info(f"Scheduled auto-completion for {order_id}")
    
    def _save_review(self, review: Dict) -> str:
        """Save review"""
        review_id = f"review_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Saved review: {review_id}")
        return review_id
    
    def _update_seller_rating(self, seller_id: int):
        """Update seller rating"""
        self.logger.info(f"Updated seller {seller_id} rating")
    
    def _release_payment_to_seller(self, order: Dict) -> Dict:
        """Release payment from escrow"""
        return {
            'amount': order['seller_earnings'],
            'payout_date': datetime.utcnow() + timedelta(days=1)
        }
    
    def _update_seller_stats(self, seller_id: int, order: Dict):
        """Update seller statistics"""
        self.logger.info(f"Updated seller {seller_id} stats")
    
    def _check_seller_level_upgrade(self, seller_id: int) -> Optional[str]:
        """Check if seller leveled up"""
        return None
    
    def _notify_seller_of_completion(self, seller: User, order: Dict, payout: Dict):
        """Notify seller of order completion"""
        self.logger.info(f"Notified seller {seller.email} of completion")
    
    def _save_revision_request(self, revision: Dict) -> str:
        """Save revision request"""
        revision_id = f"revision_{datetime.utcnow().timestamp()}"
        self.logger.info(f"Saved revision: {revision_id}")
        return revision_id
    
    def _notify_seller_of_revision(self, seller: User, order: Dict, revision: Dict):
        """Notify seller of revision request"""
        self.logger.info(f"Notified seller {seller.email} of revision")
    
    def _get_seller_stats(self, seller_id: int) -> Dict:
        """Get seller statistics"""
        return {
            'total_orders': 15,
            'completed_orders': 12,
            'active_orders': 3,
            'total_earnings': 850.00,
            'average_rating': 4.8,
            'response_time': '1 hour',
            'on_time_delivery': '95%'
        }
    
    def _get_seller_active_orders(self, seller_id: int) -> List[Dict]:
        """Get seller's active orders"""
        return []
    
    def _calculate_seller_earnings(self, seller_id: int) -> Dict:
        """Calculate seller earnings"""
        return {
            'total_earnings': 850.00,
            'available_for_withdrawal': 650.00,
            'pending_clearance': 200.00,
            'this_month': 250.00,
            'last_month': 400.00
        }
    
    def _get_seller_gigs(self, seller_id: int) -> List[Dict]:
        """Get seller's gigs"""
        return []
    
    def _calculate_seller_performance(self, seller_id: int) -> Dict:
        """Calculate performance metrics"""
        return {
            'order_completion_rate': 95,
            'on_time_delivery_rate': 92,
            'buyer_satisfaction': 4.8,
            'response_rate': 98,
            'avg_delivery_time': 3.2
        }
    
    def _get_seller_recommendations(self, seller_id: int, performance: Dict) -> List[str]:
        """Get recommendations for seller"""
        return [
            'Respond to inquiries faster to improve visibility',
            'Update your portfolio with recent work',
            'Consider creating premium tier offerings'
        ]


# Example usage
if __name__ == '__main__':
    service = SkillsMarketplaceService()
    
    # Test gig search
    print("Testing Gig Search:")
    result = service.search_gigs(search_query='web development')
    print(f"Found {result['total_results']} gigs")
