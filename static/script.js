let domain = 'localhost'
let port = '8080'
let socket;

function getTime() {
    socket.emit('update_age');
}
function updateRatingTime(data) {
    console.log(data);
    let curr_id = data['post_id'];
    let seconds = data['available_time'];
    for (post of document.getElementById('posts-container').childNodes) {
        if (post.className === 'card') {
            let id = post.querySelector('#post_id').innerHTML
            if (curr_id === id) {
                post.querySelector('.countdown_time').innerHTML = seconds;
            }
        }
    }
}
function updatePostsTime(time_data) {
    //console.log(time_data)
    for (o of time_data) {
        let curr_id = o["post_id"]
        for (post of document.getElementById('posts-container').childNodes) {
            if (post.className === 'card') {
                let id = post.querySelector('#post_id').innerHTML
                if (curr_id === id) {
                    post.querySelector('.time').innerHTML = o["time_since_post"]
                }
            }
        }
    }
}

function initWS() {
    // Establish a WebSocket connection with the server
    socket = io.connect(`http://${domain}:${port}`);
    socket.on('connect', () => {
        setInterval(getTime,1000)
        console.log('WebSocket connection established');
    });

    //Constantly being alled for 30 sec to delay post
    socket.on('update_timer', (data) => {
        //TODO: update countdown timer so user can see how many sec left
        //console.log(data)
        updateRatingTime(data)
    });

    // Called whenever data is received from the server over the WebSocket connection
    socket.on('response_post', (message) => {
        // Handle the server's response message here
        console.log(message);
        addMessageToChat(message);
    
    });
    socket.on('update_age', (time_data) => {
        updatePostsTime(time_data);
    })
    socket.on('update_like', (message) => {
        console.log(message)
        updateChat()
    })

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

// function onLike(imgElement) {
//     const likesElement = imgElement.previousElementSibling;
//     let currentLikes = parseInt(likesElement.innerText);

//     likesElement.innerText = currentLikes
//     return currentLikes
// }

//Message functions
function chatMessageHTML(messageJSON) {
    let messageHTML = styleMessage(messageJSON)
    return messageHTML;
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
            <div class="countdown_time">00:00:00</div>
            <div class="time">00:00:00</div>
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
                <p style="font-size:35px;" >${likes}</p>
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

function post_getter() { //called when the index page is loaded
    updateChat()//before set interval() to updatechat
    initWS();
}