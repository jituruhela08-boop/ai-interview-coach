"""
services/gemini_service.py — Google Gemini AI Service
Handles resume analysis, interview Q&A generation, feedback, and roadmap creation.
"""

import json
import importlib
import logging
import re
import os
from typing import Dict, List, Optional, Tuple, Any

try:
    genai = importlib.import_module("google.generativeai")
except ImportError:
    genai = None

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Wraps the Google Generative AI SDK.
    All methods return structured Python dicts / lists.
    Falls back gracefully if the API key is missing.
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.model = None
        self._configured = False
        if self.api_key:
            self._configure()

    def _configure(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL)
            self._configured = True
            logger.info("Gemini configured with model %s", GEMINI_MODEL)
        except Exception as e:
            logger.error("Gemini configuration failed: %s", e)
            self._configured = False

    def set_api_key(self, key: str):
        self.api_key = key
        self._configure()

    @property
    def is_ready(self) -> bool:
        return self._configured and self.model is not None

    # ─────────────────────────────────────────
    #  INTERNAL HELPER
    # ─────────────────────────────────────────
    def _call(self, prompt: str, json_mode: bool = False) -> str:
        if not self.is_ready:
            raise RuntimeError(
                "Gemini API key not configured. Please add your key in Settings."
            )
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if json_mode:
                # Strip markdown fences if present
                text = re.sub(r"^```(?:json)?\s*", "", text)
                text = re.sub(r"\s*```$", "", text)
            return text
        except Exception as e:
            logger.error("Gemini API call failed: %s", e)
            raise

    def _parse_json(self, text: str, fallback: Any = None) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract first JSON object/array
            match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            logger.warning("JSON parse failed; returning fallback")
            return fallback

    # ─────────────────────────────────────────
    #  RESUME ANALYSIS
    # ─────────────────────────────────────────
    def analyze_resume(self, resume_text: str,
                       target_role: str = "Software Engineer") -> Dict:
        """
        Returns:
          ats_score       : 0-100
          skills_found    : list[str]
          missing_skills  : list[str]
          suggestions     : list[str]
          gemini_review   : str (paragraph)
          strengths       : list[str]
          weaknesses      : list[str]
        """
        prompt = f"""
You are an expert ATS (Applicant Tracking System) and career coach AI.

Analyze the following resume for the target role: **{target_role}**

Resume text:
---
{resume_text[:6000]}
---

Return a JSON object with EXACTLY these keys:
{{
  "ats_score": <integer 0-100>,
  "skills_found": [<list of detected technical and soft skills>],
  "missing_skills": [<list of important skills missing for {target_role}>],
  "suggestions": [<list of 5 specific, actionable resume improvement suggestions>],
  "strengths": [<list of 3-4 resume strengths>],
  "weaknesses": [<list of 3-4 resume weaknesses>],
  "gemini_review": "<2-3 sentence professional review paragraph>"
}}

Rules:
- ats_score must reflect real ATS compatibility (keyword density, formatting, sections)
- skills_found should extract actual skills mentioned in the resume
- missing_skills should list skills typically required for {target_role}
- suggestions must be concrete and actionable
- Return ONLY valid JSON, no markdown
"""
        raw = self._call(prompt, json_mode=True)
        result = self._parse_json(raw, fallback={})
        # Validate and normalise
        return {
            "ats_score":      float(result.get("ats_score", 50)),
            "skills_found":   result.get("skills_found", []),
            "missing_skills": result.get("missing_skills", []),
            "suggestions":    result.get("suggestions", []),
            "strengths":      result.get("strengths", []),
            "weaknesses":     result.get("weaknesses", []),
            "gemini_review":  result.get("gemini_review", "Resume reviewed."),
        }

    # ─────────────────────────────────────────
    #  INTERVIEW QUESTION GENERATION
    # ─────────────────────────────────────────
    def generate_questions(self, mode: str, domain: str,
                           difficulty: str, count: int = 5,
                           resume_context: str = "") -> List[Dict]:
        """
        Returns a list of {question, type, hint} dicts.
        """
        resume_hint = (
            f"\nContext from candidate's resume: {resume_context[:1500]}"
            if resume_context else ""
        )
        prompt = f"""
You are a senior {domain} interviewer conducting a {mode} interview.
Difficulty: {difficulty}.{resume_hint}

Generate exactly {count} interview questions.
Return a JSON array where each element has:
{{
  "question": "<full interview question>",
  "type": "<Technical|Behavioral|Situational|Problem-Solving>",
  "hint": "<what a strong answer should cover — 1 sentence>"
}}

Rules:
- Questions must be relevant to {domain} at {difficulty} level
- For Technical: include coding concepts, design, architecture
- For HR/Behavioral: use STAR-method prompts
- For Mixed: alternate between technical and behavioral
- Questions should be challenging but fair
- Return ONLY a valid JSON array
"""
        raw = self._call(prompt, json_mode=True)
        result = self._parse_json(raw, fallback=[])
        if not isinstance(result, list):
            result = []
        # Normalise
        questions = []
        for i, q in enumerate(result[:count]):
            questions.append({
                "question": q.get("question", f"Question {i+1}"),
                "type":     q.get("type", "Technical"),
                "hint":     q.get("hint", ""),
            })
        return questions

    # ─────────────────────────────────────────
    #  ANSWER EVALUATION
    # ─────────────────────────────────────────
    def evaluate_answer(self, question: str, answer: str,
                        domain: str, difficulty: str) -> Dict:
        """
        Returns:
          score         : 0-100
          feedback      : str
          strengths     : list[str]
          improvements  : list[str]
          follow_up     : str
          confidence    : 0-100
        """
        if not answer.strip():
            return {
                "score": 0, "confidence": 0,
                "feedback": "No answer provided.",
                "strengths": [],
                "improvements": ["Please provide a detailed answer."],
                "follow_up": "Could you attempt to answer the question?",
            }

        prompt = f"""
You are a senior {domain} interviewer evaluating a candidate's answer.
Difficulty: {difficulty}

Question: {question}
Candidate's Answer: {answer}

Evaluate the answer and return a JSON object:
{{
  "score": <integer 0-100>,
  "confidence": <integer 0-100 based on certainty and articulation>,
  "feedback": "<2-3 sentence constructive feedback>",
  "strengths": [<list of 2-3 things the candidate did well>],
  "improvements": [<list of 2-3 specific areas to improve>],
  "follow_up": "<one relevant follow-up question to probe deeper>"
}}

Scoring rubric:
- 90-100: Exceptional — deep knowledge, clear examples, correct
- 70-89:  Good — mostly correct, decent depth
- 50-69:  Average — partial understanding, some gaps
- 30-49:  Below average — significant gaps
- 0-29:   Poor — incorrect or no relevant content

Return ONLY valid JSON.
"""
        raw = self._call(prompt, json_mode=True)
        result = self._parse_json(raw, fallback={})
        return {
            "score":        float(result.get("score", 50)),
            "confidence":   float(result.get("confidence", 50)),
            "feedback":     result.get("feedback", "Answer evaluated."),
            "strengths":    result.get("strengths", []),
            "improvements": result.get("improvements", []),
            "follow_up":    result.get("follow_up", ""),
        }

    # ─────────────────────────────────────────
    #  LEARNING ROADMAP
    # ─────────────────────────────────────────
    def generate_roadmap(self, weak_skills: List[str],
                         target_role: str,
                         experience_level: str = "Mid-level") -> List[Dict]:
        """
        Returns a list of roadmap items with learning resources.
        """
        if not weak_skills:
            weak_skills = ["System Design", "Data Structures", "Algorithms"]

        prompt = f"""
You are a senior tech career coach building a personalized learning roadmap.

Target Role: {target_role}
Experience Level: {experience_level}
Weak Skills to Address: {', '.join(weak_skills[:10])}

Generate a learning roadmap with 10-15 items. Return a JSON array:
[
  {{
    "skill": "<skill name>",
    "resource_title": "<specific book/course/resource name>",
    "resource_url": "<real URL if known, else empty string>",
    "resource_type": "<Article|Video|Course|Practice|Book>",
    "priority": "<High|Medium|Low>",
    "ai_notes": "<1-2 sentence explanation of why this helps and how to use it>"
  }}
]

Rules:
- Cover all weak skills mentioned
- Mix resource types (courses, practice problems, articles)
- Prioritize High for skills critical to the target role
- Suggest real, well-known platforms (Coursera, LeetCode, docs, YouTube, etc.)
- Return ONLY valid JSON array
"""
        raw = self._call(prompt, json_mode=True)
        result = self._parse_json(raw, fallback=[])
        if not isinstance(result, list):
            result = []
        return [
            {
                "skill":          item.get("skill", ""),
                "resource_title": item.get("resource_title", ""),
                "resource_url":   item.get("resource_url", ""),
                "resource_type":  item.get("resource_type", "Article"),
                "priority":       item.get("priority", "Medium"),
                "ai_notes":       item.get("ai_notes", ""),
            }
            for item in result
        ]

    # ─────────────────────────────────────────
    #  SKILL PROFICIENCY ESTIMATION
    # ─────────────────────────────────────────
    def estimate_skill_proficiency(self, skills: List[str],
                                   interview_history: List[Dict]) -> Dict[str, float]:
        """
        Returns {skill: proficiency_0_100} based on resume + interview performance.
        """
        history_summary = ""
        if interview_history:
            scores = [i.get("avg_score", 0) for i in interview_history[-5:]]
            history_summary = f"Recent interview scores: {scores}"

        if not skills:
            skills = ["Python", "SQL", "Communication", "Problem Solving"]

        prompt = f"""
Based on the following context, estimate proficiency levels for each skill.

Skills to evaluate: {', '.join(skills[:15])}
{history_summary}

Return a JSON object mapping each skill to a proficiency percentage (0-100):
{{
  "SkillName": <integer 0-100>,
  ...
}}

Base estimates on:
- Whether the skill appears prominently vs. briefly in resume
- Interview performance trends
- Typical skill combinations
- Industry benchmarks

Return ONLY valid JSON object.
"""
        raw = self._call(prompt, json_mode=True)
        result = self._parse_json(raw, fallback={})
        if not isinstance(result, dict):
            result = {}
        # Ensure all skills have a value
        return {s: float(result.get(s, 50)) for s in skills}

    # ─────────────────────────────────────────
    #  INTERVIEW SUMMARY REPORT
    # ─────────────────────────────────────────
    def generate_interview_summary(self, interview: Dict,
                                   questions: List[Dict]) -> str:
        """Returns a multi-paragraph narrative report."""
        q_text = "\n".join(
            f"Q{i+1}: {q['question_text']}\n"
            f"Answer: {q.get('user_answer','')[:300]}\n"
            f"Score: {q.get('score',0)}/100\n"
            for i, q in enumerate(questions)
        )
        prompt = f"""
You are an expert interview coach. Write a professional interview performance report.

Interview Details:
- Mode: {interview.get('mode','')}
- Domain: {interview.get('domain','')}
- Difficulty: {interview.get('difficulty','')}
- Average Score: {interview.get('avg_score',0)}/100
- Confidence Score: {interview.get('confidence_score',0)}/100

Questions & Answers:
{q_text[:4000]}

Write a 4-paragraph professional report covering:
1. Overall performance summary
2. Key strengths demonstrated
3. Areas needing improvement
4. Specific next steps and recommendations

Write in a professional, encouraging tone. Be specific and actionable.
"""
        return self._call(prompt)


# ─────────────────────────────────────────────
#  Module-level singleton
# ─────────────────────────────────────────────
_service_instance: Optional[GeminiService] = None

def get_gemini() -> GeminiService:
    global _service_instance
    if _service_instance is None:
        _service_instance = GeminiService()
    return _service_instance