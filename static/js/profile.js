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
                            document.getElementById('email-address').classList.add('error');
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

