"""
services/gemini_service.py
Google Gemini AI integration for AI Interview Coach
"""
import logging
from config import GEMINI_API_KEY, GEMINI_MODEL

log = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            return None
        try:
            import google.generativeai as genai
            # Note: google.generativeai is imported lazily inside _get_client()
            # to avoid hard dependency at module import time.
            genai.configure(api_key=GEMINI_API_KEY)
            _client = genai.GenerativeModel(GEMINI_MODEL)
            log.info("Gemini client initialised")
        except Exception as e:
            log.error("Gemini init error: %s", e)
            _client = None
    return _client


def _fallback(prompt_type: str, **kwargs) -> str:
    """Offline fallback responses when no API key is set."""
    if prompt_type == "interview_question":
        domain = kwargs.get("domain", "Software Engineering")
        difficulty = kwargs.get("difficulty", "Mid-level")
        questions = {
            "Python": [
                "Explain the difference between a list and a tuple in Python. When would you use each?",
                "What are Python decorators and how do they work internally?",
                "Describe the GIL (Global Interpreter Lock) and its impact on multithreading.",
                "How does Python manage memory? Explain garbage collection.",
                "What is the difference between *args and **kwargs?",
            ],
            "Machine Learning": [
                "Explain the bias-variance tradeoff.",
                "What is overfitting and how do you prevent it?",
                "Describe the difference between supervised and unsupervised learning.",
                "What is gradient descent and its variants?",
                "Explain how a neural network learns using backpropagation.",
            ],
        }
        domain_key = domain.split("/")[0].strip()
        pool = questions.get(domain_key, [
            f"Describe your experience with {domain}.",
            f"What are the best practices in {domain}?",
            f"How would you architect a scalable system using {domain}?",
            "Tell me about a challenging technical problem you solved.",
            "How do you stay updated with the latest trends in your field?",
        ])
        import random
        return random.choice(pool)

    elif prompt_type == "evaluate_answer":
        return (
            "**Score: 7/10**\n\n"
            "**Strengths:**\n• Clear explanation of core concepts\n• Good use of examples\n\n"
            "**Areas for Improvement:**\n• Could go deeper on edge cases\n• Consider mentioning real-world applications\n\n"
            "**Suggested Answer:**\nA strong answer would also cover performance implications "
            "and mention specific tools or frameworks you've used in practice."
        )

    elif prompt_type == "ats_analysis":
        return (
            "**ATS Analysis Complete**\n\n"
            "Your resume demonstrates solid technical skills. "
            "Consider adding more quantified achievements (e.g., 'reduced load time by 40%'). "
            "The formatting is ATS-friendly. Key missing keywords: Docker, Kubernetes, CI/CD pipelines."
        )

    elif prompt_type == "roadmap":
        domain = kwargs.get("domain", "Software Engineering")
        return (
            f"**{domain} Learning Roadmap**\n\n"
            "**Phase 1 — Foundations (0–3 months):**\n"
            "• Master core language syntax and idioms\n• Build 3 small projects\n• Study data structures & algorithms\n\n"
            "**Phase 2 — Intermediate (3–6 months):**\n"
            "• Learn frameworks and libraries\n• Contribute to open source\n• Build a portfolio project\n\n"
            "**Phase 3 — Advanced (6–12 months):**\n"
            "• System design patterns\n• Cloud deployment\n• Performance optimisation\n\n"
            "**Resources:** Official docs, LeetCode, System Design Primer, GitHub projects"
        )
    return "AI response not available. Please configure your Gemini API key in Settings."


def generate_interview_question(domain: str, difficulty: str, mode: str,
                                 previous_questions: list = None) -> str:
    client = _get_client()
    if not client:
        return _fallback("interview_question", domain=domain, difficulty=difficulty)

    prev = "\n".join(previous_questions[-5:]) if previous_questions else "None"
    prompt = f"""You are an expert technical interviewer. Generate a single, challenging interview question.

Domain: {domain}
Difficulty: {difficulty}
Interview Mode: {mode}
Previously Asked (avoid repeating): {prev}

Rules:
- Return ONLY the question, no preamble
- Make it specific and thought-provoking
- For Technical mode: focus on concepts, coding, system design
- For HR/Behavioral: use STAR format scenarios
- Difficulty {difficulty}: {"entry-level concepts" if "Junior" in difficulty else "advanced architecture and trade-offs"}
"""
    try:
        resp = client.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        log.error("Gemini question error: %s", e)
        return _fallback("interview_question", domain=domain, difficulty=difficulty)


def evaluate_answer(question: str, answer: str, domain: str, difficulty: str) -> str:
    client = _get_client()
    if not client:
        return _fallback("evaluate_answer")

    prompt = f"""You are an expert interviewer evaluating a candidate's answer.

Question: {question}
Candidate's Answer: {answer}
Domain: {domain} | Difficulty: {difficulty}

Provide a structured evaluation with:
1. Score: X/10
2. Strengths (bullet points)
3. Areas for Improvement (bullet points)
4. Model Answer / Key Points Missed
5. Final Verdict: Pass / Needs Work / Fail

Be specific, constructive, and professional."""
    try:
        resp = client.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        log.error("Gemini eval error: %s", e)
        return _fallback("evaluate_answer")


def analyze_resume(resume_text: str, job_description: str = "") -> dict:
    client = _get_client()
    if not client:
        return {
            "summary": _fallback("ats_analysis"),
            "ats_score": 72.0,
            "skills": ["Python", "SQL", "Git", "AWS"],
            "missing": ["Docker", "Kubernetes", "CI/CD"],
            "suggestions": "Add quantified achievements. Include a skills section with keywords.",
        }

    prompt = f"""Analyze this resume for ATS compatibility and provide structured feedback.

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION (if provided):
{job_description[:1000] if job_description else "General software engineering role"}

Return a JSON object with these exact keys:
{{
  "ats_score": <number 0-100>,
  "skills_found": ["skill1", "skill2", ...],
  "missing_skills": ["skill1", "skill2", ...],
  "strengths": ["point1", "point2", ...],
  "weaknesses": ["point1", "point2", ...],
  "suggestions": "Detailed paragraph of improvement suggestions",
  "keyword_density": <number 0-100>,
  "format_score": <number 0-100>,
  "experience_score": <number 0-100>
}}
Return ONLY valid JSON, no markdown."""
    try:
        import json
        resp = client.generate_content(prompt)
        text = resp.text.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        log.error("Gemini resume error: %s", e)
        return {
            "ats_score": 70.0,
            "skills_found": ["Python", "SQL"],
            "missing_skills": ["Docker", "Kubernetes"],
            "strengths": ["Clear formatting"],
            "weaknesses": ["Missing keywords"],
            "suggestions": "Add more technical keywords relevant to the target role.",
            "keyword_density": 60,
            "format_score": 75,
            "experience_score": 68,
        }


def generate_roadmap(domain: str, current_level: str, target_role: str) -> str:
    client = _get_client()
    if not client:
        return _fallback("roadmap", domain=domain)

    prompt = f"""Create a detailed, actionable career learning roadmap.

Domain: {domain}
Current Level: {current_level}
Target Role: {target_role}

Structure the roadmap with:
1. Phase 1 - Foundations (timeframe)
2. Phase 2 - Core Skills (timeframe)
3. Phase 3 - Advanced Topics (timeframe)
4. Phase 4 - Job Ready (timeframe)

For each phase include:
- Key topics to master
- Recommended resources (free & paid)
- Practical projects to build
- Milestones to achieve

Make it specific, realistic, and motivating."""
    try:
        resp = client.generate_content(prompt)
        return resp.text.strip()
    except Exception as e:
        log.error("Gemini roadmap error: %s", e)
        return _fallback("roadmap", domain=domain)