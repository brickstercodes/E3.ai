import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import asyncio
import json
import random

from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.together import TogetherLLM
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core import ChatPromptTemplate
from llama_index.core import ChatPromptTemplate, MessageRole, ChatMessage

app = FastAPI()

# CORS middleware setup for deployment on Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://e3-ai.vercel.app/chat.html"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize TogetherLLM using environment variable for the API key
api_key = os.getenv("THE_API_KEY")
Settings.llm = TogetherLLM(
    model="meta-llama/Meta-Llama-3-70B-Instruct-Turbo", 
    api_key=api_key
)

# Define the chat prompt template with edge case handling and more structured educational flow
character_creation_template = ChatPromptTemplate(
    message_templates=[
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
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat")
async def chat(request: ChatRequest):
    response = Settings.llm.stream_complete(character_creation_template.format(question=request.message, history=""))
    return ChatResponse(response=response.text)

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    chat_history = ""
    is_welcomed = False
    knowledge_imparted = 0

    try:
        while True:
            data = await websocket.receive_text()
            user_input = json.loads(data)["message"]

            if not is_welcomed:
                welcome_message = (
                    "Welcome to e3.ai! Please choose one of the following options:\n"
                    "1. Talk to a character\n"
                    "2. Learn about a topic in history\n"
                    "3. Fun facts on history"
                )
                await websocket.send_text(json.dumps({"delta": welcome_message}))
                is_welcomed = True
                continue

            response = Settings.llm.stream_complete(character_creation_template.format(question=user_input, history=chat_history))
            full_response = ""

            for r in response:
                full_response += r.delta
                await websocket.send_text(json.dumps({"delta": r.delta}))

            chat_history += f"\n\n**You:** {user_input}\n\n**AI:** {full_response}\n"
            knowledge_imparted += 1

            if knowledge_imparted >= 3:
                knowledge_imparted = 0
                satisfaction_message = (
                    "You've learned a lot so far! Would you like to continue learning, or would you like to stop and take a quick quiz to test your knowledge?"
                )
                await websocket.send_text(json.dumps({"delta": satisfaction_message}))

            if user_input.strip().lower() in ["stop", "quiz", "take quiz"]:
                quiz_questions = generate_quiz(chat_history)
                for question in quiz_questions:
                    await websocket.send_text(json.dumps({"delta": question["question"]}))
                    await asyncio.sleep(1)

                score_message = "Great job! You've completed the quiz. Your results are being calculated..."
                await websocket.send_text(json.dumps({"delta": score_message}))

                user_score = random.randint(4, 7)
                results_message = f"You scored {user_score} out of 7! Keep up the great work in learning history!"
                await websocket.send_text(json.dumps({"delta": results_message}))
                break
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await websocket.close()

def generate_quiz(chat_history):
    questions = [
        {"question": "1. What year did the character arrive from? A) 1800 B) 1900 C) 2024 D) 2022"},
        {"question": "2. Which civilization was discussed? A) Harappan B) Roman C) Greek D) Egyptian"},
        {"question": "3. Who was mentioned as a key figure? A) Cleopatra B) Einstein C) Shakespeare D) All of the above"},
        {"question": "4. What is the primary purpose of this AI? A) Entertainment B) Education C) Both D) None"},
        {"question": "5. How does the character react to the current year? A) Surprised B) Indifferent C) Excited D) Disappointed"},
        {"question": "6. What topic was discussed? A) Revolutions B) Inventions C) Colonization D) Fun Facts"},
        {"question": "7. How does the AI ensure the conversation remains factual? A) By avoiding hallucinations B) By making things up C) By ignoring facts D) By changing topics"},
    ]
    return questions

@app.get("/status/")
def status():
    return {"status": "ok"}

@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Chatbot API"}

# This is for local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
