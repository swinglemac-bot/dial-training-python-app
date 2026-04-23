from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse

from app.config import config
from app.routers.common import require_admin, require_member
from app.stores.admin_settings_store import get_admin_settings, update_admin_settings
from app.stores.member_auth_store import (
    clear_member_sessions,
    get_member_from_session,
    grant_admin_by_email,
    list_members_for_admin,
    login_member,
    logout_member,
    register_member,
    request_email_verification,
    request_email_verification_for_member_id,
    request_password_reset,
    request_password_reset_for_member_id,
    reset_password_with_token,
    update_member_by_admin,
    update_member_password,
    update_member_profile,
    update_member_subscription,
    verify_member_email_with_token,
)
from app.stores.team_store import (
    add_team_member_by_email,
    assign_team_workout_template,
    create_team,
    create_team_workout_template,
    get_team_dashboard,
    list_team_roster,
    list_team_workout_assignments,
    list_team_workout_templates,
    list_teams_for_member,
    update_team_membership_role,
)

router = APIRouter()


def _escape_html(value: str) -> str:
    return (
        str(value or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _render_reset_page(token: str = "", error: str = "", success: str = "") -> str:
    return f"""
    <html>
      <head><title>Dialed Password Reset (Python)</title><meta name='viewport' content='width=device-width, initial-scale=1' /></head>
      <body style='background:#070A10;color:#F3F4F6;font-family:Arial;padding:32px;'>
        <div style='max-width:420px;margin:0 auto;background:#161D2A;border-radius:16px;padding:24px;'>
          <h1>Reset access.</h1>
          <form id='reset-form'>
            <input type='hidden' name='token' value='{_escape_html(token)}' />
            <label>New Password</label>
            <input id='password' name='password' type='password' minlength='8' required />
            <button type='submit'>Reset Password</button>
          </form>
          <div id='status-error' style='color:#FF7B7B;'>{_escape_html(error)}</div>
          <div id='status-success' style='color:#AFFF2F;'>{_escape_html(success)}</div>
        </div>
        <script>
          const form = document.getElementById('reset-form');
          form.addEventListener('submit', async (event) => {{
            event.preventDefault();
            const token = form.querySelector('input[name="token"]').value;
            const password = document.getElementById('password').value;
            const response = await fetch('/api/auth/password/reset', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ token: token, nextPassword: password }})
            }});
            const body = await response.json();
            if (!response.ok) {{
              document.getElementById('status-error').textContent = body.detail || body.message || 'Reset failed';
              return;
            }}
            document.getElementById('status-success').textContent = 'Password reset complete. Return to Dialed and sign in.';
          }});
        </script>
      </body>
    </html>
    """


def _render_verification_page(error: str = "", success: str = "") -> str:
    return f"""
    <html>
      <head><title>Dialed Email Verification (Python)</title></head>
      <body style='background:#070A10;color:#F3F4F6;font-family:Arial;padding:32px;'>
        <div style='max-width:420px;margin:0 auto;background:#161D2A;border-radius:16px;padding:24px;'>
          <h1>Verify email.</h1>
          <div style='color:#FF7B7B;'>{_escape_html(error)}</div>
          <div style='color:#AFFF2F;'>{_escape_html(success)}</div>
        </div>
      </body>
    </html>
    """


def _should_expose_delivery_link(delivery: str) -> bool:
    return config.auth_expose_reset_tokens or delivery == "manual"


def _delivery_for_email() -> str:
    return "manual"


@router.get("/auth/password/reset", response_class=HTMLResponse)
def auth_password_reset_page(request: Request) -> str:
    return _render_reset_page(token=str(request.query_params.get("token", "")))


@router.get("/auth/verify-email", response_class=HTMLResponse)
def auth_verify_email_page(request: Request) -> str:
    token = str(request.query_params.get("token", "")).strip()
    if not token:
        return _render_verification_page(error="Verification token is missing.")
    try:
        verify_member_email_with_token(token)
        return _render_verification_page(success="Email verified. Return to Dialed and sign in.")
    except HTTPException as error:
        return _render_verification_page(error=str(error.detail))


@router.post("/api/auth/register")
def auth_register(payload: dict | None = None) -> dict:
    payload = payload or {}
    settings = get_admin_settings()
    if not settings["allowRegistration"]:
        message = settings["maintenanceMessage"] or "New account creation is paused right now."
        raise HTTPException(status_code=403, detail=message)

    result = register_member(payload)
    delivery = _delivery_for_email()
    token_obj = result.get("verificationToken")
    verification_link = (
        f"{config.auth_verification_web_url}?token={token_obj['token']}" if token_obj else None
    )

    return {
        "member": result["member"],
        "verificationRequired": True,
        "message": "Account created. Verify the email before signing in.",
        "delivery": delivery,
        "verificationLink": verification_link if _should_expose_delivery_link(delivery) else None,
    }


@router.post("/api/auth/login")
def auth_login(payload: dict | None = None) -> dict:
    return login_member(payload or {})


@router.post("/api/auth/email/resend-verification")
def auth_resend_verification(payload: dict | None = None) -> dict:
    payload = payload or {}
    result = request_email_verification(str(payload.get("email") or ""))
    if result.get("alreadyVerified"):
        return {"message": "This email is already verified.", "delivery": "none"}

    delivery = _delivery_for_email()
    token_obj = result.get("verificationToken")
    verification_link = (
        f"{config.auth_verification_web_url}?token={token_obj['token']}" if token_obj else None
    )
    return {
        "message": "If the account exists, a verification email has been sent.",
        "delivery": delivery,
        "verificationLink": verification_link if _should_expose_delivery_link(delivery) else None,
    }


@router.post("/api/auth/logout", response_class=Response)
def auth_logout(auth: dict = Depends(require_member)) -> Response:
    logout_member(auth["token"])
    return Response(status_code=204)


@router.get("/api/auth/me")
def auth_me(auth: dict = Depends(require_member)) -> dict:
    return {"member": auth["member"], "session": auth["session"]}


@router.patch("/api/auth/subscription")
def auth_subscription(payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    member = update_member_subscription(auth["member"]["id"], payload or {})
    return {"member": member}


@router.patch("/api/auth/profile")
def auth_profile(payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    member = update_member_profile(auth["member"]["id"], payload or {})
    return {"member": member}


@router.post("/api/auth/password/change")
def auth_password_change(payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    payload = payload or {}
    member = update_member_password(
        auth["member"]["id"],
        str(payload.get("currentPassword") or ""),
        str(payload.get("nextPassword") or ""),
        auth["token"],
    )
    return {"message": "Password updated.", "member": member}


@router.post("/api/auth/password/request-reset")
def auth_request_reset(payload: dict | None = None) -> dict:
    payload = payload or {}
    result = request_password_reset(str(payload.get("email") or ""))
    delivery = _delivery_for_email()
    token_obj = result.get("resetToken")
    reset_link = f"{config.auth_reset_web_url}?token={token_obj['token']}" if token_obj else None

    return {
        "message": "If the account exists, a password reset link has been sent.",
        "delivery": delivery,
        "resetToken": token_obj["token"] if token_obj and _should_expose_delivery_link(delivery) else None,
        "resetLink": reset_link if token_obj and _should_expose_delivery_link(delivery) else None,
        "expiresAt": token_obj["expiresAt"] if token_obj else None,
    }


@router.post("/api/auth/password/reset")
def auth_reset_password(payload: dict | None = None) -> dict:
    payload = payload or {}
    member = reset_password_with_token(str(payload.get("token") or ""), str(payload.get("nextPassword") or ""))
    return {"message": "Password reset complete.", "member": member}


@router.get("/api/admin/members")
def admin_members(auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    return {"members": list_members_for_admin()}


@router.get("/api/app/settings")
def app_settings() -> dict:
    return {"settings": get_admin_settings()}


@router.get("/api/admin/settings")
def admin_settings(auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    return {"settings": get_admin_settings()}


@router.patch("/api/admin/settings")
def admin_update_settings(payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    settings = update_admin_settings(payload or {})
    return {"settings": settings}


@router.post("/api/admin/admins/grant")
def admin_grant(payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    member = grant_admin_by_email(str((payload or {}).get("email") or ""))
    return {"message": "Admin access granted.", "member": member}


@router.patch("/api/admin/members/{member_id}")
def admin_patch_member(member_id: str, payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    member = update_member_by_admin(member_id, payload or {})
    return {"member": member}


@router.post("/api/admin/members/{member_id}/reset-password")
def admin_reset_member_password(member_id: str, auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    result = request_password_reset_for_member_id(member_id)
    delivery = _delivery_for_email()
    token_obj = result.get("resetToken")
    reset_link = f"{config.auth_reset_web_url}?token={token_obj['token']}" if token_obj else None

    return {
        "message": "Password reset link sent.",
        "delivery": delivery,
        "resetToken": token_obj["token"] if token_obj and _should_expose_delivery_link(delivery) else None,
        "resetLink": reset_link if token_obj and _should_expose_delivery_link(delivery) else None,
        "expiresAt": token_obj["expiresAt"] if token_obj else None,
    }


@router.post("/api/admin/members/{member_id}/resend-verification")
def admin_resend_verification(member_id: str, auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    result = request_email_verification_for_member_id(member_id)
    if result.get("alreadyVerified"):
        return {"message": "Member email is already verified.", "delivery": "none"}

    delivery = _delivery_for_email()
    token_obj = result.get("verificationToken")
    verification_link = (
        f"{config.auth_verification_web_url}?token={token_obj['token']}" if token_obj else None
    )
    return {
        "message": "Verification email sent.",
        "delivery": delivery,
        "verificationLink": verification_link if token_obj and _should_expose_delivery_link(delivery) else None,
    }


@router.post("/api/admin/members/{member_id}/force-logout")
def admin_force_logout(member_id: str, auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    clear_member_sessions(member_id)
    return {"message": "All active sessions revoked for this member."}


@router.post("/api/admin/teams")
def admin_create_team(payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    require_admin(auth)
    body = payload or {}
    team = create_team(
        {
            "name": body.get("name"),
            "organization": body.get("organization"),
            "createdBy": auth["member"]["id"],
            "adminMemberId": body.get("adminMemberId") or auth["member"]["id"],
            "coachMemberIds": body.get("coachMemberIds") if isinstance(body.get("coachMemberIds"), list) else [],
        }
    )
    return {"team": team}


@router.get("/api/team/me")
def team_me(auth: dict = Depends(require_member)) -> dict:
    teams = list_teams_for_member(auth["member"]["id"], auth["member"]["role"])
    return {"teams": teams}


@router.get("/api/team/{team_id}/dashboard")
def team_dashboard(team_id: str, auth: dict = Depends(require_member)) -> dict:
    dashboard = get_team_dashboard(team_id, auth["member"]["id"], auth["member"]["role"])
    return {"dashboard": dashboard}


@router.get("/api/team/{team_id}/roster")
def team_roster(team_id: str, auth: dict = Depends(require_member)) -> dict:
    members = list_team_roster(team_id, auth["member"]["id"], auth["member"]["role"])
    return {"members": members}


@router.post("/api/team/{team_id}/members")
def team_add_member(team_id: str, payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    body = payload or {}
    member = add_team_member_by_email(
        {
            "teamId": team_id,
            "email": body.get("email"),
            "role": body.get("role"),
            "actorMemberId": auth["member"]["id"],
            "actorGlobalRole": auth["member"]["role"],
        }
    )
    return {"member": member}


@router.patch("/api/team/{team_id}/members/{member_id}")
def team_update_member(team_id: str, member_id: str, payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    body = payload or {}
    member = update_team_membership_role(
        {
            "teamId": team_id,
            "memberId": member_id,
            "role": body.get("role"),
            "actorMemberId": auth["member"]["id"],
            "actorGlobalRole": auth["member"]["role"],
        }
    )
    return {"member": member}


@router.get("/api/team/{team_id}/templates")
def team_templates(team_id: str, auth: dict = Depends(require_member)) -> dict:
    templates = list_team_workout_templates(team_id, auth["member"]["id"], auth["member"]["role"])
    return {"templates": templates}


@router.post("/api/team/{team_id}/templates")
def team_create_template(team_id: str, payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    body = payload or {}
    template = create_team_workout_template(
        {
            "teamId": team_id,
            "title": body.get("title"),
            "tier": body.get("tier"),
            "category": body.get("category"),
            "exercises": body.get("exercises") if isinstance(body.get("exercises"), list) else [],
            "actorMemberId": auth["member"]["id"],
            "actorGlobalRole": auth["member"]["role"],
        }
    )
    return {"template": template}


@router.get("/api/team/{team_id}/assignments")
def team_assignments(team_id: str, auth: dict = Depends(require_member)) -> dict:
    assignments = list_team_workout_assignments(team_id, auth["member"]["id"], auth["member"]["role"])
    return {"assignments": assignments}


@router.post("/api/team/{team_id}/assignments")
def team_create_assignments(team_id: str, payload: dict | None = None, auth: dict = Depends(require_member)) -> dict:
    body = payload or {}
    assignments = assign_team_workout_template(
        {
            "teamId": team_id,
            "templateId": body.get("templateId"),
            "memberIds": body.get("memberIds") if isinstance(body.get("memberIds"), list) else [],
            "actorMemberId": auth["member"]["id"],
            "actorGlobalRole": auth["member"]["role"],
        }
    )
    return {"assignments": assignments}
