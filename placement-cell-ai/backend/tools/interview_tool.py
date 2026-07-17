import os
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage

from backend.utils.ai_utils import simple_tokens


def get_llm(temperature=0.7):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=temperature
    )


def _fallback_questions(question_type: str, num_questions: int, job_description: str) -> list[dict[str, Any]]:
    templates = {
        "hr": [
            "Tell me about yourself and why you are interested in this role.",
            "Describe a time you handled a conflict in a team.",
            "What is your biggest strength and how does it help you work with others?",
        ],
        "technical": [
            "Explain the core stack you used in your most important project.",
            "How would you design and debug a feature similar to one in this job description?",
            "What is one technical challenge you solved and how did you approach it?",
        ],
        "system_design": [
            "How would you design a scalable API for this product?",
            "What would you cache and why in a high-traffic system?",
            "How would you monitor and scale the service over time?",
        ],
        "project": [
            "Walk me through your strongest project end to end.",
            "What trade-offs did you make in that project?",
            "What would you improve if you rebuilt it today?",
        ],
    }
    base = templates.get(question_type, templates["technical"])
    focus = ", ".join(simple_tokens(job_description)[:5])
    questions: list[dict[str, Any]] = []
    for index in range(num_questions):
        question_text = base[index % len(base)]
        if focus:
            question_text = f"{question_text} (focus areas: {focus})"
        questions.append(
            {
                "question": question_text,
                "expected_answer": "A concise, specific answer with examples and measurable outcomes.",
                "difficulty": "easy" if index == 0 else "medium",
                "topic": question_type,
                "type": question_type,
                "follow_ups": ["Can you give a concrete example?", "What did you learn from it?"],
            }
        )
    return questions


@tool
def generate_interview_questions(
    student_profile: dict,
    job_description: str,
    question_type: str,
    num_questions: int = 5
) -> list[dict]:
    """Generate targeted interview questions based on type.
    question_type: 'hr' | 'technical' | 'system_design' | 'project'
    """
    llm = get_llm(temperature=0.7)
    if llm is None:
        return _fallback_questions(question_type, num_questions, job_description)
    
    type_prompt = ""
    if question_type == "hr":
        type_prompt = """Generate behavioral HR interview questions using the STAR method. Focus on teamwork, leadership, conflict resolution, and past experiences."""
    elif question_type == "technical":
        type_prompt = """Generate technical interview questions including coding concepts, framework-specific questions, and problem-solving tasks relevant to the job description."""
    elif question_type == "system_design":
        type_prompt = """Generate system design questions focused on architecture, scalability, and system design principles relevant to the job domain."""
    elif question_type == "project":
        type_prompt = """Generate deep-dive questions about the student's specific projects mentioned in their profile."""
    
    prompt_text = f"""{type_prompt}

Student Profile: {student_profile}
Job Description: {job_description}
Number of questions: {num_questions}

Return ONLY a valid JSON array of question objects with these fields:
{{
  "question": "the question text",
  "expected_answer": "what a good answer should include",
  "difficulty": "easy|medium|hard",
  "topic": "specific topic",
  "type": "{question_type}",
  "follow_ups": ["follow up question 1", "follow up question 2"]
}}

NO markdown backticks, NO extra text. Only valid JSON array!"""

    try:
        response = llm.invoke([HumanMessage(content=prompt_text)])
        cleaned_response = response.content.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        parser = JsonOutputParser()
        return parser.parse(cleaned_response)
    except Exception:
        return _fallback_questions(question_type, num_questions, job_description)


@tool
def evaluate_interview_answer(
    question: str,
    expected_answer: str,
    student_answer: str,
    question_type: str
) -> dict:
    """Evaluate a student's interview answer using Gemini AI."""
    llm = get_llm(temperature=0)
    if llm is None:
        question_tokens = set(simple_tokens(question + " " + expected_answer))
        answer_tokens = set(simple_tokens(student_answer))
        overlap = len(question_tokens & answer_tokens)
        score = min(10, max(1, overlap + 3))
        return {
            "score": score,
            "what_was_good": "The answer addresses the question at a basic level." if score >= 5 else "The answer shows some understanding but lacks detail.",
            "what_to_improve": "Add concrete examples, structure, and job-relevant keywords.",
            "model_answer": expected_answer,
            "keywords_missed": sorted(list(question_tokens - answer_tokens))[:5],
        }
    
    prompt_text = f"""You are an experienced interviewer. Evaluate this student's answer and return ONLY JSON (no markdown):

Question: {question}
Expected Answer: {expected_answer}
Student Answer: {student_answer}
Question Type: {question_type}

Return JSON with these exact fields:
{{
  "score": 0-10,
  "what_was_good": "specific positive feedback",
  "what_to_improve": "specific improvement advice",
  "model_answer": "ideal answer for this question",
  "keywords_missed": ["important terms not mentioned"]
}}

NO markdown backticks, NO extra text. Only valid JSON!"""

    try:
        response = llm.invoke([HumanMessage(content=prompt_text)])
        cleaned_response = response.content.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        parser = JsonOutputParser()
        return parser.parse(cleaned_response)
    except Exception:
        question_tokens = set(simple_tokens(question + " " + expected_answer))
        answer_tokens = set(simple_tokens(student_answer))
        overlap = len(question_tokens & answer_tokens)
        score = min(10, max(1, overlap + 3))
        return {
            "score": score,
            "what_was_good": "The answer addresses the question at a basic level." if score >= 5 else "The answer shows some understanding but lacks detail.",
            "what_to_improve": "Add concrete examples, structure, and job-relevant keywords.",
            "model_answer": expected_answer,
            "keywords_missed": sorted(list(question_tokens - answer_tokens))[:5],
        }
