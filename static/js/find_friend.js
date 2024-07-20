document.addEventListener('DOMContentLoaded', function() {
    // Searching for friends
    const searchInput = document.getElementById('searchInput');
    searchInput.addEventListener('input', function() {
        const query = searchInput.value;
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
            document.getElementById('searchResults').innerHTML = '';
        }
    });

    // Add click event listener for user items in the search results
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('user-item')) {
            const username = event.target.dataset.username;
            window.location.href = `/user_profile/${username}`;
        }
    });

    // Fetch and display friends
    fetch('/view_friends')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const friendsList = document.getElementById('friends-list');
                data.friends.forEach(friend => {
                    const li = document.createElement('li');
                    li.innerHTML = `<a href="/user/${friend}">@${friend}</a>`;
                    friendsList.appendChild(li);
                });
            } else {
                console.error('Failed to fetch friends:', data);
            }
        })
        .catch(error => console.error('Error:', error));

    // Fetch and display friend requests
    function loadFriendRequests() {
        fetch('/view_friend_requests')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const friendRequestsList = document.getElementById('friend-requests-list');
                    friendRequestsList.innerHTML = '';
                    data.requests.forEach(request => {
                        const requestItem = document.createElement('li');
                        requestItem.innerHTML = `
                            <span>${request.sender_username}</span>
                            <button class="button accept-request-button" data-request-id="${request.id}">Accept</button>
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
                                    loadFriendRequests(); // Refresh the list
                                    loadFriends(); // Refresh the friends list
                                } else {
                                    alert('Failed to accept friend request.');
                                }
                            });
                        });
                    });
                } else {
                    alert(data.message);
                }
            });
    }

    // Fetch and display friends
    function loadFriends() {
        fetch('/view_friends')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const friendsList = document.querySelector('.friends-list');
                    friendsList.innerHTML = '';
                    data.friends.forEach(friend => {
                        const friendItem = document.createElement('li');
                        friendItem.innerHTML = `<a href="/user/${friend}">${friend}</a>`;
                        friendsList.appendChild(friendItem);
                    });
                } else {
                    alert(data.message);
                }
            });
    }

    // Initial load
    loadFriendRequests();
    loadFriends();
});

// Update function to render search results with clickable usernames
function renderSearchResults(data) {
    const searchResults = document.getElementById('searchResults');
    searchResults.innerHTML = '';
    data.forEach(user => {
        const userItem = document.createElement('div');
        userItem.classList.add('user-item');
        userItem.setAttribute('data-username', user.username); // Add data-username attribute
        userItem.innerHTML = `
            <span>${user.username}</span>
            <button class="add-friend-button" data-username="${user.username}">Add Friend</button>
        `;
        searchResults.appendChild(userItem);
    });

    document.querySelectorAll('.add-friend-button').forEach(button => {
        button.addEventListener('click', (event) => {
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
}
