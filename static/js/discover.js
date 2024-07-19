document.addEventListener('DOMContentLoaded', () => {
    loadMusicRecommendations();
    loadMovieRecommendations();
    loadConcertRecommendations();
});

function loadMusicRecommendations() {
    fetch('/get_music_recommendations')
        .then(response => response.json())
        .then(data => {
            const musicContent = document.getElementById('musicContent');
            musicContent.innerHTML = data.recommendations.map(track => `
                <div class="track-item">
                    <h3>${track.name}</h3>
                    <p>Artist: ${track.artist}</p>
                    <p>Album: ${track.album}</p>
                    <a href="${track.external_url}" target="_blank">Listen on Spotify</a>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error loading music recommendations:', error));
}

function loadMovieRecommendations() {
    fetch('/movie_recommendations')
        .then(response => response.json())
        .then(data => {
            const movieRecommendations = document.getElementById('movieRecommendations');
            movieRecommendations.innerHTML = data.recommendations.map(movie => `
                <div class="movie-item">
                    <h3>${movie.title}</h3>
                    <p>Director: ${movie.director}</p>
                    <p>Year: ${movie.year}</p>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error loading movie recommendations:', error));
}

function loadConcertRecommendations() {
    fetch('/get_concert_recommendations')
        .then(response => response.json())
        .then(data => {
            const concertContent = document.getElementById('concertContent');
            concertContent.innerHTML = data.recommendations.map(concert => `
                <div class="concert-item">
                    <h3>${concert.name}</h3>
                    <p>Date: ${concert.date}</p>
                    <p>Venue: ${concert.venue}</p>
                    <p>Location: ${concert.location}</p>
                </div>
            `).join('');
        })
        .catch(error => console.error('Error loading concert recommendations:', error));
}