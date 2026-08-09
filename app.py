from flask import Flask, request, jsonify, make_response
import random, string, time, threading

app = Flask(__name__)

rooms = {}
lock = threading.Lock()
MAX_MESSAGES = 100

def code():
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(chars) for _ in range(5))

def cleanup():
    while True:
        time.sleep(300)
        cutoff = time.time() - 3600
        with lock:
            for room in list(rooms):
                rooms[room]["messages"] = [
                    m for m in rooms[room]["messages"] if m["time"] >= cutoff
                ]
                if not rooms[room]["messages"] and rooms[room]["last"] < cutoff:
                    del rooms[room]

threading.Thread(target=cleanup, daemon=True).start()

@app.after_request
def cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

@app.route("/")
def home():
    return """
    <html><body style="font-family:Arial;background:#111;color:white;padding:30px">
    <h1>Friend Chat Server</h1>
    <p>The server is online.</p>
    </body></html>
    """

@app.route("/room", methods=["POST"])
def create_room():
    with lock:
        c = code()
        while c in rooms:
            c = code()
        rooms[c] = {"messages": [], "last": time.time()}
    return jsonify(room=c)

@app.route("/room/<room>", methods=["GET"])
def get_room(room):
    room = room.upper()
    with lock:
        if room not in rooms:
            return jsonify(error="Room not found"), 404
        rooms[room]["last"] = time.time()
        return jsonify(messages=rooms[room]["messages"])

@app.route("/room/<room>/message", methods=["POST"])
def send_message(room):
    room = room.upper()
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "Guest")).strip()[:24]
    text = str(data.get("text", "")).strip()[:500]

    if not text:
        return jsonify(error="Empty message"), 400

    if room not in rooms:
        return jsonify(error="Room not found"), 404

    msg = {
        "id": time.time_ns(),
        "name": name or "Guest",
        "text": text,
        "time": time.time()
    }

    with lock:
        rooms[room]["messages"].append(msg)
        rooms[room]["messages"] = rooms[room]["messages"][-MAX_MESSAGES:]
        rooms[room]["last"] = time.time()

    return jsonify(ok=True)

@app.route("/room/<room>/exists")
def room_exists(room):
    with lock:
        return jsonify(exists=room.upper() in rooms)

@app.route("/<path:path>", methods=["OPTIONS"])
def options(path):
    return make_response("", 204)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
