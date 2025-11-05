"""
Appointment Booking System Routes
Students can book appointments with Career Services advisors
"""
from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta, time
from sqlalchemy import func
from models import db, User
from models_growth_features import (
    CareerServiceAppointment, AdvisorAvailability, 
    AppointmentFeedback, PlatformEngagement
)

bp = Blueprint("appointments", __name__, url_prefix="/appointments")


@bp.get("/")
@login_required
def appointment_home():
    """Main appointments page - view and book appointments"""
    
    # Get user's upcoming appointments
    upcoming_appointments = CareerServiceAppointment.query.filter(
        CareerServiceAppointment.student_id == current_user.id,
        CareerServiceAppointment.scheduled_at >= datetime.utcnow(),
        CareerServiceAppointment.status == 'scheduled'
    ).order_by(CareerServiceAppointment.scheduled_at).all()
    
    # Get user's past appointments
    past_appointments = CareerServiceAppointment.query.filter(
        CareerServiceAppointment.student_id == current_user.id,
        CareerServiceAppointment.scheduled_at < datetime.utcnow()
    ).order_by(CareerServiceAppointment.scheduled_at.desc()).limit(5).all()
    
    return render_template(
        "appointments/index.html",
        upcoming=upcoming_appointments,
        past=past_appointments
    )


@bp.get("/book")
@login_required
def book_appointment():
    """Appointment booking interface"""
    
    # Get all career services advisors
    advisors = User.query.filter_by(role='career_advisor').all()
    
    # If no advisors exist, show all admins as advisors (for demo)
    if not advisors:
        advisors = User.query.filter_by(is_admin=True).all()
    
    return render_template(
        "appointments/book.html",
        advisors=advisors
    )


@bp.get("/api/advisor/<int:advisor_id>/availability")
@login_required
def get_advisor_availability(advisor_id):
    """Get available time slots for an advisor"""
    
    # Get date range (next 14 days)
    start_date = datetime.utcnow().date()
    end_date = start_date + timedelta(days=14)
    
    # Get advisor's recurring availability
    availability_slots = AdvisorAvailability.query.filter_by(
        advisor_id=advisor_id,
        is_available=True
    ).all()
    
    # Generate available slots
    available_slots = []
    current_date = start_date
    
    while current_date <= end_date:
        day_name = current_date.strftime('%A').lower()
        
        # Find availability for this day
        day_slots = [slot for slot in availability_slots if slot.day_of_week == day_name]
        
        for slot in day_slots:
            # Check if slot is already booked
            slot_datetime = datetime.combine(current_date, slot.start_time)
            
            existing_appointment = CareerServiceAppointment.query.filter(
                CareerServiceAppointment.advisor_id == advisor_id,
                CareerServiceAppointment.scheduled_at == slot_datetime,
                CareerServiceAppointment.status.in_(['scheduled', 'confirmed'])
            ).first()
            
            if not existing_appointment:
                available_slots.append({
                    "date": current_date.isoformat(),
                    "time": slot.start_time.strftime('%H:%M'),
                    "datetime": slot_datetime.isoformat(),
                    "day": day_name.capitalize()
                })
        
        current_date += timedelta(days=1)
    
    return jsonify(available_slots=available_slots)


@bp.post("/api/book")
@login_required
def create_appointment():
    """Book a new appointment"""
    data = request.get_json()
    
    advisor_id = data.get('advisor_id')
    scheduled_at = datetime.fromisoformat(data.get('scheduled_at'))
    appointment_type = data.get('appointment_type', 'general')
    student_notes = data.get('notes', '')
    
    # Validate advisor exists
    advisor = User.query.get(advisor_id)
    if not advisor:
        return jsonify(error="Advisor not found"), 404
    
    # Check if slot is still available
    existing = CareerServiceAppointment.query.filter_by(
        advisor_id=advisor_id,
        scheduled_at=scheduled_at,
        status='scheduled'
    ).first()
    
    if existing:
        return jsonify(error="This time slot is no longer available"), 400
    
    # Create appointment
    appointment = CareerServiceAppointment(
        student_id=current_user.id,
        advisor_id=advisor_id,
        appointment_type=appointment_type,
        scheduled_at=scheduled_at,
        duration_minutes=30,
        location="Career Development Office - Room 205",
        status='scheduled',
        student_notes=student_notes
    )
    
    db.session.add(appointment)
    
    # Update engagement metrics
    today = datetime.utcnow().date()
    engagement = PlatformEngagement.query.filter_by(date=today).first()
    if not engagement:
        engagement = PlatformEngagement(date=today)
        db.session.add(engagement)
    engagement.appointments_booked = (engagement.appointments_booked or 0) + 1
    
    db.session.commit()
    
    return jsonify(
        success=True,
        appointment_id=appointment.id,
        message="Appointment booked successfully!"
    )


@bp.post("/api/<int:appointment_id>/cancel")
@login_required
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    
    appointment = CareerServiceAppointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appointment.student_id != current_user.id:
        return jsonify(error="Unauthorized"), 403
    
    # Check if appointment is in the future
    if appointment.scheduled_at < datetime.utcnow():
        return jsonify(error="Cannot cancel past appointments"), 400
    
    appointment.status = 'cancelled'
    db.session.commit()
    
    return jsonify(success=True, message="Appointment cancelled")


@bp.get("/<int:appointment_id>/feedback")
@login_required
def feedback_form(appointment_id):
    """Feedback form for completed appointment"""
    
    appointment = CareerServiceAppointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appointment.student_id != current_user.id:
        flash("Unauthorized access", "danger")
        return redirect(url_for('appointments.appointment_home'))
    
    # Check if feedback already exists
    existing_feedback = AppointmentFeedback.query.filter_by(
        appointment_id=appointment_id
    ).first()
    
    return render_template(
        "appointments/feedback.html",
        appointment=appointment,
        existing_feedback=existing_feedback
    )


@bp.post("/<int:appointment_id>/feedback")
@login_required
def submit_feedback(appointment_id):
    """Submit feedback for an appointment"""
    
    appointment = CareerServiceAppointment.query.get_or_404(appointment_id)
    
    # Verify ownership
    if appointment.student_id != current_user.id:
        return jsonify(error="Unauthorized"), 403
    
    # Get feedback data
    rating = request.form.get('rating', type=int)
    was_helpful = request.form.get('was_helpful') == 'true'
    followed_advice = request.form.get('followed_advice') == 'true'
    outcome_improved = request.form.get('outcome_improved') == 'true'
    comments = request.form.get('comments', '')
    would_recommend = request.form.get('would_recommend') == 'true'
    
    # Create or update feedback
    feedback = AppointmentFeedback.query.filter_by(
        appointment_id=appointment_id
    ).first()
    
    if not feedback:
        feedback = AppointmentFeedback(
            appointment_id=appointment_id,
            student_id=current_user.id
        )
        db.session.add(feedback)
    
    feedback.rating = rating
    feedback.was_helpful = was_helpful
    feedback.followed_advice = followed_advice
    feedback.outcome_improved = outcome_improved
    feedback.comments = comments
    feedback.would_recommend = would_recommend
    
    db.session.commit()
    
    flash("Thank you for your feedback!", "success")
    return redirect(url_for('appointments.appointment_home'))


# ==========================================
# ADVISOR PORTAL (for Career Services staff)
# ==========================================

@bp.get("/advisor/dashboard")
@login_required
def advisor_dashboard():
    """Dashboard for career services advisors"""
    
    # Check if user is advisor or admin
    is_advisor = getattr(current_user, 'role', '') == 'career_advisor' or \
                 getattr(current_user, 'is_admin', False)
    
    if not is_advisor:
        flash("Access denied - Advisors only", "danger")
        return redirect(url_for('index'))
    
    # Get today's appointments
    today = datetime.utcnow().date()
    today_appointments = CareerServiceAppointment.query.filter(
        CareerServiceAppointment.advisor_id == current_user.id,
        func.date(CareerServiceAppointment.scheduled_at) == today,
        CareerServiceAppointment.status == 'scheduled'
    ).order_by(CareerServiceAppointment.scheduled_at).all()
    
    # Get upcoming appointments (next 7 days)
    week_from_now = today + timedelta(days=7)
    upcoming_appointments = CareerServiceAppointment.query.filter(
        CareerServiceAppointment.advisor_id == current_user.id,
        func.date(CareerServiceAppointment.scheduled_at) > today,
        func.date(CareerServiceAppointment.scheduled_at) <= week_from_now,
        CareerServiceAppointment.status == 'scheduled'
    ).order_by(CareerServiceAppointment.scheduled_at).all()
    
    # Get feedback stats
    avg_rating = db.session.query(
        func.avg(AppointmentFeedback.rating)
    ).join(
        CareerServiceAppointment
    ).filter(
        CareerServiceAppointment.advisor_id == current_user.id
    ).scalar() or 0
    
    return render_template(
        "appointments/advisor_dashboard.html",
        today_appointments=today_appointments,
        upcoming_appointments=upcoming_appointments,
        avg_rating=round(avg_rating, 2)
    )


@bp.get("/advisor/availability")
@login_required
def manage_availability():
    """Manage advisor availability schedule"""
    
    is_advisor = getattr(current_user, 'role', '') == 'career_advisor' or \
                 getattr(current_user, 'is_admin', False)
    
    if not is_advisor:
        flash("Access denied", "danger")
        return redirect(url_for('index'))
    
    # Get current availability
    availability = AdvisorAvailability.query.filter_by(
        advisor_id=current_user.id
    ).all()
    
    return render_template(
        "appointments/availability.html",
        availability=availability
    )


@bp.post("/advisor/availability")
@login_required
def add_availability():
    """Add availability slot"""
    
    is_advisor = getattr(current_user, 'role', '') == 'career_advisor' or \
                 getattr(current_user, 'is_admin', False)
    
    if not is_advisor:
        return jsonify(error="Unauthorized"), 403
    
    day_of_week = request.form.get('day_of_week')
    start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    
    availability = AdvisorAvailability(
        advisor_id=current_user.id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        is_recurring=True
    )
    
    db.session.add(availability)
    db.session.commit()
    
    flash("Availability added successfully", "success")
    return redirect(url_for('appointments.manage_availability'))
