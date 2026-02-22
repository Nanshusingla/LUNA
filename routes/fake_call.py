from flask import Blueprint, jsonify
from services.elevenlabs_service import generate_fake_call_audio

fake_call_bp = Blueprint("fake_call", __name__)

@fake_call_bp.route("/fake-call", methods=["POST"])
def fake_call():

    script = """
    Hey! I'm outside your dorm. 
    I see you walking - I'll be there in 2 minutes.
    Don't worry, I'm close by.
    """

    file_path = generate_fake_call_audio(script)

    return jsonify({
        "status": "Fake call generated",
        "audio": file_path
    })