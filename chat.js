const socket = new WebSocket("wss://e3-ai.onrender.com/ws/chat");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const chatResponse = document.getElementById("chatResponse");

// WebSocket connection established
socket.onopen = function () {
  console.log("[open] Connection established");
  chatResponse.innerHTML +=
    "<p class='system-message'>e3.ai is here! Say hi.</p>";
};

// WebSocket message handling
socket.onmessage = function (event) {
  const data = JSON.parse(event.data);
  if (data.delta) {
    // Sanitize and format the delta response
    const formattedResponse = data.delta.replace(/\s+/g, " "); // Normalize whitespace

    chatResponse.innerHTML += `<p class="ai-response">${formattedResponse}</p>`;
  } else if (data.complete) {
    chatResponse.innerHTML += `<br />`; // Add a line break after complete response
  }
  chatResponse.scrollTop = chatResponse.scrollHeight; // Auto-scroll to bottom
};

// Handling form submission (sending user's message)
chatForm.addEventListener("submit", function (e) {
  e.preventDefault();
  if (socket.readyState === WebSocket.OPEN) {
    const userMessage = userInput.value.trim();
    if (userMessage) {
      // Sanitize the user message
      const sanitizedUserMessage = userMessage
        .replace(/</g, "&lt;") // Escape '<'
        .replace(/>/g, "&gt;") // Escape '>'
        .replace(/&/g, "&amp;"); // Escape '&'

      // Append user's message to the chat
      chatResponse.innerHTML += `<p class="user-message">You: ${sanitizedUserMessage}</p>`;
      socket.send(JSON.stringify({ message: userMessage }));
      userInput.value = ""; // Clear input after sending
    }
  } else {
    chatResponse.innerHTML += `<p class="error-message">Connection is not open. Please try again later.</p>`;
  }
});

// WebSocket close event
socket.onclose = function (event) {
  if (event.wasClean) {
    console.log(
      `[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`
    );
  } else {
    console.log("[close] Connection died");
  }
  chatResponse.innerHTML +=
    "<p class='system-message'>Disconnected from the chatbot.</p>";
};

// WebSocket error event
socket.onerror = function (error) {
  console.log(`[error] ${error.message}`);
  chatResponse.innerHTML += `<p class="error-message">Error: ${error.message}</p>`;
};
