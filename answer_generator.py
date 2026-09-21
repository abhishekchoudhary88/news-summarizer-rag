"""
Answer Generator (Gemini Version - Hybrid Mode + Conversation Memory)
------------------------------------------------------------------------
Retrieved news chunks + user ka sawaal + recent chat history, Google Gemini
API ko bhejta hai aur ek natural, context-aware answer generate karwata hai.

CONVERSATION MEMORY:
Pichle 1-2 exchanges (Q&A pairs) prompt mein include kiye jaate hain, taaki
follow-up sawaal (jaise "aur uske baare mein zyada batao") bina context ke
bhi samajh mein aaye.

HYBRID APPROACH:
Pehle retrieved news use karke answer karne ki koshish, agar wahan info
nahi hai toh general knowledge se answer, clearly label karke.
"""

from google import genai
from datetime import datetime

MAX_HISTORY_TURNS = 3  # Kitne purane Q&A pairs context mein include karne hain


def format_chat_history(chat_history):
    """
    Chat history (list of {'role':..,'content':..}) ko ek readable
    text block mein convert karta hai, sirf last N turns.
    """
    if not chat_history:
        return "Koi previous conversation nahi hai."

    recent = chat_history[-(MAX_HISTORY_TURNS * 2):]
    lines = []
    for msg in recent:
        speaker = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{speaker}: {msg['content']}")
    return "\n".join(lines)


def generate_answer(query, retrieved_chunks, api_key, chat_history=None):
    """
    query: user ka current sawaal
    retrieved_chunks: rag_pipeline.retrieve() se aaye hue relevant chunks (with scores)
    api_key: Google AI Studio ki API key
    chat_history: pichli conversation (optional) - follow-up sawaalon ke liye
    """
    context = "Koi relevant news article nahi mila."
    if retrieved_chunks:
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            context_parts.append(
                f"[Article {i} - Source: {chunk['metadata']['source']} "
                f"(Relevance: {chunk['score']}%)]\n{chunk['text']}"
            )
        context = "\n\n".join(context_parts)

    history_text = format_chat_history(chat_history or [])
    today_str = datetime.now().strftime("%A, %d %B %Y")

    prompt = f"""Aaj ki actual date hai: {today_str}

Neeche conversation history, kuch recent news articles, aur ek naya sawaal diya gaya hai.

PREVIOUS CONVERSATION:
{history_text}

NEWS ARTICLES:
{context}

NEW QUESTION: {query}

INSTRUCTIONS:
1. Agar user aaj ki date/din puche, seedha upar di gayi actual date se jawab do - kisi
   news article ki zaroorat nahi hai iske liye.
2. Agar naya sawaal previous conversation se related hai (jaise "aur batao", "uska matlab kya hai"),
   toh conversation history ko context ke roop mein use karo.
3. Pehle check karo ki news articles mein is sawaal ka answer hai ya nahi.
4. Agar HAI, toh un articles ke basis pe answer do, shuru mein likho "(News ke basis par)".
5. Agar NAHI hai, toh apne general knowledge se answer do, shuru mein likho
   "(General knowledge se, live news mein nahi mila)".
6. Answer clear aur concise rakho.

Answer:"""

    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt
    )

    return interaction.output_text
