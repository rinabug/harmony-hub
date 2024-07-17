document.addEventListener('DOMContentLoaded', () => {
    const spotifyLoginButton = document.getElementById('loginSpotify');

    spotifyLoginButton.addEventListener('click', () => {
        // Redirect to Spotify login page or handle Spotify OAuth flow
        window.location.href = '/loginSpotify';  // Redirect to your Flask login route
    });
});
