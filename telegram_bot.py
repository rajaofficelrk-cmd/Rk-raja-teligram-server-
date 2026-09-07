import asyncio
import os

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError
)

from utils import add_log


class TelegramBot:

    def __init__(self):
        self.api_id = None
        self.api_hash = None
        self.phone = None

        self.client = None
        self.loop = None

        self.is_connected = False
        self.need_code = False
        self.need_password = False

    def _run(self, coroutine):

        if not self.loop:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        return self.loop.run_until_complete(
            coroutine
        )

    async def _initialize(
        self,
        phone,
        api_id,
        api_hash
    ):
        self.phone = phone
        self.api_id = int(api_id)
        self.api_hash = api_hash

        session_dir = os.environ.get(
            "SESSION_DIR",
            "sessions"
        )

        os.makedirs(
            session_dir,
            exist_ok=True
        )

        session_path = os.path.join(
            session_dir,
            "telegram_session"
        )

        self.client = TelegramClient(
            session_path,
            self.api_id,
            self.api_hash
        )

        await self.client.connect()

        if await self.client.is_user_authorized():

            self.is_connected = True
            self.need_code = False
            self.need_password = False

            add_log(
                "Existing Telegram session restored.",
                "success"
            )

            return True, "Already logged in."

        await self.client.send_code_request(
            self.phone
        )

        self.need_code = True

        add_log(
            "Telegram verification code sent.",
            "info"
        )

        return True, (
            "Verification code sent to Telegram."
        )

    def initialize(
        self,
        phone,
        api_id,
        api_hash
    ):
        try:
            return self._run(
                self._initialize(
                    phone,
                    api_id,
                    api_hash
                )
            )

        except Exception as e:

            add_log(
                f"Initialization error: {e}",
                "error"
            )

            return False, str(e)

    async def _verify_code(self, code):

        try:

            await self.client.sign_in(
                phone=self.phone,
                code=code
            )

            self.is_connected = True
            self.need_code = False
            self.need_password = False

            add_log(
                "Telegram login successful.",
                "success"
            )

            return True, "Login successful."

        except SessionPasswordNeededError:

            self.need_password = True

            return False, (
                "2FA password required."
            )

        except PhoneCodeInvalidError:

            return False, (
                "Invalid verification code."
            )

        except PhoneCodeExpiredError:

            return False, (
                "Verification code expired."
            )

        except Exception as e:

            return False, str(e)

    def verify_code(self, code):

        try:
            return self._run(
                self._verify_code(code)
            )

        except Exception as e:
            return False, str(e)

    async def _verify_password(
        self,
        password
    ):

        try:

            await self.client.sign_in(
                password=password
            )

            self.is_connected = True
            self.need_password = False

            add_log(
                "Telegram 2FA verification successful.",
                "success"
            )

            return True, "Login successful."

        except Exception as e:
            return False, str(e)

    def verify_password(self, password):

        try:
            return self._run(
                self._verify_password(password)
            )

        except Exception as e:
            return False, str(e)

    async def _send_message(
        self,
        target,
        message
    ):

        try:

            if not await self.client.is_user_authorized():
                self.is_connected = False

                return False, (
                    "Telegram session is not authorized."
                )

            entity = await self.client.get_entity(
                target
            )

            await self.client.send_message(
                entity,
                message
            )

            return True, "Message sent successfully."

        except Exception as e:

            return False, str(e)

    def send_message(
        self,
        target,
        message
    ):

        try:

            if not self.client:
                return False, (
                    "Telegram client not initialized."
                )

            result = self._run(
                self._send_message(
                    target,
                    message
                )
            )

            return result

        except Exception as e:

            self.is_connected = False

            return False, str(e)

    async def _get_contacts(self):

        try:

            dialogs = await self.client.get_dialogs()

            contacts = []

            for dialog in dialogs:

                entity = dialog.entity

                if not entity:
                    continue

                item = {
                    "name": dialog.name or "Unknown",
                    "type": type(entity).__name__
                }

                if getattr(
                    entity,
                    "username",
                    None
                ):

                    item["identifier"] = (
                        "@" + entity.username
                    )

                elif getattr(
                    entity,
                    "id",
                    None
                ):

                    item["identifier"] = str(
                        entity.id
                    )

                else:

                    item["identifier"] = "Unknown"

                contacts.append(item)

            return True, contacts

        except Exception as e:

            return False, str(e)

    def get_contacts(self):

        try:

            return self._run(
                self._get_contacts()
            )

        except Exception as e:

            return False, str(e)
