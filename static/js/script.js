

const messageBar = document.querySelector(".bar-wrapper input[type='text']");
const sendBtn = document.querySelector(".bar-wrapper button");
const messageBox = document.querySelector(".message-box");

sendBtn.onclick = sendMessage;

function sendMessage() {
    const userInput = messageBar.value.trim();
    if (userInput === "") {
        return; // Exit if the input is empty
    }
    const formData = new FormData();
    formData.append('query', userInput);
    toggleLoading(true); // Show loading indicator
    fetch('https://open-ai-co-pilot.onrender.com/query_data', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        toggleLoading(false); // Hide loading indicator
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        appendMessage(userInput, 'user'); // Append the user's message
        appendResponseMessage(data.message); // Append the server's response
    })
    .catch(error => {
        toggleLoading(false); // Ensure loading indicator is hidden in case of an error
        console.error('There was a problem with the fetch operation:', error);
    });
    messageBar.value = ''; // Clear input field
}

function uploadFile() {
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file) {
        appendMessage('No file selected for upload.', 'bot');
        return;
    }
    const formData = new FormData();
    formData.append('file', file);
    toggleLoading(true);
    fetch('https://open-ai-co-pilot.onrender.com/post_data', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        toggleLoading(false);
        if (!response.ok) throw new Error('File upload failed: ' + response.statusText);
        return response.json();
    })
    .then(data => {
        appendResponseMessage(data.message);
    })
    .catch(error => {
        console.error('There was a problem with the file upload:', error);
        appendMessage(error.message, 'bot');
    });
}

function appendMessage(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "chat " + sender;
    const messageText = document.createElement("span");
    messageText.className = "message-text";
    messageText.innerText = message;
    messageDiv.appendChild(messageText);
    messageBox.appendChild(messageDiv);
    messageBox.scrollTop = messageBox.scrollHeight;
}

function appendResponseMessage(message) {
    const messageDiv = document.createElement("div");
    messageDiv.className = "chat bot";
    
    const parsedMessage = parseMessageContent(message);

    if (parsedMessage.length === 0) {
        const messageText = document.createElement("span");
        messageText.className = "message-text";
        messageText.innerText = message;
        messageDiv.appendChild(messageText);
    } else {
        parsedMessage.forEach(content => {
            if (typeof content === 'string') {
                // Skip text content if there are media elements
            } else {
                messageDiv.appendChild(content);
            }
        });
    }

    messageBox.appendChild(messageDiv);
    messageBox.scrollTop = messageBox.scrollHeight;
}

function parseMessageContent(message) {
    const mediaRegex = /{\s*"(link|image|video|pdf)"\s*:\s*"([^"]+)"\s*}/g;
    const contents = [];
    let lastIndex = 0;
    let match;

    while ((match = mediaRegex.exec(message)) !== null) {
        if (match.index > lastIndex) {
            // Skip non-media text content
        }
        lastIndex = mediaRegex.lastIndex;

        const mediaType = match[1];
        const mediaUrl = match[2];
        if (mediaType === 'image' || (mediaType === 'link' && /\.(jpg|jpeg|png|gif)$/i.test(mediaUrl))) {
            const img = document.createElement("img");
            img.src = mediaUrl;
            img.alt = "Image";
            contents.push(img);
        } else if (mediaType === 'video' || (mediaType === 'link' && /\.(mp4|webm)$/i.test(mediaUrl))) {
            const video = document.createElement("video");
            video.src = mediaUrl;
            video.controls = true;
            contents.push(video);
        } else if (mediaType === 'pdf' || (mediaType === 'link' && /\.pdf$/i.test(mediaUrl))) {
            const link = document.createElement("a");
            link.href = mediaUrl;
            link.innerText = "Download PDF";
            link.target = "_blank";
            link.className = "pdf-link";
            contents.push(link);
        } else if (/youtube\.com\/watch\?v=/.test(mediaUrl) || /youtu\.be\//.test(mediaUrl)) {
            const iframe = document.createElement("iframe");
            iframe.src = mediaUrl.replace("watch?v=", "embed/");
            iframe.width = "560";
            iframe.height = "315";
            iframe.frameBorder = "0";
            iframe.allowFullscreen = true;
            contents.push(iframe);
        }
    }

    if (lastIndex < message.length) {
        // Skip remaining non-media text content
    }

    return contents;
}

function toggleLoading(show) {
    if (show) {
        // Show loading indicator with bot image
        let response = `
            <div class="chat response loading">
                <img src="/static/images/chatbot.jpg">
                <div class="bubble-wave">
                    <div class="bubble"></div>
                    <div class="bubble"></div>
                    <div class="bubble"></div>
                </div>
            </div>`;
        messageBox.insertAdjacentHTML("beforeend", response);
        messageBox.scrollTop = messageBox.scrollHeight; // Scroll to the bottom
    } else {
        // Hide loading indicator
        const loadingResponse = document.querySelector(".chat.response.loading");
        if (loadingResponse) {
            loadingResponse.remove();
        }
    }
}

function endChat() {
    fetch('https://open-ai-co-pilot.onrender.com/end_chat', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        appendResponseMessage(data.message);
    })
    .catch(error => {
        console.log('There was a problem with the fetch operation:', error);
        appendResponseMessage('error Chat ended and resources cleaned up.');
    });
}
