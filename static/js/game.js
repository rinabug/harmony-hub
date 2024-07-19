document.addEventListener('DOMContentLoaded', () => {
    loadGlobalLeaderboard();
    loadFriendsLeaderboard();
    loadTrivia();
});

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

function loadTrivia() {
    fetch('/get_trivia_question')
        .then(response => response.json())
        .then(data => {
            const triviaContent = document.getElementById('triviaContent');
            triviaContent.innerHTML = `
                <h3>${data.question}</h3>
                <div id="options">
                    ${Object.entries(data.options).map(([letter, option]) => `
                        <button onclick="submitAnswer('${letter}')">${letter}) ${option}</button>
                    `).join('')}
                </div>
            `;
        })
        .catch(error => console.error('Error loading trivia question:', error));
}

function submitAnswer(answer) {
    fetch('/answer_trivia', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answer: answer })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadTrivia();
        loadGlobalLeaderboard();
        loadFriendsLeaderboard();
    })
    .catch(error => console.error('Error submitting answer:', error));
}