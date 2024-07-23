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

    const userBtn = document.querySelector('#user-btn');
    const editProfileText = document.querySelector('#edit-profile-text');
    const profile = document.querySelector('#profile-section');

    function toggleProfile() {
        profile.classList.toggle('active');
    }

    userBtn.addEventListener('click', toggleProfile);
    editProfileText.addEventListener('click', toggleProfile);

    document.querySelector('#profile-form').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        const actionUrl = this.getAttribute('action');

        fetch(actionUrl, {
            method: "POST",
            body: formData
        }).then(response => {
            if (response.ok) {
                window.location.reload();
            } else {
                response.json().then(data => {
                    if (data.errors) {
                        if (data.errors.username) {
                            document.getElementById('username').classList.add('error');
                            document.getElementById('username-error').innerText = data.errors.username;
                        }
                        if (data.errors.email) {
                            document.getElementById('email_address').classList.add('error');
                            document.getElementById('email-error').innerText = data.errors.email;
                        }
                    }
                });
            }
        });
    });

    const uploadPhotoBtn = document.getElementById('upload-photo-btn');
    const uploadPhotoInput = document.getElementById('upload-photo');
    const profilePicturePlaceholder = document.getElementById('profile-picture-placeholder');

    uploadPhotoBtn.addEventListener('click', function() {
        uploadPhotoInput.click();
    });

    uploadPhotoInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                profilePicturePlaceholder.innerHTML = `<img src="${e.target.result}" alt="Profile Picture">`;
            };
            reader.readAsDataURL(file);
        }
    });
});
document.addEventListener('DOMContentLoaded', function () {
    const favoriteMovieForm = document.getElementById('favorite-movie-form');
    const recentlyWatchedForm = document.getElementById('recently-watched-form');
    
    favoriteMovieForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const query = document.getElementById('favorite-movie-search').value;
        searchAndAddMovie(query, 'favorite');
    });

    recentlyWatchedForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const query = document.getElementById('recently-watched-search').value;
        searchAndAddMovie(query, 'recently-watched');
    });
});

function searchAndAddMovie(query, type) {
    fetch(`/search_movie`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        const resultsDiv = type === 'favorite' ? document.getElementById('favorite-movie-results') : document.getElementById('recently-watched-results');
        resultsDiv.innerHTML = '';  // Clear previous results

        data.results.forEach(result => {
            const movieItem = document.createElement('div');
            movieItem.classList.add('movie-item');

            const poster = document.createElement('img');
            poster.src = `https://image.tmdb.org/t/p/w500${result.poster_path}`;
            poster.alt = result.title;
            poster.classList.add('album-image');

            const title = document.createElement('h3');
            title.textContent = result.title;

            const overview = document.createElement('p');
            overview.textContent = result.overview;

            const form = document.createElement('form');
            form.method = 'post';
            form.action = type === 'favorite' ? '/add_favorite' : '/add_recently_watched';

            const movieIdInput = document.createElement('input');
            movieIdInput.type = 'hidden';
            movieIdInput.name = 'movie_id';
            movieIdInput.value = result.id;

            const movieTitleInput = document.createElement('input');
            movieTitleInput.type = 'hidden';
            movieTitleInput.name = 'movie_title';
            movieTitleInput.value = result.title;

            const moviePosterInput = document.createElement('input');
            moviePosterInput.type = 'hidden';
            moviePosterInput.name = 'movie_poster';
            moviePosterInput.value = `https://image.tmdb.org/t/p/w500${result.poster_path}`;

            const movieOverviewInput = document.createElement('input');
            movieOverviewInput.type = 'hidden';
            movieOverviewInput.name = 'movie_overview';
            movieOverviewInput.value = result.overview;

            const movieTrailerInput = document.createElement('input');
            movieTrailerInput.type = 'hidden';
            movieTrailerInput.name = 'movie_trailer';
            movieTrailerInput.value = result.trailer;

            const button = document.createElement('button');
            button.type = 'submit';
            button.textContent = type === 'favorite' ? 'Add to Favorites' : 'Add to Recently Watched';

            form.appendChild(movieIdInput);
            form.appendChild(movieTitleInput);
            form.appendChild(moviePosterInput);
            form.appendChild(movieOverviewInput);
            form.appendChild(movieTrailerInput);
            form.appendChild(button);

            movieItem.appendChild(poster);
            movieItem.appendChild(title);
            movieItem.appendChild(overview);
            movieItem.appendChild(form);

            resultsDiv.appendChild(movieItem);

            form.addEventListener('submit', function (event) {
                event.preventDefault();
                addMovie(result, type);
            });
        });
    })
    .catch(error => console.error('Error:', error));
}

function addMovie(movie, type) {
    const url = type === 'favorite' ? '/add_favorite' : '/add_recently_watched';
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(movie)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const section = type === 'favorite' ? document.getElementById('favoriteMoviesContent') : document.getElementById('recentlyWatchedContent');
            const movieItem = document.createElement('div');
            movieItem.classList.add('movie-item');

            const poster = document.createElement('img');
            poster.src = movie.poster_path;
            poster.alt = movie.title;
            poster.classList.add('album-image');

            const title = document.createElement('h3');
            title.textContent = movie.title;

            const overview = document.createElement('p');
            overview.textContent = movie.overview;

            movieItem.appendChild(poster);
            movieItem.appendChild(title);
            movieItem.appendChild(overview);

            if (movie.trailer) {
                const trailer = document.createElement('iframe');
                trailer.src = movie.trailer;
                trailer.width = '560';
                trailer.height = '315';
                trailer.frameBorder = '0';
                trailer.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
                trailer.allowFullscreen = true;
                movieItem.appendChild(trailer);
            }

            section.insertBefore(movieItem, section.firstChild);
        }
    })
    .catch(error => console.error('Error:', error));
}

/*notification system*/
document.addEventListener('DOMContentLoaded', function() {

        const notificationBtn = document.getElementById('notification-btn');
        const notificationsSection = document.getElementById('notifications');
        const notificationBadge = document.getElementById('notification-count');

        notificationBtn.addEventListener('click', function() {
            notificationsSection.classList.toggle('active');
            if (notificationsSection.classList.contains('active')) {
                fetchNotifications();
            }
        });

        function fetchNotifications() {
            fetch('/api/notifications')
                .then(response => response.json())
                .then(data => {
                    notificationsSection.innerHTML = '';
                    if (data.length === 0) {
                        notificationsSection.innerHTML = '<p>No new notifications</p>';
                    } else {
                        const ul = document.createElement('ul');
                        data.forEach(notification => {
                            const li = document.createElement('li');
                            li.innerHTML = `<strong>${notification.message}</strong> - ${new Date(notification.created_at).toLocaleString()}`;
                            li.dataset.id = notification.id;
                            li.addEventListener('click', function() {
                                markNotificationRead(notification.id);
                                ul.removeChild(li);
                                updateNotificationBadge(parseInt(notificationBadge.textContent) - 1); // Update badge count immediately
                                if (ul.children.length === 0) {
                                    notificationsSection.innerHTML = '<p>No new notifications</p>';
                                }
                            });
                            ul.appendChild(li);
                        });
                        notificationsSection.appendChild(ul);
                    }
                })
                .catch(error => console.error('Error fetching notifications:', error));
        }

        function markNotificationRead(notificationId) {
            fetch('/mark_notification_read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ notification_id: notificationId })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    console.error('Error marking notification as read');
                }
            })
            .catch(error => console.error('Error marking notification as read:', error));
        }

        function updateNotificationBadge(count) {
            if (count > 0) {
                notificationBadge.textContent = count;
                notificationBadge.style.display = 'inline';
            } else {
                notificationBadge.style.display = 'none';
            }
        }

        // Initial fetch to set the badge count on page load
        fetch('/api/notifications')
            .then(response => response.json())
            .then(data => {
                updateNotificationBadge(data.length);
            })
            .catch(error => console.error('Error fetching notifications:', error));
    });