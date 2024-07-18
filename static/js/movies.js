document.addEventListener('DOMContentLoaded', function() {
    const addToWishlistButton = document.getElementById('add-to-wishlist');
    const wishlistElement = document.getElementById('wishlist');
    const reviewForm = document.getElementById('review-form');
    const reviewsElement = document.getElementById('reviews');
    const getTriviaButton = document.getElementById('get-trivia');
    const triviaQuestionElement = document.getElementById('trivia-question');
    const getRecommendationsButton = document.getElementById('get-recommendations');
    const recommendationsElement = document.getElementById('recommendations');

    function loadWishlist() {
        fetch('/get_wishlist')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    wishlistElement.innerHTML = data.wishlist.map(movie => 
                        `<li>${movie[0]} (${movie[1]}) - Directed by ${movie[2]}</li>`
                    ).join('');
                }
            });
    }

    function loadReviews() {
        fetch('/get_reviews')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    reviewsElement.innerHTML = data.reviews.map(review => 
                        `<div>
                            <h3>${review[0]} (${review[1]})</h3>
                            <p>Director: ${review[2]}</p>
                            <p>Rating: ${review[3]}/5</p>
                            <p>${review[4]}</p>
                        </div>`
                    ).join('');
                }
            });
    }

    addToWishlistButton.addEventListener('click', function() {
        const movieTitle = document.getElementById('movie-title').value;
        fetch('/add_to_wishlist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `movie_title=${encodeURIComponent(movieTitle)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                loadWishlist();
            } else {
                alert(data.message);
            }
        });
    });

    reviewForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const movieTitle = document.getElementById('review-movie-title').value;
        const rating = document.getElementById('rating').value;
        const reviewText = document.getElementById('review-text').value;
        fetch('/add_review', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `movie_title=${encodeURIComponent(movieTitle)}&rating=${rating}&review_text=${encodeURIComponent(reviewText)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                loadReviews();
            } else {
                alert(data.message);
            }
        });
    });

    getTriviaButton.addEventListener('click', function() {
        fetch('/movie_trivia')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    triviaQuestionElement.textContent = data.question;
                } else {
                    triviaQuestionElement.textContent = data.message;
                }
            });
    });

    getRecommendationsButton.addEventListener('click', function() {
        fetch('/movie_recommendations')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    recommendationsElement.innerHTML = data.recommendations.map(movie => `<li>${movie}</li>`).join('');
                }
            });
    });

    loadWishlist();
    loadReviews();
});