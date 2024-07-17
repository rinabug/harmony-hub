document.addEventListener('DOMContentLoaded', () => {
    loadLeaderboard();
    loadTrivia();
    loadUserProfile();
});

function loadUserProfile() {
    fetch('/profile')
        .then(response => response.json())
        .then(data => {
            document.getElementById('profileName').innerText = data.display_name;
            document.getElementById('profileEmail').innerText = data.email;
        })
        .catch(error => console.error('Error loading profile:', error));
}