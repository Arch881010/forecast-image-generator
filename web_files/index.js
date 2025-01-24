document.addEventListener('DOMContentLoaded', function() {
    fetch('./title/')
        .then(response => response.json())
        .then(data => {
            document.getElementById('jsUpdate').textContent = data.title;
            document.getElementById('titleChange').textContent = "Welcome to " + data.title;
            document.getElementById('setImage').src = "./output/weather_forecast.png?nocache=" + new Date().getTime();
        })
        .catch(error => console.error('Error fetching title:', error));
});