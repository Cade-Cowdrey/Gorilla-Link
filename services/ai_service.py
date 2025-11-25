"""
AI Service - GorillaGPT Assistant & AI-powered features
Handles: Chat conversations, resume/essay building, smart matching, predictions
"""

import openai
from typing import List, Dict, Any, Optional
from datetime import datetime
from extensions import db
from models_extended import AIConversation, PredictiveModel, UserPrediction, AutomatedTag
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Central AI service for PittState-Connect"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
    
    def chat(self, user_id: int, message: str, context: Optional[Dict] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        GorillaGPT chat assistant
        """
        try:
            # Generate session_id if not provided
            if not session_id:
                session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
            
            # Build conversation context from history
            conversation_history = self._get_conversation_history(user_id, session_id, limit=10)
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
            ]
            
            # Add conversation history
            for conv in conversation_history:
                messages.append({"role": "user", "content": conv.message})
                if conv.response:
                    messages.append({"role": "assistant", "content": conv.response})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Save to database
            conversation = AIConversation(
                user_id=user_id,
                session_id=session_id,
                message=message,
                response=assistant_message,
                context=context,
                model_used=self.model,
                tokens_used=tokens_used
            )
            db.session.add(conversation)
            db.session.commit()
            
            return {
                "response": assistant_message,
                "session_id": session_id,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            return {
                "response": "I'm sorry, I encountered an error. Please try again.",
                "error": str(e)
            }
    
    def build_resume(self, user_id: int, user_data: Dict) -> str:
        """
        AI-powered resume builder
        """
        prompt = f"""
        Create a professional resume based on the following information:
        
        Name: {user_data.get('name')}
        Email: {user_data.get('email')}
        Major: {user_data.get('major')}
        Graduation Year: {user_data.get('graduation_year')}
        Skills: {', '.join(user_data.get('skills', []))}
        Experience: {user_data.get('experience', 'No experience listed')}
        Education: {user_data.get('education', '')}
        
        Format it professionally with clear sections.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional resume writer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Resume building error: {e}")
            return "Error generating resume. Please try again."
    
    def improve_essay(self, essay_text: str, prompt: str) -> Dict[str, Any]:
        """
        AI essay improvement suggestions
        """
        analysis_prompt = f"""
        Review the following scholarship essay and provide:
        1. Grammar and spelling corrections
        2. Structure improvements
        3. Content enhancement suggestions
        4. Tone and style recommendations
        
        Essay Prompt: {prompt}
        
        Essay:
        {essay_text}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert writing tutor specializing in scholarship essays."},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            suggestions = response.choices[0].message.content
            
            return {
                "suggestions": suggestions,
                "word_count": len(essay_text.split()),
                "character_count": len(essay_text)
            }
            
        except Exception as e:
            logger.error(f"Essay improvement error: {e}")
            return {"suggestions": "Error analyzing essay.", "error": str(e)}
    
    def smart_match_scholarships(self, user_profile: Dict, scholarships: List[Dict]) -> List[Dict]:
        """
        AI-powered scholarship matching based on user profile
        """
        results = []
        
        for scholarship in scholarships:
            match_score = self._calculate_match_score(user_profile, scholarship)
            results.append({
                "scholarship": scholarship,
                "match_score": match_score,
                "reasons": self._generate_match_reasons(user_profile, scholarship)
            })
        
        # Sort by match score descending
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results
    
    def _calculate_match_score(self, user_profile: Dict, scholarship: Dict) -> float:
        """
        Calculate match score between user and scholarship
        """
        score = 0.0
        
        # Major match
        if user_profile.get("major") == scholarship.get("major_requirement"):
            score += 30.0
        
        # GPA requirement
        user_gpa = user_profile.get("gpa", 0.0)
        required_gpa = scholarship.get("min_gpa", 0.0)
        if user_gpa >= required_gpa:
            score += 25.0
        
        # Year match
        if str(user_profile.get("graduation_year")) in scholarship.get("eligible_years", []):
            score += 20.0
        
        # Interest/skills alignment (simplified)
        user_interests = set(user_profile.get("interests", []))
        scholarship_tags = set(scholarship.get("tags", []))
        overlap = len(user_interests.intersection(scholarship_tags))
        score += min(25.0, overlap * 5.0)
        
        return min(100.0, score)
    
    def _generate_match_reasons(self, user_profile: Dict, scholarship: Dict) -> List[str]:
        """
        Generate human-readable match reasons
        """
        reasons = []
        
        if user_profile.get("major") == scholarship.get("major_requirement"):
            reasons.append(f"Your major ({user_profile['major']}) matches the requirement")
        
        if user_profile.get("gpa", 0) >= scholarship.get("min_gpa", 0):
            reasons.append(f"Your GPA meets the {scholarship.get('min_gpa')} minimum")
        
        return reasons
    
    def predict_user_success(self, user_id: int, user_data: Dict) -> Dict[str, Any]:
        """
        Predict student success metrics using AI
        """
        # Simplified prediction model (in production, use trained ML model)
        factors = []
        score = 50.0  # Base score
        
        # GPA factor
        gpa = user_data.get("gpa", 0.0)
        if gpa >= 3.5:
            score += 20.0
            factors.append("Strong GPA")
        elif gpa >= 3.0:
            score += 10.0
        
        # Engagement factor
        posts_count = user_data.get("posts_count", 0)
        if posts_count > 20:
            score += 15.0
            factors.append("High engagement")
        elif posts_count > 5:
            score += 8.0
        
        # Network factor
        connections = user_data.get("connections_count", 0)
        if connections > 50:
            score += 15.0
            factors.append("Strong network")
        elif connections > 20:
            score += 8.0
        
        score = min(100.0, score)
        confidence = 0.75  # Simplified confidence score
        
        # Save prediction
        prediction = UserPrediction(
            user_id=user_id,
            prediction_type="success_score",
            score=score,
            confidence=confidence,
            factors={"factors": factors}
        )
        db.session.add(prediction)
        db.session.commit()
        
        return {
            "success_score": score,
            "confidence": confidence,
            "factors": factors
        }
    
    def auto_tag_content(self, content: str, resource_type: str, resource_id: int) -> List[str]:
        """
        Auto-generate tags for content using AI
        """
        prompt = f"Generate 5-7 relevant tags for the following {resource_type}:\n\n{content[:500]}"
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a content tagging expert. Generate only comma-separated tags, no explanation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            
            tags_text = response.choices[0].message.content
            tags = [tag.strip() for tag in tags_text.split(",")]
            
            # Save tags to database
            for tag in tags[:7]:  # Limit to 7 tags
                auto_tag = AutomatedTag(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    tag=tag,
                    confidence=0.85
                )
                db.session.add(auto_tag)
            
            db.session.commit()
            return tags
            
        except Exception as e:
            logger.error(f"Auto-tagging error: {e}")
            return []
    
    def _get_conversation_history(self, user_id: int, session_id: str, limit: int = 10):
        """
        Retrieve recent conversation history
        """
        return AIConversation.query.filter_by(
            user_id=user_id,
            session_id=session_id
        ).order_by(AIConversation.timestamp.desc()).limit(limit).all()
    
    def _get_system_prompt(self) -> str:
        """
        System prompt for GorillaGPT
        """
        return """You are GorillaGPT, the friendly AI assistant for PittState-Connect at Pittsburg State University.
        
        You help students, faculty, and alumni with:
        - Finding scholarships and career opportunities
        - Academic advice and course planning
        - Campus resources and events
        - Networking and mentorship connections
        - General university information
        
        Be helpful, encouraging, and specific to PSU. Use the Gorilla mascot spirit! 🦍
        Keep responses concise and actionable."""


# Singleton instance
_ai_service_instance = None

def get_ai_service(api_key: str = None, model: str = "gpt-4o-mini"):
    """Get or create AI service singleton"""
    global _ai_service_instance
    if _ai_service_instance is None and api_key:
        _ai_service_instance = AIService(api_key, model)
    return _ai_service_instance
