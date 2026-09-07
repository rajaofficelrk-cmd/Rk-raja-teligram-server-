from flask import Flask, render_template, request, jsonify
from telegram_bot import TelegramBot
from sender import MessageSender
from utils import add_log, load_messages_from_file

import os

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret"
)

bot = TelegramBot()
sender = MessageSender(bot)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start_login", methods=["POST"])
def start_login():
    try:
        data = request.get_json(force=True)

        phone = data.get("phone_number", "").strip()
        api_id = data.get("api_id", "").strip()
        api_hash = data.get("api_hash", "").strip()

        if not phone or not api_id or not api_hash:
            return jsonify({
                "success": False,
                "message": "All login fields are required."
            })

        return_value = bot.initialize(
            phone,
            api_id,
            api_hash
        )

        return jsonify({
            "success": return_value[0],
            "message": return_value[1]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


@app.route("/verify_code", methods=["POST"])
def verify_code():
    try:
        data = request.get_json(force=True)
        code = data.get("code", "").strip()

        if not code:
            return jsonify({
                "success": False,
                "message": "Verification code required."
            })

        success, message = bot.verify_code(code)

        return jsonify({
            "success": success,
            "message": message
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


@app.route("/verify_password", methods=["POST"])
def verify_password():
    try:
        data = request.get_json(force=True)

        password = data.get("password", "")

        if not password:
            return jsonify({
                "success": False,
                "message": "2FA password required."
            })

        success, message = bot.verify_password(password)

        return jsonify({
            "success": success,
            "message": message
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


@app.route("/get_contacts")
def get_contacts():
    if not bot.is_connected:
        return jsonify({
            "success": False,
            "message": "Please login first."
        })

    success, result = bot.get_contacts()

    if not success:
        return jsonify({
            "success": False,
            "message": result
        })

    return jsonify({
        "success": True,
        "contacts": result
    })


@app.route("/send_message", methods=["POST"])
def send_message():
    if not bot.is_connected:
        return jsonify({
            "success": False,
            "message": "Please login first."
        })

    try:
        target = request.form.get(
            "target",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()

        if not target:
            return jsonify({
                "success": False,
                "message": "Target is required."
            })

        if not message:
            return jsonify({
                "success": False,
                "message": "Message is required."
            })

        success, result = sender.send_once(
            target,
            message
        )

        return jsonify({
            "success": success,
            "message": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


@app.route("/start_sending", methods=["POST"])
def start_sending():
    if not bot.is_connected:
        return jsonify({
            "success": False,
            "message": "Please login first."
        })

    try:
        target = request.form.get(
            "target",
            ""
        ).strip()

        messages_text = request.form.get(
            "messages",
            ""
        )

        messages = [
            x.strip()
            for x in messages_text.splitlines()
            if x.strip()
        ]

        if not target:
            return jsonify({
                "success": False,
                "message": "Target is required."
            })

        if not messages:
            return jsonify({
                "success": False,
                "message": "No messages provided."
            })

        success, result = sender.start(
            target,
            messages
        )

        return jsonify({
            "success": success,
            "message": result
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        })


@app.route("/stop_sending", methods=["POST"])
def stop_sending():
    sender.stop()

    return jsonify({
        "success": True,
        "message": "Sending stopped."
    })


@app.route("/get_status")
def get_status():
    return jsonify(
        sender.status()
    )


@app.route("/get_logs")
def get_logs():
    from utils import logs

    return jsonify({
        "logs": logs[-100:]
    })


if __name__ == "__main__":
    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
)
