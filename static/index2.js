let map;
let markers = []

// add map
function initMap() {
    var dublin = {lat: 53.349805, lng: -6.26031};
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 13,
        center: dublin
    });
}

fetch('/static/data.json')
    .then(response => {
        if (!response.ok) {
            if (response.status >= 400 && response.status < 500) {
                console.error("CLient-side error");
            } else if (response.status >= 500) {
                console.error("Server-side error");
            }
        }
        return response.json();
    })

    .then(staticData => {
        static_stations = staticData;
        return fetch('/stations');
    })

    .then(response => response.json())
    .then(stationData => {
        createStationTable(stationData);
        autoDropDown(
            document.getElementById("start"),
            document.getElementById("start-list"),
            stationData
        );

        autoDropDown(
            document.getElementById("end"),
            document.getElementById("end-list"),
            stationData
        );
        autoDropDown(
            document.getElementById("stationSearch"),
            document.getElementById("search-list"),
            stationData
        );
        stations = stationData;
        initMap();
        StationPing();
        showAvailability(stationData)
    })
    .catch(error => console.error("Network error: ", error));

// format the header
function formatHeader(headerText) {
    return headerText
        .split('_') // split string
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()) //capitalize
        .join(' '); //use space to join word
}


function StationPing() {
    stations.forEach(station => {
        var markerColor = "";
        if (station.Status === "High") {
            markerColor = "http://maps.google.com/mapfiles/ms/icons/green-dot.png";
        } else if (station.Status === "Empty") {
            markerColor = "http://maps.google.com/mapfiles/ms/icons/red-dot.png"
        } else {
            markerColor = "http://maps.google.com/mapfiles/ms/icons/orange-dot.png"
        }

        var staticStation = static_stations.find(staticStation => staticStation.number === station.Number);

        if (staticStation) {
            var marker = new google.maps.Marker({
                position: {
                    lat: staticStation.position_lat,
                    lng: staticStation.position_lng,
                },
                map: map,
                title: station.name,
                station_number: station.number,
                icon: {
                    url: markerColor,
                    scaledSize: new google.maps.Size(30, 30),
                },
            });

            markers.push(marker);
            marker.addListener("click", function () {
                var infoWindow = new google.maps.InfoWindow({
                    content: "Station Name: " + station.Name + '<br>' + "Station Number: " + station.Number
                });
                infoWindow.open(map, marker);
            });
        }
    });
}


// Shows the route between two locations
function findRoute() {
    var start = document.getElementById("start").value;
    var end = document.getElementById("end").value;
    start = `${start} Dublin`;
    end = `${end} Dublin`;

    var directionsService = new google.maps.DirectionsService();
    var directionsDisplay = new google.maps.DirectionsRenderer();
    var polyline = new google.maps.Polyline({
        path: [],
        geodesic: true,
        strokeColor: '#FF0000',
        strokeOpacity: 1.0,
        strokeWeight: 2
    })

    directionsDisplay.setMap(map);

    removeMarkers();

    var request = {
        origin: start,
        destination: end,
        travelMode: "BICYCLING"
        // travelMode: "DRIVING"
    };

    directionsService.route(request, function (result, status) {
        if (status == "OK") {
            directionsDisplay.setDirections(result);
            var routeDist = result.routes[0].legs[0].distance.value;
            var totalDist = result.routes[0].legs[0].distance.text;

            if (infoWindow) {
                infoWindow.close();
            }

            var route = result.routes[0].overview_path;
            var routeLen = route.length;
            var middlePointIndex = Math.floor(routeLen / 2);
            var midRoute = route[middlePointIndex];

            var CO2emission = ((routeDist / 1000) * 108.2).toFixed(2)
            var time = (((routeDist / 1000) / 12) * 60).toFixed(1)

            var infoWindow = new google.maps.InfoWindow({
                content: "<b>Total Distance: </b>" + totalDist + "<br><b>Time: </b>" + time + " minutes" + "<br><b>Co2 not emitted: </b>" + CO2emission + "g"
            });

            infoWindow.setPosition(midRoute);
            infoWindow.open(map);

            var startPing = new google.maps.Marker({
                position: route[0],
                map: map,
                title: start
            });

            var endPing = new google.maps.Marker({
                position: route[route.length - 1],
                map: map,
                title: end
            });

            console.log("Start position:", route[0]);
            console.log("End position:", route[route.length - 1]);

            for (var i = 0; i < route.length; i++) {
                polyline.getPath().push(route[i]);
            }
            polyline.setMap(map);

        } else {
            console.error("Directions request failed due to " + status);
        }
    });
}

function removeMarkers() {
    for (var i = 0; i < markers.length; i++) {
        markers[i].setMap(null);
    }
}

// show station tables


function showStation() {
    //read local station json
    document.getElementById('station').style.display = "block";
    // document.getElementById('stationButton').style.display="block";
    document.getElementById('map').style.display = "none";
    document.getElementById("legend").style.display = "none";


}

function closeStation() {
    document.getElementById('station').style.display = "none";
    // document.getElementById('stationButton').style.display="none";
    document.getElementById('map').style.display = "block";
    document.getElementById("legend").style.display = "block";

}


function fetchWeather() {
    fetch('/current-weather')
        .then(response => response.json())
        .then(data => {
            const currentWeather = document.getElementById('current-weather');
            currentWeather.innerHTML = `
            <div class="weather-info" style="text-align: center">
                <div class="weather-icon-container">
                    <img class="weather-icon" src="${data.icon_url}" alt="Weather Icon" />
                </div>
                <div>
                    <div class="weather-temp">${data.temperature}°C</div>
                    <div class="weather-desc">${data.description}</div>
                </div>
            </div>
        `;
        })
        .catch(error => console.error('Error:', error));
}


// Call fetchWeather when the page loads
document.addEventListener('DOMContentLoaded', fetchWeather);

//station page
function createStationTable(data) {
    const stationsContainer = document.getElementById('searchContainer');
    // stationsContainer.innerHTML = '';
    const searchInput = document.getElementById('stationSearch')
    searchInput.type = 'text';
    searchInput.id = 'stationSearch';
    searchInput.placeholder = 'Search for stations...';
    // stationsContainer.appendChild(searchInput);

    // create search button
    const searchButton = document.createElement('button');
    searchButton.textContent = 'Search';
    searchButton.id = 'searchButton';
    stationsContainer.appendChild(searchButton);

    // create container to put result
    const searchResults = document.createElement('div');
    searchResults.id = 'searchResults';
    searchResults.className = 'search-results';
    // stationsContainer.appendChild(searchResults);

    // create table
    let table = document.createElement('table');
    let caption = table.createCaption();
    caption.textContent = 'Station List';

    let headerRow = table.insertRow();
    let headers = ["Number", "Address", "Bike_stands", "Available_bikes", "Available_stands", "Status"];
    headers.forEach(headerText => {
        let header = document.createElement('th');
        let formattedHeaderText = formatHeader(headerText);
        let textNode = document.createTextNode(formattedHeaderText);
        header.appendChild(textNode);
        headerRow.appendChild(header);
    });

    data.forEach(item => {
        let row = table.insertRow();
        row.setAttribute('station-name', item.Address);
        headers.forEach(header => {
            let cell = row.insertCell();
            let value = item[header];
            let textNode = document.createTextNode(value);
            if (header === 'Status') {
                cell.className = value.toLowerCase();
            }
            cell.appendChild(textNode);
        });
    });
    document.getElementById('station').appendChild(table);

    // drop down list container


    // const autocompleteContainer = document.createElement('div');
    // // // update with user's input
    // autocompleteContainer.setAttribute('class', 'autocomplete-container');
    // stationsContainer.appendChild(autocompleteContainer);
    //     <div id="station" style="margin:auto;display:none">
    //     <div id="searchContainer">
    //         <input type="text" id="stationSearch" placeholder="Enter station name">
    //         <button id="searchButton"> Search</button>
    //     </div>
    // </div>

    // eventlistner on search bar
    //     searchInput
    // searchInput.addEventListener('input', async function (e) {
    //     const userInput = e.target.value.toLowerCase();
    //     autocompleteContainer.innerHTML = '';
    //     if (!userInput) return;
    //     //     filter matching stations
    //     const filteredStations = data.filter(station => station.Address.toLowerCase().startsWith(userInput));
    //     if (filteredStations.length == 0) {
    //         autocompleteContainer.innerHTML = '<div class="autocomplete-item">No results found</div>';
    //     } else {
    //         filteredStations.forEach(station => {
    //             const item = document.createElement('div');
    //             item.textContent = station.Address;
    //             item.addEventListener('click', async () => {
    //                 searchInput.value = station.Address;
    //
    //                 autocompleteContainer.innerHTML = '';
    //             });
    //             autocompleteContainer.appendChild(item);
    //         });
    //     }
    // });

    searchButton.addEventListener('click', async function () {
        console.log('search button clicked')
        // if input is null, show all stations
        if (!searchInput.value) {
            showAllStations();
        } else {
            await filterStation(searchInput.value);
        }
        searchResults.innerHTML = '';
    });

}

// show all stations
function showAllStations() {
    const rows = document.querySelectorAll('#station table tr');
    document.getElementById('stationSearch').value = '';
    rows.forEach(row => {
        row.style.display = '';
    });
}


function filterStation(stationName) {
    console.log('filtering station for:', stationName);
    const rows = document.querySelectorAll('#station table tr');
    rows.forEach(row => {
        const nameAttribute = row.getAttribute('station-name');
        if (nameAttribute && nameAttribute.toLowerCase() === stationName.toLowerCase() || row.rowIndex === 0) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

//time picker
document.addEventListener('DOMContentLoaded', function () {
    const today = new Date();
    const maxDate = new Date();
    maxDate.setDate(today.getDate() + 3);

    const formatDate = (date) => {
        let day = date.getDate().toString().padStart(2, '0');
        let month = (date.getMonth() + 1).toString().padStart(2, '0');
        let year = date.getFullYear();
        return `${year}-${month}-${day}`;
    };
    const formatTime = (date) => {
        let hours = date.getHours().toString().padStart(2, '0');
        let minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    };

    document.getElementById('departureDate').min = formatDate(today);
    document.getElementById('departureDate').max = formatDate(maxDate);
    document.getElementById('departureTime').min = formatTime(today);

});

//toggle time picker
// set now button
function setNow() {
    const now = new Date();
    const dateTime = now.toISOString().slice(0, 16);
    document.getElementById('time_picker').value = dateTime;
    document.getElementById('time_picker').style.display = 'none';
}

// toggle time picker
function toggleTimepicker() {
    const picker = document.getElementById('time_picker');
    picker.style.display = 'block';
}

//set popup
function showAvailability() {
    // fetch data from flask
    const startStation = document.getElementById("start").value;
    const endStation = document.getElementById("end").value;
    const isNow = document.getElementById("time_picker").style.display === 'none';
    if (isNow) {
        fetchStationsData(startStation, endStation);
    } else {
        const departureDate = document.getElementById("departureDate").value;
        const departureTime = document.getElementById("departureTime").value;
        fetchPredictions(startStation, endStation, departureDate, departureTime);
    }
}

function fetchStationsData(startStation, endStation) {
    fetch('/stations')
        .then(response => response.json())
        .then(data => {
            const startStationData = data.find(station => station.Address === startStation)
            const endStationData = data.find(station => station.Address === endStation)
            updatePopup(startStationData, endStationData);
        })
}

// this function is for prediction mode

function fetchPredictions(startStation, endStation, departureDate, departureTime) {
    fetch('/process-input', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({startStation, endStation, departureDate, departureTime})
    })
        .then(response => response.json())
        .then(predicitonData => {
            updatePredictionPopup(predicitonData.start_station, predicitonData.end_station);
        });
}


function updatePopup(startStation, endStation) {
    document.getElementById('startInfo').innerHTML = `<span style="font-weight: bold"> Start:</span> ${startStation.Address} <br> Capacity: ${startStation.Bike_stands}<br>Available Bikes: ${startStation.Available_bikes}\nAvailable Stands: ${startStation.Available_stands}<br><br>`;
    document.getElementById('endInfo').innerHTML = `<span style="font-weight: bold">End:</span> ${endStation.Address} <br> Capacity: ${endStation.Bike_stands}\nAvailable Bikes: ${endStation.Available_bikes}<br> Available Stands: ${endStation.Available_stands}`;
    document.getElementById('availabilityModal').style.display = 'block';
}


async function fetchStaticStationData(stationName) {
    try {
        const response = await fetch('/static/data.json');
        const data = await response.json();
        const stationData = data.find(station => station.address === stationName);
        if (stationData) {
            console.log(`Capacity for ${stationName}: ${stationData.bike_stands}`);
            return stationData.bike_stands;
        } else {
            console.error(`Station not found: ${stationName}`);
            return null;
        }
    } catch (error) {
        console.log('Error loading or parsing data.json:', error);
    }
}

// get future weather
async function fetchWeatherForecast(depatureDate, departureTime) {
    const dateInput = document.getElementById('departureDate').value;
    const timeInput = document.getElementById('departureTime').value;
    const dateTimeString = dateInput + 'T' + timeInput + ':00'; // '2023-07-16T15:45:00'

    const dateTime = new Date(dateTimeString);
    // set minute and seconds to 0
    dateTime.setMinutes(0, 0, 0);

    const year = dateTime.getFullYear();
    const month = (dateTime.getMonth() + 1).toString().padStart(2, '0');
    const day = dateTime.getDate().toString().padStart(2, '0');
    const hours = dateTime.getHours().toString().padStart(2, '0');
    const minutes = '00';
    const seconds = '00';

    const formattedDateTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    try {
        const response = await fetch('/futureWeather', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({datetime_str: formattedDateTime})
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${formattedDateTime}`);
        }
        const weatherData = await response.json();
        return weatherData
    } catch (error) {
        console.error('Failed to fetch weather data: ', error)
    }
}


async function updatePredictionPopup(startStation, endStation) {
    const startStationInput = document.getElementById("start").value;
    const endStationInput = document.getElementById("end").value;
    const startCapacity = await fetchStaticStationData(startStationInput);
    const endCapacity = await fetchStaticStationData(endStationInput);
    const weatherData = await fetchWeatherForecast();
    document.getElementById('weatherInfo').innerHTML = `<span style="font-weight: bold;">Weather:</span><br>${weatherData.temperature}°C &nbsp &nbsp ${weatherData.weatherMain}<br><br>`;
    document.getElementById('startInfo').innerHTML = `<span style="font-weight: bold;">Start:</span> ${startStationInput}<br>Capacity: ${startCapacity}<br>Predicted Available Bikes: ${startStation.predicted_bikes}<br>Predicted Available Stands: ${startCapacity - startStation.predicted_bikes}<br>`;
    document.getElementById('endInfo').innerHTML = `<span style="font-weight: bold;">End: </span>${endStationInput}<br>Capacity: ${endCapacity}<br>Predicted Available Bikes: ${endStation.predicted_bikes}<br>Predicted Available Stands: ${endCapacity - endStation.predicted_bikes}<br>`;

    // document.getElementById('weatherInfo').textContent = `Weather:\n ${weatherData.temperature}°C\n ${weatherData.weatherMain}\n`;
    // document.getElementById('startInfo').textContent = `Start:${startStationInput} \n Capacity: ${startCapacity}\nPredicted Available Bikes: ${startStation.predicted_bikes} \n  Predicted Availabale Stands: ${startCapacity - startStation.predicted_bikes}`;
    // document.getElementById('endInfo').textContent = `End: ${endStationInput} \n Capacity: ${endCapacity} \n Predicted Available Bikes: ${endStation.predicted_bikes} \n Predictied Availabale Stands:  ${endCapacity - endStation.predicted_bikes}`;
    document.getElementById('availabilityModal').style.display = 'block';

}

// close popup
function closePopup() {
    document.getElementById('availabilityModal').style.display = 'none';
}

//send data to flask
function sendData() {
    const startStation = document.getElementById("start").value;
    const endStation = document.getElementById("end").value;
    const departureDate = document.getElementById("departureDate").value;
    const departureTime = document.getElementById("departureTime").value;

    fetch('/process-input', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({startStation, endStation, departureDate, departureTime})
    })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

//start-end dropdowns

function autoDropDown(inputElement, dropdownContainer, data) {
    inputElement.addEventListener("input", async function (e) {
        const userInput = e.target.value.toLowerCase();
        dropdownContainer.innerHTML = "";
        if (!userInput) return;

        const filteredStations = data.filter(station => station.Address.toLowerCase().startsWith(userInput));
        if (filteredStations.length === 0) {
            dropdownContainer.innerHTML = '<div class="autocomplete-item">No results found</div>';
        } else {
            filteredStations.forEach(station => {
                const item = document.createElement("div");
                item.textContent = station.Address;
                item.addEventListener("click", async () => {
                    inputElement.value = station.Address;
                    dropdownContainer.innerHTML = "";
                });
                dropdownContainer.appendChild(item);
            });
        }
    });
}

function goButtonHandler() {
    const startInput = document.getElementById('start').value.trim();
    const endInput = document.getElementById('end').value.trim();
    const timePicker = document.getElementById('time_picker');
    const departureDate = document.getElementById('departureDate').value;
    const departureTime = document.getElementById('departureTime').value;
    const nowBtn = document.getElementById('now_btn');
    const bookBtn = document.getElementById('book_btn');

    // if start and end is input
    if (!startInput || !endInput) {
        alert('Please enter both start and end locations.');
        return;
    }
    // if user select later
    if (timePicker.style.display === 'block') {
        if (!departureDate || !departureTime) {
            alert('Please select both date and time for your booking.');
            return;
        }
    }
    findRoute();
    showAvailability();
    sendData();

}



