"""Constants, templates, and prompt definitions for AI Interview Agent."""

# Interview states
class InterviewState:
    IDLE = "idle"
    RESUME_PROCESSING = "resume_processing"
    READY = "ready"
    INTRODUCTION = "introduction"
    ASKING_QUESTION = "asking_question"
    LISTENING = "listening"
    PROCESSING_ANSWER = "processing_answer"
    GENERATING_FOLLOWUP = "generating_followup"
    ASKING_FOLLOWUP = "asking_followup"
    LISTENING_FOLLOWUP = "listening_followup"
    SELECTING_NEXT_QUESTION = "selecting_next_question"
    CLOSING = "closing"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    ERROR = "error"


# Valid state transitions
STATE_TRANSITIONS = {
    InterviewState.IDLE: [InterviewState.RESUME_PROCESSING],
    InterviewState.RESUME_PROCESSING: [InterviewState.READY, InterviewState.ERROR],
    InterviewState.READY: [InterviewState.INTRODUCTION, InterviewState.IDLE],
    InterviewState.INTRODUCTION: [InterviewState.ASKING_QUESTION],
    InterviewState.ASKING_QUESTION: [InterviewState.LISTENING],
    InterviewState.LISTENING: [InterviewState.PROCESSING_ANSWER, InterviewState.ASKING_QUESTION],
    InterviewState.PROCESSING_ANSWER: [
        InterviewState.GENERATING_FOLLOWUP,
        InterviewState.SELECTING_NEXT_QUESTION,
    ],
    InterviewState.GENERATING_FOLLOWUP: [InterviewState.ASKING_FOLLOWUP, InterviewState.SELECTING_NEXT_QUESTION],
    InterviewState.ASKING_FOLLOWUP: [InterviewState.LISTENING_FOLLOWUP],
    InterviewState.LISTENING_FOLLOWUP: [InterviewState.PROCESSING_ANSWER],
    InterviewState.SELECTING_NEXT_QUESTION: [
        InterviewState.ASKING_QUESTION,
        InterviewState.CLOSING,
    ],
    InterviewState.CLOSING: [InterviewState.GENERATING_REPORT],
    InterviewState.GENERATING_REPORT: [InterviewState.COMPLETED],
    InterviewState.COMPLETED: [InterviewState.IDLE],
    InterviewState.ERROR: [InterviewState.IDLE, InterviewState.READY],
}

# Fix the typo in transitions dict
STATE_TRANSITIONS[InterviewState.LISTENING_FOLLOWUP] = [InterviewState.PROCESSING_ANSWER]


# Difficulty levels
class DifficultyLevel:
    EASY = 1
    MEDIUM = 2
    HARD = 3
    EXPERT = 4

    NAMES = {1: "easy", 2: "medium", 3: "hard", 4: "expert"}
    LEVELS = {"easy": 1, "medium": 2, "hard": 3, "expert": 4}

    @classmethod
    def to_name(cls, level: int) -> str:
        return cls.NAMES.get(level, "medium")

    @classmethod
    def from_name(cls, name: str) -> int:
        return cls.LEVELS.get(name.lower(), 2)


# Adaptive difficulty thresholds
DIFFICULTY_THRESHOLDS = {
    "increase": 85,
    "maintain_low": 60,
    "decrease_high": 59,
    "decrease_low": 40,
}
ROLLING_WINDOW_SIZE = 3

# Question types
QUESTION_TYPES = ["resume", "technical", "behavioral"]

# Scoring thresholds
SCORING_THRESHOLDS = {
    "excellent": 85,
    "good": 70,
    "average": 55,
    "below_average": 40,
    "poor": 0,
}

# Emotion labels (DeepFace)
EMOTION_LABELS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]

# Positive / negative emotion grouping for confidence scoring
POSITIVE_EMOTIONS = {"happy", "surprise", "neutral"}
NEGATIVE_EMOTIONS = {"angry", "disgust", "fear", "sad"}

# Behavioral question bank
BEHAVIORAL_QUESTIONS = [
    "Tell me about a time you faced a significant challenge at work. How did you handle it?",
    "Describe a situation where you had to work with a difficult team member.",
    "Give an example of a goal you reached and how you achieved it.",
    "Tell me about a time when you had to make a difficult decision quickly.",
    "Describe a situation where you showed leadership.",
    "Tell me about a time you failed. What did you learn?",
    "How do you handle tight deadlines and pressure?",
    "Describe a time when you had to adapt to a significant change at work.",
    "Tell me about a time you went above and beyond for a project.",
    "How do you prioritize your work when you have multiple deadlines?",
    "Describe a situation where you had to resolve a conflict within your team.",
    "Tell me about a time you received constructive criticism. How did you respond?",
]

# Technical question templates by difficulty
TECHNICAL_QUESTION_TEMPLATES = {
    "easy": [
        "Can you explain what {skill} is and how you have used it?",
        "What are the basic concepts of {skill}?",
        "How would you describe {skill} to a beginner?",
        "What projects have you done using {skill}?",
    ],
    "medium": [
        "How does {skill} compare to alternative technologies? When would you choose it?",
        "Can you walk me through how you would implement a {skill} solution for a real-world problem?",
        "What are the best practices when working with {skill}?",
        "How do you debug issues in {skill}?",
    ],
    "hard": [
        "How would you architect a scalable system using {skill}? What trade-offs would you consider?",
        "Explain the internal workings of {skill} and how that affects performance.",
        "How would you optimize a {skill} application that is experiencing bottlenecks?",
        "Design a system that integrates {skill} with {other_skill} at scale.",
    ],
    "expert": [
        "If you were to redesign {skill} from scratch, what would you change and why?",
        "What are the edge cases and failure modes of {skill} that most engineers overlook?",
        "How would you handle a production incident involving {skill} at 3 AM?",
        "Contribute a critical analysis of {skill}'s architecture and propose improvements.",
    ],
}

# Resume question templates
RESUME_QUESTION_TEMPLATES = [
    "Tell me more about your project '{project}'. What was your role and what technologies did you use?",
    "I see you listed {skill} on your resume. Can you describe a challenging problem you solved using it?",
    "You worked on {project}. What were the biggest technical challenges you faced?",
    "How did you apply {skill} in your previous role?",
    "What was the most impactful contribution you made to {project}?",
    "Can you describe how {skill} and {other_skill} relate in your experience?",
]

# Introduction prompt template
INTRODUCTION_TEMPLATE = (
    "Hello {name}! Welcome to your AI-powered interview. "
    "I've reviewed your resume and I'm impressed by your experience with {top_skills}. "
    "Today's interview will cover your technical skills, past projects, and behavioral scenarios. "
    "I'll ask you {question_count} questions, and I may ask follow-up questions based on your answers. "
    "Please speak clearly and take your time. Let's begin!"
)

# Closing prompt template
CLOSING_TEMPLATE = (
    "Thank you, {name}, for taking the time to interview with us today. "
    "You answered {answered_count} questions and scored an average of {avg_score:.1f} out of 100. "
    "I'll now generate a detailed report with your results and feedback. "
    "Best of luck!"
)

# Follow-up prompt template
FOLLOWUP_PROMPT = (
    "The candidate was asked: '{question}'\n"
    "They answered: '{answer}'\n"
    "Score: {score}/100\n\n"
    "Generate a follow-up question that digs deeper into their response. "
    "The follow-up should test deeper understanding or clarify vague points."
)

# Question generation prompt
QUESTION_GENERATION_PROMPT = (
    "You are an expert technical interviewer. Generate {count} interview questions "
    "for a candidate with the following skills: {skills}\n"
    "Projects: {projects}\n"
    "Difficulty level: {difficulty}\n"
    "Question types needed: {types}\n\n"
    "Return each question on a new line, prefixed with its type in brackets, e.g.:\n"
    "[technical] What is the time complexity of...\n"
    "[resume] Tell me about your project...\n"
    "[behavioral] Describe a time when...\n"
)

# Feedback generation prompt
FEEDBACK_PROMPT = (
    "You are an expert interview coach. Analyze the following interview data and provide feedback.\n\n"
    "Candidate: {name}\n"
    "Total Questions: {total_questions}\n"
    "Average Score: {avg_score:.1f}/100\n"
    "Score Breakdown:\n{score_breakdown}\n\n"
    "Question-by-question performance:\n{question_details}\n\n"
    "Emotion Analysis:\n{emotion_summary}\n\n"
    "Provide:\n"
    "1. Top 3 strengths (specific and actionable)\n"
    "2. Top 3 weaknesses (specific and constructive)\n"
    "3. Top 3 suggestions for improvement (actionable advice)\n"
    "4. Overall assessment (2-3 sentences)\n\n"
    "Format your response as JSON with keys: strengths, weaknesses, suggestions, overall_assessment"
)

# Skill taxonomy - common technical skills grouped by category
SKILL_TAXONOMY = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    ],
    "web_frameworks": [
        "react", "angular", "vue", "django", "flask", "fastapi", "express",
        "spring", "rails", "laravel", "nextjs", "nuxt", "svelte",
    ],
    "databases": [
        "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra",
        "dynamodb", "sqlite", "oracle", "sql server", "mariadb", "neo4j",
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
        "ci/cd", "git", "github actions", "ansible", "prometheus", "grafana",
    ],
    "ml_ai": [
        "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
        "nlp", "computer vision", "data science", "pandas", "numpy", "keras",
        "transformers", "llm", "neural networks", "reinforcement learning",
    ],
    "data_tools": [
        "spark", "hadoop", "kafka", "airflow", "tableau", "power bi",
        "excel", "sql", "nosql", "etl", "data warehouse",
    ],
    "mobile": [
        "android", "ios", "react native", "flutter", "swift", "kotlin",
        "xamarin", "ionic",
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving",
        "agile", "scrum", "project management", "mentoring",
    ],
}

# Flatten skill taxonomy for quick lookup
ALL_SKILLS = []
for category_skills in SKILL_TAXONOMY.values():
    ALL_SKILLS.extend(category_skills)
ALL_SKILLS = list(set(ALL_SKILLS))


# ═══════════════════════════════════════════════════════════════════════
# Copilot Suggestion Templates
# ═══════════════════════════════════════════════════════════════════════

COPILOT_SUGGESTION_TEMPLATES = {
    "follow_up": {
        "icon": "🔄",
        "color": "#3498db",
        "templates": [
            "Ask follow-up about {topic}",
            "Probe deeper into {topic} — candidate may have more to share",
            "The candidate mentioned {topic} briefly — explore further",
            "Follow up on {topic} to assess depth of understanding",
        ],
    },
    "probe_deeper": {
        "icon": "🔍",
        "color": "#9b59b6",
        "templates": [
            "Candidate seems strong in {skill}, probe deeper",
            "Ask about trade-offs or edge cases in {skill}",
            "Request a real-world example of {skill}",
            "Ask the candidate to compare {skill} with an alternative",
        ],
    },
    "rephrase": {
        "icon": "💬",
        "color": "#e67e22",
        "templates": [
            "Candidate avoided {concept}, consider rephrasing",
            "Rephrase the question on {topic} — candidate may need a simpler angle",
            "Try asking about {concept} from a different perspective",
            "Give a concrete scenario before asking about {concept}",
        ],
    },
    "star_method": {
        "icon": "⭐",
        "color": "#f1c40f",
        "templates": [
            "STAR method not used, suggest asking for specific example",
            "Ask: 'Can you describe a specific situation where this happened?'",
            "Prompt for the result/outcome of their example",
            "Guide candidate to structure: Situation → Task → Action → Result",
        ],
    },
    "gap_fill": {
        "icon": "🎯",
        "color": "#e74c3c",
        "templates": [
            "Gap identified: {topic} not yet covered",
            "Ask about {topic} — it's a required skill for this role",
            "{topic} is important for this position, consider a question here",
            "The candidate hasn't demonstrated {topic} — ask about it",
        ],
    },
    "encourage": {
        "icon": "👏",
        "color": "#2ecc71",
        "templates": [
            "Candidate is doing well — offer positive reinforcement",
            "Acknowledge the candidate's strengths before moving on",
            "Good answer! Briefly praise before next question",
        ],
    },
    "redirect": {
        "icon": "🔀",
        "color": "#95a5a6",
        "templates": [
            "Consider changing topic — candidate struggling in this area",
            "Redirect to a stronger topic for the candidate",
            "Pivot to {topic} to build confidence",
        ],
    },
    "strong_area": {
        "icon": "💪",
        "color": "#27ae60",
        "templates": [
            "Candidate is strong in {skill}, probe deeper",
            "Excellent {skill} knowledge — ask advanced follow-up",
            "The candidate excels at {skill} — test edge cases",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Coaching Resources Database (summary keys — full data in resource_recommender.py)
# ═══════════════════════════════════════════════════════════════════════

COACHING_RESOURCE_CATEGORIES = {
    "programming": {
        "label": "Programming Languages",
        "topics": ["python", "java", "javascript", "typescript", "c++", "go", "rust"],
    },
    "web": {
        "label": "Web Development",
        "topics": ["react", "angular", "vue", "django", "flask", "fastapi", "spring", "nextjs"],
    },
    "databases": {
        "label": "Databases",
        "topics": ["mysql", "postgresql", "mongodb", "redis", "sql"],
    },
    "cloud": {
        "label": "Cloud & DevOps",
        "topics": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "git"],
    },
    "ml_ai": {
        "label": "Machine Learning & AI",
        "topics": ["machine learning", "deep learning", "tensorflow", "pytorch", "nlp", "scikit-learn"],
    },
    "algorithms": {
        "label": "Algorithms & System Design",
        "topics": ["data structures", "algorithms", "system design"],
    },
    "soft_skills": {
        "label": "Soft Skills",
        "topics": ["leadership", "communication", "problem solving"],
    },
    "practice_platforms": {
        "label": "Practice Platforms",
        "topics": ["general"],
        "platforms": [
            {"name": "LeetCode", "url": "https://leetcode.com/", "type": "algorithms"},
            {"name": "HackerRank", "url": "https://www.hackerrank.com/", "type": "general"},
            {"name": "Pramp", "url": "https://www.pramp.com/", "type": "mock_interviews"},
            {"name": "Interviewing.io", "url": "https://interviewing.io/", "type": "mock_interviews"},
            {"name": "Exercism", "url": "https://exercism.org/", "type": "languages"},
            {"name": "Codewars", "url": "https://www.codewars.com/", "type": "algorithms"},
        ],
    },
}

COACHING_LEVEL_THRESHOLDS = {
    "beginner_max": 40,
    "intermediate_max": 70,
    "advanced_min": 70,
}

COACHING_TIME_ESTIMATES = {
    "beginner_to_intermediate": "2-4 weeks",
    "intermediate_to_advanced": "4-8 weeks",
    "advanced_to_expert": "8-12 weeks",
    "quick_familiarization": "3-5 days",
}
