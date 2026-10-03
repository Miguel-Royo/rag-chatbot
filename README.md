# Babson Handbook RAG Chatbot

OIM3641 – Activity 10. A Streamlit chatbot that answers questions about the Babson student handbook using RAG (LlamaIndex + Gemini).

**Run it:** `uv sync`, add `GEMINI_API_KEY=your-key` to a `.env` file, then `uv run streamlit run app.py`

## Results

| Question | My chatbot | Claude |
|---|---|---|
| Can I get credit for courses taken somewhere else? | Correct: 12/16 credit limit, C or better, transcript required | Correct and more detailed |
| Are any interest-free loans offered? | Correct: Mass No Interest Loan | Correct, plus federal subsidized loans |
| What if I'm a transfer student? (follow-up) | "No information": ignored the earlier questions | Understood the follow-up, explained transfer rules |

**My chatbot**

![Transfer credit](screenshots/1-bot-transfer-credit.png)
![Loans](screenshots/2-bot-loans.png)
![Follow-up](screenshots/3-bot-followup.png)

**Claude**

![Transfer credit](screenshots/4-claude-transfer-credit.png)
![Loans](screenshots/5-claude-loans.png)
![Follow-up](screenshots/6-claude-followup.png)

## Observations

- My chatbot gave accurate, Babson-specific answers because it reads the actual handbook. Claude gave even fuller answers because it had the handbook and read more of it. My bot only uses the 2 most relevant chunks.
- The follow-up question failed on my chatbot. It treated "What if I'm a transfer student?" as a brand-new question.
- Problems I had to fix: the PDF wasn't being read until I installed `llama-index-readers-file`, and `gemini-2.5-flash` was no longer available to new API keys, so I switched to `gemini-3.8-flash`.

## Memory

LLMs don't actually remember anything. Chat apps like Claude or ChatGPT re-send the whole conversation with every new message, so the model "sees" the history each time. When a chat gets too long, older parts get cut or summarized.

My chatbot has **no memory**. It saves the messages only to display them on screen. Each question goes to Gemini by itself, which is why the follow-up failed.
