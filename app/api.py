from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
from main import initialize_contexi
from rag import perform_cgrag
from app.utils import load_config

app = FastAPI()

config = load_config()
default_chain_type = config.get('llm_chain', {}).get('default', 'fast')

class QueryRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str


@app.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QueryRequest, chain_type: Literal["smart", "fast"] = default_chain_type):
    query = request.question
    if not query:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Initialize the components if not already done
    if not hasattr(app.state, 'retriever') or not hasattr(app.state, 'llm'):
        # You might want to get these values from configuration or environment variables
        code_path = "/Users/satyendrak/Desktop/new-sem/dealservice/"
        is_git_repo = False
        app.state.retriever, app.state.llm, _, _ = initialize_contexi(code_path, is_git_repo, chain_type)

    answer, _ = perform_cgrag(query, app.state.retriever, app.state.llm, chain_type=chain_type)

    return AnswerResponse(answer=answer)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)