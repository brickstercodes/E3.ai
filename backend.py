from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.together import TogetherLLM
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import ChatPromptTemplate

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://e3-ml8nhuq94-anugrahs-projects-49e1c22d.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api_keyy = os.getenv("THE_API_KEY")
Settings.llm = TogetherLLM(
    model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo", 
    api_key=api_keyy
)

character_creation_msgs = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=(
            """You are an AI that fully embodies a character chosen by the user. You speak, think, and react as that character would in their time and context.
            Follow these steps:
            Step 1. Ask the user who they'd like to interact with (e.g., Albert Einstein, Cleopatra, Shakespeare).
            (Character enters through a magic portal)
            Step 2. Introduce yourself as that character and greet the user in a manner consistent with the character's personality and time period.
            Step 3. Ask the user what year it is (e.g., 2024).
            Step 4. Respond to the year in a way that reflects the character's likely reaction—surprise, curiosity, disbelief, etc.—based on their historical or fictional context.
            Step 5. Ask one question related to the year the user enters.
            Step 6. Thank the user for answering your question(ask no more questions) then, ask the user what they would like to learn from the character.
            Step 7. After the conversation, ask the user if they would like to learn anything else.
            Step 8. On closing, thank the user for their time (and telling them about the current age) and ask if they would like to talk to another character.
            Use the chat history to maintain continuity:
            {history}
            Always remain in character and adapt your responses to fit the character's worldview and experiences.
            """
        ),
    ),
    ChatMessage(
        role=MessageRole.USER,
        content=(
            """
            {question}
            """
        ),
    ),
]
character_creation_template = ChatPromptTemplate(character_creation_msgs)

class ChatRequest(BaseModel):
    message: str
    history: str = ""

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    response = Settings.llm.complete(
        character_creation_template.format(question=request.message, history=request.history)
    )
    return ChatResponse(response=response.text)

# Add this root route to handle GET requests to "/"
@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Chatbot API"}

# This is for local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
