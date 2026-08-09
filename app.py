from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import string
import time

app = Flask(__name__)
CORS(app)

rooms = {}

def make_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if code not in rooms:
            return code

@app.route("/")
def home():
    return "Friend Chat Server Online"

@app.route("/room", methods=["POST"])
def create_room():
    code = make_code()

    rooms[code] = {
        "created": time.time(),
        "messages": []
    }

    return jsonify({
        "room": code
    })

@app.route("/room/<room>/exists", methods=["GET"])
def room_exists(room):
    room = room.upper()

    return jsonify({
        "exists": room in rooms
    })

@app.route("/room/<room>", methods=["GET"])
def get_room(room):
    room = room.upper()

    if room not in rooms:
        return jsonify({
            "error": "Room not found"
        }), 404

    return jsonify({
        "messages": rooms[room]["messages"]
    })

@app.route("/room/<room>/message", methods=["POST"])
def send_message(room):
    room = room.upper()

    if room not in rooms:
        return jsonify({
            "error": "Room not found"
        }), 404

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "Guest")).strip()[:24]
    text = str(data.get("text", "")).strip()[:500]

    if not text:
        return jsonify({
            "error": "Empty message"
        }), 400

    message = {
        "id": len(rooms[room]["messages"]) + 1,
        "name": name or "Guest",
        "text": text
    }

    rooms[room]["messages"].append(message)

    return jsonify({
        "success": True,
        "message": message
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
