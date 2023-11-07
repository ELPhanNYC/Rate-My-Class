function initWS() {
    // Establish a WebSocket connection with the server
    const socket = io.connect('http://0.0.0.0:8080');
    socket.on('connect', () => {
        console.log('WebSocket connection established');
      });
    // Called whenever data is received from the server over the WebSocket connection
    socket.onmessage = function (ws_message) {
        const message = JSON.parse(ws_message.data);
        console.log(message)
        const messageType = message.messageType
        addMessageToChat(message);
    }  
}

function sendPost(){
    const ratingElem = document.getElementById("rating-element");
    const formData = {
        professor: document.getElementById('rating-form-prof').value,
        rating: document.getElementById('rating-form-rating').value,
        difficulty: document.getElementById('rating-form-diff').value,
        comments: document.getElementById('rating-form-comments').value,
      };
  
    // Convert the form data to a JSON string
    const jsonData = JSON.stringify(formData);
    // Send the JSON data via WebSocket
    socket.emit('submit_form', formData);
    ratingElem.focus();
}


function chatMessageHTML(messageJSON) {
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

    // Call onLike to update the likes value
    // const updatedLikes = onLike(imgElement);
    // Send the request with the updated likes value
    // pressed = !pressed
    request.open("POST", "/like");
    request.setRequestHeader('Content-Type', 'application/json')
    request.send(JSON.stringify({'post_id': post_id}));
}

function styleMessage(messageJSON) {
    const post_id = messageJSON.post_id;
    const username = messageJSON.username;
    const comments = messageJSON.comments;
    const professor = messageJSON.professor;
    const difficulty = messageJSON.difficulty;
    const rating = messageJSON.rating;
    const likes = messageJSON.likes;
    const likedOrNot = messageJSON.liked;
    //console.log(messageJSON.liked_by)
    //if (pressed == true) {
       // isLiked = `<img id="${post_id}" onclick="likePostRequest(this)" src="./static/images/thumb-up.png" height="35px">`;
    //} 
    //else {
        //isLiked = `<img id="${post_id}" onclick="likePostRequest(this)" src="./static/images/non-shaded-thumbs-up.png" height="35px">`;
    //}

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
    try{
        const chatMessages = document.getElementById("posts-container");
        chatMessages.innerHTML += chatMessageHTML(messageJSON);
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
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearChat();
            const messages = JSON.parse(this.response);
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
    // setInterval(updateChat, 3000);# no more polling
    initWS();
}
