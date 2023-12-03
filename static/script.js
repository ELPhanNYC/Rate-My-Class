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
                post.querySelector('.countdown_time').innerHTML = "Like count will show in: " + seconds;
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
                    time_since = o["time_since_post"];

                    let hours = time_since.split(":")[0];
                    let minutes = time_since.split(":")[1];
                    let days = Math.floor(Number(hours) / 24);
                    let remaining = Math.floor(Number(hours) % 24);

                    if (days > 0) {
                        post.querySelector('.time').innerHTML = `${days} days, ${remaining} hours ago`;
                    } else {
                        post.querySelector('.time').innerHTML = `${hours} hours, ${minutes} minutes ago`;
                    }
                }
            }
        }
    }
}

function initWS() {
    // Establish a WebSocket connection with the server
    socket = io.connect(`http://${domain}:${port}`, {transports: ['websocket']});
    socket.on('connect', (message) => {
        setInterval(getTime,1000)
        console.log('WebSocket connection established');
        console.log(message);
    });

    //Constantly being alled for 30 sec to delay post
    socket.on('update_timer', (data) => {
        if (data['available'] == false){
            updateRatingTime(data);
        }else if (data['available'] == true){
            updateChat()
        }
        
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
        updateChat() //updateChat for all messages
    })

}

function sendPost(){
    const ratingElem = document.getElementById("rating-element");
    console.log("SEND POST FUNCTION CALLED")
    
    const formData = {
        professor: document.getElementById('rating-form-prof').value,
        course: document.querySelector('.selected-option').innerText.replace("Selected: ", ""), //NEW
        rating: document.getElementById('rating-form-rating').value,
        difficulty: document.getElementById('rating-form-diff').value,
        comments: document.getElementById('rating-form-comments').value,
      };
    // Send the JSON data via WebSocket
    console.log("formData")
    console.log(formData)
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
function styleMessage(messageJSON) {
    console.log(messageJSON)
    const post_id = messageJSON.post_id;
    const username = messageJSON.username;
    const comments = messageJSON.comments;
    const professor = messageJSON.professor;
    const course = messageJSON.course; 
    const difficulty = messageJSON.difficulty;
    const rating = messageJSON.rating;
    const likes = messageJSON.likes;
    const likedOrNot = messageJSON.liked;
    const availableOrNot = messageJSON.available;
    let pfp = messageJSON.pfp;
    let src = "";
    let isLiked = ``;

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

    if (availableOrNot == false){
        console.log('new post')
        return `
    
        <div class="card">
            <p id='post_id'>${post_id}</p>
            <div class = "card-header">
                <p>
                    <img class="pfp" src=${src}/>
                    User: ${username}
                    Course: ${course}
                    Professor: ${professor}
                </p>
                <div class="countdown_time">Rating count is available.</div>
                <div class="time">.</div>
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
                    ${isLiked}
                </div>
            </div>
            
        </div>
        
        `
    } else {
        return `
        
        <div class="card">
            <p id='post_id'>${post_id}</p>
            <div class = "card-header">
                <p>
                    <img class="pfp" src=${src}/>
                    User: ${username}
                    Course: ${course}
                    Professor: ${professor}
                </p>
                <div class="countdown_time">Rating count is available.</div>
                <div class="time">.</div>
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
    }
}

function chatMessageHTML(messageJSON) {
    return styleMessage(messageJSON)
    
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
    initWS();
    updateChat();
    //before set interval() to updatechat
    
}


//new
let isOpen = false;

function toggleDropdown() {
    const options = document.getElementById('options');
    isOpen = !isOpen;
    options.style.display = isOpen ? 'block' : 'none';
}

function filterOptions() {
    const searchTerm = document.querySelector('.options input').value.toLowerCase();
    const options = document.querySelectorAll('.option');

    options.forEach(option => {
        const label = option.innerText.toLowerCase();
        if (label.includes(searchTerm)) {
            option.style.display = 'block';
        } else {
             option.style.display = 'none';
        }
    });
}

function selectOption(value) {
    const selectedOption = document.querySelector('.selected-option');
    selectedOption.innerText = `Selected: ${value}`;
    selectOption.value = value
    toggleDropdown();
}


function filterChat(value) { //same thing as update chat but only get the selected course posts
    const request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            clearChat();
            const messages = JSON.parse(this.response);
            console.log(messages.reverse())
            for (const message of messages.reverse()) {
                if (message.course == value){ //only add message if its the same as the selected course
                    addMessageToChat(message);
                }
              
            }         
        }
    }
    request.open("GET", "/filterPosts");
    request.send();
}

function sendAllChats() {
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
    request.open("GET", "/sendAllPosts");
    request.send();
}


function filterCourse(value){ //value = course number
    selectOption(value); //update search bar html
    
    if (value != "ALL CLASSES"){
        filterChat(value); //filter the posts
    }
    
    else{
        sendAllChats();
    }
}