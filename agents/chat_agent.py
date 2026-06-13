from .llm_synthesis import call_llm

CHAT_SYSTEM = """
You are HiveLogic AI, a financial research assistant.

Use:
- Chat history
- Research report
- Financial metrics
- Citations
- Retrieved filing/PDF evidence

Rules:
- Never provide investment advice.
- Never predict stock prices.
- Never invent facts.
- If information is unavailable, say so.
- Use retrieved evidence whenever possible.
- Answer naturally like a chatbot.
- Do NOT explain your reasoning.
- Do NOT say things like:
  "The user is asking..."
  "I will answer..."
  "According to instructions..."
- Just answer the question directly.
"""

def chat_agent_node(
    report_context,
    history,
    question,
):

    prompt = f"""
Chat History:
{history}

Question:
{question}

Report Context:
{report_context}

Answer the user's question directly.
If the question refers to previous messages,
use the chat history.
"""

    return call_llm(
        CHAT_SYSTEM,
        prompt,
    )