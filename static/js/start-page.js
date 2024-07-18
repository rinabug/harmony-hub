/* logged out message*/
window.onload = function() {
    var flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
        flashMessages.style.display = 'block';
        setTimeout(function() {
            flashMessages.style.display = 'none';
        }, 3000); // Display the message for 3 seconds
    }
};
