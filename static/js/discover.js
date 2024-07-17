document.addEventListener('DOMContentLoaded', () => {
    loadConcerts();
    loadMusic();
    loadTopArtists();
});

function loadTopArtists() {
    fetch('/api/spotify/top-artists')
        .then(response => response.json())
        .then(data => {
            const topArtistsContent = document.getElementById('topArtistsContent');
            topArtistsContent.innerHTML = data.items.map(item => `<p>${item.name}</p>`).join('');
        })
        .catch(error => console.error('Error loading top artists:', error));
}
