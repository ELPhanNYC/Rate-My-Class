let domain = 'localhost'
let port = '8080'
let socket;

function initWS() {
    // Establish a WebSocket connection with the server
    socket = io.connect(`http://${domain}:${port}`);
    socket.on('connect', () => {
        console.log('WebSocket connection established');
      });
    // Called whenever data is received from the server over the WebSocket connection
    socket.on('response_post', (message) => {
        // Handle the server's response message here
        console.log(message);
        addMessageToChat(message);
    });
}

function sendPost(){
    const ratingElem = document.getElementById("rating-element");
    const formData = {
        professor: document.getElementById('rating-form-prof').value,
        rating: document.getElementById('rating-form-rating').value,
        difficulty: document.getElementById('rating-form-diff').value,
        comments: document.getElementById('rating-form-comments').value,
      };
    // Send the JSON data via WebSocket
    socket.emit('submit_form', formData);
    window.location.replace(`http://${domain}:${port}`);
}


function chatMessageHTML(messageJSON) {
    console.log("chatMessageHTML")
    let messageHTML = styleMessage(messageJSON)
    return messageHTML;
}

function onLike(imgElement) {
    const likesElement = imgElement.previousElementSibling;
    let currentLikes = parseInt(likesElement.innerText);

    likesElement.innerText = currentLikes
    return currentLikes
}


function likePostRequest(imgElement) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            // The request is successful, the likes have already been updated by onLike
            console.log(this.response);
        }
    }
    // Get the post_id from the clicked element
    const post_id = imgElement.id;
    request.open("POST", "/like");
    request.setRequestHeader('Content-Type', 'application/json')
    request.send(JSON.stringify({'post_id': post_id}));
}

function styleMessage(messageJSON) {
    console.log("styleMessage")
    const post_id = messageJSON.post_id;
    const username = messageJSON.username;
    const comments = messageJSON.comments;
    const professor = messageJSON.professor;
    const difficulty = messageJSON.difficulty;
    const rating = messageJSON.rating;
    const likes = messageJSON.likes;
    const likedOrNot = messageJSON.liked;

    if (likedOrNot == true) {
       isLiked = `<img id="${post_id}" onclick="likePostRequest(this)" src="./static/images/thumb-up.png" height="35px">`;
    } 
    else {
        isLiked = `<img id="${post_id}" onclick="likePostRequest(this)" src="./static/images/non-shaded-thumbs-up.png" height="35px">`;
    }

    let card = `
    
    <div class="card">
        <p id='post_id'>${post_id}</p>
        <div class = "card-header">
            <p>
                User: ${username}
                Professor: ${professor}
            </p>
        </div>
        <div class = "content">
            <div class = "card-item">
                <p>Rating</p>
                <div class = "box">
                    <p class = "box-values">${rating}</p>
                </div>
            </div>
            <div class = "card-item">
                <p>Difficulty</p>
                <div class = "box">
                    <p class = "box-values">${difficulty}</p>
                </div>
            </div>
            <div class = "card-item-comment">
                <p class = "comment-title">Comments</p>
                <div class = "comments">
                    <p class = "comment-content">${comments}</p>
                </div>
            </div>
            <div class="likes">
                <p style="font-size:35px;">${likes}</p>
                ${isLiked}
            </div>
        </div>
        
    </div>
    
    `

    return card;
}

function addMessageToChat(messageJSON) {
    console.log("Outside addMessage")
    try{
        console.log("Inside addMessage")
        const chatMessages = document.getElementById("posts-container");
        console.log("Adding to the innerHTML")
        chatMessages.innerHTML = chatMessageHTML(messageJSON) + chatMessages.innerHTML;
    }    
    catch{
        TypeError
    }
}

function clearChat() {
    try{
        const chatMessages = document.getElementById("posts-container");
    chatMessages.innerHTML = "";
    }
    catch{
        TypeError
    }
    
}

function updateChat() {
    console.log("updateChat")
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearChat();
            const messages = JSON.parse(this.response);
            console.log(messages.reverse())
            for (const message of messages.reverse()) {
                addMessageToChat(message);
            }
        }
    }
    request.open("GET", "/posts");
    request.send();
}

function post_getter() {
    updateChat()
    initWS();
}
