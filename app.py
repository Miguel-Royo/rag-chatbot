import os

import streamlit as st
from dotenv import load_dotenv
from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.google_genai import GoogleGenAI

# --- Configuration ---
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
DATA_DIR = "data/handbook"

# Embeddings run locally (free); only the final answer call goes to Gemini.
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


# --- Query engine ---
# st.cache_resource keeps the index in memory across Streamlit reruns,
# so the handbook is indexed once instead of on every question.
@st.cache_resource(show_spinner="Indexing the student handbook...")
def get_query_engine():
    """Load the handbook, build a vector index, and return a query engine."""
    if not API_KEY:
        st.error("GEMINI_API_KEY not found. Add it to your .env file.")
        st.stop()

    # Set the LLM here, after the key check (GoogleGenAI errors without a key).
    Settings.llm = GoogleGenAI(model="gemini-3.8-flash", api_key=API_KEY)

    documents = SimpleDirectoryReader(DATA_DIR).load_data()  # Load
    index = VectorStoreIndex.from_documents(documents, show_progress=True)  # Chunk + embed + index
    return index.as_query_engine()  # Retrieve + synthesize


# --- UI ---
st.title("Babson Handbook Chatbot")
st.caption("Ask me anything about the Babson undergraduate student handbook.")

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

    query_engine = get_query_engine()
    with st.chat_message("assistant"):
        with st.spinner("Searching the handbook..."):
            # query() returns a Response object; the text is in .response.
            # Only the current question is sent, not the chat history.
            answer = query_engine.query(question).response
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
