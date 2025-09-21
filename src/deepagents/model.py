from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


def get_default_model():
    # return ChatAnthropic(model_name="claude-sonnet-4-20250514", max_tokens=64000)
    return ChatOpenAI(model_name="gpt-5-nano", max_tokens=64000)
    # return ChatOllama(model="gpt-oss:20b", num_predict=64000)