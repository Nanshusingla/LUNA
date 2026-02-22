from flask import Blueprint, request, jsonify
from services.maps_service import get_safety_analysis

help_bp = Blueprint('help_poles', __name__)

@help_bp.route('/get_closest', methods=['POST'])
def get_closest():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No location received"}), 400

        user_lat = data.get('lat')
        user_lng = data.get('lng')

        # Get data from the simplified service
        result = get_safety_analysis(user_lat, user_lng)

        return jsonify({
            "closest_point": result['name'],
            "travel_time": result['time']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500