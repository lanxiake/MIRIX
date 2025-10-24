TEMPORARY_MESSAGE_LIMIT = 2  # 减少到2个消息就触发记忆吸收
MAXIMUM_NUM_IMAGES_IN_CLOUD = 600

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-1.5-pro",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
]
OPENAI_MODELS = [
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-4o-mini",
    "gpt-4o",
    "o4-mini",
    "gpt-5-mini",
    "gpt-5",
]
DEEPSEEK_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner",
]

STUCK_TIMEOUT = 10
RUNNING_TIMEOUT = 30
TOTAL_TIMEOUT = 60

SKIP_META_MEMORY_MANAGER = False

# Whether to use the reflexion agent
WITH_REFLEXION_AGENT = False

# Whether to use the background agent
WITH_BACKGROUND_AGENT = False
