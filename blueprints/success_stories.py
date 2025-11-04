"""
PSU Connect - Success Stories Feature
Social feed for user achievements and career milestones
"""

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func, desc
from extensions import db
from models_growth_features import (
    SuccessStory, StoryReaction, StoryComment
)
from datetime import datetime, timedelta

success_stories_bp = Blueprint('success_stories', __name__, url_prefix='/success-stories')


# =====================
# SUCCESS STORIES FEED
# =====================

@success_stories_bp.route('/')
@success_stories_bp.route('/feed')
def feed():
    """Main success stories feed"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', 'all')  # all, job_offer, promotion, graduation
    
    # Build query
    query = SuccessStory.query.filter_by(is_public=True)
    
    if filter_type != 'all':
        query = query.filter_by(story_type=filter_type)
    
    # Order by featured first, then recent
    stories = query.order_by(
        desc(SuccessStory.is_featured),
        desc(SuccessStory.created_at)
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Get reaction counts for each story
    story_data = []
    for story in stories.items:
        reactions = db.session.query(
            StoryReaction.reaction_type,
            func.count(StoryReaction.id)
        ).filter_by(story_id=story.id).group_by(StoryReaction.reaction_type).all()
        
        reaction_counts = {r[0]: r[1] for r in reactions}
        
        # Check if current user reacted
        user_reaction = None
        if current_user.is_authenticated:
            user_reaction_obj = StoryReaction.query.filter_by(
                story_id=story.id,
                user_id=current_user.id
            ).first()
            if user_reaction_obj:
                user_reaction = user_reaction_obj.reaction_type
        
        # Get comment count
        comment_count = StoryComment.query.filter_by(story_id=story.id).count()
        
        story_data.append({
            'story': story,
            'reactions': reaction_counts,
            'user_reaction': user_reaction,
            'comment_count': comment_count
        })
    
    return render_template('success_stories/feed.html',
                         stories=story_data,
                         pagination=stories,
                         current_filter=filter_type)


@success_stories_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_story():
    """Create new success story"""
    if request.method == 'POST':
        story = SuccessStory(
            user_id=current_user.id,
            story_type=request.form.get('story_type'),
            title=request.form.get('title'),
            content=request.form.get('content'),
            company_name=request.form.get('company_name'),
            position=request.form.get('position'),
            salary_range=request.form.get('salary_range'),
            tags=request.form.get('tags', '').split(','),
            image_url=request.form.get('image_url'),
            is_public=request.form.get('is_public') == 'on'
        )
        
        db.session.add(story)
        db.session.commit()
        
        flash('Success story shared! Congratulations! 🎉', 'success')
        return redirect(url_for('success_stories.view_story', story_id=story.id))
    
    return render_template('success_stories/create.html')


@success_stories_bp.route('/<int:story_id>')
def view_story(story_id):
    """View single success story with comments"""
    story = SuccessStory.query.get_or_404(story_id)
    
    # Increment view count
    story.views_count += 1
    db.session.commit()
    
    # Get reactions
    reactions = db.session.query(
        StoryReaction.reaction_type,
        func.count(StoryReaction.id)
    ).filter_by(story_id=story.id).group_by(StoryReaction.reaction_type).all()
    
    reaction_counts = {r[0]: r[1] for r in reactions}
    
    # Check if current user reacted
    user_reaction = None
    if current_user.is_authenticated:
        user_reaction_obj = StoryReaction.query.filter_by(
            story_id=story.id,
            user_id=current_user.id
        ).first()
        if user_reaction_obj:
            user_reaction = user_reaction_obj.reaction_type
    
    # Get comments (top-level only)
    comments = StoryComment.query.filter_by(
        story_id=story.id,
        parent_comment_id=None
    ).order_by(StoryComment.created_at.desc()).all()
    
    return render_template('success_stories/detail.html',
                         story=story,
                         reactions=reaction_counts,
                         user_reaction=user_reaction,
                         comments=comments)


@success_stories_bp.route('/<int:story_id>/react', methods=['POST'])
@login_required
def react_to_story(story_id):
    """Add or update reaction to story"""
    story = SuccessStory.query.get_or_404(story_id)
    reaction_type = request.json.get('type')  # like, celebrate, insightful, love, support
    
    # Check for existing reaction
    existing = StoryReaction.query.filter_by(
        story_id=story_id,
        user_id=current_user.id
    ).first()
    
    if existing:
        if existing.reaction_type == reaction_type:
            # Remove reaction
            db.session.delete(existing)
            db.session.commit()
            return jsonify({'success': True, 'action': 'removed'})
        else:
            # Update reaction
            existing.reaction_type = reaction_type
    else:
        # Create new reaction
        reaction = StoryReaction(
            story_id=story_id,
            user_id=current_user.id,
            reaction_type=reaction_type
        )
        db.session.add(reaction)
    
    db.session.commit()
    
    return jsonify({'success': True, 'action': 'added'})


@success_stories_bp.route('/<int:story_id>/comment', methods=['POST'])
@login_required
def comment_on_story(story_id):
    """Add comment to story"""
    story = SuccessStory.query.get_or_404(story_id)
    content = request.form.get('content')
    parent_comment_id = request.form.get('parent_comment_id', type=int)
    
    if not content or len(content.strip()) < 1:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('success_stories.view_story', story_id=story_id))
    
    comment = StoryComment(
        story_id=story_id,
        user_id=current_user.id,
        content=content,
        parent_comment_id=parent_comment_id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added!', 'success')
    return redirect(url_for('success_stories.view_story', story_id=story_id))


@success_stories_bp.route('/my-stories')
@login_required
def my_stories():
    """View user's own success stories"""
    stories = SuccessStory.query.filter_by(user_id=current_user.id).order_by(
        desc(SuccessStory.created_at)
    ).all()
    
    # Get stats for each story
    story_stats = []
    for story in stories:
        reaction_count = StoryReaction.query.filter_by(story_id=story.id).count()
        comment_count = StoryComment.query.filter_by(story_id=story.id).count()
        
        story_stats.append({
            'story': story,
            'reactions': reaction_count,
            'comments': comment_count,
            'views': story.views_count
        })
    
    return render_template('success_stories/my_stories.html', stories=story_stats)
