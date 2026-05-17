"""Resource recommender — maps weak areas to curated learning resources."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Resource:
    """A single learning resource."""
    title: str
    type: str  # "video", "article", "course", "practice_problem", "book"
    url: str = ""
    platform: str = ""  # "leetcode", "coursera", "youtube", "udemy", etc.
    difficulty: str = "intermediate"
    description: str = ""
    estimated_time: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "type": self.type,
            "url": self.url,
            "platform": self.platform,
            "difficulty": self.difficulty,
            "description": self.description,
            "estimated_time": self.estimated_time,
        }


# ── Curated Resource Database ─────────────────────────────────────────

_RESOURCE_DB: Dict[str, List[Dict[str, Any]]] = {
    # ── Programming Languages ──
    "python": [
        {"title": "Python Official Tutorial", "type": "article", "url": "https://docs.python.org/3/tutorial/", "platform": "python.org", "difficulty": "beginner", "description": "Official Python tutorial covering all fundamentals", "estimated_time": "8-10 hours"},
        {"title": "Automate the Boring Stuff with Python", "type": "book", "url": "https://automatetheboringstuff.com/", "platform": "book", "difficulty": "beginner", "description": "Practical Python programming for beginners", "estimated_time": "2-4 weeks"},
        {"title": "Python for Everybody Specialization", "type": "course", "url": "https://www.coursera.org/specializations/python", "platform": "coursera", "difficulty": "beginner", "description": "University of Michigan's Python specialization", "estimated_time": "8 weeks"},
        {"title": "LeetCode Python Problems", "type": "practice_problem", "url": "https://leetcode.com/problemset/all/?languageTags=python", "platform": "leetcode", "difficulty": "intermediate", "description": "Practice Python with algorithm problems", "estimated_time": "Ongoing"},
    ],
    "java": [
        {"title": "Java Programming Masterclass", "type": "course", "url": "https://www.udemy.com/course/java-the-complete-java-developer-course/", "platform": "udemy", "difficulty": "beginner", "description": "Comprehensive Java course from basics to advanced", "estimated_time": "6-8 weeks"},
        {"title": "Effective Java (3rd Edition)", "type": "book", "url": "", "platform": "book", "difficulty": "intermediate", "description": "Best practices for Java platform", "estimated_time": "4-6 weeks"},
        {"title": "LeetCode Java Problems", "type": "practice_problem", "url": "https://leetcode.com/problemset/all/?languageTags=java", "platform": "leetcode", "difficulty": "intermediate", "description": "Practice Java with algorithm problems", "estimated_time": "Ongoing"},
    ],
    "javascript": [
        {"title": "JavaScript.info", "type": "article", "url": "https://javascript.info/", "platform": "javascript.info", "difficulty": "beginner", "description": "Modern JavaScript tutorial", "estimated_time": "10-15 hours"},
        {"title": "Eloquent JavaScript", "type": "book", "url": "https://eloquentjavascript.net/", "platform": "book", "difficulty": "intermediate", "description": "A modern introduction to JavaScript", "estimated_time": "3-4 weeks"},
        {"title": "JavaScript30", "type": "course", "url": "https://javascript30.com/", "platform": "wesbos", "difficulty": "intermediate", "description": "30 Day Vanilla JS Challenge", "estimated_time": "30 days"},
    ],
    "typescript": [
        {"title": "TypeScript Official Handbook", "type": "article", "url": "https://www.typescriptlang.org/docs/handbook/", "platform": "typescriptlang.org", "difficulty": "beginner", "description": "Official TypeScript documentation", "estimated_time": "6-8 hours"},
        {"title": "Understanding TypeScript", "type": "course", "url": "https://www.udemy.com/course/understanding-typescript/", "platform": "udemy", "difficulty": "beginner", "description": "Comprehensive TypeScript course", "estimated_time": "3-4 weeks"},
    ],

    # ── Web Frameworks ──
    "react": [
        {"title": "React Official Tutorial", "type": "article", "url": "https://react.dev/learn", "platform": "react.dev", "difficulty": "beginner", "description": "Official React learning guide", "estimated_time": "8-10 hours"},
        {"title": "The Road to React", "type": "book", "url": "https://www.road-to-react.com/", "platform": "book", "difficulty": "beginner", "description": "Comprehensive React book with hands-on projects", "estimated_time": "3-4 weeks"},
        {"title": "React - The Complete Guide", "type": "course", "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "platform": "udemy", "difficulty": "intermediate", "description": "Deep dive into React and Redux", "estimated_time": "4-6 weeks"},
    ],
    "angular": [
        {"title": "Angular Official Tour of Heroes", "type": "article", "url": "https://angular.io/tutorial", "platform": "angular.io", "difficulty": "beginner", "description": "Official Angular getting-started tutorial", "estimated_time": "6-8 hours"},
        {"title": "Angular Complete Course", "type": "course", "url": "https://www.udemy.com/course/the-complete-guide-to-angular-2/", "platform": "udemy", "difficulty": "intermediate", "description": "Comprehensive Angular development course", "estimated_time": "4-6 weeks"},
    ],
    "vue": [
        {"title": "Vue.js Official Guide", "type": "article", "url": "https://vuejs.org/guide/introduction.html", "platform": "vuejs.org", "difficulty": "beginner", "description": "Official Vue.js documentation and guide", "estimated_time": "6-8 hours"},
        {"title": "Vue Mastery", "type": "course", "url": "https://www.vuemastery.com/courses/", "platform": "vuemastery", "difficulty": "beginner", "description": "Video courses for Vue.js developers", "estimated_time": "2-4 weeks"},
    ],
    "django": [
        {"title": "Django Official Tutorial", "type": "article", "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/", "platform": "djangoproject.com", "difficulty": "beginner", "description": "Official Django getting-started tutorial", "estimated_time": "4-6 hours"},
        {"title": "Django for Beginners", "type": "book", "url": "https://djangoforbeginners.com/", "platform": "book", "difficulty": "beginner", "description": "Step-by-step guide to Django web development", "estimated_time": "2-3 weeks"},
    ],
    "flask": [
        {"title": "Flask Mega-Tutorial", "type": "article", "url": "https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world", "platform": "miguelgrinberg", "difficulty": "beginner", "description": "Comprehensive Flask web development tutorial", "estimated_time": "2-3 weeks"},
    ],
    "fastapi": [
        {"title": "FastAPI Official Tutorial", "type": "article", "url": "https://fastapi.tiangolo.com/tutorial/", "platform": "fastapi.tiangolo.com", "difficulty": "beginner", "description": "Official FastAPI tutorial with interactive examples", "estimated_time": "4-6 hours"},
        {"title": "Full Stack FastAPI Template", "type": "practice_problem", "url": "https://github.com/fastapi/full-stack-fastapi-template", "platform": "github", "difficulty": "intermediate", "description": "Production-ready FastAPI full stack template", "estimated_time": "1-2 weeks"},
    ],
    "spring": [
        {"title": "Spring Framework Documentation", "type": "article", "url": "https://spring.io/projects/spring-framework", "platform": "spring.io", "difficulty": "intermediate", "description": "Official Spring Framework documentation", "estimated_time": "Ongoing"},
        {"title": "Spring Boot in Action", "type": "book", "url": "", "platform": "book", "difficulty": "intermediate", "description": "Comprehensive Spring Boot book", "estimated_time": "4-6 weeks"},
    ],
    "nextjs": [
        {"title": "Next.js Learn Course", "type": "course", "url": "https://nextjs.org/learn", "platform": "nextjs.org", "difficulty": "beginner", "description": "Official Next.js interactive tutorial", "estimated_time": "6-8 hours"},
    ],

    # ── Databases ──
    "mysql": [
        {"title": "MySQL Official Tutorial", "type": "article", "url": "https://dev.mysql.com/doc/refman/8.0/en/tutorial.html", "platform": "mysql.com", "difficulty": "beginner", "description": "Official MySQL getting-started guide", "estimated_time": "4-6 hours"},
        {"title": "LeetCode Database Problems", "type": "practice_problem", "url": "https://leetcode.com/problemset/database/", "platform": "leetcode", "difficulty": "intermediate", "description": "SQL practice problems including MySQL", "estimated_time": "Ongoing"},
    ],
    "postgresql": [
        {"title": "PostgreSQL Official Tutorial", "type": "article", "url": "https://www.postgresql.org/docs/current/tutorial.html", "platform": "postgresql.org", "difficulty": "beginner", "description": "Official PostgreSQL tutorial", "estimated_time": "4-6 hours"},
        {"title": "PostgreSQL Exercises", "type": "practice_problem", "url": "https://pgexercises.com/", "platform": "pgexercises.com", "difficulty": "intermediate", "description": "Interactive PostgreSQL exercises", "estimated_time": "1-2 weeks"},
    ],
    "mongodb": [
        {"title": "MongoDB University M001", "type": "course", "url": "https://university.mongodb.com/", "platform": "mongodb university", "difficulty": "beginner", "description": "Free MongoDB basics course", "estimated_time": "2-3 weeks"},
        {"title": "MongoDB Official Manual", "type": "article", "url": "https://www.mongodb.com/docs/manual/", "platform": "mongodb.com", "difficulty": "intermediate", "description": "Comprehensive MongoDB documentation", "estimated_time": "Ongoing"},
    ],
    "redis": [
        {"title": "Redis University", "type": "course", "url": "https://university.redis.com/", "platform": "redis university", "difficulty": "beginner", "description": "Free Redis courses from basics to advanced", "estimated_time": "2-4 weeks"},
    ],
    "sql": [
        {"title": "SQLBolt", "type": "practice_problem", "url": "https://sqlbolt.com/", "platform": "sqlbolt", "difficulty": "beginner", "description": "Interactive SQL lessons and exercises", "estimated_time": "3-5 hours"},
        {"title": "Mode SQL Tutorial", "type": "article", "url": "https://mode.com/sql-tutorial/", "platform": "mode", "difficulty": "intermediate", "description": "Advanced SQL tutorial with real data", "estimated_time": "6-8 hours"},
    ],

    # ── Cloud & DevOps ──
    "aws": [
        {"title": "AWS Cloud Practitioner Essentials", "type": "course", "url": "https://aws.amazon.com/training/learn-about/cloud-practitioner/", "platform": "aws", "difficulty": "beginner", "description": "Official AWS entry-level course", "estimated_time": "6 hours"},
        {"title": "AWS Solutions Architect Course", "type": "course", "url": "https://www.udemy.com/course/aws-certified-solutions-architect-associate-saa-c03/", "platform": "udemy", "difficulty": "intermediate", "description": "AWS Solutions Architect certification prep", "estimated_time": "4-6 weeks"},
    ],
    "azure": [
        {"title": "Azure Fundamentals AZ-900", "type": "course", "url": "https://learn.microsoft.com/en-us/training/paths/azure-fundamentals/", "platform": "microsoft learn", "difficulty": "beginner", "description": "Microsoft Azure fundamentals learning path", "estimated_time": "8-10 hours"},
    ],
    "gcp": [
        {"title": "Google Cloud Fundamentals", "type": "course", "url": "https://cloud.google.com/training/cloud-infrastructure", "platform": "google cloud", "difficulty": "beginner", "description": "Google Cloud Platform fundamentals courses", "estimated_time": "8-10 hours"},
    ],
    "docker": [
        {"title": "Docker Getting Started", "type": "article", "url": "https://docs.docker.com/get-started/", "platform": "docker.com", "difficulty": "beginner", "description": "Official Docker getting started guide", "estimated_time": "3-4 hours"},
        {"title": "Docker for Beginners", "type": "course", "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/", "platform": "udemy", "difficulty": "beginner", "description": "Docker and Kubernetes comprehensive course", "estimated_time": "4-6 weeks"},
    ],
    "kubernetes": [
        {"title": "Kubernetes Official Tutorials", "type": "article", "url": "https://kubernetes.io/docs/tutorials/", "platform": "kubernetes.io", "difficulty": "intermediate", "description": "Official Kubernetes learning tutorials", "estimated_time": "8-10 hours"},
        {"title": "CKA Certification Course", "type": "course", "url": "https://www.udemy.com/course/certified-kubernetes-administrator-with-practice-tests/", "platform": "udemy", "difficulty": "intermediate", "description": "Kubernetes administrator certification prep", "estimated_time": "4-6 weeks"},
    ],
    "terraform": [
        {"title": "HashiCorp Learn Terraform", "type": "article", "url": "https://developer.hashicorp.com/terraform/tutorials", "platform": "hashicorp", "difficulty": "beginner", "description": "Official Terraform tutorials", "estimated_time": "4-6 hours"},
    ],
    "git": [
        {"title": "Pro Git Book", "type": "book", "url": "https://git-scm.com/book/en/v2", "platform": "book", "difficulty": "beginner", "description": "Comprehensive free Git book", "estimated_time": "2-3 weeks"},
        {"title": "Learn Git Branching", "type": "practice_problem", "url": "https://learngitbranching.js.org/", "platform": "learngitbranching", "difficulty": "intermediate", "description": "Interactive Git visualization and exercises", "estimated_time": "3-5 hours"},
    ],

    # ── ML / AI ──
    "machine learning": [
        {"title": "Machine Learning by Andrew Ng", "type": "course", "url": "https://www.coursera.org/learn/machine-learning", "platform": "coursera", "difficulty": "beginner", "description": "Stanford's iconic ML course on Coursera", "estimated_time": "11 weeks"},
        {"title": "Hands-On Machine Learning", "type": "book", "url": "", "platform": "book", "difficulty": "intermediate", "description": "Practical ML with Scikit-Learn, Keras, and TensorFlow", "estimated_time": "6-8 weeks"},
    ],
    "deep learning": [
        {"title": "Deep Learning Specialization", "type": "course", "url": "https://www.coursera.org/specializations/deep-learning", "platform": "coursera", "difficulty": "intermediate", "description": "Andrew Ng's deep learning specialization", "estimated_time": "16-20 weeks"},
        {"title": "Deep Learning Book", "type": "book", "url": "https://www.deeplearningbook.org/", "platform": "book", "difficulty": "advanced", "description": "Comprehensive deep learning textbook by Goodfellow et al.", "estimated_time": "8-12 weeks"},
    ],
    "tensorflow": [
        {"title": "TensorFlow Developer Certificate", "type": "course", "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "platform": "coursera", "difficulty": "intermediate", "description": "TensorFlow in practice certificate", "estimated_time": "4-6 weeks"},
    ],
    "pytorch": [
        {"title": "PyTorch Official Tutorials", "type": "article", "url": "https://pytorch.org/tutorials/", "platform": "pytorch.org", "difficulty": "beginner", "description": "Official PyTorch tutorials and examples", "estimated_time": "8-10 hours"},
        {"title": "PyTorch Deep Learning", "type": "course", "url": "https://www.udemy.com/course/pytorch-for-deep-learning-and-computer-vision/", "platform": "udemy", "difficulty": "intermediate", "description": "Deep learning with PyTorch course", "estimated_time": "3-4 weeks"},
    ],
    "nlp": [
        {"title": "NLP Specialization", "type": "course", "url": "https://www.coursera.org/specializations/natural-language-processing", "platform": "coursera", "difficulty": "intermediate", "description": "deeplearning.ai NLP specialization", "estimated_time": "12-16 weeks"},
        {"title": "Hugging Face NLP Course", "type": "course", "url": "https://huggingface.co/learn/nlp-course", "platform": "huggingface", "difficulty": "intermediate", "description": "Free NLP course using Transformers", "estimated_time": "6-8 hours"},
    ],
    "scikit-learn": [
        {"title": "Scikit-Learn Official Tutorials", "type": "article", "url": "https://scikit-learn.org/stable/tutorial/index.html", "platform": "scikit-learn.org", "difficulty": "beginner", "description": "Official scikit-learn tutorials", "estimated_time": "6-8 hours"},
    ],

    # ── DSA / Algorithms ──
    "data structures": [
        {"title": "LeetCode Explore - Data Structures", "type": "practice_problem", "url": "https://leetcode.com/explore/learn/card/data-structure/", "platform": "leetcode", "difficulty": "beginner", "description": "Interactive data structure learning cards", "estimated_time": "2-3 weeks"},
        {"title": "Grokking Algorithms", "type": "book", "url": "", "platform": "book", "difficulty": "beginner", "description": "Illustrated guide to algorithms and data structures", "estimated_time": "2-3 weeks"},
    ],
    "algorithms": [
        {"title": "LeetCode Problems by Topic", "type": "practice_problem", "url": "https://leetcode.com/problemset/", "platform": "leetcode", "difficulty": "intermediate", "description": "Practice algorithm problems sorted by topic", "estimated_time": "Ongoing"},
        {"title": "Introduction to Algorithms (CLRS)", "type": "book", "url": "", "platform": "book", "difficulty": "advanced", "description": "The definitive algorithms textbook", "estimated_time": "12-16 weeks"},
    ],
    "system design": [
        {"title": "System Design Primer", "type": "article", "url": "https://github.com/donnemartin/system-design-primer", "platform": "github", "difficulty": "intermediate", "description": "Comprehensive system design guide", "estimated_time": "1-2 weeks"},
        {"title": "Designing Data-Intensive Applications", "type": "book", "url": "", "platform": "book", "difficulty": "advanced", "description": "Modern data system design by Martin Kleppmann", "estimated_time": "6-8 weeks"},
        {"title": "Grokking System Design", "type": "course", "url": "https://www.designgurus.io/course/grokking-the-system-design-interview", "platform": "designgurus", "difficulty": "intermediate", "description": "System design interview preparation", "estimated_time": "3-4 weeks"},
    ],

    # ── Soft Skills ──
    "leadership": [
        {"title": "Leadership in Tech", "type": "course", "url": "https://www.coursera.org/learn/leadership-collaboration", "platform": "coursera", "difficulty": "intermediate", "description": "Leadership skills for technology professionals", "estimated_time": "4 weeks"},
    ],
    "communication": [
        {"title": "Effective Communication", "type": "course", "url": "https://www.coursera.org/learn/effective-business-communication", "platform": "coursera", "difficulty": "beginner", "description": "Business communication skills course", "estimated_time": "4 weeks"},
    ],
    "problem solving": [
        {"title": "Computational Thinking", "type": "course", "url": "https://www.edx.org/learn/computational-thinking", "platform": "edx", "difficulty": "beginner", "description": "Structured problem-solving course", "estimated_time": "4 weeks"},
    ],

    # ── Practice Platforms ──
    "general": [
        {"title": "LeetCode", "type": "practice_problem", "url": "https://leetcode.com/", "platform": "leetcode", "difficulty": "intermediate", "description": "Algorithm and data structure practice", "estimated_time": "Ongoing"},
        {"title": "HackerRank", "type": "practice_problem", "url": "https://www.hackerrank.com/", "platform": "hackerrank", "difficulty": "beginner", "description": "Coding challenges and skill assessments", "estimated_time": "Ongoing"},
        {"title": "Pramp (Mock Interviews)", "type": "practice_problem", "url": "https://www.pramp.com/", "platform": "pramp", "difficulty": "intermediate", "description": "Free peer-to-peer mock interviews", "estimated_time": "1 hour/session"},
        {"title": "Interviewing.io", "type": "practice_problem", "url": "https://interviewing.io/", "platform": "interviewing.io", "difficulty": "intermediate", "description": "Anonymous mock interviews with engineers", "estimated_time": "1 hour/session"},
    ],
}


class ResourceRecommender:
    """Maps weak areas to curated learning resources.

    The resource database covers programming languages, frameworks,
    databases, cloud/devops, ML/AI, algorithms, and soft skills.

    Args:
        custom_resources: Optional additional resources to merge with defaults.
    """

    def __init__(self, custom_resources: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        self._db: Dict[str, List[Resource]] = {}

        # Build from default database
        for topic, resources in _RESOURCE_DB.items():
            self._db[topic.lower()] = [
                Resource(
                    title=r["title"],
                    type=r["type"],
                    url=r.get("url", ""),
                    platform=r.get("platform", ""),
                    difficulty=r.get("difficulty", "intermediate"),
                    description=r.get("description", ""),
                    estimated_time=r.get("estimated_time", ""),
                )
                for r in resources
            ]

        # Merge custom resources
        if custom_resources:
            for topic, resources in custom_resources.items():
                key = topic.lower()
                existing = self._db.get(key, [])
                for r in resources:
                    existing.append(Resource(
                        title=r.get("title", ""),
                        type=r.get("type", "article"),
                        url=r.get("url", ""),
                        platform=r.get("platform", ""),
                        difficulty=r.get("difficulty", "intermediate"),
                        description=r.get("description", ""),
                        estimated_time=r.get("estimated_time", ""),
                    ))
                self._db[key] = existing

    @property
    def topic_count(self) -> int:
        """Number of topics in the database."""
        return len(self._db)

    @property
    def total_resources(self) -> int:
        """Total number of resources across all topics."""
        return sum(len(resources) for resources in self._db.values())

    def recommend(
        self,
        topic: str,
        current_level: str = "beginner",
        max_results: int = 5,
        resource_types: Optional[List[str]] = None,
    ) -> List[Resource]:
        """Recommend resources for a weak area.

        Args:
            topic: The weak topic (e.g., "python", "react", "system design").
            current_level: "beginner", "intermediate", or "advanced".
            max_results: Maximum number of resources to return.
            resource_types: Optional filter by type ("video", "course", etc.).

        Returns:
            List of Resource objects sorted by relevance.
        """
        topic_lower = topic.lower().strip()

        # Direct lookup
        resources = self._db.get(topic_lower, [])

        # Fuzzy lookup if no direct match
        if not resources:
            for key in self._db:
                if key in topic_lower or topic_lower in key:
                    resources = self._db[key]
                    break

        # Still nothing — return general resources
        if not resources:
            resources = self._db.get("general", [])

        # Filter by type
        if resource_types:
            type_set = {t.lower() for t in resource_types}
            resources = [r for r in resources if r.type.lower() in type_set]

        # Filter by difficulty — match current level or one step above
        level_order = {"beginner": 0, "intermediate": 1, "advanced": 2, "expert": 3}
        current_idx = level_order.get(current_level, 0)

        # Prefer resources at or slightly above current level
        def level_score(r: Resource) -> int:
            r_idx = level_order.get(r.difficulty, 1)
            # Prefer exact match, then one above, then below
            diff = r_idx - current_idx
            if diff == 0:
                return 0
            elif diff == 1:
                return 1
            elif diff == -1:
                return 2
            else:
                return 3

        resources = sorted(resources, key=level_score)
        return resources[:max_results]

    def get_all_topics(self) -> List[str]:
        """List all topics in the resource database."""
        return sorted(self._db.keys())

    def add_resource(self, topic: str, resource: Resource) -> None:
        """Add a custom resource to the database.

        Args:
            topic: Topic category.
            resource: The Resource to add.
        """
        key = topic.lower()
        if key not in self._db:
            self._db[key] = []
        self._db[key].append(resource)
