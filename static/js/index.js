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

/*sidebar functionality*/
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');

    menuToggle.addEventListener('click', function() {
        sidebar.classList.toggle('open');
        mainContent.classList.toggle('collapsed');
    });
});