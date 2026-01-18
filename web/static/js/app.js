const socket = io();
const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const micStatus = document.getElementById('mic-status');
const micHub = document.querySelector('.mic-hub');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('start-btn');
const voiceToggle = document.getElementById('voice-toggle');
const speakerOn = document.getElementById('speaker-on');
const speakerOff = document.getElementById('speaker-off');

let voiceEnabled = true;

// Toggle Voice
voiceToggle.addEventListener('click', () => {
    voiceEnabled = !voiceEnabled;
    speakerOn.classList.toggle('hidden');
    speakerOff.classList.toggle('hidden');
});

// UI: Add Message
function addMessage(text, sender) {
    if (!text || text === "...") return;
    const div = document.createElement('div');
    div.classList.add('msg', sender);
    div.innerText = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Audio: Play
function playAudio(hexString) {
    if (!hexString || !voiceEnabled) return;
    const byteArray = new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    const blob = new Blob([byteArray], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
}

// Socket Response
socket.on('assistant_response', (data) => {
    // Reset Mic UI
    micHub.classList.remove('mic-active');
    micStatus.innerText = "Tap to speak";
    micBtn.disabled = false;
    userInput.disabled = false;

    if (data.user_said) addMessage(data.user_said, 'user');
    addMessage(data.response, 'assistant');
    playAudio(data.audio);
});

// Start Overlay
startBtn.addEventListener('click', () => {
    overlay.style.opacity = '0';
    setTimeout(() => {
        overlay.style.display = 'none';
        socket.emit('request_greeting');
    }, 500);
});

// Actions
function handleChat() {
    const text = userInput.value.trim();
    if (!text) return;
    addMessage(text, 'user');
    userInput.value = '';
    socket.emit('send_message', { message: text });
}

function handleVoice() {
    // Set UI to Listening mode
    micHub.classList.add('mic-active');
    micStatus.innerText = "Listening...";
    micBtn.disabled = true;
    userInput.disabled = true;
    
    socket.emit('start_voice');
}

sendBtn.addEventListener('click', handleChat);
userInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') handleChat(); });
micBtn.addEventListener('click', handleVoice);