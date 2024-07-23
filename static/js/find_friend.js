document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContainer = document.getElementById('main-container');
    const mainContent = document.getElementById('main-content');
    const header = document.querySelector('header');
    const friendsList = document.getElementById('friendsForMessaging');
    const chatWindow = document.getElementById('chatWindow');
    const messagesList = document.getElementById('messagesList');
    const messageInput = document.getElementById('messageInput');
    const sendMessageBtn = document.getElementById('sendMessageBtn');
    const backToFriendsBtn = document.getElementById('backToFriendsBtn');
    const currentChatFriend = document.getElementById('currentChatFriend');
    
    let socket;
    let currentFriend;
    let currentUsername;
    let userId;

    function setCurrentUserData(username, id) {
        currentUsername = username;
        userId = id;
    }

    menuToggle.addEventListener('click', function() {
        sidebar.classList.toggle('open');
        mainContainer.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        header.classList.toggle('expanded');
    });

    function loadFriends() {
        fetch('/get_friends')
            .then(response => response.json())
            .then(data => {
                friendsList.innerHTML = '';
                data.friends.forEach(friend => {
                    const li = document.createElement('li');
                    li.textContent = friend.username;
                    li.addEventListener('click', () => startChat(friend));
                    friendsList.appendChild(li);
                });
            });
    }


    function updateFriendsForMessaging(friends) {
        friendsList.innerHTML = '';
        friends.forEach(friend => {
            const li = document.createElement('li');
            li.textContent = friend.username;
            li.addEventListener('click', () => startChat(friend));
            friendsList.appendChild(li);
        });
    }

    function startChat(friend) {
        currentFriend = friend;
        currentChatFriend.textContent = friend.username;
        chatWindow.style.display = 'block';
        document.getElementById('friendsList').style.display = 'none';
        
        loadMessages(friend.id);
        joinChatRoom(friend.id);
        
        messageInput.value = '';
        messageInput.focus();
    }

    function loadMessages(friendId) {
        fetch(`/get_messages/${friendId}`)
            .then(response => response.json())
            .then(data => {
                messagesList.innerHTML = '';
                data.messages.forEach(message => {
                    const messageItem = document.createElement('div');
                    messageItem.classList.add('message-item');
                    messageItem.classList.add(message.sender_id == currentFriendId ? 'received' : 'sent');
                    messageItem.innerHTML = `
                        <div class="sender">${message.sender_username}</div>
                        <div class="message-content">${message.content}</div>
                        <div class="timestamp">${new Date(message.timestamp).toLocaleString()}</div>
                    `;
                    messagesList.appendChild(messageItem);
                });
            });
    }

    function joinChatRoom(friendId) {
        if (socket) {
            socket.disconnect();
        }
        socket = io();
        const room = `${Math.min(userId, friendId)}_${Math.max(userId, friendId)}`;
        socket.emit('join', {username: currentUsername, room: room});

        socket.on('new_message', function(data) {
            const messageItem = document.createElement('div');
            messageItem.classList.add('message-item');
            messageItem.classList.add(data.sender_id == currentFriendId ? 'received' : 'sent');
            messageItem.innerHTML = `
                <div class="sender">${data.sender_username}</div>
                <div class="message-content">${data.content}</div>
                <div class="timestamp">${new Date(data.timestamp).toLocaleString()}</div>
            `;
            messagesList.appendChild(messageItem);
        });

        socket.on('user_joined', function(data) {
            console.log('User joined:', data);
        });

        socket.on('user_left', function(data) {
            console.log('User left:', data);
        });
    }

    function appendMessage(sender, content, timestamp) {
        const messageEl = document.createElement('div');
        messageEl.classList.add('message', sender === currentUsername ? 'sent' : 'received');
        
        const senderEl = document.createElement('div');
        senderEl.classList.add('sender');
        senderEl.textContent = sender;
        
        const contentEl = document.createElement('div');
        contentEl.classList.add('content');
        contentEl.textContent = content;
        
        const timeEl = document.createElement('div');
        timeEl.classList.add('timestamp');
        timeEl.textContent = formatTimestamp(timestamp);
        
        messageEl.appendChild(senderEl);
        messageEl.appendChild(contentEl);
        messageEl.appendChild(timeEl);
        
        messagesList.appendChild(messageEl);
        scrollToBottom();
    }
    //window.setCurrentUserData = setCurrentUserData;

    function formatTimestamp(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function scrollToBottom() {
        messagesList.scrollTop = messagesList.scrollHeight;
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message && currentFriend) {
            const room = `${Math.min(userId, currentFriend.id)}_${Math.max(userId, currentFriend.id)}`;
            socket.emit('send_message', {
                sender: currentUsername,
                receiver: currentFriend.username,
                message: message,
                room: room
            });
            messageInput.value = '';
        }
    }

    sendMessageBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    backToFriendsBtn.addEventListener('click', function() {
        chatWindow.style.display = 'none';
        document.getElementById('friendsList').style.display = 'block';
        if (socket) {
            socket.disconnect();
        }
        currentFriend = null;
        messagesList.innerHTML = '';
    });

    function loadFriendRequests() {
        fetch('/get_friend_requests')
            .then(response => response.json())
            .then(data => {
                const requestsList = document.getElementById('friend-requests-list');
                requestsList.innerHTML = '';
                data.requests.forEach(request => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        ${request.username}
                        <button class="accept-request" data-id="${request.id}">Accept</button>
                        <button class="reject-request" data-id="${request.id}">Reject</button>
                    `;
                    requestsList.appendChild(li);
                });
                addRequestListeners();
            });
    }

    function addRequestListeners() {
        document.querySelectorAll('.accept-request').forEach(button => {
            button.addEventListener('click', function() {
                const requestId = this.dataset.id;
                acceptFriendRequest(requestId);
            });
        });

        document.querySelectorAll('.reject-request').forEach(button => {
            button.addEventListener('click', function() {
                const requestId = this.dataset.id;
                rejectFriendRequest(requestId);
            });
        });
    }

    function acceptFriendRequest(requestId) {
        fetch('/accept_friend_request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ request_id: requestId })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            alert(data.message);
            loadFriendRequests();
            loadFriends();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to accept friend request. Please try again.');
        });
    }

    function rejectFriendRequest(requestId) {
        fetch('/reject_friend_request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ request_id: requestId })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadFriendRequests();
        });
    }

    function sendFriendRequest(username) {
        fetch('/send_friend_request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username: username })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        });
    }

    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function() {
        const query = this.value;
        if (query.length > 0) {
            fetch(`/search_friends?q=${query}`)
                .then(response => response.json())
                .then(data => {
                    const searchResults = document.getElementById('searchResults');
                    searchResults.innerHTML = '';
                    data.forEach(user => {
                        const userItem = document.createElement('div');
                        userItem.classList.add('user-item');
                        userItem.innerHTML = `
                            <span>${user.username}</span>
                            <button class="send-request-button" data-username="${user.username}">Send Request</button>
                        `;
                        searchResults.appendChild(userItem);
                    });
                    addSendRequestListeners();
                });
        } else {
            document.getElementById('searchResults').innerHTML = '';
        }
    });

    function addSendRequestListeners() {
        document.querySelectorAll('.send-request-button').forEach(button => {
            button.addEventListener('click', function(event) {
                event.stopPropagation();
                const username = this.dataset.username;
                sendFriendRequest(username);
            });
        });
    }

    const sendRequestBtn = document.getElementById('send-request-btn');
    sendRequestBtn.addEventListener('click', function() {
        const username = document.getElementById('friend-username').value;
        if (username) {
            sendFriendRequest(username);
        }
    });

    // Initial load
    loadFriends();
    loadFriendRequests();
    window.setCurrentUserData = setCurrentUserData;
});

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    searchInput.addEventListener('input', function() {
        const query = searchInput.value;
        if (query.length > 0) {
            fetch(`/search_friends?q=${query}`)
                .then(response => response.json())
                .then(data => {
                    searchResults.innerHTML = '';
                    data.forEach(user => {
                        const userItem = document.createElement('div');
                        userItem.classList.add('user-item');
                        userItem.innerHTML = `
                            <a href="/user/${user.username}">${user.username}</a>
                            <button class="button add-friend-button" data-username="${user.username}">Add Friend</button>
                        `;
                        searchResults.appendChild(userItem);

                        userItem.querySelector('.add-friend-button').addEventListener('click', (event) => {
                            event.stopPropagation();
                            const username = event.target.dataset.username;
                            fetch(`/send_request`, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ username })
                            }).then(response => {
                                if (response.ok) {
                                    alert('Friend request sent!');
                                    event.target.disabled = true;
                                    event.target.innerText = 'Request Sent';
                                } else {
                                    response.json().then(data => {
                                        alert(data.error || 'Failed to send friend request.');
                                    });
                                }
                            });
                        });
                    });
                });
        } else {
            searchResults.innerHTML = '';
        }
    });
});
