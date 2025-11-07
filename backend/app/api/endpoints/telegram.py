"""
Telegram routes - Clean API endpoints with dependency injection.

This module provides FastAPI routes for Telegram functionality without
using global variables. Services are injected via FastAPI dependencies.
"""

import logging
import re
from datetime import datetime
from typing import Any, Literal
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.config import get_telegram_config
from app.models import ErrorDetail, StandardResponse, utcnow
from app.services import TelegramBotAPI, TelegramMembershipService
from app.timezone_utils import get_period_end

logger = logging.getLogger(__name__)

# Module-level manager instance (set by app on startup)
_manager = None


def set_telegram_manager(manager):
    """Set the global telegram manager instance."""
    global _manager
    _manager = manager


def get_telegram_service() -> TelegramMembershipService:
    """Dependency: Get the Telegram service instance."""
    if _manager is None:
        raise HTTPException(status_code=503, detail="Telegram services not initialized")
    return _manager.get_service()


def get_telegram_bot() -> TelegramBotAPI:
    """Dependency: Get the Telegram bot API instance."""
    if _manager is None:
        raise HTTPException(status_code=503, detail="Telegram services not initialized")
    return _manager.get_bot()


# Request/Response models
class GrantAccessRequest(BaseModel):
    """Request model for granting access."""

    ext_user_id: str = Field(..., min_length=1, description="External user ID from payment system")
    chat_ids: list[int] = Field(..., description="List of chat IDs to grant access to")
    period_days: int = Field(..., gt=0, description="Number of days of access (must be positive)")
    ref: str | None = Field(default=None, description="Payment reference ID")


class GrantAccessData(BaseModel):
    """Data model for grant access response."""

    user_id: str = Field(..., description="Internal user ID")
    invites: dict[int, str] = Field(
        ..., description="Map of chat_id to invite_link or join instruction"
    )
    period_end: str = Field(..., description="Period end datetime in UTC (ISO format)")
    errors: dict[int, str] | None = Field(
        default=None, description="Map of chat_id to error description if any failed"
    )


def get_telegram_router() -> APIRouter:
    """
    Create and return the Telegram router.

    This function creates a new router instance with all Telegram endpoints.
    Call this in your main app to include Telegram routes.

    Usage:
        app.include_router(get_telegram_router(), tags=["Telegram"])
    """
    router = APIRouter()

    # --- Channel management ---
    class ChannelAddRequest(BaseModel):
        """Request model to add/register a Telegram channel in the system."""

        chat_id: int = Field(
            ..., description="Telegram chat ID (use -100... for channels/supergroups if possible)"
        )
        name: str | None = Field(None, description="Friendly channel name")
        join_model: Literal["invite_link", "join_request"] = Field(
            default="invite_link", description="How users join the channel"
        )
        invite_ttl_seconds: int | None = Field(
            default=None, description="Override default invite TTL (seconds)"
        )
        invite_member_limit: int | None = Field(
            default=None, description="Override default invite member limit"
        )

    class ChannelAddData(BaseModel):
        """Data model for channel add response."""

        chat_id: int
        stored_chat_id: int
        name: str | None = None
        join_model: str
        checks: dict[str, Any] = Field(default_factory=dict)

    @router.post("/api/telegram/channels", response_model=StandardResponse[ChannelAddData])
    async def add_channel(
        payload: ChannelAddRequest,
        service: TelegramMembershipService = Depends(get_telegram_service),
        bot: TelegramBotAPI = Depends(get_telegram_bot),
        current_user: dict = Depends(get_current_user),
    ):
        """Add/register a Telegram channel and validate bot permissions.

        Requires authentication via JWT token.

        - Verifies the chat exists (tries provided chat_id; if positive, also tries -100 prefix form)
        - Verifies the bot is administrator and has needed permissions
        - Upserts channel document into DB that the app uses
        """
        input_chat_id = payload.chat_id
        tried_chat_ids = []
        resolved_chat_id = None
        checks: dict[str, Any] = {}

        # Get bot id
        me = await bot.get_me()
        bot_id = me.get("id")
        checks["bot_id"] = bot_id

        # Try as-is chat_id
        for candidate in [
            input_chat_id,
            int(f"-100{input_chat_id}") if input_chat_id > 0 else None,
        ]:
            if candidate is None or candidate in tried_chat_ids:
                continue
            tried_chat_ids.append(candidate)
            try:
                chat_info = await bot.get_chat(candidate)
                resolved_chat_id = candidate
                checks["chat_found"] = True
                checks["chat_type"] = chat_info.get("type")
                checks["chat_title"] = chat_info.get("title")
                break
            except Exception as e:
                checks.setdefault("chat_errors", []).append({"chat_id": candidate, "error": str(e)})

        if resolved_chat_id is None:
            print("Chat resolution checks:", checks)
            return StandardResponse.error_response(
                message="Unable to resolve chat_id",
                error_code="CHAT_NOT_FOUND",
                error_description=f"Provide the -100... form for channels/supergroups. Tried: {tried_chat_ids}",
            )

        # Verify bot administrator status and permissions
        try:
            member = await bot.get_chat_member(resolved_chat_id, bot_id)
            status = member.get("status")
            checks["bot_member_status"] = status

            is_admin = status in ("administrator", "creator")
            checks["is_admin"] = is_admin

            perms = {
                "can_invite_users": member.get("can_invite_users", False),
                "can_manage_chat": member.get("can_manage_chat", False)
                or member.get("can_manage_topics", False),
                # for bans
                "can_restrict_members": member.get("can_restrict_members", False),
            }
            checks["permissions"] = perms

            missing_perms = [k for k, v in perms.items() if not v]
            if not is_admin or missing_perms:
                return StandardResponse.error_response(
                    message="Bot must be admin with required permissions",
                    error_code="INSUFFICIENT_PERMISSIONS",
                    error_description=f"Missing: {', '.join(missing_perms) if missing_perms else 'admin status'}",
                )
        except Exception as e:
            return StandardResponse.error_response(
                message="Failed to verify bot permissions",
                error_code="PERMISSION_CHECK_FAILED",
                error_description=str(e),
            )

        # Upsert channel in DB
        now = utcnow()
        existing = await service.db.channels.find_one({"chat_id": resolved_chat_id})
        doc_update = {
            "name": payload.name or checks.get("chat_title"),
            "join_model": payload.join_model,
            "updated_at": now,
        }
        if payload.invite_ttl_seconds is not None:
            doc_update["invite_ttl_seconds"] = payload.invite_ttl_seconds
        if payload.invite_member_limit is not None:
            doc_update["invite_member_limit"] = payload.invite_member_limit

        if existing:
            await service.db.channels.update_one({"_id": existing["_id"]}, {"$set": doc_update})
        else:
            create_doc = {
                "chat_id": resolved_chat_id,
                **doc_update,
                "created_at": now,
            }
            await service.db.channels.insert_one(create_doc)

        data = ChannelAddData(
            chat_id=input_chat_id,
            stored_chat_id=resolved_chat_id,
            name=doc_update.get("name"),
            join_model=payload.join_model,
            checks=checks,
        )

        return StandardResponse.success_response(
            message="Channel added successfully. Using invite_link by default for simplest user journey.",
            data=data,
        )

    # --- Force removal ---
    class ForceRemoveRequest(BaseModel):
        """Force remove a user from a Telegram channel and expire membership."""

        ext_user_id: str = Field(..., description="External user ID")
        chat_id: int = Field(..., description="Telegram chat ID (-100 form for channels)")
        reason: str | None = Field(None, description="Reason for removal (for audit)")
        dry_run: bool = Field(False, description="If true, only report what would happen")

    class ForceRemoveData(BaseModel):
        """Data model for force remove response."""

        removed: bool = Field(..., description="Whether user was removed from chat")
        expired_membership: bool = Field(..., description="Whether membership was expired")
        details: dict[str, Any] = Field(default_factory=dict, description="Additional details")

    @router.post("/api/telegram/force-remove", response_model=StandardResponse[ForceRemoveData])
    async def force_remove(
        req: ForceRemoveRequest,
        service: TelegramMembershipService = Depends(get_telegram_service),
        bot: TelegramBotAPI = Depends(get_telegram_bot),
        current_user: dict = Depends(get_current_user),
    ):
        """Forcefully ban a user from a channel and mark membership expired.

        Requires authentication via JWT token.

        Useful for manual moderation or testing without waiting for the scheduler.
        """
        # Find internal user
        user_doc = await service.db.users.find_one({"ext_user_id": req.ext_user_id})
        if not user_doc:
            return StandardResponse.error_response(
                message="User not found",
                error_code="USER_NOT_FOUND",
                error_description=f"No user found with ext_user_id: {req.ext_user_id}",
            )

        telegram_user_id = user_doc.get("telegram_user_id")
        if not telegram_user_id:
            return StandardResponse.error_response(
                message="User has no telegram_user_id linked",
                error_code="NO_TELEGRAM_ID",
                error_description="User must link their Telegram account first",
            )

        # Find membership
        membership_doc = await service.db.memberships.find_one(
            {
                "user_id": user_doc["_id"],
                "chat_id": req.chat_id,
                "status": "active",
            }
        )

        details: dict[str, Any] = {
            "telegram_user_id": telegram_user_id,
            "membership_found": bool(membership_doc),
            "dry_run": req.dry_run,
        }

        if req.dry_run:
            data = ForceRemoveData(removed=False, expired_membership=False, details=details)
            return StandardResponse.success_response(
                message="Dry run completed - no actions taken", data=data
            )

        removed = False
        expired = False

        # Ban user from chat
        try:
            removed = await service.ban_member(req.chat_id, telegram_user_id)
        except Exception as e:
            logger.error(f"Force-remove ban error: {e}")
            details["ban_error"] = str(e)

        # Expire membership if present
        if membership_doc:
            try:
                await service.expire_membership(membership_doc["_id"])
                expired = True
            except Exception as e:
                logger.error(f"Force-remove expire error: {e}")
                details["expire_error"] = str(e)

        # Audit
        try:
            await service.log_audit(
                action="FORCE_REMOVE",
                user_id=user_doc["_id"],
                chat_id=req.chat_id,
                meta={"reason": req.reason or "manual", **details},
            )
        except Exception:
            pass

        data = ForceRemoveData(removed=removed, expired_membership=expired, details=details)

        if removed:
            return StandardResponse.success_response(
                message=f"User removed from chat. Membership expired: {expired}", data=data
            )
        else:
            return StandardResponse(
                success=False,
                message="Failed to remove user from chat",
                data=data,
                error=ErrorDetail(
                    code="REMOVAL_FAILED",
                    description=details.get("ban_error", "Unknown error during removal"),
                ),
            )

    @router.post("/api/telegram/grant-access", response_model=StandardResponse[GrantAccessData])
    async def grant_access(
        request: GrantAccessRequest,
        service: TelegramMembershipService = Depends(get_telegram_service),
        current_user: dict = Depends(get_current_user),
    ):
        """
        Grant access to Telegram channels for a user.

        Requires authentication via JWT token.

        This endpoint is called by the payment system after successful payment.
        It creates or updates memberships and generates invite links.

        Period end is calculated at 23:59:59 UTC for the requested number of days.
        """
        try:
            # Upsert user
            user = await service.upsert_user(request.ext_user_id)

            # Calculate period end at end of day in UTC
            period_end = get_period_end(request.period_days)

            invites: dict[int, str] = {}
            errors: dict[int, str] = {}

            for chat_id in request.chat_ids:
                # Get channel configuration
                channel = await service.get_channel(chat_id)
                if not channel:
                    logger.warning(f"Channel {chat_id} not found in database, skipping")
                    errors[chat_id] = "CHANNEL_NOT_FOUND"
                    continue

                # Upsert membership
                await service.upsert_membership(
                    user_id=user.id, chat_id=chat_id, period_end=period_end, status="active"
                )

                # If we already know the user's telegram_user_id, proactively unban
                if user.telegram_user_id:
                    try:
                        await service.unban_member(chat_id, user.telegram_user_id)
                    except Exception:
                        pass

                # Create invite link based on join model
                if channel.join_model == "invite_link":
                    invite = await service.create_invite_link(
                        user_id=user.id, chat_id=chat_id, channel=channel
                    )
                    if invite:
                        invites[chat_id] = invite.invite_link
                    else:
                        err = f"Failed to create invite link for chat {chat_id}"
                        logger.error(err)
                        errors[chat_id] = "INVITE_LINK_CREATION_FAILED"
                else:
                    # For join_request model, return a generic message
                    invites[chat_id] = "join_request_model"

            # Log audit
            await service.log_audit(
                action="GRANT_ACCESS",
                user_id=user.id,
                ref=request.ref,
                meta={
                    "ext_user_id": request.ext_user_id,
                    "chat_ids": request.chat_ids,
                    "period_days": request.period_days,
                    "period_end": period_end.isoformat(),
                },
            )

            # success is True only if all chats succeeded (or are join_request)
            success_flag = len(errors) == 0

            data = GrantAccessData(
                user_id=str(user.id),
                invites=invites,
                period_end=period_end.isoformat(),
                errors=errors or None,
            )

            if success_flag:
                return StandardResponse.success_response(
                    message=f"Access granted until {period_end.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    data=data,
                )
            else:
                return StandardResponse(
                    success=False,
                    message="Access granted with some errors",
                    data=data,
                    error=ErrorDetail(
                        code="PARTIAL_FAILURE",
                        description=f"Failed to grant access to {len(errors)} channel(s)",
                    ),
                )

        except Exception as e:
            logger.error(f"Error granting access: {e}")
            return StandardResponse.error_response(
                message="Failed to grant access",
                error_code="GRANT_ACCESS_FAILED",
                error_description=str(e),
            )

    @router.post("/webhooks/telegram/{secret_path}")
    async def telegram_webhook(
        secret_path: str,
        request: Request,
        service: TelegramMembershipService = Depends(get_telegram_service),
        bot: TelegramBotAPI = Depends(get_telegram_bot),
    ):
        """
        Handle Telegram webhook updates.

        Processes chat_join_request, chat_member updates, and /start messages.
        """
        config = get_telegram_config()

        # Verify secret path with basic normalization (strip and URL-decode once)
        incoming = (secret_path or "").strip()
        expected = (config.TELEGRAM_WEBHOOK_SECRET_PATH or "").strip()
        if not (
            incoming == expected or unquote(incoming) == expected or incoming == unquote(expected)
        ):
            logger.warning(
                "Invalid webhook secret path: incoming=%r expected=%r",
                incoming,
                expected,
            )
            raise HTTPException(status_code=404, detail="Not found")

        try:
            update = await request.json()
            update_id = update.get("update_id")

            logger.info(f"Received webhook update {update_id}")

            # Handle chat_join_request
            if "chat_join_request" in update:
                await _handle_chat_join_request(update["chat_join_request"], service, bot)

            # Handle chat_member updates
            elif "chat_member" in update:
                await _handle_chat_member(update["chat_member"], service)

            # Handle my_chat_member (bot added/removed)
            elif "my_chat_member" in update:
                await _handle_my_chat_member(update["my_chat_member"], service)

            # Handle /start command with deep link
            elif "message" in update:
                message = update["message"]
                if message.get("text", "").startswith("/start"):
                    await _handle_start_command(message, service)

            return Response(status_code=200)

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            # Return 200 to avoid Telegram retries
            return Response(status_code=200)

    return router


# Webhook handler functions
async def _handle_chat_join_request(
    join_request: dict[str, Any], service: TelegramMembershipService, bot: TelegramBotAPI
):
    """Handle chat join request."""
    from_user = join_request["from"]
    chat = join_request["chat"]

    telegram_user_id = from_user["id"]
    chat_id = chat["id"]

    logger.info(f"Chat join request from user {telegram_user_id} for chat {chat_id}")

    # Find user by telegram_user_id
    user = await service.get_user_by_telegram_id(telegram_user_id)

    if not user:
        logger.warning(
            f"User with telegram_id {telegram_user_id} not found, declining join request"
        )
        await bot.decline_chat_join_request(chat_id, telegram_user_id)
        await service.log_audit(
            action="DECLINE_JOIN_REQUEST",
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            meta={"reason": "user_not_found"},
        )
        return

    # Check if user has active membership
    membership = await service.get_active_membership(user.id, chat_id)

    if not membership:
        logger.warning(
            f"User {telegram_user_id} has no active membership for chat {chat_id}, declining"
        )
        await bot.decline_chat_join_request(chat_id, telegram_user_id)
        await service.log_audit(
            action="DECLINE_JOIN_REQUEST",
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            user_id=user.id,
            meta={"reason": "no_active_membership"},
        )
        return

    # Approve join request
    success = await bot.approve_chat_join_request(chat_id, telegram_user_id)

    if success:
        logger.info(f"Approved join request for user {telegram_user_id} to chat {chat_id}")
        await service.log_audit(
            action="APPROVE_JOIN_REQUEST",
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            user_id=user.id,
        )
    else:
        logger.error(f"Failed to approve join request for user {telegram_user_id}")


async def _handle_chat_member(
    chat_member_update: dict[str, Any], service: TelegramMembershipService
):
    """Handle chat member status changes."""
    chat = chat_member_update["chat"]
    new_member = chat_member_update["new_chat_member"]
    old_member = chat_member_update["old_chat_member"]

    chat_id = chat["id"]
    user = new_member["user"]
    telegram_user_id = user["id"]
    username = user.get("username")

    old_status = old_member["status"]
    new_status = new_member["status"]

    logger.info(
        f"Chat member update: user {telegram_user_id}, chat {chat_id}, {old_status} -> {new_status}"
    )

    # If user joined
    if old_status in ["left", "kicked"] and new_status in ["member", "administrator", "creator"]:
        internal_user = await service.get_user_by_telegram_id(telegram_user_id)

        if internal_user:
            # Check if there's an unused invite link for this user and chat
            invite_doc = await service.db.invites.find_one(
                {"user_id": internal_user.id, "chat_id": chat_id, "used": False, "revoked": False}
            )

            if invite_doc:
                await service.mark_invite_used(invite_doc["invite_link"], chat_id, telegram_user_id)
        else:
            # Auto-attribution path: user is not yet linked, try to attribute this join to a pending invite
            try:
                candidate_invite = await service.db.invites.find_one(
                    {
                        "chat_id": chat_id,
                        "used": False,
                        "revoked": False,
                        "expire_at": {"$gte": datetime.utcnow()},
                    },
                    sort=[("created_at", -1)],
                )

                if candidate_invite:
                    user_doc = await service.db.users.find_one({"_id": candidate_invite["user_id"]})
                    if user_doc and user_doc.get("ext_user_id"):
                        # Link this telegram_user_id to the ext_user_id inferred from invite
                        linked = await service.link_telegram_user(
                            user_doc["ext_user_id"], telegram_user_id, username
                        )
                        if linked:
                            await service.mark_invite_used(
                                candidate_invite["invite_link"], chat_id, telegram_user_id
                            )
                            await service.log_audit(
                                action="INVITE_ATTRIBUTED_ON_JOIN",
                                telegram_user_id=telegram_user_id,
                                chat_id=chat_id,
                                user_id=linked.id,
                                meta={"heuristic": "latest_unexpired_invite"},
                            )
            except Exception as e:
                logger.warning(f"Auto-attribution on join failed: {e}")

        await service.log_audit(
            action="MEMBER_JOINED",
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            meta={"username": username, "old_status": old_status, "new_status": new_status},
        )

    # If user left or was kicked
    elif old_status in ["member", "administrator", "creator"] and new_status in ["left", "kicked"]:
        await service.log_audit(
            action="MEMBER_LEFT",
            telegram_user_id=telegram_user_id,
            chat_id=chat_id,
            meta={"username": username, "old_status": old_status, "new_status": new_status},
        )


async def _handle_my_chat_member(
    my_chat_member: dict[str, Any], service: TelegramMembershipService
):
    """Handle bot status changes in chats."""
    chat = my_chat_member["chat"]
    new_member = my_chat_member["new_chat_member"]
    old_member = my_chat_member["old_chat_member"]

    chat_id = chat["id"]
    old_status = old_member["status"]
    new_status = new_member["status"]

    logger.info(f"Bot status change in chat {chat_id}: {old_status} -> {new_status}")

    await service.log_audit(
        action="BOT_STATUS_CHANGE",
        chat_id=chat_id,
        meta={"old_status": old_status, "new_status": new_status},
    )


async def _handle_start_command(message: dict[str, Any], service: TelegramMembershipService):
    """Handle /start command with optional deep link."""
    from_user = message["from"]
    text = message.get("text", "")

    telegram_user_id = from_user["id"]
    username = from_user.get("username")

    # Extract deep link parameter
    parts = text.split(maxsplit=1)
    deep_link_param = parts[1] if len(parts) > 1 else None

    logger.info(f"Start command from user {telegram_user_id}, param: {deep_link_param}")

    # If deep link contains ext_user_id, validate, upsert, link, and assist joining
    if deep_link_param:
        # Basic validation to avoid abuse: allow alphanum, dash, underscore, colon, dot
        if not re.fullmatch(r"[A-Za-z0-9_\-:\.]+", deep_link_param):
            logger.warning(f"Invalid deep link param format: {deep_link_param}")
            await service.log_audit(
                action="START_COMMAND_INVALID_PARAM",
                telegram_user_id=telegram_user_id,
                meta={"param": deep_link_param},
            )
        else:
            try:
                # Ensure user exists then link Telegram account
                user = await service.upsert_user(deep_link_param)
                await service.link_telegram_user(deep_link_param, telegram_user_id, username)
                logger.info(
                    f"Linked telegram user {telegram_user_id} to ext_user_id {deep_link_param}"
                )

                # If user has active memberships, proactively share access instructions/links
                invites: dict[int, str] = {}
                instructions: dict[int, str] = {}

                async for membership_doc in service.db.memberships.find(
                    {"user_id": user.id, "status": "active"}
                ):
                    chat_id = membership_doc.get("chat_id")
                    channel = await service.get_channel(chat_id)
                    if not channel:
                        continue
                    # If user is already a member, backfill invite usage for cleanliness
                    try:
                        bot = _manager.get_bot() if _manager else None
                        if bot:
                            member_info = await bot.get_chat_member(chat_id, telegram_user_id)
                            status = member_info.get("status")
                            # If the user is currently banned (kicked), attempt to unban proactively
                            if status == "kicked" and user.telegram_user_id:
                                try:
                                    await service.unban_member(chat_id, user.telegram_user_id)
                                    # Refresh status (best-effort)
                                    member_info = await bot.get_chat_member(
                                        chat_id, user.telegram_user_id
                                    )
                                    status = member_info.get("status")
                                except Exception:
                                    pass
                            if status in ("member", "administrator", "creator"):
                                await service.db.invites.update_many(
                                    {
                                        "user_id": user.id,
                                        "chat_id": chat_id,
                                        "used": False,
                                        "revoked": False,
                                    },
                                    {"$set": {"used": True, "updated_at": utcnow()}},
                                )
                                await service.log_audit(
                                    action="INVITE_USED_BACKFILL",
                                    user_id=user.id,
                                    telegram_user_id=telegram_user_id,
                                    chat_id=chat_id,
                                )
                                # No need to create a new invite if already in channel
                                continue
                    except Exception:
                        # Non-fatal; continue with usual flow
                        pass
                    if channel.join_model == "invite_link":
                        invite = await service.create_invite_link(user.id, chat_id, channel)
                        if invite:
                            invites[chat_id] = invite.invite_link
                    else:
                        instructions[chat_id] = "Open the channel and tap Request to Join."

                lines = ["Welcome! Your account has been linked."]
                if invites:
                    lines.append("\nYour access links:")
                    for cid, link in invites.items():
                        lines.append(f"• {cid}: {link}")
                if instructions:
                    lines.append("\nFor these channels, request to join:")
                    for cid, note in instructions.items():
                        lines.append(f"• {cid}: {note}")
                if not invites and not instructions:
                    lines.append(
                        "\nNo active subscriptions found. If you purchased recently, please wait a minute and try again."
                    )

                # Send message to user if bot is available
                try:
                    bot = _manager.get_bot() if _manager else None
                    if bot:
                        await bot.send_message(telegram_user_id, "\n".join(lines))
                except Exception as e:
                    logger.warning(f"Failed to send start message to user {telegram_user_id}: {e}")

            except Exception as e:
                logger.error(f"Error linking user on /start: {e}")

    await service.log_audit(
        action="START_COMMAND",
        telegram_user_id=telegram_user_id,
        meta={"username": username, "deep_link_param": deep_link_param},
    )
