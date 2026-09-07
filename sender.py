import threading
import time

from utils import add_log


class MessageSender:

    def __init__(self, bot):

        self.bot = bot

        self.running = False
        self.thread = None

        self.target = None
        self.messages = []

        self.sent = 0
        self.failed = 0

        self.current_status = (
            "Not Started"
        )

    def send_once(
        self,
        target,
        message
    ):

        try:

            if not self.bot.is_connected:
                return False, (
                    "Telegram is not connected."
                )

            success, result = (
                self.bot.send_message(
                    target,
                    message
                )
            )

            if success:

                self.sent += 1

                self.current_status = (
                    f"Sent: {self.sent} | "
                    f"Failed: {self.failed}"
                )

                add_log(
                    f"Message sent to {target}",
                    "success"
                )

            else:

                self.failed += 1

                add_log(
                    f"Message failed: {result}",
                    "error"
                )

            return success, result

        except Exception as e:

            self.failed += 1

            add_log(
                f"Send error: {e}",
                "error"
            )

            return False, str(e)

    def start(
        self,
        target,
        messages
    ):

        if self.running:
            return False, (
                "Sender is already running."
            )

        self.target = target
        self.messages = messages

        self.sent = 0
        self.failed = 0

        self.running = True

        self.current_status = "Running"

        self.thread = threading.Thread(
            target=self._worker,
            daemon=True
        )

        self.thread.start()

        add_log(
            f"Worker started for {target}",
            "success"
        )

        return True, "Sender started."

    def _worker(self):

        index = 0

        while self.running:

            try:

                if not self.bot.is_connected:

                    self.current_status = (
                        "Waiting for Telegram connection"
                    )

                    add_log(
                        "Telegram disconnected. "
                        "Waiting...",
                        "error"
                    )

                    time.sleep(10)
                    continue

                message = self.messages[
                    index % len(self.messages)
                ]

                self.send_once(
                    self.target,
                    message
                )

                index += 1

                # Controlled interval.
                # Do not use this to bypass
                # Telegram rate limits.
                for _ in range(30):

                    if not self.running:
                        break

                    time.sleep(1)

            except Exception as e:

                add_log(
                    f"Worker error: {e}",
                    "error"
                )

                time.sleep(10)

        self.current_status = (
            f"Stopped | "
            f"Sent: {self.sent} | "
            f"Failed: {self.failed}"
        )

        add_log(
            "Worker stopped.",
            "info"
        )

    def stop(self):

        self.running = False

        add_log(
            "Stop requested.",
            "info"
        )

    def status(self):

        return {
            "active": self.running,
            "status": self.current_status,
            "sent": self.sent,
            "failed": self.failed,
            "target": self.target or ""
      }
