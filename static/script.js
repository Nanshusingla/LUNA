// Constants
const USER_ID = "eilleen";
const alarmAudio = new Audio("/static/static/alarm.mp3");
alarmAudio.loop = true;

// Audio context unlock (for mobile browsers)
document.addEventListener('click', () => {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();
}, { once: true });

// Status update function
async function startTimer(minutes) {

    const seconds = minutes * 60;

    await sendLocationToServer();

    const res = await fetch("/start-timer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, seconds: seconds })
    });

    const data = await res.json();
    
    updateStatus("Timer On", "#f59e0b");

    const statusEl = document.getElementById("status");
    if (statusEl) statusEl.innerText = "Timer started for " + minutes + " minutes";
}

// Show/hide loading
function toggleLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Display result with styling
function displayResult(message, type = 'info') {
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = message;
    resultDiv.className = 'result-box ' + type;
}

// Fake Call Function
function triggerFakeCall() {
    displayResult("📞 Initiating fake call...", "info");
    
    fetch('/fake-call', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            displayResult("✅ Fake call triggered! Your phone should ring shortly.", "success");
            
            if (data.audio) {
                let audio = new Audio(data.audio);
                audio.play();
            }
        })
        .catch(error => {
            displayResult("❌ Error triggering call. Please try again.", "error");
            console.error(error);
        });
}

// Find Help Pole Function
function findHelpPole() {
    displayResult("📍 Locating nearest help pole...", "info");
    toggleLoading(true);

    const callFlask = (lat, lng) => {
        fetch('/get_closest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ lat: lat, lng: lng })
        })
        .then(response => response.json())
        .then(data => {
            toggleLoading(false);
            if (data.closest_point) {
                displayResult(`
                    <strong>📍 Nearest Help Pole:</strong><br>
                    ${data.closest_point}<br><br>
                    <strong>🚶 Walking Time:</strong> ${data.travel_time}
                `, "success");
            } else {
                displayResult("❌ " + (data.error || "Could not find help pole"), "error");
            }
        })
        .catch(err => {
            toggleLoading(false);
            displayResult("❌ Server error. Please try again.", "error");
            console.error(err);
        });
    };

    if (navigator.geolocation) {
        const options = { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 };

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                callFlask(pos.coords.latitude, pos.coords.longitude);
            },
            (err) => {
                console.error("Geo Error:", err.message);
                toggleLoading(false);
                
                if (err.code === 1) {
                    displayResult("❌ Location permission denied. Using default location.", "error");
                } else if (err.code === 2) {
                    displayResult("❌ Network/GPS signal lost. Using default location.", "error");
                } else {
                    displayResult("❌ Location timeout. Using default location.", "error");
                }
                
                callFlask(42.3912, -72.5267);
            },
            options
        );
    } else {
        toggleLoading(false);
        displayResult("❌ Geolocation not supported by your browser.", "error");
    }
}


// Share Location Function
function shareLocation() {
    displayResult("📍 Getting your location...", "info");
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                const mapsLink = `https://www.google.com/maps?q=${lat},${lng}`;
                
                if (navigator.share) {
                    navigator.share({
                        title: 'My Current Location - LUNA Safety',
                        text: 'I am sharing my live location with you for safety.',
                        url: mapsLink
                    }).then(() => {
                        displayResult("✅ Location shared successfully!", "success");
                    }).catch(() => {
                        fallbackShare(mapsLink);
                    });
                } else {
                    fallbackShare(mapsLink);
                }
            },
            (err) => {
                displayResult("❌ Could not get your location. Please enable location services.", "error");
            }
        );
    } else {
        displayResult("❌ Geolocation not supported by your browser.", "error");
    }
}

function fallbackShare(link) {
    navigator.clipboard.writeText(link).then(() => {
        displayResult(`✅ Location link copied to clipboard!<br><br><a href="${link}" target="_blank" style="color:#4361ee;">Open in Maps</a>`, "success");
    });
}

// Send Location to Server
async function sendLocationToServer() {
    if (!navigator.geolocation) throw new Error("Geolocation not supported");

    return new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;

            try {
                await fetch("/api/location", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_id: USER_ID, latitude: lat, longitude: lng })
                });
                resolve({ lat, lng });
            } catch (e) {
                reject(e);
            }
        }, reject);
    });
}

// Timer Functions
async function startTimer(minutes) {
    const seconds = minutes * 60;

    await sendLocationToServer();

    await fetch("/start-timer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, seconds })
    });

    setRunningStatus();  
}

async function cancelTimer() {
    await fetch("/cancel-timer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID })
    });

    setSafeStatus();  

    const timerEl = document.getElementById("timerStatus");
    if (timerEl) timerEl.innerText = "";
}

async function sendSOS() {
    await sendLocationToServer();

    const res = await fetch("/api/sos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID })
    });

    const data = await res.json();
    alert("SOS Sent!\n" + data.maps_link);
}

async function checkStatus() {
    const res = await fetch("/timer-status/" + USER_ID);
    if (!res.ok) return;

    const data = await res.json();
    if (!data.ok) return;

    const timerEl = document.getElementById("timerStatus");
    if (!timerEl) return;

    const minutes = Math.floor(data.remaining_seconds / 60);
    const seconds = data.remaining_seconds % 60;

    timerEl.innerText = `Remaining: ${minutes}m ${seconds}s`;
}
setInterval(checkStatus, 1000);

function setSafeStatus() {
    const text = document.getElementById("status");
    const dot = document.querySelector(".status-dot");

    if (text) text.innerText = "Safe";
    if (dot) dot.style.backgroundColor = "#2ecc71";
}

function setRunningStatus() {
    const text = document.getElementById("status");
    const dot = document.querySelector(".status-dot");

    if (text) text.innerText = "Timer Running";
    if (dot) dot.style.backgroundColor = "#f39c12"; 
}

// --- Emergency contacts (front-end state) ---
let CONTACTS = [];

function renderContacts() {
    const box = document.getElementById("contactsList");
    if (!box) return;

    if (CONTACTS.length === 0) {
        box.innerHTML = `<p style="opacity:.7;">No contacts added yet.</p>`;
        return;
    }

    box.innerHTML = CONTACTS.map((c, idx) => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #eee;">
            <div>
                <strong>${c.name || "(No name)"}</strong><br>
                <span style="opacity:.8;">${c.email}</span>
            </div>
            <button onclick="removeContact(${idx})" class="secondary-btn" style="padding:6px 10px;">Remove</button>
        </div>
    `).join("");
}

function addContact() {
    const nameEl = document.getElementById("cName");
    const emailEl = document.getElementById("cEmail");
    const name = (nameEl?.value || "").trim();
    const email = (emailEl?.value || "").trim();

    if (!email || !email.includes("@")) {
        alert("Please enter a valid email.");
        return;
    }

    CONTACTS.push({ name, email });
    if (nameEl) nameEl.value = "";
    if (emailEl) emailEl.value = "";
    renderContacts();
}

function removeContact(idx) {
    CONTACTS.splice(idx, 1);
    renderContacts();
}

async function saveContacts() {
    const res = await fetch("/api/contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: USER_ID, contacts: CONTACTS })
    });

    const data = await res.json();
    if (!data.ok) {
        alert("Failed to save contacts: " + (data.error || "unknown error"));
        return;
    }

    alert(`Saved ${data.count} contact(s).`);
}

renderContacts();