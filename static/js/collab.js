document.addEventListener('DOMContentLoaded', function() {
    // Function to dynamically load chat messages
    function loadChatMessages() {
        fetch('/get_global_messages')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const chatContent = document.getElementById('chatContent');
                    chatContent.innerHTML = '';
                    data.messages.forEach(msg => {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = 'message-item';
                        messageDiv.innerHTML = `
                            <span class="username">${msg.username}:</span> ${msg.message}
                            <span class="timestamp">${new Date(msg.timestamp).toLocaleString()}</span>
                        `;
                        chatContent.appendChild(messageDiv);
                    });
                    chatContent.scrollTop = chatContent.scrollHeight;
                }
            })
            .catch(error => console.error('Error loading messages:', error));
    }

    // Load chat messages initially
    loadChatMessages();

    // Set up interval to refresh messages every 5 seconds
    setInterval(loadChatMessages, 5000);

    // Function to handle sending chat messages
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
        chatForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(chatForm);
            fetch('/send_global_message', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(result => {
                if (result.status === 'success') {
                    loadChatMessages();  // Reload chat messages after sending a new one
                    chatForm.reset();    // Clear the chat input
                }
            })
            .catch(error => console.error('Error sending message:', error));
        });
    }
});
