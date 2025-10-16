// Location Tracker for Analytics
class LocationTracker {
    constructor() {
        this.apiUrl = '/api/analytics/track/';
        this.sessionId = this.getOrCreateSessionId();
        this.locationRequested = localStorage.getItem('location_requested') === 'true';
    }

    getOrCreateSessionId() {
        let sessionId = sessionStorage.getItem('analytics_session_id');
        if (!sessionId) {
            sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('analytics_session_id', sessionId);
        }
        return sessionId;
    }

    async requestLocation() {
        if (this.locationRequested) return;

        // Show location permission request
        if ('geolocation' in navigator) {
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, {
                        enableHighAccuracy: true,
                        timeout: 10000,
                        maximumAge: 300000 // 5 minutes
                    });
                });

                const location = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };

                // Get location details from coordinates
                await this.reverseGeocode(location);
                localStorage.setItem('location_requested', 'true');
                
            } catch (error) {
                console.log('Location access denied or failed:', error);
                // Track without location
                this.trackVisit();
            }
        } else {
            console.log('Geolocation not supported');
            this.trackVisit();
        }
    }

    async reverseGeocode(location) {
        try {
            // Use a free geocoding service
            const response = await fetch(
                `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${location.latitude}&longitude=${location.longitude}&localityLanguage=en`
            );
            const data = await response.json();
            
            const locationData = {
                country: data.countryName || 'Unknown',
                city: data.city || data.locality || 'Unknown',
                region: data.principalSubdivision || '',
                latitude: location.latitude,
                longitude: location.longitude
            };

            this.trackVisit(locationData);
        } catch (error) {
            console.log('Geocoding failed:', error);
            this.trackVisit({
                latitude: location.latitude,
                longitude: location.longitude
            });
        }
    }

    async trackVisit(locationData = null) {
        const visitData = {
            session_id: this.sessionId,
            page_url: window.location.href,
            page_title: document.title,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`,
            timestamp: new Date().toISOString(),
            ...locationData
        };

        try {
            await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(visitData)
            });
        } catch (error) {
            console.log('Analytics tracking failed:', error);
        }
    }

    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    // Auto-track page views
    trackPageView() {
        // Track immediately without location
        this.trackVisit();
        
        // Request location permission on first visit
        if (!this.locationRequested) {
            // Show a nice popup asking for location
            this.showLocationPermissionModal();
        }
    }

    showLocationPermissionModal() {
        // Create a beautiful modal for location permission
        const modal = document.createElement('div');
        modal.innerHTML = `
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            " id="location-modal">
                <div style="
                    background: white;
                    padding: 2rem;
                    border-radius: 12px;
                    max-width: 400px;
                    margin: 1rem;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                ">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">📍</div>
                    <h3 style="margin: 0 0 1rem 0; color: #333;">Enable Location</h3>
                    <p style="color: #666; margin-bottom: 2rem; line-height: 1.5;">
                        We'd like to show you personalized content based on your location. 
                        Your location data is kept private and secure.
                    </p>
                    <div style="display: flex; gap: 1rem; justify-content: center;">
                        <button onclick="locationTracker.handleLocationAllow()" style="
                            background: #007bff;
                            color: white;
                            border: none;
                            padding: 0.75rem 1.5rem;
                            border-radius: 6px;
                            cursor: pointer;
                            font-weight: 500;
                        ">Allow Location</button>
                        <button onclick="locationTracker.handleLocationDeny()" style="
                            background: #6c757d;
                            color: white;
                            border: none;
                            padding: 0.75rem 1.5rem;
                            border-radius: 6px;
                            cursor: pointer;
                            font-weight: 500;
                        ">Not Now</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    handleLocationAllow() {
        document.getElementById('location-modal').remove();
        this.requestLocation();
    }

    handleLocationDeny() {
        document.getElementById('location-modal').remove();
        localStorage.setItem('location_requested', 'true');
    }
}

// Initialize location tracker
const locationTracker = new LocationTracker();

// Auto-track when page loads
document.addEventListener('DOMContentLoaded', () => {
    locationTracker.trackPageView();
});

// Track page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        locationTracker.trackPageView();
    }
});