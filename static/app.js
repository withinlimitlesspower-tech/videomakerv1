let currentSessionId = null;

// Load sessions on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSessions();
    document.getElementById('new-chat-btn').addEventListener('click', createNewSession);
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        const sessions = await response.json();
        const list = document.getElementById('chat-list');
        list.innerHTML = '';
        sessions.forEach(session => {
            const li = document.createElement('li');
            li.textContent = session.name;
            li.dataset.id = session.id;
            li.addEventListener('click', () => loadSession(session.id));
            if (currentSessionId === session.id) {
                li.classList.add('active');
            }
            list.appendChild(li);
        });
        // If no session exists, create one
        if (sessions.length === 0) {
            createNewSession();
        } else if (!currentSessionId) {
            // Load the first session
            loadSession(sessions[0].id);
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
    }
}

async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', { method: 'POST' });
        const session = await response.json();
        currentSessionId = session.id;
        document.getElementById('messages').innerHTML = '';
        loadSessions();
    } catch (error) {
        console.error('Error creating session:', error);
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    try {
        const response = await fetch(`/api/sessions/${sessionId}/messages`);
        const messages = await response.json();
        messages.forEach(msg => addMessageToUI(msg.role, msg.content));
        // Update active class in sidebar
        document.querySelectorAll('#chat-list li').forEach(li => {
            li.classList.toggle('active', li.dataset.id == sessionId);
        });
        // Scroll to bottom
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    } catch (error) {
        console.error('Error loading messages:', error);
    }
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    if (!content || !currentSessionId) return;
    input.value = '';
    addMessageToUI('user', content);
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSessionId, content: content })
        });
        if (!response.ok) {
            throw new Error('Failed to send message');
        }
        const data = await response.json();
        addMessageToUI('assistant', data.content);
        // Refresh sidebar to update session name
        loadSessions();
    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToUI('assistant', 'Error: Could not get response');
    }
}

function addMessageToUI(role, content) {
    const messagesDiv = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    // Check if content contains a URL (for video/audio) and make it clickable
    // Simple check: if content contains 'http'
    if (content.includes('http')) {
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        const parts = content.split(urlRegex);
        parts.forEach(part => {
            if (part.match(urlRegex)) {
                // Determine if video or audio based on extension
                const isAudio = part.endsWith('.mp3') || part.endsWith('.wav');
                const isVideo = part.endsWith('.mp4') || part.endsWith('.webm');
                if (isAudio) {
                    const audio = document.createElement('audio');
                    audio.controls = true;
                    audio.src = part;
                    div.appendChild(audio);
                } else if (isVideo) {
                    const video = document.createElement('video');
                    video.controls = true;
                    video.width = 320;
                    video.src = part;
                    div.appendChild(video);
                } else {
                    const link = document.createElement('a');
                    link.href = part;
                    link.target = '_blank';
                    link.textContent = 'Open link';
                    div.appendChild(link);
                }
            } else {
                div.appendChild(document.createTextNode(part));
            }
        });
    } else {
        div.textContent = content;
    }
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
