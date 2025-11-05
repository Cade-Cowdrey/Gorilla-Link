"""Stripe Payment Routes"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models_monetization import (
    EmployerSubscription, EmployerTier, SubscriptionStatus,
    RevenueTransaction, JobBoost, ScholarshipSponsorship,
    CareerFairParticipation, EmployerBrandingPackage
)
from datetime import datetime, timedelta
import stripe
import os

# Create blueprint
bp = Blueprint('payments', __name__, url_prefix='/payments')

# Stripe configuration
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')

# Stripe Price IDs (create these in Stripe Dashboard)
PRICE_IDS = {
    'professional_monthly': os.environ.get('STRIPE_PROFESSIONAL_PRICE_ID', 'price_professional_monthly'),
    'professional_annual': os.environ.get('STRIPE_PROFESSIONAL_ANNUAL_ID', 'price_professional_annual'),
    'enterprise_monthly': os.environ.get('STRIPE_ENTERPRISE_PRICE_ID', 'price_enterprise_monthly'),
    'enterprise_annual': os.environ.get('STRIPE_ENTERPRISE_ANNUAL_ID', 'price_enterprise_annual'),
    'platinum_monthly': os.environ.get('STRIPE_PLATINUM_PRICE_ID', 'price_platinum_monthly'),
    'platinum_annual': os.environ.get('STRIPE_PLATINUM_ANNUAL_ID', 'price_platinum_annual'),
}


@bp.route('/pricing')
def pricing():
    """Show pricing page"""
    return render_template('employer_pricing.html', 
                         stripe_key=STRIPE_PUBLISHABLE_KEY)


@bp.route('/upgrade')
@login_required
def upgrade():
    """Upgrade subscription page"""
    plan = request.args.get('plan', 'professional')
    promo = request.args.get('promo', '')
    
    # Get or create subscription
    subscription = EmployerSubscription.query.filter_by(user_id=current_user.id).first()
    if not subscription:
        subscription = EmployerSubscription(user_id=current_user.id)
        db.session.add(subscription)
        db.session.commit()
    
    return render_template('payments/upgrade.html',
                         subscription=subscription,
                         plan=plan,
                         promo=promo,
                         stripe_key=STRIPE_PUBLISHABLE_KEY)


@bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    try:
        data = request.get_json()
        plan = data.get('plan', 'professional')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        # Get price ID
        price_key = f"{plan}_{billing_cycle}"
        price_id = PRICE_IDS.get(price_key)
        
        if not price_id:
            return jsonify({'error': 'Invalid plan selected'}), 400
        
        # Get or create Stripe customer
        subscription = EmployerSubscription.query.filter_by(user_id=current_user.id).first()
        if not subscription:
            subscription = EmployerSubscription(user_id=current_user.id)
            db.session.add(subscription)
            db.session.commit()
        
        if not subscription.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=getattr(current_user, 'company_name', current_user.name),
                metadata={'user_id': current_user.id}
            )
            subscription.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=subscription.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payments.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payments.upgrade', plan=plan, _external=True),
            metadata={
                'user_id': current_user.id,
                'plan': plan,
            }
        )
        
        return jsonify({'sessionId': checkout_session.id})
        
    except Exception as e:
        current_app.logger.error(f"Checkout error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route('/success')
@login_required
def success():
    """Payment success page"""
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Update subscription
            subscription = EmployerSubscription.query.filter_by(user_id=current_user.id).first()
            if subscription and session.subscription:
                stripe_subscription = stripe.Subscription.retrieve(session.subscription)
                
                # Update subscription details
                subscription.stripe_subscription_id = stripe_subscription.id
                subscription.stripe_price_id = stripe_subscription['items']['data'][0]['price']['id']
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                
                # Set tier based on plan
                plan = session.metadata.get('plan', 'professional')
                subscription.tier = EmployerTier[plan.upper()]
                
                db.session.commit()
                
                flash(f'Successfully upgraded to {plan.title()} plan!', 'success')
        
        except Exception as e:
            current_app.logger.error(f"Success page error: {str(e)}")
            flash('Payment succeeded, but there was an error updating your account. Please contact support.', 'warning')
    
    return render_template('payments/success.html')


@bp.route('/webhook', methods=['POST'])
def webhook():
    """Stripe webhook handler"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_completed(session)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_payment_succeeded(invoice)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)
    
    return jsonify({'status': 'success'})


def handle_checkout_completed(session):
    """Handle successful checkout"""
    user_id = session['metadata'].get('user_id')
    if not user_id:
        return
    
    subscription = EmployerSubscription.query.filter_by(user_id=user_id).first()
    if subscription and session.get('subscription'):
        subscription.stripe_subscription_id = session['subscription']
        subscription.status = SubscriptionStatus.ACTIVE
        db.session.commit()


def handle_subscription_updated(stripe_subscription):
    """Handle subscription updates"""
    subscription = EmployerSubscription.query.filter_by(
        stripe_subscription_id=stripe_subscription['id']
    ).first()
    
    if subscription:
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'])
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'])
        subscription.status = SubscriptionStatus.ACTIVE if stripe_subscription['status'] == 'active' else SubscriptionStatus.CANCELLED
        db.session.commit()


def handle_subscription_cancelled(stripe_subscription):
    """Handle subscription cancellation"""
    subscription = EmployerSubscription.query.filter_by(
        stripe_subscription_id=stripe_subscription['id']
    ).first()
    
    if subscription:
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        db.session.commit()


def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    subscription = EmployerSubscription.query.filter_by(
        stripe_customer_id=invoice['customer']
    ).first()
    
    if subscription:
        # Create revenue transaction
        amount = invoice['amount_paid']
        transaction = RevenueTransaction(
            user_id=subscription.user_id,
            transaction_type='subscription',
            amount=amount,
            description=f"Subscription payment - {subscription.tier.value}",
            stripe_payment_intent_id=invoice.get('payment_intent'),
            stripe_invoice_id=invoice['id'],
            payment_status='succeeded',
            psu_share_amount=RevenueTransaction.calculate_psu_share(amount),
            platform_revenue=amount - RevenueTransaction.calculate_psu_share(amount),
            paid_at=datetime.utcnow()
        )
        db.session.add(transaction)
        db.session.commit()


def handle_payment_failed(invoice):
    """Handle failed payment"""
    subscription = EmployerSubscription.query.filter_by(
        stripe_customer_id=invoice['customer']
    ).first()
    
    if subscription:
        subscription.status = SubscriptionStatus.PAST_DUE
        db.session.commit()
        
        # TODO: Send email notification to user


@bp.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    """Cancel subscription"""
    subscription = EmployerSubscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_subscription_id:
        flash('No active subscription found.', 'error')
        return redirect(url_for('dashboard.employer_dashboard'))
    
    try:
        # Cancel at period end (don't cancel immediately)
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        flash('Your subscription will be cancelled at the end of the current billing period.', 'info')
        
    except Exception as e:
        current_app.logger.error(f"Cancellation error: {str(e)}")
        flash('Error cancelling subscription. Please contact support.', 'error')
    
    return redirect(url_for('dashboard.employer_dashboard'))


@bp.route('/portal')
@login_required
def customer_portal():
    """Redirect to Stripe customer portal"""
    subscription = EmployerSubscription.query.filter_by(user_id=current_user.id).first()
    
    if not subscription or not subscription.stripe_customer_id:
        flash('No billing information found.', 'error')
        return redirect(url_for('dashboard.employer_dashboard'))
    
    try:
        portal_session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=url_for('dashboard.employer_dashboard', _external=True)
        )
        return redirect(portal_session.url)
        
    except Exception as e:
        current_app.logger.error(f"Portal error: {str(e)}")
        flash('Error accessing billing portal. Please contact support.', 'error')
        return redirect(url_for('dashboard.employer_dashboard'))


# One-time payment routes (job boosts, scholarships, etc.)

@bp.route('/boost/<int:job_id>', methods=['POST'])
@login_required
def boost_job(job_id):
    """Purchase job boost"""
    data = request.get_json()
    boost_type = data.get('boost_type', '7day')
    
    # Pricing
    boost_prices = {
        '24hr': 4900,  # $49.00
        '7day': 9900,  # $99.00
        '30day': 19900  # $199.00
    }
    
    amount = boost_prices.get(boost_type)
    if not amount:
        return jsonify({'error': 'Invalid boost type'}), 400
    
    try:
        # Create payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'user_id': current_user.id,
                'job_id': job_id,
                'boost_type': boost_type,
                'type': 'job_boost'
            }
        )
        
        return jsonify({'clientSecret': payment_intent.client_secret})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/boost/confirm', methods=['POST'])
@login_required
def confirm_boost():
    """Confirm job boost payment"""
    data = request.get_json()
    payment_intent_id = data.get('payment_intent_id')
    
    try:
        payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if payment_intent.status == 'succeeded':
            # Create boost record
            boost_durations = {
                '24hr': timedelta(hours=24),
                '7day': timedelta(days=7),
                '30day': timedelta(days=30)
            }
            
            boost_type = payment_intent.metadata['boost_type']
            duration = boost_durations.get(boost_type, timedelta(days=7))
            
            boost = JobBoost(
                job_id=payment_intent.metadata['job_id'],
                user_id=current_user.id,
                boost_type=boost_type,
                boost_cost=payment_intent.amount,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + duration,
                stripe_payment_intent_id=payment_intent_id,
                paid=True
            )
            db.session.add(boost)
            
            # Create revenue transaction
            transaction = RevenueTransaction(
                user_id=current_user.id,
                transaction_type='boost',
                amount=payment_intent.amount,
                description=f"Job boost - {boost_type}",
                stripe_payment_intent_id=payment_intent_id,
                payment_status='succeeded',
                psu_share_amount=RevenueTransaction.calculate_psu_share(payment_intent.amount),
                platform_revenue=payment_intent.amount - RevenueTransaction.calculate_psu_share(payment_intent.amount),
                paid_at=datetime.utcnow()
            )
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Payment not completed'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
