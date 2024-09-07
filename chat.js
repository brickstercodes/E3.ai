const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const chatResponse = document.getElementById('chatResponse');

let socket;

function connectWebSocket() {
    socket = new WebSocket('wss://e3-ai.onrender.com/ws/chat');

    socket.onopen = function(e) {
        console.log("Connection established");
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.delta) {
            chatResponse.innerHTML += data.delta;
        }
    };

    socket.onclose = function(event) {
        if (event.wasClean) {
            console.log(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
            console.log('Connection died');
            setTimeout(connectWebSocket, 5000); // Try to reconnect after 5 seconds
        }
    };

    socket.onerror = function(error) {
        console.log(`WebSocket Error: ${error.message}`);
    };
}

connectWebSocket();

chatForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const message = userInput.value;
    if (message.trim() !== '') {
        socket.send(JSON.stringify({message: message}));
        userInput.value = '';
        chatResponse.innerHTML += `<p><strong>You:</strong> ${message}</p>`;
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
