"""
Skills Assessment Service
LeetCode-style coding assessment platform with:
- Docker sandbox for safe code execution
- Automated test case grading
- Skill badges and certificates
- Employer-custom assessments
- Multiple programming languages
- Time limits and anti-cheat
- Difficulty levels (Easy/Medium/Hard)
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, desc
from extensions import db
from models import User, UserSkill
import logging
from typing import Dict, List, Optional, Any, Tuple
import json
import subprocess
import tempfile
import os
import time
import hashlib
import re

logger = logging.getLogger(__name__)


class SkillsAssessmentService:
    """
    Service for creating and grading coding assessments
    """
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        'python': {
            'extension': '.py',
            'docker_image': 'python:3.11-alpine',
            'run_command': 'python {filename}',
            'timeout': 10
        },
        'javascript': {
            'extension': '.js',
            'docker_image': 'node:18-alpine',
            'run_command': 'node {filename}',
            'timeout': 10
        },
        'java': {
            'extension': '.java',
            'docker_image': 'openjdk:17-alpine',
            'compile_command': 'javac {filename}',
            'run_command': 'java {classname}',
            'timeout': 15
        },
        'cpp': {
            'extension': '.cpp',
            'docker_image': 'gcc:latest',
            'compile_command': 'g++ -o {output} {filename}',
            'run_command': './{output}',
            'timeout': 15
        },
        'go': {
            'extension': '.go',
            'docker_image': 'golang:1.21-alpine',
            'run_command': 'go run {filename}',
            'timeout': 10
        }
    }
    
    # Difficulty levels with point values
    DIFFICULTY_LEVELS = {
        'easy': {'points': 10, 'time_limit_minutes': 30},
        'medium': {'points': 25, 'time_limit_minutes': 45},
        'hard': {'points': 50, 'time_limit_minutes': 60}
    }
    
    # Skill categories
    SKILL_CATEGORIES = [
        'Algorithms', 'Data Structures', 'System Design',
        'Database', 'Web Development', 'Mobile Development',
        'Machine Learning', 'DevOps', 'Security'
    ]
    
    @staticmethod
    def create_assessment(
        title: str,
        description: str,
        difficulty: str,
        category: str,
        language: str,
        test_cases: List[Dict],
        starter_code: str = None,
        created_by_user_id: int = None,
        employer_id: int = None,
        is_custom: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new coding assessment
        
        Args:
            title: Assessment title
            description: Problem description
            difficulty: easy/medium/hard
            category: Skill category
            language: Programming language
            test_cases: List of test cases with input/expected output
            starter_code: Optional starter code template
            created_by_user_id: Admin user creating assessment
            employer_id: Employer ID if custom assessment
            is_custom: Whether this is employer-custom assessment
            
        Returns:
            Dictionary with created assessment details
        """
        try:
            if difficulty not in SkillsAssessmentService.DIFFICULTY_LEVELS:
                return {'success': False, 'error': 'Invalid difficulty level'}
            
            if language not in SkillsAssessmentService.SUPPORTED_LANGUAGES:
                return {'success': False, 'error': f'Language {language} not supported'}
            
            # Create assessment record (simplified - would use a proper Assessment model)
            assessment_data = {
                'id': hashlib.md5(f"{title}{datetime.utcnow()}".encode()).hexdigest()[:16],
                'title': title,
                'description': description,
                'difficulty': difficulty,
                'category': category,
                'language': language,
                'test_cases': test_cases,
                'starter_code': starter_code or SkillsAssessmentService._generate_starter_code(language),
                'points': SkillsAssessmentService.DIFFICULTY_LEVELS[difficulty]['points'],
                'time_limit_minutes': SkillsAssessmentService.DIFFICULTY_LEVELS[difficulty]['time_limit_minutes'],
                'created_by': created_by_user_id,
                'employer_id': employer_id,
                'is_custom': is_custom,
                'created_at': datetime.utcnow().isoformat(),
                'total_attempts': 0,
                'success_rate': 0.0
            }
            
            # In production, this would be saved to database
            # For now, we'll return the structure
            
            logger.info(f"Created assessment: {title} ({difficulty}) for {language}")
            
            return {
                'success': True,
                'assessment': assessment_data,
                'message': 'Assessment created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating assessment: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _generate_starter_code(language: str) -> str:
        """
        Generate starter code template for a language
        """
        templates = {
            'python': '''def solution():
    """
    Your solution here
    """
    pass

if __name__ == "__main__":
    result = solution()
    print(result)
''',
            'javascript': '''function solution() {
    // Your solution here
}

console.log(solution());
''',
            'java': '''public class Solution {
    public static void main(String[] args) {
        // Your solution here
        System.out.println(solution());
    }
    
    public static Object solution() {
        // Your code here
        return null;
    }
}
''',
            'cpp': '''#include <iostream>
using namespace std;

int solution() {
    // Your solution here
    return 0;
}

int main() {
    cout << solution() << endl;
    return 0;
}
''',
            'go': '''package main

import "fmt"

func solution() interface{} {
    // Your solution here
    return nil
}

func main() {
    fmt.Println(solution())
}
'''
        }
        return templates.get(language, '// Starter code not available')
    
    @staticmethod
    def execute_code(
        code: str,
        language: str,
        test_input: str = "",
        timeout: int = None
    ) -> Dict[str, Any]:
        """
        Execute code in Docker sandbox with test input
        
        Args:
            code: User's code to execute
            language: Programming language
            test_input: Input to provide to the code
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        try:
            if language not in SkillsAssessmentService.SUPPORTED_LANGUAGES:
                return {'success': False, 'error': f'Language {language} not supported'}
            
            lang_config = SkillsAssessmentService.SUPPORTED_LANGUAGES[language]
            timeout = timeout or lang_config['timeout']
            
            # Security checks
            security_check = SkillsAssessmentService._security_check(code, language)
            if not security_check['safe']:
                return {
                    'success': False,
                    'error': 'Security violation detected',
                    'details': security_check['reason']
                }
            
            # Create temporary directory for code execution
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write code to file
                filename = f"solution{lang_config['extension']}"
                filepath = os.path.join(temp_dir, filename)
                
                with open(filepath, 'w') as f:
                    f.write(code)
                
                # Prepare Docker command
                docker_cmd = [
                    'docker', 'run',
                    '--rm',
                    '--network', 'none',  # No network access
                    '--memory', '256m',  # Memory limit
                    '--cpus', '1',  # CPU limit
                    '--pids-limit', '50',  # Process limit
                    '-v', f'{temp_dir}:/workspace',
                    '-w', '/workspace',
                    lang_config['docker_image']
                ]
                
                # Compile if needed
                if 'compile_command' in lang_config:
                    compile_cmd = lang_config['compile_command'].format(
                        filename=filename,
                        output='solution.out',
                        classname='Solution'
                    )
                    full_compile_cmd = docker_cmd + compile_cmd.split()
                    
                    try:
                        compile_result = subprocess.run(
                            full_compile_cmd,
                            capture_output=True,
                            text=True,
                            timeout=timeout
                        )
                        
                        if compile_result.returncode != 0:
                            return {
                                'success': False,
                                'error': 'Compilation failed',
                                'stderr': compile_result.stderr,
                                'stdout': compile_result.stdout
                            }
                    except subprocess.TimeoutExpired:
                        return {
                            'success': False,
                            'error': 'Compilation timeout',
                            'timeout_seconds': timeout
                        }
                
                # Run the code
                run_cmd = lang_config['run_command'].format(
                    filename=filename,
                    output='solution.out',
                    classname='Solution'
                )
                full_run_cmd = docker_cmd + run_cmd.split()
                
                start_time = time.time()
                
                try:
                    result = subprocess.run(
                        full_run_cmd,
                        input=test_input,
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
                    
                    execution_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'stdout': result.stdout.strip(),
                        'stderr': result.stderr.strip(),
                        'return_code': result.returncode,
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'timeout_seconds': timeout
                    }
                    
                except subprocess.TimeoutExpired:
                    return {
                        'success': False,
                        'error': 'Execution timeout',
                        'timeout_seconds': timeout
                    }
                
        except Exception as e:
            logger.error(f"Error executing code: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _security_check(code: str, language: str) -> Dict[str, Any]:
        """
        Perform security checks on submitted code
        """
        # Dangerous patterns to detect
        dangerous_patterns = {
            'python': [
                r'import\s+os', r'import\s+sys', r'import\s+subprocess',
                r'__import__', r'eval\(', r'exec\(', r'compile\(',
                r'open\(', r'file\(', r'input\('
            ],
            'javascript': [
                r'require\(', r'import\s+', r'eval\(', r'Function\(',
                r'child_process', r'fs\.', r'process\.'
            ],
            'java': [
                r'Runtime\.', r'ProcessBuilder', r'System\.exit',
                r'File\(', r'FileReader', r'FileWriter'
            ],
            'cpp': [
                r'system\(', r'exec\(', r'fopen\(', r'popen\('
            ],
            'go': [
                r'os\.', r'exec\.', r'syscall\.'
            ]
        }
        
        patterns = dangerous_patterns.get(language, [])
        
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return {
                    'safe': False,
                    'reason': f'Potentially dangerous code detected: {pattern}'
                }
        
        # Check code length (prevent abuse)
        if len(code) > 50000:  # 50KB max
            return {
                'safe': False,
                'reason': 'Code exceeds maximum length'
            }
        
        return {'safe': True}
    
    @staticmethod
    def grade_submission(
        user_id: int,
        assessment_id: str,
        code: str,
        language: str,
        test_cases: List[Dict]
    ) -> Dict[str, Any]:
        """
        Grade a user's code submission against test cases
        
        Args:
            user_id: ID of the user
            assessment_id: ID of the assessment
            code: User's submitted code
            language: Programming language
            test_cases: List of test cases to run
            
        Returns:
            Dictionary with grading results
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Track results
            results = []
            passed_count = 0
            total_count = len(test_cases)
            total_execution_time = 0
            
            for i, test_case in enumerate(test_cases):
                test_input = test_case.get('input', '')
                expected_output = test_case.get('expected_output', '').strip()
                is_hidden = test_case.get('hidden', False)
                
                # Execute code with this test case
                execution = SkillsAssessmentService.execute_code(
                    code=code,
                    language=language,
                    test_input=test_input
                )
                
                if not execution.get('success'):
                    results.append({
                        'test_case': i + 1,
                        'passed': False,
                        'error': execution.get('error'),
                        'hidden': is_hidden,
                        'input': test_input if not is_hidden else 'Hidden',
                        'expected': expected_output if not is_hidden else 'Hidden',
                        'actual': None
                    })
                    continue
                
                actual_output = execution.get('stdout', '').strip()
                passed = actual_output == expected_output
                
                if passed:
                    passed_count += 1
                
                total_execution_time += execution.get('execution_time_ms', 0)
                
                results.append({
                    'test_case': i + 1,
                    'passed': passed,
                    'execution_time_ms': execution.get('execution_time_ms'),
                    'hidden': is_hidden,
                    'input': test_input if not is_hidden else 'Hidden',
                    'expected': expected_output if not is_hidden else 'Hidden',
                    'actual': actual_output if not is_hidden else ('Correct' if passed else 'Incorrect'),
                    'stderr': execution.get('stderr') if execution.get('stderr') else None
                })
            
            # Calculate score
            score_percentage = (passed_count / total_count * 100) if total_count > 0 else 0
            all_passed = passed_count == total_count
            
            # Create submission record
            submission_data = {
                'id': hashlib.md5(f"{user_id}{assessment_id}{datetime.utcnow()}".encode()).hexdigest()[:16],
                'user_id': user_id,
                'assessment_id': assessment_id,
                'code': code,
                'language': language,
                'passed': all_passed,
                'score_percentage': score_percentage,
                'test_cases_passed': passed_count,
                'test_cases_total': total_count,
                'total_execution_time_ms': total_execution_time,
                'submitted_at': datetime.utcnow().isoformat(),
                'results': results
            }
            
            # Award points and badges if all tests passed
            if all_passed:
                SkillsAssessmentService._award_achievement(
                    user_id=user_id,
                    assessment_id=assessment_id,
                    assessment_title='Sample Assessment',  # Would fetch from DB
                    difficulty='medium',  # Would fetch from DB
                    category='Algorithms'  # Would fetch from DB
                )
            
            logger.info(f"Graded submission for user {user_id}: {passed_count}/{total_count} tests passed")
            
            return {
                'success': True,
                'submission': submission_data,
                'all_tests_passed': all_passed,
                'score_percentage': round(score_percentage, 1),
                'tests_passed': passed_count,
                'tests_total': total_count,
                'execution_time_ms': round(total_execution_time, 2),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error grading submission: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _award_achievement(
        user_id: int,
        assessment_id: str,
        assessment_title: str,
        difficulty: str,
        category: str
    ) -> None:
        """
        Award badges and points to user for completing assessment
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return
            
            # Award points
            points = SkillsAssessmentService.DIFFICULTY_LEVELS[difficulty]['points']
            
            # Add skill badge (simplified)
            badge_data = {
                'user_id': user_id,
                'assessment_id': assessment_id,
                'title': f'{assessment_title} Master',
                'difficulty': difficulty,
                'category': category,
                'points': points,
                'earned_at': datetime.utcnow().isoformat(),
                'badge_type': 'assessment_completion'
            }
            
            # In production, save to UserBadge table
            logger.info(f"Awarded {points} points and badge to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error awarding achievement: {str(e)}")
    
    @staticmethod
    def get_user_progress(user_id: int) -> Dict[str, Any]:
        """
        Get user's assessment progress and statistics
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with progress data
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # In production, query from database
            # For now, return structure
            progress_data = {
                'total_assessments_attempted': 15,
                'total_assessments_passed': 12,
                'success_rate': 80.0,
                'total_points_earned': 385,
                'badges_earned': 12,
                'skill_level': 'Intermediate',
                'languages_mastered': ['Python', 'JavaScript'],
                'categories_completed': {
                    'Algorithms': {'attempted': 8, 'passed': 7},
                    'Data Structures': {'attempted': 5, 'passed': 4},
                    'Web Development': {'attempted': 2, 'passed': 1}
                },
                'difficulty_breakdown': {
                    'easy': {'attempted': 6, 'passed': 6, 'success_rate': 100.0},
                    'medium': {'attempted': 7, 'passed': 5, 'success_rate': 71.4},
                    'hard': {'attempted': 2, 'passed': 1, 'success_rate': 50.0}
                },
                'recent_submissions': [
                    {
                        'assessment_title': 'Two Sum Problem',
                        'difficulty': 'easy',
                        'passed': True,
                        'score': 100.0,
                        'submitted_at': '2025-11-01T14:30:00'
                    },
                    {
                        'assessment_title': 'Binary Tree Traversal',
                        'difficulty': 'medium',
                        'passed': True,
                        'score': 100.0,
                        'submitted_at': '2025-10-28T10:15:00'
                    }
                ],
                'leaderboard_rank': 42,
                'total_users': 500
            }
            
            logger.info(f"Retrieved progress for user {user_id}")
            
            return {
                'success': True,
                'user_id': user_id,
                'progress': progress_data
            }
            
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_leaderboard(
        category: str = None,
        time_period: str = 'all_time',
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get leaderboard rankings
        
        Args:
            category: Optional skill category filter
            time_period: all_time/monthly/weekly
            limit: Number of users to return
            
        Returns:
            Dictionary with leaderboard data
        """
        try:
            # In production, query from database with proper aggregations
            # For now, return structure
            
            leaderboard = []
            for i in range(1, min(limit + 1, 51)):
                leaderboard.append({
                    'rank': i,
                    'user_id': f'user_{i}',
                    'username': f'Student{i}',
                    'total_points': 1000 - (i * 15),
                    'assessments_passed': 50 - i,
                    'badges_earned': 25 - (i // 2),
                    'success_rate': 95.0 - (i * 0.5),
                    'skill_level': 'Expert' if i <= 10 else 'Advanced' if i <= 30 else 'Intermediate'
                })
            
            logger.info(f"Retrieved leaderboard: top {limit}")
            
            return {
                'success': True,
                'leaderboard': leaderboard,
                'category': category,
                'time_period': time_period,
                'total_participants': 500
            }
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_certificate(user_id: int, assessment_id: str) -> Dict[str, Any]:
        """
        Generate completion certificate for passed assessment
        
        Args:
            user_id: ID of the user
            assessment_id: ID of the assessment
            
        Returns:
            Dictionary with certificate details
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Generate certificate
            certificate_id = hashlib.md5(f"{user_id}{assessment_id}".encode()).hexdigest()
            
            certificate_data = {
                'certificate_id': certificate_id,
                'user_id': user_id,
                'user_name': user.full_name,
                'assessment_id': assessment_id,
                'assessment_title': 'Sample Assessment',  # Would fetch from DB
                'difficulty': 'medium',
                'category': 'Algorithms',
                'issued_at': datetime.utcnow().isoformat(),
                'verification_url': f'https://pittstate.edu/verify/{certificate_id}',
                'is_verified': True,
                'issuer': 'PittState Connect Skills Assessment Program'
            }
            
            logger.info(f"Generated certificate {certificate_id} for user {user_id}")
            
            return {
                'success': True,
                'certificate': certificate_data,
                'download_url': f'/api/certificates/{certificate_id}/download',
                'share_url': f'/api/certificates/{certificate_id}/share'
            }
            
        except Exception as e:
            logger.error(f"Error creating certificate: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_employer_assessment_analytics(employer_id: int, assessment_id: str) -> Dict[str, Any]:
        """
        Get analytics for employer-custom assessments
        
        Args:
            employer_id: ID of the employer
            assessment_id: ID of the custom assessment
            
        Returns:
            Dictionary with assessment analytics
        """
        try:
            # In production, aggregate from database
            analytics = {
                'assessment_id': assessment_id,
                'total_attempts': 45,
                'unique_candidates': 38,
                'average_score': 72.5,
                'pass_rate': 64.4,
                'average_completion_time_minutes': 28.5,
                'difficulty_rating': 'Medium',
                'score_distribution': {
                    '0-20': 3,
                    '21-40': 5,
                    '41-60': 8,
                    '61-80': 15,
                    '81-100': 14
                },
                'top_performers': [
                    {'user_id': 'u1', 'name': 'Alice Johnson', 'score': 100, 'time_minutes': 22},
                    {'user_id': 'u2', 'name': 'Bob Smith', 'score': 98, 'time_minutes': 25},
                    {'user_id': 'u3', 'name': 'Carol Davis', 'score': 95, 'time_minutes': 27}
                ],
                'common_mistakes': [
                    'Edge case handling (15 candidates)',
                    'Time complexity optimization (12 candidates)',
                    'Null pointer checks (8 candidates)'
                ]
            }
            
            logger.info(f"Retrieved analytics for assessment {assessment_id}")
            
            return {
                'success': True,
                'analytics': analytics,
                'employer_id': employer_id
            }
            
        except Exception as e:
            logger.error(f"Error getting employer analytics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def detect_plagiarism(code1: str, code2: str, language: str) -> Dict[str, Any]:
        """
        Detect code similarity between submissions (basic plagiarism check)
        
        Args:
            code1: First code sample
            code2: Second code sample
            language: Programming language
            
        Returns:
            Dictionary with similarity analysis
        """
        try:
            # Normalize code (remove comments, whitespace)
            normalized1 = SkillsAssessmentService._normalize_code(code1, language)
            normalized2 = SkillsAssessmentService._normalize_code(code2, language)
            
            # Calculate similarity using simple string comparison
            # In production, use more sophisticated algorithms (AST comparison, token-based)
            
            # Levenshtein distance approximation
            len1, len2 = len(normalized1), len(normalized2)
            max_len = max(len1, len2)
            
            if max_len == 0:
                similarity = 100.0
            else:
                # Simple character-level similarity
                matching_chars = sum(c1 == c2 for c1, c2 in zip(normalized1, normalized2))
                similarity = (matching_chars / max_len) * 100
            
            is_plagiarism = similarity > 85.0  # Threshold for flagging
            
            return {
                'success': True,
                'similarity_percentage': round(similarity, 2),
                'is_suspicious': is_plagiarism,
                'threshold': 85.0,
                'recommendation': 'Manual review recommended' if is_plagiarism else 'No plagiarism detected'
            }
            
        except Exception as e:
            logger.error(f"Error detecting plagiarism: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _normalize_code(code: str, language: str) -> str:
        """
        Normalize code for comparison
        """
        # Remove comments
        if language == 'python':
            code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
        elif language in ['javascript', 'java', 'cpp', 'go']:
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Remove whitespace and lowercase
        code = re.sub(r'\s+', '', code)
        code = code.lower()
        
        return code
