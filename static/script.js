function chatMessageHTML(messageJSON) {
    let messageHTML = styleMessage(messageJSON)
    return messageHTML;
}

function onLike(imgElement) {
    console.log("Like clicked!")
    const likesElement = imgElement.previousElementSibling;
    let currentLikes = parseInt(likesElement.innerText);
    
    if (imgElement.src.endsWith("/static/images/non-shaded-thumbs-up.png")) {
        currentLikes++;
        imgElement.src = "./static/images/thumb-up.png";
    } else {
        currentLikes--;
        imgElement.src = "./static/images/non-shaded-thumbs-up.png";
    }

    likesElement.innerText = currentLikes.toString();
}

function styleMessage(messageJSON) {
    const username = messageJSON.username;
    const comments = messageJSON.comments;
    const professor = messageJSON.professor;
    const difficulty = messageJSON.difficulty;
    const rating = messageJSON.rating;

    // Add these two fields to json response body
    // Need to send a request to /like endpoint on click of the button
    // const likes = messageJSON.likeCount;
    // const likedByUser = messageJSON.likedByUser;
    const likes = 7;
    const likedByUser = false;

    if (likedByUser == true) {
        isLiked = '<img id="like" onclick="onLike(this)" src="./static/images/thumb-up.png" height="35px">';
    } else {
        isLiked = '<img id="like" onclick="onLike(this)" src="./static/images/non-shaded-thumbs-up.png" height="35px">';
    }

    let card = `
    
    <div class="card">
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
    setInterval(updateChat, 1000);
}
