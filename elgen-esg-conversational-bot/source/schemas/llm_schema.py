from enum import Enum


class SupportedLLModels(str, Enum):
    gpt4all = "GPT4ALL"
    fake = "FAKE"
    gpt2 = "GPT2"
    falcon = "FALCON"
    llama_cpp = "LlamaCpp"
    open_ai = "OpenAI"


class ExposedModels(str, Enum):
    falcon = "FALCON"
    open_ai = "OpenAI"
