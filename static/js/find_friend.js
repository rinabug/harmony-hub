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
    let currentUsername = "{{ session.username | safe }}";
    let userId = "{{ session.user_id | safe }}";

    menuToggle.addEventListener('click', function() {
        sidebar.classList.toggle('open');
        mainContainer.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        header.classList.toggle('expanded');
    });

    function loadFriends() {
        fetch('/view_friends')
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
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(message => {
                        const sender = message.sender_id === parseInt(userId) ? currentUsername : currentFriend.username;
                        appendMessage(sender, message.content, new Date(message.timestamp));
                    });
                    scrollToBottom();
                } else {
                    messagesList.innerHTML = '<p>No messages yet.</p>';
                }
            })
            .catch(error => {
                messagesList.innerHTML = '<p>Error loading messages.</p>';
            });
    }

    function joinChatRoom(friendId) {
        if (socket) {
            socket.disconnect();
        }
        socket = io();
        const room = `${Math.min(userId, friendId)}_${Math.max(userId, friendId)}`;
        socket.emit('join', { username: currentUsername, room: room });

        socket.on('new_message', function(data) {
            appendMessage(data.sender, data.content, new Date(data.timestamp));
            scrollToBottom();
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

        const senderEl = document.createElement('span');
        senderEl.classList.add('sender');
        senderEl.textContent = sender + ': ';

        const contentEl = document.createElement('span');
        contentEl.classList.add('content');
        contentEl.textContent = content;

        const timeEl = document.createElement('span');
        timeEl.classList.add('timestamp');
        timeEl.textContent = formatTimestamp(timestamp);

        messageEl.appendChild(senderEl);
        messageEl.appendChild(contentEl);
        messageEl.appendChild(timeEl);

        messagesList.appendChild(messageEl);
    }

    function formatTimestamp(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function scrollToBottom() {
        messagesList.scrollTop = messagesList.scrollHeight;
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

    function loadFriendRequests() {
        fetch('/view_friend_requests')
            .then(response => response.json())
            .then(data => {
                const friendRequestsList = document.getElementById('friend-requests-list');
                friendRequestsList.innerHTML = '';
                data.requests.forEach(request => {
                    const requestItem = document.createElement('li');
                    requestItem.innerHTML = `
                        <span>${request.username}</span>
                        <button class="button accept-request-button" data-request-id="${request.id}">Accept</button>
                        <button class="button reject-request-button" data-request-id="${request.id}">Reject</button>
                    `;
                    friendRequestsList.appendChild(requestItem);

                    requestItem.querySelector('.accept-request-button').addEventListener('click', function(event) {
                        const requestId = event.target.dataset.requestId;
                        fetch('/accept_friend_request', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ request_id: requestId })
                        }).then(response => response.json()).then(data => {
                            if (data.status === 'success') {
                                alert('Friend request accepted!');
                                loadFriendRequests();
                                loadFriends();
                            } else {
                                alert('Failed to accept friend request.');
                            }
                        });
                    });

                    requestItem.querySelector('.reject-request-button').addEventListener('click', function(event) {
                        const requestId = event.target.dataset.requestId;
                        fetch('/reject_friend_request', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ request_id: requestId })
                        }).then(response => response.json()).then(data => {
                            if (data.status === 'success') {
                                alert('Friend request rejected!');
                                loadFriendRequests();
                            } else {
                                alert('Failed to reject friend request.');
                            }
                        });
                    });
                });
            });
    }

    // Initial load
    loadFriends();
    loadFriendRequests();
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
