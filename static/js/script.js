function initializeMap(lat, lon, zoom) {
    // Initialize the map
    var map = L.map('map').setView([lat, lon], zoom);

    // Add Google Maps hybrid tiles
    L.tileLayer('https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '© Google Maps'
    }).addTo(map);

    // Add Nominatim geocoder control
    var geocoder = L.Control.Geocoder.nominatim();
    L.Control.geocoder({
        defaultMarkGeocode: false,
        geocoder: geocoder
    }).on('markgeocode', function(e) {
        var center = e.geocode.center;
        var lat = center.lat;
        var lng = center.lng;
        var name = e.geocode.name;

        // Center the map
        map.setView([lat, lng], 16);

        // Remove existing marker
        if (window.currentMarker) {
            map.removeLayer(window.currentMarker);
        }

        // Add new marker
        window.currentMarker = L.marker([lat, lng])
            .addTo(map)
            .bindPopup(`Searched Location: ${name}`)
            .openPopup();

        // Update session map_center via AJAX
        fetch('/search_location', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `lat=${lat}&lon=${lng}`
        });
    }).addTo(map);

    // Handle double-click to auto-fill sidebar form
    map.on('dblclick', function(e) {
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;

        // Auto-fill sidebar form
        document.getElementById('lat').value = lat.toFixed(6);
        document.getElementById('lon').value = lng.toFixed(6);

        // Remove existing marker
        if (window.currentMarker) {
            map.removeLayer(window.currentMarker);
        }

        // Add new marker
        window.currentMarker = L.marker([lat, lng])
            .addTo(map)
            .bindPopup(`Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}`)
            .openPopup();
    });
}