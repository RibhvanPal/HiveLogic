import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
import traceback

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile",
)

_llm = None


def get_llm():
    global _llm
    print(f"[LLM] Provider: Groq")
    print(f"[LLM] Model: {GROQ_MODEL}")
    if _llm is not None:
        return _llm
    _llm = ChatGroq(
        api_key=GROQ_API_KEY,
        model=GROQ_MODEL,
        temperature=0.1,
        max_tokens=1500,
    )
    return _llm


def call_llm(system_prompt: str, user_prompt: str) -> str:
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = llm.invoke(messages)
        if hasattr(response, "content"):
            return str(response.content)
        return str(response)

    except Exception as e:
        print("\nLLM ERROR")
        traceback.print_exc()
        print("===============================\n")
        return f"LLM unavailable: {e}"