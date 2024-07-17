document.addEventListener('DOMContentLoaded', () => {
    function loadGlobalLeaderboard() {
        fetch('/get_global_leaderboard')
            .then(response => response.json())
            .then(data => {
                const globalLeaderboardContent = document.getElementById('globalLeaderboardContent');
                globalLeaderboardContent.innerHTML = `
                    <ol>
                        ${data.map(item => `<li>${item.username}: ${item.score} points</li>`).join('')}
                    </ol>
                `;
            })
            .catch(error => console.error('Error loading global leaderboard:', error));
    }

    function loadFriendsLeaderboard() {
        fetch('/get_friends_leaderboard')
            .then(response => response.json())
            .then(data => {
                const friendsLeaderboardContent = document.getElementById('friendsLeaderboardContent');
                friendsLeaderboardContent.innerHTML = `
                    <ol>
                        ${data.map(item => `<li>${item.username}: ${item.score} points</li>`).join('')}
                    </ol>
                `;
            })
            .catch(error => console.error('Error loading friends leaderboard:', error));
    }

    loadGlobalLeaderboard();
    loadFriendsLeaderboard();
    setInterval(loadGlobalLeaderboard, 60000); // Refresh every minute
    setInterval(loadFriendsLeaderboard, 60000); // Refresh every minute
});
