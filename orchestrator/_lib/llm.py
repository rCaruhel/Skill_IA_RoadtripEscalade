import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def get_llm(temperature=0):
    backend = os.getenv("LLM_BACKEND", "ollama")
    if backend == "mistral":
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(model="mistral-small-latest", temperature=temperature)
    elif backend == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=temperature)
    elif backend == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
    elif backend == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=temperature)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1"), temperature=temperature)
