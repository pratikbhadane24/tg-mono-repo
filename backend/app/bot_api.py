"""
Telegram Bot API client wrapper.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TelegramBotAPI:
    """Wrapper for Telegram Bot API."""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def _make_request(self, method: str, **params) -> dict[str, Any]:
        """Make a request to the Telegram Bot API.

        Improved error handling: always try to parse Telegram's JSON response and
        surface the 'description' field so 4xx errors are actionable.
        """
        url = f"{self.base_url}/{method}"
        try:
            response = await self.client.post(url, json=params)
            text = response.text

            # Try to parse JSON regardless of status
            try:
                payload = response.json()
            except Exception:
                payload = None

            if response.status_code != 200:
                desc = (payload or {}).get("description") if isinstance(payload, dict) else None
                msg = desc or f"HTTP {response.status_code}: {text[:500]}"
                logger.error(f"Telegram API HTTP error for {method}: {msg}")
                raise Exception(msg)

            # 200 OK but API-level error
            if not isinstance(payload, dict):
                logger.error(f"Telegram API returned non-JSON for {method}: {text[:500]}")
                raise Exception("Telegram API returned non-JSON response")

            if not payload.get("ok"):
                error_msg = payload.get("description", "Unknown error")
                logger.error(f"Telegram API error for {method}: {error_msg}")
                raise Exception(f"Telegram API error: {error_msg}")

            return payload.get("result", {})
        except httpx.HTTPError as e:
            # Network/transport layer errors (DNS, connect, TLS, timeouts)
            logger.error(
                "HTTP error calling %s: %r (%s)",
                method,
                e,
                e.__class__.__name__,
            )
            raise
        except Exception as e:
            logger.error(f"Error calling {method}: {e}")
            raise

    async def get_me(self) -> dict[str, Any]:
        """Get information about the bot."""
        return await self._make_request("getMe")

    async def set_webhook(self, url: str, secret_token: str | None = None) -> bool:
        """Set the webhook URL for the bot."""
        params = {
            "url": url,
            "allowed_updates": ["message", "chat_member", "my_chat_member", "chat_join_request"],
        }
        if secret_token:
            params["secret_token"] = secret_token

        result = await self._make_request("setWebhook", **params)
        return result is not None

    async def delete_webhook(self) -> bool:
        """Delete the webhook."""
        result = await self._make_request("deleteWebhook")
        return result is not None

    async def get_webhook_info(self) -> dict[str, Any]:
        """Get current webhook status."""
        return await self._make_request("getWebhookInfo")

    async def create_chat_invite_link(
        self,
        chat_id: int,
        expire_date: datetime | None = None,
        member_limit: int | None = None,
        creates_join_request: bool = False,
    ) -> dict[str, Any]:
        """Create a chat invite link."""
        params = {"chat_id": chat_id, "creates_join_request": creates_join_request}

        if expire_date:
            # Convert to proper UNIX timestamp in UTC regardless of tz-awareness
            if expire_date.tzinfo is None:
                dt_utc = expire_date.replace(tzinfo=UTC)
            else:
                dt_utc = expire_date.astimezone(UTC)
            params["expire_date"] = int(dt_utc.timestamp())

        if member_limit is not None:
            params["member_limit"] = member_limit

        return await self._make_request("createChatInviteLink", **params)

    async def revoke_chat_invite_link(self, chat_id: int, invite_link: str) -> dict[str, Any]:
        """Revoke a chat invite link."""
        return await self._make_request(
            "revokeChatInviteLink", chat_id=chat_id, invite_link=invite_link
        )

    async def approve_chat_join_request(self, chat_id: int, user_id: int) -> bool:
        """Approve a chat join request."""
        result = await self._make_request(
            "approveChatJoinRequest", chat_id=chat_id, user_id=user_id
        )
        return result is not None

    async def decline_chat_join_request(self, chat_id: int, user_id: int) -> bool:
        """Decline a chat join request."""
        result = await self._make_request(
            "declineChatJoinRequest", chat_id=chat_id, user_id=user_id
        )
        return result is not None

    async def ban_chat_member(
        self,
        chat_id: int,
        user_id: int,
        until_date: datetime | None = None,
        revoke_messages: bool = False,
    ) -> bool:
        """Ban a user from a chat."""
        params = {"chat_id": chat_id, "user_id": user_id, "revoke_messages": revoke_messages}

        if until_date:
            params["until_date"] = int(until_date.timestamp())

        result = await self._make_request("banChatMember", **params)
        return result is not None

    async def unban_chat_member(
        self, chat_id: int, user_id: int, only_if_banned: bool = True
    ) -> bool:
        """Unban a user from a chat."""
        result = await self._make_request(
            "unbanChatMember", chat_id=chat_id, user_id=user_id, only_if_banned=only_if_banned
        )
        return result is not None

    async def get_chat_member(self, chat_id: int, user_id: int) -> dict[str, Any]:
        """Get information about a chat member."""
        return await self._make_request("getChatMember", chat_id=chat_id, user_id=user_id)

    async def get_chat(self, chat_id: int) -> dict[str, Any]:
        """Get information about a chat."""
        return await self._make_request("getChat", chat_id=chat_id)

    async def send_message(
        self, chat_id: int, text: str, parse_mode: str | None = None
    ) -> dict[str, Any]:
        """Send a message to a chat."""
        params = {"chat_id": chat_id, "text": text}

        if parse_mode:
            params["parse_mode"] = parse_mode

        return await self._make_request("sendMessage", **params)
