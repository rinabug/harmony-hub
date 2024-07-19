document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContainer = document.getElementById('main-container');
    const mainContent = document.getElementById('main-content');
    const header = document.querySelector('header');

    menuToggle.addEventListener('click', function() {
        sidebar.classList.toggle('open');
        mainContainer.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        header.classList.toggle('expanded');
    });

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
                            <span>${user.username}</span>
                            <button class="send-request-button" data-username="${user.username}">Send Request</button>
                        `;
                        userItem.addEventListener('click', () => {
                            window.location.href = `/friend_profile/${user.username}`;
                        });
                        searchResults.appendChild(userItem);
                    });

                    document.querySelectorAll('.send-request-button').forEach(button => {
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
                                } else {
                                    alert('Failed to send friend request.');
                                }
                            });
                        });
                    });
                });
        } else {
            document.getElementById('searchResults').innerHTML = '';
        }
    });
});