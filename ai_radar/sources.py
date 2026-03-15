"""
Data sources configuration for AI Radar.
Contains all URLs, GitHub orgs, search queries, HuggingFace tasks,
and Tavily search queries used for discovery.
"""

SOURCES = [
    {"name": "arXiv AI", "url": "https://arxiv.org/list/cs.AI/recent", "type": "research", "priority": "high"},
    {"name": "arXiv ML", "url": "https://arxiv.org/list/cs.LG/recent", "type": "research", "priority": "high"},
    {"name": "Papers With Code", "url": "https://paperswithcode.com/latest", "type": "research", "priority": "high"},
    {"name": "OpenAI Blog", "url": "https://openai.com/blog", "type": "company", "priority": "high"},
    {"name": "Anthropic", "url": "https://www.anthropic.com/news", "type": "company", "priority": "high"},
    {"name": "Google DeepMind", "url": "https://deepmind.google/discover/blog/", "type": "company", "priority": "high"},
    {"name": "Meta AI", "url": "https://ai.meta.com/blog/", "type": "company", "priority": "high"},
    {"name": "Google AI Blog", "url": "https://ai.googleblog.com/", "type": "company", "priority": "high"},
    {"name": "Mistral", "url": "https://mistral.ai/news/", "type": "company", "priority": "medium"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog", "type": "developer", "priority": "high"},
    {"name": "Microsoft AI", "url": "https://blogs.microsoft.com/ai/", "type": "company", "priority": "medium"},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/", "type": "news", "priority": "high"},
    {"name": "VentureBeat AI", "url": "https://venturebeat.com/ai/", "type": "news", "priority": "high"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/ai-artificial-intelligence", "type": "news", "priority": "medium"},
    {"name": "Wired AI", "url": "https://www.wired.com/tag/artificial-intelligence/", "type": "news", "priority": "medium"},
    {"name": "Product Hunt AI", "url": "https://www.producthunt.com/topics/artificial-intelligence", "type": "products", "priority": "high"},
    {"name": "There's An AI", "url": "https://theresanaiforthat.com/", "type": "products", "priority": "medium"},
    {"name": "Futurepedia", "url": "https://www.futurepedia.io/", "type": "products", "priority": "medium"},
    {"name": "The Rundown AI", "url": "https://www.therundown.ai/", "type": "newsletter", "priority": "high"},
    {"name": "Ben's Bites", "url": "https://bensbites.com/", "type": "newsletter", "priority": "high"},
    {"name": "AI Breakfast", "url": "https://aibreakfast.beehiiv.com/", "type": "newsletter", "priority": "medium"},
]

GITHUB_ORGS = [
    "openai", "anthropics", "google-deepmind", "facebookresearch",
    "mistralai", "huggingface", "microsoft", "ollama-org",
    "langchain-ai", "run-llama", "chroma-core", "ggerganov",
]

GITHUB_SEARCH_QUERIES = [
    "AI agent framework stars:>100 created:>2026-03-01",
    "LLM inference serving stars:>50 pushed:>2026-03-01",
    "AI RAG retrieval stars:>50 created:>2026-03-01",
    "flutter AI plugin created:>2026-03-01",
    "laravel AI package created:>2026-03-01",
    "Parkinson tremor wearable AI",
    "edge AI medical wearable",
]

HF_TASKS = [
    "text-generation",
    "image-to-text",
    "text-to-image",
    "automatic-speech-recognition",
    "text-to-speech",
    "image-classification",
]

TAVILY_QUERIES = [
    "new AI model released today 2026",
    "LLM release announcement this week",
    "new AI tool launched product hunt this week",
    "best new AI tools developers 2026",
    "new AI marketing tools ads copy video 2026",
    "AI research paper published arxiv this week",
    "AI breakthrough research 2026",
    "trending AI repositories github this week",
    "new open source AI project 2026",
    "AI startup funding acquisition news today",
    "artificial intelligence news today 2026",
    "AI tools marketing agencies advertising 2026",
    "AI video generation ads tools 2026",
    "AI coding tools developers Laravel PHP Flutter 2026",
    "AI API new release developers 2026",
]
