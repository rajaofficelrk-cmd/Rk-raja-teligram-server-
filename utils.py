from datetime import datetime
import threading


logs = []

_log_lock = threading.Lock()


def add_log(
    message,
    log_type="info"
):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    entry = {
        "time": timestamp,
        "message": str(message),
        "type": log_type
    }

    with _log_lock:

        logs.append(entry)

        if len(logs) > 100:
            del logs[:-100]

    print(
        f"[{timestamp}] {message}",
        flush=True
    )


def load_messages_from_file(file):

    try:

        content = file.read()

        if isinstance(content, bytes):
            content = content.decode(
                "utf-8",
                errors="replace"
            )

        return [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

    except Exception as e:

        add_log(
            f"File error: {e}",
            "error"
        )

        return []
