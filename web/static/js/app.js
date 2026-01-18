const chatWindow = document.getElementById('chat-window');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const overlay = document.getElementById('overlay');
const startBtn = document.getElementById('start-btn');
const voiceToggle = document.getElementById('voice-toggle');
const speakerOn = document.getElementById('speaker-on');
const speakerOff = document.getElementById('speaker-off');

let voiceEnabled = true;

// Toggle Voice Output
voiceToggle.addEventListener('click', () => {
    voiceEnabled = !voiceEnabled;
    speakerOn.classList.toggle('hidden');
    speakerOff.classList.toggle('hidden');
    console.log("Voice Output Enabled:", voiceEnabled);
});

function addMessage(text, sender) {
    if (!text) return;
    const div = document.createElement('div');
    div.classList.add('msg', sender);
    div.innerText = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function playAudio(hexString) {
    // TRIGGER: Only play if voice is enabled on UI
    if (!hexString || !voiceEnabled) return;
    
    const byteArray = new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
    const blob = new Blob([byteArray], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
}

async function handleChat(text) {
    if (!text) return;
    addMessage(text, 'user');
    userInput.value = '';
    
    const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
    });
    const data = await res.json();
    addMessage(data.response, 'assistant');
    playAudio(data.audio);
}

async function startConcierge() {
    overlay.style.display = 'none';
    const res = await fetch('/get_greeting');
    const data = await res.json();
    addMessage(data.response, 'assistant');
    playAudio(data.audio);
}

async function handleVoice() {
    micBtn.style.color = "#ff4b4b";
    const res = await fetch('/voice', { method: 'POST' });
    const data = await res.json();
    
    if (data.user_said && data.user_said !== "...") {
        addMessage(data.user_said, 'user');
        addMessage(data.response, 'assistant');
        playAudio(data.audio);
    }
    micBtn.style.color = "";
}

startBtn.addEventListener('click', startConcierge);
sendBtn.addEventListener('click', () => handleChat(userInput.value.trim()));
userInput.addEventListener('keypress', (e) => { if(e.key === 'Enter') handleChat(userInput.value.trim()); });
micBtn.addEventListener('click', handleVoice);