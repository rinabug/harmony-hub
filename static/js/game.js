document.addEventListener('DOMContentLoaded', () => {
    const questionElement = document.getElementById('question');
    const optionsElement = document.getElementById('options');
    const resultElement = document.getElementById('result');
    const nextQuestionButton = document.getElementById('nextQuestion');

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

    function loadQuestion() {
        fetch('/get_trivia_question')
            .then(response => response.json())
            .then(data => {
                if (data.question) {
                    displayQuestion(data);
                } else {
                    console.error('No question received from server');
                    questionElement.textContent = 'Error loading question. Please try again.';
                }
            })
            .catch(error => {
                console.error('Error loading question:', error);
                questionElement.textContent = 'Error loading question. Please try again.';
            });
    }

    function displayQuestion(data) {
        questionElement.textContent = Array.isArray(data.question) ? data.question[0] : data.question;
        optionsElement.innerHTML = '';
        Object.entries(data.options).forEach(([letter, option]) => {
            const button = document.createElement('button');
            button.className = 'trivia-option button';
            button.dataset.answer = letter;
            button.textContent = `${letter}) ${option}`;
            optionsElement.appendChild(button);
        });
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
                loadGlobalLeaderboard();
                loadFriendsLeaderboard();
            }
            nextQuestionButton.style.display = 'block';
            optionsElement.querySelectorAll('.trivia-option').forEach(button => {
                button.disabled = true;
                if (button.dataset.answer === data.correct_answer) {
                    button.classList.add('correct-answer');
                }
            });
        })
        .catch(error => {
            console.error('Error submitting answer:', error);
            resultElement.textContent = 'Error submitting answer. Please try again.';
        });
    }

    optionsElement.addEventListener('click', (event) => {
        if (event.target.classList.contains('trivia-option') && !event.target.disabled) {
            submitAnswer(event.target.dataset.answer);
        }
    });

    nextQuestionButton.addEventListener('click', loadQuestion);

    // Initial loads
    loadGlobalLeaderboard();
    loadFriendsLeaderboard();
    loadQuestion();

    // Refresh leaderboards every minute
    setInterval(() => {
        loadGlobalLeaderboard();
        loadFriendsLeaderboard();
    }, 60000);
});
