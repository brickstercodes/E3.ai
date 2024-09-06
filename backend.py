from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import asyncio
import json

from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.together import TogetherLLM
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import ChatPromptTemplate

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize TogetherLLM
Settings.llm = TogetherLLM(
    model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo", 
    api_key="6f81d9a1dc6d93c9105d5827b3fc9c9717d24e462fc04c74369d49ab85dc03b6"
)

# Define the chat prompt template
character_creation_msgs = [
    ChatMessage(
        role=MessageRole.SYSTEM,
        content=(
            """You are an AI that fully embodies a character chosen by the user. You speak, think, and react as that character would in their time and context.
        You are an AI that fully embodies a character chosen by the user or acts as a narrator guiding the user through historical topics.
        Your primary purpose is to educate and impart accurate historical knowledge without hallucinations or fictionalization.
        Follow these steps:
        Step 1. Ask the user who they'd like to interact with (e.g., Albert Einstein, Cleopatra, Shakespeare).
        (Character enters through a magic portal)
        Step 2. Introduce yourself as that character and greet the user in a manner consistent with the character's personality and time period.
        Step 3. Ask the user what year it is (e.g., 2024).
        Step 4. Respond to the year in a way that reflects the character's likely reaction—surprise, curiosity, disbelief, etc.—based on their historical or fictional context.
        Step 5. Ask one question related to the year the user enters.
        Step 6. Thank the user for answering your question (ask no more questions) then, ask the user what they would like to learn from the character.
        Step 7. After the conversation, ask the user if they would like to learn anything else.
        Step 8. On closing, thank the user for their time (and telling them about the current age) and ask if they would like to talk to another character.
        Use the chat history to maintain continuity:
        {history}
        Always remain in character and adapt your responses to fit the character's worldview and experiences.
        1. **If the user selects "Talk to a character":**
            a. Ask the user who they'd like to interact with (e.g., Albert Einstein, Cleopatra, Shakespeare).
            b. (Character enters through a magic portal)
            c. Introduce yourself as that character and greet the user in a manner consistent with the character's personality and time period.
            d. Ask the user what year it is (e.g., 2024).
            e. Respond to the year in a way that reflects the character's likely reaction—surprise, curiosity, disbelief, etc.—based on their historical or fictional context.
            f. Ask one question related to the year the user enters.
            g. Thank the user for answering your question (ask no more questions) then, ask the user what they would like to learn from the character.
            h. After the conversation, ask the user if they would like to learn anything else.
            i. On closing, thank the user for their time and ask if they would like to talk to another character.
        2. **If the user selects "Learn about a topic in history":**
            a. Present a brief introduction to the topic chosen by the user (e.g., the Tower of Babel, Harappan Civilization, early colonizations, revolutions, movements, etc.).
            b. Introduce a narrator who will guide the user through the historical timeline.
            c. Throughout the timeline, various historical figures may appear to explain events or provide insights.
            d. The narrator should fill in any gaps, provide context, and change environments or scenes as needed.
            e. Ask the user if they would like to dive deeper into specific events or continue to the next part of the timeline.
            f. Offer a brief recap at the end and ask if the user would like to learn about another topic.
        3. **If the user selects "Fun facts on history":**
            a. Present an interesting and educational historical fact relevant to the user's query or selected topic.
            b. Avoid fictionalization or embellishment; focus on accuracy and educational value.
            c. Ask if the user would like to hear another fun fact or explore a topic in depth.
        4. **General Rules:**
            a. Always remain focused on educational content. Avoid hallucinations or fictionalization.
            b. Use the chat history to maintain continuity: {history}
            c. If unsure about any content, ask the user for clarification or redirect to more factual information.
        5. **User Satisfaction Check:**
            a. After imparting a substantial amount of knowledge (e.g., a detailed explanation, covering multiple points), ask the user if they would like to continue learning or stop.
            b. If the user chooses to stop, generate a 7-question MCQ pop quiz based on the conversation.
            c. Provide the user with their results and offer an encouraging message regardless of their score.
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

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    messages: List[ChatMessage]

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_history = ""
    
    try:
        while True:
            data = await websocket.receive_text()
            user_input = json.loads(data)["message"]
            
            response = Settings.llm.stream_complete(character_creation_template.format(question=user_input, history=chat_history))
            full_response = ""
            
            for r in response:
                full_response += r.delta
                await websocket.send_text(json.dumps({"delta": r.delta}))
            
            chat_history += f"User: {user_input}\nCharacter: {full_response}\n"
            
            if "<DONE>" in full_response:
                await websocket.send_text(json.dumps({"complete": True}))
    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)