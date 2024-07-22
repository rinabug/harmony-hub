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
                const friendsList = document.getElementById('friends-list');
                friendsList.innerHTML = '';
                data.friends.forEach(friend => {
                    const li = document.createElement('li');
                    li.textContent = friend.username;
                    friendsList.appendChild(li);
                });
                updateFriendsForMessaging(data.friends);
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
    }

    function loadMessages(friendId) {
        fetch(`/get_messages/${friendId}`)
            .then(response => response.json())
            .then(data => {
                messagesList.innerHTML = '';
                data.messages.forEach(message => {
                    const messageEl = document.createElement('div');
                    messageEl.textContent = `${message[1] === friendId ? currentFriend.username : 'You'}: ${message[3]}`;
                    messagesList.appendChild(messageEl);
                });
                messagesList.scrollTop = messagesList.scrollHeight;
            });
    }

    function joinChatRoom(friendId) {
        if (socket) {
            socket.disconnect();
        }
        socket = io();
        const room = `${Math.min(friendId, userId)}_${Math.max(friendId, userId)}`;
        socket.emit('join', {username: currentUsername, room: room});

        socket.on('new_message', function(data) {
            const messageEl = document.createElement('div');
            messageEl.textContent = `${data.sender === currentUsername ? 'You' : currentFriend.username}: ${data.content}`;
            messagesList.appendChild(messageEl);
            messagesList.scrollTop = messagesList.scrollHeight;
        });
    }

    sendMessageBtn.addEventListener('click', function() {
        const message = messageInput.value.trim();
        if (message) {
            socket.emit('send_message', {
                sender: currentUsername,
                receiver: currentFriend.username,
                message: message
            });
            messageInput.value = '';
        }
    });

    backToFriendsBtn.addEventListener('click', function() {
        chatWindow.style.display = 'none';
        document.getElementById('friendsList').style.display = 'block';
        if (socket) {
            socket.disconnect();
        }
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
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadFriendRequests();
            loadFriends();
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
});
