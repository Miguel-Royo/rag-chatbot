"""Babson Handbook Chatbot: a Streamlit RAG app built on LlamaIndex and Gemini."""

import os
from pathlib import Path

import httpx
import streamlit as st
from dotenv import load_dotenv
from google.genai import errors as genai_errors
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI

# --- Configuration ---
load_dotenv()
DATA_DIR = Path("data") / "handbook"
LLM_MODEL = "gemini-3.8-flash"
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


# --- Fail-fast checks: the app can't do its job if these fail ---
def get_api_key():
    """Return the Gemini API key from .env, or stop the app with a message on how to fix it."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        st.error(
            "**GEMINI_API_KEY not found.** Open the `.env` file next to `app.py` and add a line "
            "like `GEMINI_API_KEY=your-key-here` (spelled exactly like that), then restart the app."
        )
        st.stop()
    return api_key


def check_data_dir():
    """Make sure DATA_DIR is a folder with at least one visible file, or stop the app."""
    if not DATA_DIR.is_dir():
        st.error(
            f"**Handbook folder not found.** The app expected a folder at `{DATA_DIR}` "
            f"(full path: `{DATA_DIR.resolve()}`). Create it and put the handbook PDF inside."
        )
        st.stop()

    # Hidden files like .DS_Store don't count: LlamaIndex skips them too.
    visible_files = [f for f in DATA_DIR.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not visible_files:
        st.error(
            f"**The `{DATA_DIR}` folder is empty.** Put the student handbook PDF "
            "(or other documents) in it, then restart the app."
        )
        st.stop()


# --- Query engine ---
# st.cache_resource keeps the index in memory across Streamlit reruns,
# so the handbook is indexed once instead of on every question.
@st.cache_resource(show_spinner="Indexing the student handbook...")
def get_query_engine(api_key):
    """Load the handbook, build a vector index, and return a query engine."""
    # Embeddings run locally (free); only the final answer call goes to Gemini.
    Settings.embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    Settings.llm = GoogleGenAI(model=LLM_MODEL, api_key=api_key)

    documents = SimpleDirectoryReader(str(DATA_DIR)).load_data()  # Load
    index = VectorStoreIndex.from_documents(documents, show_progress=True)  # Chunk + embed + index
    return index.as_query_engine()  # Retrieve + synthesize


def answer_question(query_engine, question):
    """Send one question to the engine; on failure show an error and return None."""
    try:
        with st.spinner("Searching the handbook..."):
            # query() returns a Response object; the text is in .response.
            return query_engine.query(question).response
    except genai_errors.ClientError as e:
        if e.code == 429:
            st.error("Gemini's rate limit was hit. Wait a minute, then ask again.")
        else:
            st.error(f"Gemini rejected the request (error {e.code}). Check that your API key is valid.")
    except genai_errors.ServerError:
        st.error("Gemini is having trouble right now. Try your question again in a moment.")
    except (httpx.ConnectError, httpx.TimeoutException):
        st.error("Couldn't reach Gemini. Check your internet connection, then ask again.")
    except Exception as e:
        st.error(f"Something went wrong answering that question: {e}")
    return None


# --- UI ---
st.title("Babson Handbook Chatbot")
st.caption("Ask me anything about the Babson undergraduate student handbook.")

api_key = get_api_key()
check_data_dir()

try:
    query_engine = get_query_engine(api_key)
except ValueError as e:
    st.error(f"**Couldn't read the documents in `{DATA_DIR}`.** {e}")
    st.stop()
except OSError as e:
    st.error(
        "**Couldn't build the search index.** A file may be unreadable, or the embedding model "
        f"couldn't be downloaded (check your internet connection). Details: {e}"
    )
    st.stop()
except Exception as e:
    st.error(f"**Couldn't build the search index.** Details: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Redisplay the conversation so far (Streamlit reruns the script on every input).
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("Ask a question about the handbook"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        answer = answer_question(query_engine, question)  # Fallback: errors don't stop the app
        if answer:
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
