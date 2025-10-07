import os

from chatbot import Chatbot
from db.database import Database
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database and chatbot
db = Database()
db.connect()
chatbot = Chatbot(db=db)

# Track connected admin users per chat room
admin_connections = {}  # {chat_id: [sid1, sid2, ...]}


# ============================================================================
# REST API Endpoints
# ============================================================================


@app.route("/")
def index():
    """Serve the frontend application"""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path>")
def serve_static(path):
    """Serve static files"""
    try:
        print(f"Attempting to serve {path}")
        return send_from_directory(app.static_folder, path)
    except:
        # Try with .html extension for Next.js static export
        try:
            print(f"Attempting to serve {path}.html")
            return send_from_directory(app.static_folder, f"{path}.html")
        except:
            print("Failed to serve .html file, serving index.html")
            return send_from_directory(app.static_folder, "index.html")


@app.route("/api/chats", methods=["GET"])
def get_all_chats():
    """Get all chats"""
    try:
        chats = db.get_all_chats()

        # Convert datetime objects to strings
        for chat in chats:
            chat["created_at"] = chat["created_at"].isoformat() if chat["created_at"] else None

        return jsonify({"success": True, "chats": chats}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chats/<int:chat_id>", methods=["GET"])
def get_chat_by_id(chat_id):
    """Get a specific chat and its history"""
    try:
        chat = db.get_chat_by_id(chat_id)
        if not chat:
            return jsonify({"success": False, "error": "Chat not found"}), 404

        history = db.get_chat_history(chat_id)

        # Convert datetime objects to strings
        chat["created_at"] = chat["created_at"].isoformat() if chat["created_at"] else None
        for msg in history:
            msg["created_at"] = msg["created_at"].isoformat() if msg["created_at"] else None

        return jsonify({"success": True, "chat": chat, "history": history}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/model", methods=["GET", "POST"])
def handle_model():
    """Get or set the current AI model"""
    if request.method == "GET":
        return jsonify({"success": True, "model": chatbot.get_current_model()}), 200
    else:  # POST
        data = request.get_json()
        model_name = data.get("model")
        if model_name in ["openai", "gemini"]:
            chatbot.set_model(model_name)
            return jsonify({"success": True, "model": model_name}), 200
        else:
            return jsonify({"success": False, "error": 'Invalid model name. Use "openai" or "gemini".'}), 400


# ============================================================================
# SocketIO Event Handlers - Student Chat
# ============================================================================


@socketio.on("student_connect")
def handle_student_connect(data):
    """Handle student connection to a chat"""
    chat_id = data.get("chat_id")

    if not chat_id:
        # Create a new chat
        chat_id = db.create_chat()
        if chat_id:
            emit("chat_created", {"chat_id": chat_id})
        else:
            emit("error", {"message": "Failed to create chat"})
            return

    # Join the chat room
    join_room(f"chat_{chat_id}")

    # Get chat details
    chat = db.get_chat_by_id(chat_id)
    history = db.get_chat_history(chat_id)

    # Convert datetime objects in chat
    if chat:
        chat["created_at"] = chat["created_at"].isoformat() if chat["created_at"] else None

    # Convert datetime objects in history
    for msg in history:
        msg["created_at"] = msg["created_at"].isoformat() if msg["created_at"] else None

    # Check if admin is connected
    is_admin_connected = f"chat_{chat_id}" in admin_connections and len(admin_connections[f"chat_{chat_id}"]) > 0

    emit(
        "student_connected",
        {"chat_id": chat_id, "chat": chat, "history": history, "is_admin_connected": is_admin_connected},
    )

    print(f"Student connected to chat {chat_id}")


@socketio.on("student_disconnect")
def handle_student_disconnect():
    """Handle student disconnection"""
    print("Student disconnected")


@socketio.on("student_message")
def handle_student_message(data):
    """Handle message from student"""
    chat_id = data.get("chat_id")
    message = data.get("message")

    if not chat_id or not message:
        emit("error", {"message": "Invalid message data"})
        return

    # Check if chat exists
    chat = db.get_chat_by_id(chat_id)
    if not chat:
        emit("error", {"message": "Chat not found"})
        return

    # Save student message
    db.add_message(chat_id, "human", message)

    # Broadcast message to all users in the chat room (including admin)
    socketio.emit("new_message", {"chat_id": chat_id, "role": "human", "message": message}, room=f"chat_{chat_id}")

    # If human is enabled, don't generate AI response
    if chat["is_human_enabled"]:
        print(f"Human enabled for chat {chat_id}, skipping AI response")
        return

    # Generate AI response with tool calling support
    history = db.get_chat_history(chat_id)
    result = chatbot.generate_response(message, history, chat_id=chat_id)

    ai_response = result["response"]
    needs_escalation = result.get("needs_escalation", False)
    booking_id = result.get("booking_id")

    # Save AI response
    db.add_message(chat_id, "ai", ai_response)

    # Broadcast AI response
    socketio.emit("new_message", {"chat_id": chat_id, "role": "ai", "message": ai_response}, room=f"chat_{chat_id}")

    # Handle booking confirmation if a slot was booked
    if booking_id:
        socketio.emit("booking_confirmed", {"chat_id": chat_id, "booking_id": booking_id}, room=f"chat_{chat_id}")

    # Handle escalation if needed
    if needs_escalation:
        db.update_chat_human_enabled(chat_id, True)
        socketio.emit("escalation_triggered", {"chat_id": chat_id, "is_human_enabled": True}, room=f"chat_{chat_id}")


# ============================================================================
# SocketIO Event Handlers - Admin
# ============================================================================


@socketio.on("admin_connect")
def handle_admin_connect(data):
    """Handle admin connection to a chat"""
    chat_id = data.get("chat_id")

    if not chat_id:
        emit("error", {"message": "Chat ID required"})
        return

    # Join the chat room
    room = f"chat_{chat_id}"
    join_room(room)

    # Track admin connection
    if room not in admin_connections:
        admin_connections[room] = []
    admin_connections[room].append(request.sid)

    # Get chat details
    chat = db.get_chat_by_id(chat_id)
    history = db.get_chat_history(chat_id)

    # Convert datetime objects in chat
    if chat:
        chat["created_at"] = chat["created_at"].isoformat() if chat["created_at"] else None

    # Convert datetime objects in history
    for msg in history:
        msg["created_at"] = msg["created_at"].isoformat() if msg["created_at"] else None

    emit("admin_connected", {"chat_id": chat_id, "chat": chat, "history": history})

    # Notify student that admin is connected
    socketio.emit("admin_status_changed", {"chat_id": chat_id, "is_admin_connected": True}, room=room)

    print(f"Admin connected to chat {chat_id}")


@socketio.on("admin_disconnect_from_chat")
def handle_admin_disconnect_from_chat(data):
    """Handle admin disconnecting from a specific chat"""
    chat_id = data.get("chat_id")

    if chat_id:
        room = f"chat_{chat_id}"
        leave_room(room)

        # Remove admin from tracking
        if room in admin_connections and request.sid in admin_connections[room]:
            admin_connections[room].remove(request.sid)

            # Notify if no more admins
            if len(admin_connections[room]) == 0:
                socketio.emit("admin_status_changed", {"chat_id": chat_id, "is_admin_connected": False}, room=room)

        print(f"Admin disconnected from chat {chat_id}")


@socketio.on("disconnect")
def handle_disconnect():
    """Handle general disconnection"""
    # Remove admin from all rooms they were in
    for room, sids in list(admin_connections.items()):
        if request.sid in sids:
            sids.remove(request.sid)
            if len(sids) == 0:
                chat_id = room.replace("chat_", "")
                socketio.emit("admin_status_changed", {"chat_id": int(chat_id), "is_admin_connected": False}, room=room)

    print("Client disconnected")


@socketio.on("admin_message")
def handle_admin_message(data):
    """Handle message from admin (human operator)"""
    chat_id = data.get("chat_id")
    message = data.get("message")

    if not chat_id or not message:
        emit("error", {"message": "Invalid message data"})
        return

    # Check if chat exists and human is enabled
    chat = db.get_chat_by_id(chat_id)
    if not chat:
        emit("error", {"message": "Chat not found"})
        return

    if not chat["is_human_enabled"]:
        emit("error", {"message": "Human intervention not enabled for this chat"})
        return

    # Save admin message
    db.add_message(chat_id, "human_operator", message)

    # Broadcast message to all users in the chat room
    socketio.emit(
        "new_message", {"chat_id": chat_id, "role": "human_operator", "message": message}, room=f"chat_{chat_id}"
    )


@socketio.on("toggle_human_enabled")
def handle_toggle_human_enabled(data):
    """Toggle human intervention for a chat"""
    chat_id = data.get("chat_id")
    is_enabled = data.get("is_enabled")

    if chat_id is None or is_enabled is None:
        emit("error", {"message": "Invalid data"})
        return

    # Update database
    success = db.update_chat_human_enabled(chat_id, is_enabled)

    if success:
        # Broadcast to all users in the chat room
        socketio.emit(
            "human_enabled_changed", {"chat_id": chat_id, "is_human_enabled": is_enabled}, room=f"chat_{chat_id}"
        )
    else:
        emit("error", {"message": "Failed to update chat"})


# ============================================================================
# Run the application
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
