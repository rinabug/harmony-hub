document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('register-form');

    registerForm.addEventListener('submit', event => {
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        if (username.length < 3) {
            event.preventDefault();
            alert('Username must be at least 3 characters long.');
            return;
        }

        if (!isValidEmail(email)) {
            event.preventDefault();
            alert('Please enter a valid email address.');
            return;
        }

        if (password.length < 8 || !/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            event.preventDefault();
            alert('Password must be at least 8 characters long and contain at least one special character.');
            return;
        }

    });
});

function isValidEmail(email) {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
}