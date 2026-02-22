import time
import threading
from flask import Blueprint, request, jsonify
from services.email_service import send_email

timer_bp = Blueprint("timer", __name__)

# In-memory stores (demo)
timers = {}  # user_id -> {"active": bool, "ends_at": float}
timers_lock = threading.Lock()

last_location = {}  # user_id -> {"latitude": float, "longitude": float}
emergency_contacts = {}  # user_id -> [{"name": str, "email": str}]


def maps_link(latitude: float, longitude: float) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"


def send_sos(user_id: str, reason: str = "manual") -> dict:
    # Uses last saved location + contacts, prints demo message
    loc = last_location.get(user_id)
    if not loc:
        return {"ok": False, "error": "no last location saved"}

    latitude = loc["latitude"]
    longitude = loc["longitude"]
    link = maps_link(latitude, longitude)

    contacts = emergency_contacts.get(user_id, [])
    message = f"[SOS] ({reason}) Location: {link}"

    print(f"user={user_id} -> {message}")
    for c in contacts:
        print(f"notify: {c.get('name')} {c.get('email')}")

    return {"ok": True, "maps_link": link, "contacts": contacts, "message": message}


def auto_trigger_panic(user_id: str):
    result = send_sos(user_id, reason="timer_expired")

    subject = "⚠️ LUNA Safety Alert: Timer expired"

    body = (
        "This is an automated safety alert from LUNA.\n\n"
        f"User: {user_id}\n"
        "Reason: Timer expired (no check-in)\n"
        f"Last known location: {result.get('maps_link', 'No location saved')}\n"
    )

    contacts = emergency_contacts.get(user_id, [])
    for c in contacts:
        email = (c.get("email") or "").strip()
        if email:
            r = send_email(email, subject, body)
            print(f"[EMAIL] to={email} result={r}")

    if not result.get("ok"):
        print(f"[AUTO PANIC] user={user_id} -> {result.get('error')}")


def timer_watcher():
    # Background thread to check expired timers
    while True:
        time.sleep(1)
        now = time.time()
        expired_users = []

        with timers_lock:
            for user_id, t in list(timers.items()):
                if t.get("active") and now >= t.get("ends_at", 0):
                    expired_users.append(user_id)

            for user_id in expired_users:
                timers[user_id]["active"] = False  

        for user_id in expired_users:
            auto_trigger_panic(user_id)


def start_timer_watcher_once():
    threading.Thread(target=timer_watcher, daemon=True).start()

# API endpoints


@timer_bp.route("/api/location", methods=["POST"])
def save_location():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "demo"))

    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "latitude/longitude must be numbers"}), 400

    last_location[user_id] = {"latitude": latitude, "longitude": longitude}
    return jsonify({"ok": True, "saved": last_location[user_id]})


@timer_bp.route("/api/contacts", methods=["POST"])
def set_contacts():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "demo"))
    contacts = data.get("contacts", [])

    if not isinstance(contacts, list):
        return jsonify({"ok": False, "error": "contacts must be a list"}), 400

    cleaned = []
    for c in contacts:
        if not isinstance(c, dict):
            continue
        name = str(c.get("name", "")).strip()
        email = str(c.get("email", "")).strip()
        if email:
            cleaned.append({"name": name, "email": email})

    emergency_contacts[user_id] = cleaned
    return jsonify({"ok": True, "count": len(cleaned), "contacts": cleaned})


@timer_bp.route("/api/sos", methods=["POST"])
def manual_sos():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "demo"))
    return jsonify(send_sos(user_id, reason="manual"))


@timer_bp.route("/start-timer", methods=["POST"])
def start_timer():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "demo"))

    try:
        seconds = int(data.get("seconds", 0))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "seconds must be an integer"}), 400

    if seconds < 5:
        return jsonify({"ok": False, "error": "seconds must be >= 5"}), 400

    ends_at = time.time() + seconds
    with timers_lock:
        timers[user_id] = {"active": True, "ends_at": ends_at}

    return jsonify({"ok": True, "ends_at": ends_at})


@timer_bp.route("/cancel-timer", methods=["POST"])
def cancel_timer():
    data = request.get_json(force=True)
    user_id = str(data.get("user_id", "demo"))

    with timers_lock:
        if user_id in timers:
            timers[user_id]["active"] = False

    return jsonify({"ok": True})


@timer_bp.route("/timer-status/<user_id>", methods=["GET"])
def timer_status(user_id):
    timer = timers.get(user_id)
    if not timer:
        return jsonify({"ok": False, "error": "no timer found"}), 404

    remaining = 0
    if timer.get("active"):
        remaining = max(0, int(timer["ends_at"] - time.time()))

    return jsonify({"ok": True, "remaining_seconds": remaining, "active": timer.get("active", False)})