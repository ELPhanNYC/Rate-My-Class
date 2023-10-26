// pressed = false

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
    console.log(messageJSON)
    const post_id = messageJSON.post_id;
    const username = messageJSON.username;
    const comments = messageJSON.comments;
    const professor = messageJSON.professor;
    const difficulty = messageJSON.difficulty;
    const rating = messageJSON.rating;
    const likes = messageJSON.likes;
    const likedOrNot = messageJSON.liked;

    let pfp = messageJSON.pfp;
    let src = ""

    if (pfp === "/static/images/default_pfp.jpg") {
        src = "/get_default"
    } else {
        src = `/get_pfp/${pfp}`
    }

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
                <img class="pfp" src=${src}/>
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
    const chatMessages = document.getElementById("posts-container");
    chatMessages.innerHTML += chatMessageHTML(messageJSON);
}

function clearChat() {
    const chatMessages = document.getElementById("posts-container");
    chatMessages.innerHTML = "";
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
    setInterval(updateChat, 3000);
}
