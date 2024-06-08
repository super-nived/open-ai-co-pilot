// Define the appList object
window.appList = {
  dataInterface: "Data Interface",
  digitalProductPassport: "Digital Passport",
  userAuthentication: "User Authentication",
  inventoryManagement: "Inventory Management",
  orderProcessing: "Order Processing",
  customerSupport: "Customer Support",
  analyticsDashboard: "Analytics Dashboard",
  paymentGateway: "Payment Gateway",
  shippingLogistics: "Shipping & Logistics",
  productCatalog: "Product Catalog",
  marketingTools: "Marketing Tools",
  reportingModule: "Reporting Module"
};

// Function to generate a list of app names with different colors
function generateAppList() {
  const appListDiv = document.createElement("div");
  appListDiv.className = "app-list";

  const colors = [
      "rgba(255, 87, 51, 0.7)", "rgba(51, 255, 87, 0.7)", "rgba(51, 87, 255, 0.7)",
      "rgba(243, 51, 255, 0.7)", "rgba(255, 51, 128, 0.7)", "rgba(51, 255, 243, 0.7)",
      "rgba(255, 199, 51, 0.7)", "rgba(255, 87, 51, 0.7)", "rgba(175, 51, 255, 0.7)",
      "rgba(51, 255, 175, 0.7)", "rgba(255, 51, 51, 0.7)", "rgba(51, 51, 255, 0.7)"
  ];

  let colorIndex = 0;

  for (const key in window.appList) {
      const appItem = document.createElement("div");
      appItem.className = "chat bot";
      appItem.style.backgroundColor = colors[colorIndex % colors.length];
      appItem.style.color = "white";
      appItem.style.padding = "10px";
      appItem.style.borderRadius = "5px";
      appItem.style.marginBottom = "10px";
      appItem.style.opacity = "0.9";
      appItem.innerText = window.appList[key];
      appItem.onclick = function() { showOptionsModal(key); };
      appListDiv.appendChild(appItem);
      colorIndex++;
  }

  const initialBotMessage = document.querySelector(".chat.response");
  initialBotMessage.appendChild(appListDiv);
}

// Function to show options modal
function showOptionsModal(appName) {
  const modal = document.getElementById('optionsModal');
  const shortExplainButton = document.getElementById('shortExplainButton');
  const detailedExplainButton = document.getElementById('detailedExplainButton');

  shortExplainButton.onclick = function() { 
    sendExplanationRequest(appName, "short");
    closeModal();
  };
  detailedExplainButton.onclick = function() { 
    sendExplanationRequest(appName, "detailed");
    closeModal();
  };

  modal.style.display = 'block';
}

// Function to send the explanation request
function sendExplanationRequest(appName, explainType) {
  const formData = new FormData();
  formData.append('appname', appName);
  formData.append('explaintype', explainType);

  const fullUrl = `${baseUrl}/appdetail`;

  fetch(fullUrl, {
      method: 'POST',
      body: formData,
  })
  .then(response => response.json())
  .then(data => {
      appendResponseMessage(data.message);
  })
  .catch(error => {
      appendResponseMessage(error.message);
      console.error('There was a problem with the fetch operation:', error);
  });
}

// Ensure the DOM is fully loaded before running the function
document.addEventListener("DOMContentLoaded", function() {
  generateAppList();
});

// Function to close the modal
function closeModal() {
  document.getElementById('optionsModal').style.display = 'none';
}

// Common variables
const messageBar = document.querySelector(".bar-wrapper input[type='text']");
const sendBtn = document.querySelector(".bar-wrapper button");
const messageBox = document.querySelector(".message-box");
const baseUrl = window.location.href; // Get the base URL dynamically

// Define the getPlatformContext function
window.getPlatformContext = () => {
  // Example data
  return {
    auth_token: "example_token",
    euser: "example_user",
    plant_code: "example_plant",
    company_code: "example_company"
  };
};

// Another function that uses the data from getPlatformContext
function usePlatformContext() {
  const context = window.getPlatformContext();

  console.log('Auth Token:', context.auth_token);
  console.log('Euser:', context.euser);
  console.log('Plant Code:', context.plant_code);
  console.log('Company Code:', context.company_code);

  // You can use the data as needed in your function
  // For example, you might want to return or process the data
  return context;
}

// Call the function to see the output
usePlatformContext();

sendBtn.onclick = sendMessage;

// Event listener for the "Enter" key press on the message bar
messageBar.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        event.preventDefault(); // Prevent the default action (form submission)
        sendMessage(); // Call the sendMessage function
    }
});

// Function to send a message
function sendMessage() {
    const userInput = messageBar.value.trim();
    if (userInput === "") {
        return; // Exit if the input is empty
    }
    const formData = new FormData();
    formData.append('query', userInput);
    appendMessage(userInput, 'user'); // Append the user's message immediately
    toggleLoading(true); // Show loading indicator

    const fullUrl = `${baseUrl}/query_data`;

    fetch(fullUrl, {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        toggleLoading(false); // Hide loading indicator
        return response.json();
    })
    .then(data => {
        appendResponseMessage(data.message); // Append the server's response
    })
    .catch(error => {
        toggleLoading(false); 
        appendResponseMessage(error.message);// Ensure loading indicator is hidden in case of an error
        console.error('There was a problem with the fetch operation:', error);
    });
    messageBar.value = ''; // Clear input field
}

// Function to upload a file
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

    const fullUrl = `${baseUrl}/post_data`;

    fetch(fullUrl, {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        toggleLoading(false);
        return response.json();
    })
    .then(data => {
        appendResponseMessage(data.message);
    })
    .catch(error => {
        appendResponseMessage(error.message);
        console.error('There was a problem with the file upload:', error);
        appendMessage(error.message, 'bot');
    });
}

// Function to append a message
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

// Function to append a response message
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

// Function to parse message content
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

// Function to toggle loading indicator
function toggleLoading(show) {
    if (show) {
        // Show loading indicator with bot image
        let response = `
            <div class="chat response loading">
                <img id="robot" src="/static/images/chatbot.jpg">
                <div class="bubble-wave">
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

// Function to end chat
function endChat() {
    const fullUrl = `${baseUrl}/end_query`;

    fetch(fullUrl, {
        method: 'GET'
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        appendResponseMessage(data.message);
    })
    .catch(error => {
        console.log('There was a problem with the fetch operation:', error);
        appendMessage(error.message, 'bot');
    });
}

// Modal functions
function showModal() {
  document.getElementById('authModal').style.display = 'block';
  showLoginForm(); // Show login form by default when modal opens
}

function closeModal() {
  document.getElementById('authModal').style.display = 'none';
}

window.onclick = function(event) {
  let modal = document.getElementById('authModal');
  if (event.target == modal) {
    closeModal();
  }
}

document.querySelector('.close').onclick = function() {
  closeModal();
}

function showLoginForm() {
  document.getElementById('Login').style.display = 'block';
  document.getElementById('Register').style.display = 'none';
}

function showRegisterForm() {
  document.getElementById('Login').style.display = 'none';
  document.getElementById('Register').style.display = 'block';
}

function loginUser() {
  // Collect login data from input fields
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;

  if (!username || !password) {
    alert("Both username and password are required.");
    return;
  }

  // Send a POST request to the server
  fetch('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
    appendMessage(data.message, 'bot'); // Success message
      closeModal();  // Assuming there's a function to close the modal
    } 
  })
  .catch(error => {
    console.error('Error:', error);
    appendMessage(error.message, 'bot');
  });
}

function registerUser() {
  // Collect registration data from input fields
  const username = document.getElementById('registerUsername').value;
  const password = document.getElementById('registerPassword').value;

  if (!username || !password) {
    alert("Both username and password are required.");
    return;
  }

  // Send a POST request to the server
  fetch('/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
        appendMessage(data.message, 'bot');  // Success message
      closeModal();  // Close the modal on successful registration
    } else {
      alert(data.error);  // Show error message
    }
  })
  .catch(error => {
    console.error('Error:', error);
    appendMessage(error.message, 'bot');
  });
}
