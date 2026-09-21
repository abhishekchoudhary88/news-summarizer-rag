"""
News RAG Chatbot - Main App (v6 - Animated, ChatGPT-style Polished UI)
--------------------------------------------------------------------------
New in this version:
- Fade-in / slide-up animations on messages, header, and suggestion cards
- Sidebar history items redesigned: consistent icons, active chat
  highlighted using Streamlit's built-in primary button style (like
  ChatGPT's selected-conversation highlight)
- Default session name changed from "New chat" to "Untitled conversation"
  with a consistent 💬 icon on every history entry
- Animated welcome icon on the empty state
"""

import streamlit as st
import os
import random
import uuid
from datetime import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from news_fetcher import fetch_articles, RSS_FEEDS
from rag_pipeline import NewsRAGStore, EMBEDDING_MODEL_NAME
from answer_generator import generate_answer
import auth

load_dotenv()

st.set_page_config(page_title="News Summarizer", page_icon="🦉", layout="centered")

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to   { opacity: 1; }
    }
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-6px); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50%      { opacity: 0.4; }
    }

    .block-container {
        padding-top: 2.5rem;
        max-width: 780px;
    }
    #MainMenu, footer {visibility: hidden;}

    .welcome-icon {
        font-size: 2.6rem;
        animation: bounce 2.2s ease-in-out infinite;
        margin-bottom: 4px;
    }
    .app-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 2px;
        animation: fadeInUp 0.5s ease-out;
    }
    .app-subtitle {
        color: #94A3B8;
        font-size: 0.9rem;
        margin-bottom: 1.6rem;
        animation: fadeInUp 0.5s ease-out 0.1s backwards;
    }

    .stChatMessage {
        border-radius: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        animation: fadeInUp 0.35s ease-out;
    }
    .msg-time {
        font-size: 0.7rem;
        color: #B0B8C4;
        margin-top: -6px;
        margin-bottom: 8px;
    }

    div[data-testid="stVerticalBlock"] .stButton {
        animation: fadeInUp 0.4s ease-out;
    }
    .stButton button {
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        text-align: left;
        color: #334155;
        transition: all 0.15s ease;
    }
    .stButton button:hover {
        border-color: #2563EB;
        color: #2563EB;
        background-color: #F8FAFF;
        transform: translateX(2px);
    }

    .source-tag {
        display: inline-block;
        background-color: #EFF6FF;
        color: #2563EB;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .score-tag {
        display: inline-block;
        background-color: #ECFDF5;
        color: #059669;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }

    section[data-testid="stSidebar"] {
        background-color: #FAFAFA;
    }
    section[data-testid="stSidebar"] .stButton button {
        border: none;
        background-color: transparent;
        font-size: 0.85rem;
        padding: 6px 10px;
    }
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #EEF2FF;
        transform: none;
    }
    section[data-testid="stSidebar"] .stButton button[kind="primary"] {
        background-color: #E0E7FF !important;
        color: #1E3A8A !important;
        font-weight: 600;
        border: none;
    }

    .sidebar-section-label {
        font-size: 0.72rem;
        font-weight: 700;
        color: #94A3B8;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-top: 18px;
        margin-bottom: 6px;
    }
    .thinking-dots span {
        animation: pulse 1.2s infinite;
    }
    .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
</style>
""", unsafe_allow_html=True)


DEFAULT_SESSION_TITLE = "Untitled conversation"


# ---------------- LOGIN GATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# Google OAuth se login (Streamlit ka built-in st.login/st.user) - agar
# user Google se pehle se logged in hai (secrets.toml configured hone par)
google_logged_in = False
try:
    if st.user.is_logged_in:
        google_logged_in = True
        st.session_state.logged_in = True
        st.session_state.user_email = st.user.email
        st.session_state.login_method = "google"
except Exception:
    # st.user tab error deta hai jab [auth] secrets.toml mein configure nahi hai -
    # tab sirf email/password login available rahega
    pass

if not st.session_state.logged_in:
    st.markdown('<p class="welcome-icon" style="text-align:center;">🦉</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-title" style="text-align:center;">News Summarizer</p>', unsafe_allow_html=True)
    st.markdown('<p class="app-subtitle" style="text-align:center;">Sign in to start chatting with your news</p>', unsafe_allow_html=True)

    # Google login button - sirf tab dikhega jab secrets.toml mein [auth] configured ho
    try:
        st.button("🔵 Continue with Google", use_container_width=True,
                   on_click=lambda: st.login("google"))
        st.markdown('<p style="text-align:center; color:#94A3B8; font-size:0.8rem;">or</p>',
                    unsafe_allow_html=True)
    except Exception:
        pass

    login_tab, signup_tab = st.tabs(["Log In", "Sign Up"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log In", use_container_width=True, type="primary")
            if submitted:
                success, message = auth.login(login_email, login_password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_email.strip().lower()
                    st.session_state.login_method = "email"
                    st.rerun()
                else:
                    st.error(message)

    with signup_tab:
        with st.form("signup_form"):
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password",
                                             help="At least 6 characters")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
            if submitted:
                if signup_password != signup_confirm:
                    st.error("Passwords do not match.")
                else:
                    success, message = auth.signup(signup_email, signup_password)
                    if success:
                        st.success(message + " Please log in from the 'Log In' tab.")
                    else:
                        st.error(message)

    st.stop()  # App yahin ruk jaata hai - login ke bina neeche ka code chalega hi nahi


# ---------------- CACHING ----------------
@st.cache_resource(show_spinner=False)
def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def generate_dynamic_suggestions(articles, num=3):
    """Fetched articles ke asli headlines se fresh suggestion questions banata hai."""
    if not articles:
        return []
    sample = random.sample(articles, min(num, len(articles)))
    suggestions = []
    for art in sample:
        title = art["title"].strip()
        if len(title) > 70:
            title = title[:67] + "..."
        suggestions.append(f"Tell me more about: {title}")
    return suggestions


def make_session_title(first_message):
    """Pehle sawaal se chat session ka short title banata hai (jaise ChatGPT karta hai)."""
    title = first_message.strip()
    if len(title) > 40:
        title = title[:37] + "..."
    return title


# ---------------- SESSION STATE ----------------
if "rag_store" not in st.session_state:
    with st.spinner("Loading..."):
        model = load_embedding_model()
    st.session_state.rag_store = NewsRAGStore(model=model)
if "news_loaded" not in st.session_state:
    st.session_state.news_loaded = False
if "suggestions" not in st.session_state:
    st.session_state.suggestions = []

if "sessions" not in st.session_state:
    first_id = str(uuid.uuid4())
    st.session_state.sessions = {
        first_id: {"title": DEFAULT_SESSION_TITLE, "messages": [], "created": datetime.now()}
    }
    st.session_state.current_session_id = first_id


def do_fetch_news(feeds):
    with st.spinner("Fetching latest news..."):
        articles, errors = fetch_articles(feeds, limit_per_feed=15)
        if articles:
            st.session_state.rag_store.build_index(articles)
            st.session_state.news_loaded = True
            st.session_state.article_count = len(articles)
            st.session_state.last_fetch_time = datetime.now().strftime("%I:%M %p")
            st.session_state.raw_articles = articles
            st.session_state.suggestions = generate_dynamic_suggestions(articles)
        else:
            st.error("Could not fetch any articles. All sources failed.")
        st.session_state.last_fetch_errors = errors


def start_new_chat():
    new_id = str(uuid.uuid4())
    st.session_state.sessions[new_id] = {
        "title": DEFAULT_SESSION_TITLE, "messages": [], "created": datetime.now()
    }
    st.session_state.current_session_id = new_id
    if st.session_state.news_loaded:
        st.session_state.suggestions = generate_dynamic_suggestions(
            st.session_state.get("raw_articles", []))


current = st.session_state.sessions[st.session_state.current_session_id]

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("### 🦉 News Summarizer")
    st.caption(f"👤 {st.session_state.user_email}")
    if st.button("🚪 Log out", use_container_width=True):
        if st.session_state.get("login_method") == "google":
            st.logout()
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.rerun()

    # Gemini key - check environment variable (local .env) AND st.secrets
    # (Streamlit Cloud secrets), taaki chahe kahin bhi set ki ho, mil jaaye
    saved_key = os.environ.get("GEMINI_API_KEY", "")
    if not saved_key:
        try:
            saved_key = st.secrets.get("GEMINI_API_KEY", "")
        except Exception:
            saved_key = ""

    if saved_key:
        api_key = saved_key
    else:
        api_key = st.text_input("Gemini API Key", type="password",
                                 help="aistudio.google.com/apikey")

    if st.button("✏️  New chat", use_container_width=True, type="primary"):
        start_new_chat()
        st.rerun()

    if st.button("🔄  Refresh news", use_container_width=True):
        do_fetch_news(list(RSS_FEEDS.keys()))

    if st.session_state.news_loaded:
        st.caption(f"{st.session_state.get('article_count', 0)} articles • updated {st.session_state.last_fetch_time}")

    if st.session_state.get("last_fetch_errors"):
        with st.expander(f"⚠️ {len(st.session_state.last_fetch_errors)} source(s) had issues"):
            for err in st.session_state.last_fetch_errors:
                st.caption(f"• {err}")

    # ---- Chat History List ----
    st.markdown('<p class="sidebar-section-label">Recent</p>', unsafe_allow_html=True)
    sorted_sessions = sorted(
        st.session_state.sessions.items(),
        key=lambda x: x[1]["created"], reverse=True
    )
    for sid, sdata in sorted_sessions:
        is_active = sid == st.session_state.current_session_id
        label = f"💬  {sdata['title']}"
        if st.button(label, key=f"hist_{sid}", use_container_width=True,
                     type="primary" if is_active else "secondary"):
            st.session_state.current_session_id = sid
            st.rerun()

    # ---- news sources ab hardcoded/default hain, koi separate UI nahi ----

# Auto-fetch on first load if API key already available
if not st.session_state.news_loaded and saved_key:
    do_fetch_news(list(RSS_FEEDS.keys()))

# ---------------- MAIN AREA ----------------
if not current["messages"]:
    st.markdown('<p class="welcome-icon">🦉</p>', unsafe_allow_html=True)
st.markdown('<p class="app-title">News Summarizer</p>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Ask me anything about today\'s news</p>', unsafe_allow_html=True)

if not st.session_state.news_loaded:
    st.info("Click **Refresh news** in the sidebar to get started.")
else:
    if not current["messages"] and st.session_state.suggestions:
        for q in st.session_state.suggestions:
            if st.button(q, use_container_width=True, key=f"sugg_{q}"):
                st.session_state.pending_query = q
                st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

    for msg in current["messages"]:
        avatar = "🧑" if msg["role"] == "user" else "🦉"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if "time" in msg:
                st.markdown(f'<p class="msg-time">{msg["time"]}</p>', unsafe_allow_html=True)

    user_query = st.chat_input("Ask about the news...")
    if "pending_query" in st.session_state:
        user_query = st.session_state.pop("pending_query")

    if user_query:
        if not api_key:
            st.error("Add your Gemini API key in the sidebar first.")
        else:
            now_str = datetime.now().strftime("%I:%M %p")

            if not current["messages"]:
                current["title"] = make_session_title(user_query)

            current["messages"].append({"role": "user", "content": user_query, "time": now_str})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_query)
                st.markdown(f'<p class="msg-time">{now_str}</p>', unsafe_allow_html=True)

            with st.chat_message("assistant", avatar="🦉"):
                placeholder = st.empty()
                placeholder.markdown(
                    '<span class="thinking-dots">Thinking<span>.</span><span>.</span><span>.</span></span>',
                    unsafe_allow_html=True
                )
                retrieved = st.session_state.rag_store.retrieve(user_query, top_k=5)
                answer = generate_answer(
                    user_query, retrieved, api_key,
                    chat_history=current["messages"][:-1]
                )
                placeholder.empty()
                st.markdown(answer)

                if retrieved:
                    with st.expander("Sources"):
                        seen = set()
                        for chunk in retrieved:
                            title = chunk["metadata"]["title"]
                            link = chunk["metadata"]["link"]
                            source = chunk["metadata"]["source"]
                            score = chunk["score"]
                            if title not in seen:
                                st.markdown(
                                    f'<span class="source-tag">{source}</span> '
                                    f'<span class="score-tag">{score}% match</span><br>'
                                    f'[{title}]({link})',
                                    unsafe_allow_html=True
                                )
                                seen.add(title)

            current["messages"].append({
                "role": "assistant", "content": answer,
                "time": datetime.now().strftime("%I:%M %p")
            })
            st.rerun()
