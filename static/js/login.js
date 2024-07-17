document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');

    loginForm.addEventListener('submit', event => {
        const identifier = document.getElementById('identifier').value;
        const password = document.getElementById('password').value;

        if (identifier.trim() === '') {
            event.preventDefault();
            alert('Please enter a username or email.');
            return;
        }

        if (password.trim() === '') {
            event.preventDefault();
            alert('Please enter your password.');
            return;
        }

    });
});
