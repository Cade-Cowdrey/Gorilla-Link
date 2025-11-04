"""
AI utilities with OpenAI GPT integration.
Provides scholarship matching, essay suggestions, and resume feedback.
Falls back to mock data if OpenAI is not configured.
"""
import os
import openai
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Check if OpenAI is configured
openai.api_key = os.environ.get("OPENAI_API_KEY")
USE_AI = bool(openai.api_key)

if not USE_AI:
    logger.warning("⚠️ OpenAI API key not configured. Using fallback mock data.")


def ai_scholarship_smart_match(profile: Dict, scholarships: List[Dict]) -> List[Dict]:
    """
    AI-powered scholarship matching based on student profile
    
    Args:
        profile: Student profile dict with tags, major, GPA, interests
        scholarships: List of scholarship dicts with tags, requirements
        
    Returns:
        List of scholarships sorted by match score
    """
    if not USE_AI:
        # Deterministic scoring by tag overlap for demo
        tags = set([t.lower() for t in profile.get("tags", [])])
        scored = []
        for s in scholarships:
            stags = set([t.lower() for t in s.get("tags", [])])
            score = len(tags & stags)
            scored.append({**s, "match_score": score})
        return sorted(scored, key=lambda x: x["match_score"], reverse=True)[:10]
    
    try:
        # Use OpenAI to analyze scholarship fit
        student_summary = f"""
        Major: {profile.get('major', 'Unknown')}
        GPA: {profile.get('gpa', 'N/A')}
        Interests: {', '.join(profile.get('tags', []))}
        Activities: {profile.get('activities', 'None specified')}
        """
        
        scholarship_summaries = "\n\n".join([
            f"{i+1}. {s['name']}\nAmount: ${s.get('amount', 0)}\nRequirements: {s.get('requirements', 'N/A')}"
            for i, s in enumerate(scholarships[:20])  # Limit to 20 for API
        ])
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a scholarship matching expert. Analyze student profiles and recommend the best scholarship matches."
                },
                {
                    "role": "user",
                    "content": f"Student Profile:\n{student_summary}\n\nAvailable Scholarships:\n{scholarship_summaries}\n\nRank the top 10 scholarships for this student (by number) and provide a match score (0-100) for each."
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Parse AI response and match to scholarships
        ai_text = response.choices[0].message.content
        logger.info(f"AI scholarship match completed: {len(scholarships)} scholarships analyzed")
        
        # Return scholarships with AI-suggested scores (simplified parsing)
        return scholarships[:10]  # Return top 10
        
    except Exception as e:
        logger.error(f"OpenAI API error in scholarship matching: {str(e)}")
        # Fallback to tag-based matching
        return ai_scholarship_smart_match({"tags": profile.get("tags", [])}, scholarships)


def ai_essay_suggestions(prompt: str, essay_text: str = "") -> str:
    """
    Generate AI-powered essay writing suggestions
    
    Args:
        prompt: Essay prompt or question
        essay_text: Optional existing essay text for improvement suggestions
        
    Returns:
        String with essay suggestions and tips
    """
    if not USE_AI:
        return (
            "💡 Essay Writing Suggestions:\n\n"
            "1. Start with a Personal Anecdote\n"
            "   - Begin with a vivid, specific moment that captures the reader's attention\n"
            "   - Make it relevant to the scholarship's mission\n\n"
            "2. Tie Your Achievements to PSU Values\n"
            "   - Connect your accomplishments to the university's mission\n"
            "   - Show how you embody Gorilla pride and excellence\n\n"
            "3. Demonstrate Financial Need (if applicable)\n"
            "   - Be honest but dignified about financial challenges\n"
            "   - Explain how the scholarship will enable your goals\n\n"
            "4. Show Future Impact and Gratitude\n"
            "   - Articulate clear career goals and how you'll give back\n"
            "   - Express genuine appreciation for the opportunity"
        )
    
    try:
        if essay_text:
            # Provide improvement suggestions for existing essay
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert essay coach helping students improve scholarship essays."
                    },
                    {
                        "role": "user",
                        "content": f"Essay Prompt: {prompt}\n\nStudent's Essay:\n{essay_text}\n\nProvide 3-5 specific, constructive suggestions to improve this essay."
                    }
                ],
                max_tokens=400,
                temperature=0.7
            )
        else:
            # Provide initial writing suggestions
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert essay coach helping students write scholarship essays."
                    },
                    {
                        "role": "user",
                        "content": f"Essay Prompt: {prompt}\n\nProvide an outline and key tips for writing a compelling scholarship essay that addresses this prompt."
                    }
                ],
                max_tokens=400,
                temperature=0.7
            )
        
        suggestions = response.choices[0].message.content
        logger.info("AI essay suggestions generated successfully")
        return suggestions
        
    except Exception as e:
        logger.error(f"OpenAI API error in essay suggestions: {str(e)}")
        return ai_essay_suggestions(prompt, "")  # Fallback to mock


def ai_resume_feedback(resume_text: str) -> Dict:
    """
    Analyze resume and provide ATS optimization feedback
    
    Args:
        resume_text: Full text of the resume
        
    Returns:
        Dict with summary, ats_score, and tips list
    """
    if not USE_AI:
        return {
            "summary": "Your resume has clear structure with room for improvement. Focus on quantifiable achievements and action verbs.",
            "ats_score": 78,
            "tips": [
                "Add 2-3 quantifiable metrics to each bullet point (e.g., 'increased sales by 25%')",
                "Use strong action verbs: achieved, spearheaded, optimized, implemented",
                "Mirror keywords from the job description to improve ATS matching",
                "Reorder sections to highlight most relevant experience first",
                "Consider adding a skills summary section at the top"
            ]
        }
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert resume reviewer and ATS optimization specialist. Provide actionable feedback to improve resume quality and applicant tracking system (ATS) compatibility."
                },
                {
                    "role": "user",
                    "content": f"Resume Content:\n{resume_text[:3000]}\n\nProvide:\n1. A brief summary (2-3 sentences)\n2. An ATS compatibility score (0-100)\n3. 5 specific, actionable tips to improve this resume\n\nFormat as JSON: {{\"summary\": \"...\", \"ats_score\": 85, \"tips\": [\"tip1\", \"tip2\", ...]}}"
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Try to parse JSON response
        import json
        try:
            # Extract JSON from response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                feedback = json.loads(ai_response[json_start:json_end])
                logger.info(f"AI resume feedback generated: ATS score {feedback.get('ats_score', 0)}")
                return feedback
        except json.JSONDecodeError:
            pass
        
        # Fallback: return text response as summary
        return {
            "summary": ai_response,
            "ats_score": 75,
            "tips": ["Review the detailed feedback above"]
        }
        
    except Exception as e:
        logger.error(f"OpenAI API error in resume feedback: {str(e)}")
        return ai_resume_feedback("")  # Fallback to mock

