# FastAPI RAG Pipeline Chatbot

This is a boilerplate project for a FastAPI-based chatbot using a Retrieval-Augmented Generation (RAG) pipeline with MongoDB, Weaviate, OpenAI, LangChain, and Hugging Face.

## Prerequisites
- Python 3.8+
- MongoDB running locally or remotely
- Weaviate instance running locally or remotely
- OpenAI API key

## Setup

1. Clone this repository:
```bash
git clone <repo-url>
```

2. Navigate to the project directory:
```bash
cd fastapi-rag-pipeline-chatbot
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the FastAPI server:
```bash
uvicorn app.main:app --reload
```

5. Access the API at:
`http://localhost:8000`
