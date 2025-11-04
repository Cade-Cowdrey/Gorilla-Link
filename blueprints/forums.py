"""
PSU Connect - Discussion Forums
Reddit-style Q&A community for PSU students and alumni
"""

from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models_growth_features import ForumCategory, ForumTopic, ForumPost, ForumVote
from sqlalchemy import func, desc
from datetime import datetime

forums_bp = Blueprint('forums', __name__, url_prefix='/forums')


@forums_bp.route('/')
def index():
    """Forum categories overview"""
    categories = ForumCategory.query.order_by(ForumCategory.display_order).all()
    
    # Get stats for each category
    for cat in categories:
        cat.topic_count = ForumTopic.query.filter_by(category_id=cat.id).count()
        cat.post_count = db.session.query(func.count(ForumPost.id)).join(
            ForumTopic
        ).filter(ForumTopic.category_id == cat.id).scalar()
        
        # Get latest post
        latest = db.session.query(ForumPost).join(
            ForumTopic
        ).filter(
            ForumTopic.category_id == cat.id
        ).order_by(desc(ForumPost.created_at)).first()
        
        cat.latest_post = latest
    
    # Get overall stats
    total_topics = ForumTopic.query.count()
    total_posts = ForumPost.query.count()
    total_users = db.session.query(
        func.count(func.distinct(ForumTopic.created_by))
    ).scalar()
    
    return render_template('forums/index.html',
                         categories=categories,
                         total_topics=total_topics,
                         total_posts=total_posts,
                         total_users=total_users)


@forums_bp.route('/category/<int:category_id>')
def category_topics(category_id):
    """List topics in a category"""
    category = ForumCategory.query.get_or_404(category_id)
    
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'recent')  # recent, popular, unanswered
    
    query = ForumTopic.query.filter_by(category_id=category_id)
    
    if sort == 'popular':
        query = query.order_by(desc(ForumTopic.view_count))
    elif sort == 'unanswered':
        query = query.filter_by(is_answered=False)
        query = query.order_by(desc(ForumTopic.created_at))
    else:  # recent
        query = query.order_by(desc(ForumTopic.last_activity))
    
    topics = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('forums/category.html',
                         category=category,
                         topics=topics,
                         sort=sort)


@forums_bp.route('/topic/<int:topic_id>')
def view_topic(topic_id):
    """View a topic and its posts"""
    topic = ForumTopic.query.get_or_404(topic_id)
    
    # Increment view count
    topic.view_count += 1
    db.session.commit()
    
    # Get posts with pagination
    page = request.args.get('page', 1, type=int)
    posts = ForumPost.query.filter_by(
        topic_id=topic_id
    ).order_by(
        desc(ForumPost.is_best_answer),  # Best answer first
        ForumPost.created_at
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Get user votes
    user_votes = {}
    if current_user.is_authenticated:
        votes = ForumVote.query.filter_by(user_id=current_user.id).all()
        user_votes = {v.post_id: v.vote_type for v in votes}
    
    return render_template('forums/topic.html',
                         topic=topic,
                         posts=posts,
                         user_votes=user_votes)


@forums_bp.route('/create-topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    """Create a new topic"""
    if request.method == 'POST':
        data = request.form
        
        category_id = data.get('category_id', type=int)
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        tags = data.get('tags', '').strip()
        
        if not all([category_id, title, content]):
            return jsonify({'error': 'All fields required'}), 400
        
        # Verify category exists
        category = ForumCategory.query.get(category_id)
        if not category:
            return jsonify({'error': 'Invalid category'}), 400
        
        # Create topic
        topic = ForumTopic(
            category_id=category_id,
            title=title,
            content=content,
            tags=tags.split(',') if tags else [],
            created_by=current_user.id,
            last_activity=datetime.utcnow()
        )
        db.session.add(topic)
        db.session.flush()  # Get topic.id
        
        # Create first post (same as topic content)
        first_post = ForumPost(
            topic_id=topic.id,
            content=content,
            created_by=current_user.id
        )
        db.session.add(first_post)
        
        db.session.commit()
        
        return redirect(url_for('forums.view_topic', topic_id=topic.id))
    
    # GET - show form
    categories = ForumCategory.query.order_by(ForumCategory.display_order).all()
    return render_template('forums/create_topic.html', categories=categories)


@forums_bp.route('/topic/<int:topic_id>/reply', methods=['POST'])
@login_required
def reply_to_topic(topic_id):
    """Reply to a topic"""
    topic = ForumTopic.query.get_or_404(topic_id)
    
    if topic.is_locked:
        return jsonify({'error': 'Topic is locked'}), 403
    
    data = request.json
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id', type=int)
    
    if not content:
        return jsonify({'error': 'Content required'}), 400
    
    # Create post
    post = ForumPost(
        topic_id=topic_id,
        content=content,
        created_by=current_user.id,
        parent_id=parent_id
    )
    db.session.add(post)
    
    # Update topic activity
    topic.last_activity = datetime.utcnow()
    topic.reply_count += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'post_id': post.id,
        'created_at': post.created_at.isoformat()
    })


@forums_bp.route('/post/<int:post_id>/vote', methods=['POST'])
@login_required
def vote_post(post_id):
    """Upvote or downvote a post"""
    post = ForumPost.query.get_or_404(post_id)
    
    data = request.json
    vote_type = data.get('vote_type')  # 'up' or 'down'
    
    if vote_type not in ['up', 'down']:
        return jsonify({'error': 'Invalid vote type'}), 400
    
    # Can't vote on own posts
    if post.created_by == current_user.id:
        return jsonify({'error': 'Cannot vote on your own post'}), 403
    
    # Check existing vote
    existing_vote = ForumVote.query.filter_by(
        user_id=current_user.id,
        post_id=post_id
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            # Remove vote (toggle)
            if vote_type == 'up':
                post.upvotes -= 1
            else:
                post.downvotes -= 1
            db.session.delete(existing_vote)
        else:
            # Change vote
            if vote_type == 'up':
                post.upvotes += 1
                post.downvotes -= 1
            else:
                post.downvotes += 1
                post.upvotes -= 1
            existing_vote.vote_type = vote_type
    else:
        # New vote
        vote = ForumVote(
            user_id=current_user.id,
            post_id=post_id,
            vote_type=vote_type
        )
        db.session.add(vote)
        
        if vote_type == 'up':
            post.upvotes += 1
        else:
            post.downvotes += 1
    
    db.session.commit()
    
    # Award points for getting upvoted
    if vote_type == 'up' and not existing_vote:
        from blueprints.gamification import award_points
        award_points(post.author.id, 5, 'post_upvoted')
    
    return jsonify({
        'success': True,
        'upvotes': post.upvotes,
        'downvotes': post.downvotes,
        'score': post.upvotes - post.downvotes
    })


@forums_bp.route('/post/<int:post_id>/mark-best', methods=['POST'])
@login_required
def mark_best_answer(post_id):
    """Mark a post as the best answer (topic creator only)"""
    post = ForumPost.query.get_or_404(post_id)
    topic = post.topic
    
    # Only topic creator can mark best answer
    if topic.created_by != current_user.id:
        return jsonify({'error': 'Only topic creator can mark best answer'}), 403
    
    # Can't mark your own post as best answer
    if post.created_by == current_user.id:
        return jsonify({'error': 'Cannot mark your own post as best answer'}), 403
    
    # Remove previous best answer
    ForumPost.query.filter_by(
        topic_id=topic.id,
        is_best_answer=True
    ).update({'is_best_answer': False})
    
    # Mark this as best answer
    post.is_best_answer = True
    topic.is_answered = True
    
    db.session.commit()
    
    # Award points to answer author
    from blueprints.gamification import award_points
    award_points(post.created_by, 25, 'best_answer')
    
    return jsonify({'success': True})


@forums_bp.route('/post/<int:post_id>/edit', methods=['POST'])
@login_required
def edit_post(post_id):
    """Edit a post"""
    post = ForumPost.query.get_or_404(post_id)
    
    # Only author can edit (or admin)
    if post.created_by != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Content required'}), 400
    
    post.content = content
    post.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True})


@forums_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a post"""
    post = ForumPost.query.get_or_404(post_id)
    
    # Only author can delete (or admin)
    if post.created_by != current_user.id:
        return jsonify({'error': 'Not authorized'}), 403
    
    # Can't delete first post (delete topic instead)
    if post == post.topic.posts[0]:
        return jsonify({'error': 'Cannot delete first post. Delete topic instead.'}), 400
    
    db.session.delete(post)
    
    # Update topic reply count
    post.topic.reply_count -= 1
    
    db.session.commit()
    
    return jsonify({'success': True})


@forums_bp.route('/search')
def search():
    """Search topics and posts"""
    query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    page = request.args.get('page', 1, type=int)
    
    if not query:
        return redirect(url_for('forums.index'))
    
    # Search topics
    topics_query = ForumTopic.query.filter(
        (ForumTopic.title.ilike(f'%{query}%')) |
        (ForumTopic.content.ilike(f'%{query}%'))
    )
    
    if category_id:
        topics_query = topics_query.filter_by(category_id=category_id)
    
    topics = topics_query.order_by(
        desc(ForumTopic.last_activity)
    ).paginate(page=page, per_page=20, error_out=False)
    
    categories = ForumCategory.query.all()
    
    return render_template('forums/search.html',
                         query=query,
                         topics=topics,
                         categories=categories,
                         selected_category=category_id)


@forums_bp.route('/my-topics')
@login_required
def my_topics():
    """User's topics"""
    page = request.args.get('page', 1, type=int)
    
    topics = ForumTopic.query.filter_by(
        created_by=current_user.id
    ).order_by(
        desc(ForumTopic.created_at)
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('forums/my_topics.html', topics=topics)


@forums_bp.route('/my-posts')
@login_required
def my_posts():
    """User's posts"""
    page = request.args.get('page', 1, type=int)
    
    posts = ForumPost.query.filter_by(
        created_by=current_user.id
    ).order_by(
        desc(ForumPost.created_at)
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('forums/my_posts.html', posts=posts)
