document.addEventListener('DOMContentLoaded', () => {
    const questionElement = document.getElementById('question');
    const optionsElement = document.getElementById('options');
    const resultElement = document.getElementById('result');
    const nextQuestionButton = document.getElementById('nextQuestion');

    function loadQuestion() {
        fetch('/get_trivia_question')
            .then(response => response.json())
            .then(data => {
                displayQuestion(data);
            })
            .catch(error => console.error('Error loading question:', error));
    }

    function displayQuestion(data) {
        questionElement.textContent = data.question;
        optionsElement.innerHTML = Object.entries(data.options).map(([letter, option]) => 
            `<button class="trivia-option button" data-answer="${letter}">${letter}) ${option}</button>`
        ).join('');
        resultElement.textContent = '';
        nextQuestionButton.style.display = 'none';
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
            resultElement.textContent = data.message;
            if (data.status === 'correct') {
                loadGlobalLeaderboard(); // Update global leaderboard if the answer is correct
                loadFriendsLeaderboard(); // Update friends leaderboard if the answer is correct
            }
            nextQuestionButton.style.display = 'block';
        })
        .catch(error => console.error('Error submitting answer:', error));
    }

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

    optionsElement.addEventListener('click', (event) => {
        if (event.target.classList.contains('trivia-option')) {
            submitAnswer(event.target.dataset.answer);
        }
    });

    nextQuestionButton.addEventListener('click', loadQuestion);

    if (!questionElement.textContent.trim()) {
        loadQuestion();
    }
});
