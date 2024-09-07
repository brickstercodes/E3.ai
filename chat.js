const socket = new WebSocket("wss://e3-ai.onrender.com/ws/chat");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");
const chatResponse = document.getElementById("chatResponse");

socket.onopen = function (e) {
  console.log("[open] Connection established");
  chatResponse.innerText += "Connected to the chatbot.\n";
};

socket.onmessage = function (event) {
  const data = JSON.parse(event.data);
  if (data.delta) {
    chatResponse.innerText += data.delta;
  } else if (data.complete) {
    chatResponse.innerText += "\n\n";
  }
};

socket.onclose = function (event) {
  if (event.wasClean) {
    console.log(
      `[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`
    );
  } else {
    console.log("[close] Connection died");
  }
  chatResponse.innerText += "Disconnected from the chatbot.\n";
};

socket.onerror = function (error) {
  console.log(`[error] ${error.message}`);
  chatResponse.innerText += `Error: ${error.message}\n`;
};

chatForm.addEventListener("submit", function (e) {
  e.preventDefault();
  if (socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ message: userInput.value }));
    chatResponse.innerText += `You: ${userInput.value}\n`;
    userInput.value = "";
  } else {
    chatResponse.innerText +=
      "Connection is not open. Please try again later.\n";
  }
});

// Add click event listeners to the option divs
document.querySelector('.option1').addEventListener('click', function() {
    userInput.value = this.textContent.trim();
    chatForm.dispatchEvent(new Event('submit'));
});

document.querySelector('.option2').addEventListener('click', function() {
    userInput.value = this.textContent.trim();
    chatForm.dispatchEvent(new Event('submit'));
});

document.querySelector('.option3').addEventListener('click', function() {
    userInput.value = this.textContent.trim();
    chatForm.dispatchEvent(new Event('submit'));
});
