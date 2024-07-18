document.addEventListener('DOMContentLoaded', () => {
    loadFriends();
    loadBadges();
    setupSendFriendRequestButton();
    loadFriendRequests();
});

function loadFriends() {
    fetch('/view_friends')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const friendsContent = document.getElementById('friendsContent');
                friendsContent.innerHTML = data.friends.map(friend => `<p>${friend}</p>`).join('');
            } else {
                console.error('Error loading friends:', data.message);
            }
        })
        .catch(error => console.error('Error loading friends:', error));
}

function loadBadges() {
    fetch('/api/badges')
        .then(response => response.json())
        .then(data => {
            const badgesContent = document.getElementById('badgesContent');
            badgesContent.innerHTML = data.map(item => `<p>${item.name}</p>`).join('');
        })
        .catch(error => console.error('Error loading badges:', error));
}

function setupSendFriendRequestButton() {
    const sendRequestBtn = document.getElementById('send-request-btn');
    sendRequestBtn.addEventListener('click', () => {
        const friendUsername = document.getElementById('friend-username').value;
        if (friendUsername) {
            sendFriendRequest(friendUsername);
        }
    });
}

function sendFriendRequest(friendUsername) {
    fetch('/send_friend_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ receiver_username: friendUsername }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
            } else {
                alert('Failed to send friend request. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error sending friend request:', error);
            alert('An error occurred while sending the friend request.');
        });
}

function loadFriendRequests() {
    fetch('/view_friend_requests')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const friendRequestsList = document.getElementById('friend-requests-list');
                if (data.requests.length === 0) {
                    friendRequestsList.innerHTML = '<li>No friend requests :(</li>';
                } else {
                    friendRequestsList.innerHTML = data.requests.map(request => `
                        <li>
                            <span>${request.sender_username}</span>
                            <button onclick="acceptFriendRequest(${request.id})">Accept</button>
                        </li>
                    `).join('');
                }
            } else {
                console.error('Error loading friend requests:', data.message);
            }
        })
        .catch(error => console.error('Error loading friend requests:', error));
}

function acceptFriendRequest(requestId) {
    fetch('/accept_friend_request', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ request_id: requestId }),
    })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                loadFriendRequests();
                loadFriends();
            } else {
                alert('Failed to accept friend request. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error accepting friend request:', error);
            alert('An error occurred while accepting the friend request.');
        });
}