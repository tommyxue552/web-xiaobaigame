# -*- coding: utf-8 -*-
"""
????????7.4?
-------------------
??????????????Token ?????????
??????????? Controller?
"""
import re
import io
import qrcode
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..services import download_service
from sqlalchemy import update
from ..models.download_resource import DownloadResource

router = APIRouter(tags=["Download"])

MOBILE_UA_REGEX = r"Android|iPhone|iPad|iPod|webOS|BlackBerry|Windows Phone"
SITE_NAME = "???????"
SITE_URL = "http://localhost:8000"

_qr_cache: dict[str, bytes] = {}


def _is_mobile(user_agent: str) -> bool:
    return bool(re.search(MOBILE_UA_REGEX, user_agent, re.IGNORECASE))


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP", "")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host or ""
    return ""


def _html_esc(s) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace(chr(34), "&quot;")
    )



from sqlalchemy.sql import func


async def _increment_resource_success(db: AsyncSession, resource_id: int) -> None:
    """??7.8: ??????? success_count ??? last_check_at"""
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(DownloadResource)
        .where(DownloadResource.id == resource_id)
        .values(
            success_count=DownloadResource.success_count + 1,
            last_check_at=datetime.utcnow(),
        )
    )
    await db.flush()


async def _increment_resource_fail(db: AsyncSession, resource_id: int) -> None:
    """??7.8: ??????? fail_count ??? last_check_at"""
    from sqlalchemy import update as sql_update
    await db.execute(
        sql_update(DownloadResource)
        .where(DownloadResource.id == resource_id)
        .values(
            fail_count=DownloadResource.fail_count + 1,
            last_check_at=datetime.utcnow(),
        )
    )
    await db.flush()


@router.get("/api/download/qr/{token_str}", summary="???????")
async def generate_qr_code(token_str: str, db: AsyncSession = Depends(get_db)):
    if token_str in _qr_cache:
        return StreamingResponse(
            io.BytesIO(_qr_cache[token_str]),
            media_type="image/png",
        )

    token = await download_service.get_token_by_string(db, token_str)
    if not token:
        raise HTTPException(status_code=404, detail="???????")

    qr_url = f"{SITE_URL}/d/{token_str}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()
    buf.seek(0)

    _qr_cache[token_str] = png_bytes

    return StreamingResponse(buf, media_type="image/png")


@router.get("/download/{resource_id}", summary="??????")
async def download_entry(
    resource_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_agent = request.headers.get("user-agent", "")
    ip = _get_client_ip(request)

    try:
        token_obj, created = await download_service.get_or_create_token(db, resource_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    is_mobile = _is_mobile(user_agent)
    device_type = "mobile" if is_mobile else "pc"

    if is_mobile:
        info = await download_service.resolve_resource_for_download(db, token_obj)
        if not info:
            raise HTTPException(status_code=404, detail="???????????")

        await download_service.log_download_action(
        db, token_obj.token, resource_id, token_obj.game_id,
        ip, user_agent, device_type, "redirect",
    )
        # 模块7.8: 记录成功跳转
        await _increment_resource_success(db, resource_id)

        return RedirectResponse(info["share_url"], status_code=302)

    info = await download_service.resolve_resource_for_download(db, token_obj)
    if not info:
        raise HTTPException(status_code=404, detail="???????????")

    await download_service.log_download_action(
        db, token_obj.token, resource_id, token_obj.game_id,
        ip, user_agent, device_type, "view",
    )

    return HTMLResponse(
        content=_render_pc_download_page(token_obj.token, info)
    )


@router.get("/d/{token_str}", summary="Token ????")
async def token_download(
    token_str: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user_agent = request.headers.get("user-agent", "")
    ip = _get_client_ip(request)
    is_mobile = _is_mobile(user_agent)
    device_type = "mobile" if is_mobile else "pc"

    token_obj = await download_service.get_token_by_string(db, token_str)
    if not token_obj:
        return HTMLResponse(
            content=_render_error_page("??????????"),
            status_code=404,
        )

    info = await download_service.resolve_resource_for_download(db, token_obj)
    if not info:
        return HTMLResponse(
            content=_render_error_page("???????????"),
            status_code=404,
        )

    await download_service.log_download_action(
        db, token_str, token_obj.resource_id, token_obj.game_id,
        ip, user_agent, device_type,
        "redirect" if is_mobile else "view",
    )

    if is_mobile:
        return RedirectResponse(info["share_url"], status_code=302)

    return HTMLResponse(
        content=_render_pc_download_page(token_str, info)
    )


# ==================== ???? ====================


def _render_pc_download_page(token_str: str, info: dict) -> str:
    game_title = _html_esc(info["game_title"])
    provider_name = _html_esc(info["provider_name"])
    extract_code = _html_esc(info["extract_code"])
    resource_title = _html_esc(info["resource_title"])

    provider_info = ""
    if extract_code:
        provider_info += f"""
        <div class="dl-info-row">
            <span class="dl-info-label">???</span>
            <span class="dl-info-value extract-code">{extract_code}</span>
        </div>"""

    resource_title_html = ""
    if resource_title:
        resource_title_html = f'<p class="qr-resource-title">{resource_title}</p>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>???? - {game_title} - {SITE_NAME}</title>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                         "Microsoft YaHei", sans-serif;
            background: #0f0f1a;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 40px 20px;
        }}
        .header {{
            width: 100%;
            max-width: 500px;
            margin-bottom: 32px;
        }}
        .header .logo {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #fff;
            text-decoration: none;
        }}
        .header .logo span {{ color: #e94560; }}
        .dl-card {{
            background: #1a1a2e;
            border: 1px solid #2a2a40;
            border-radius: 12px;
            padding: 36px 32px;
            max-width: 460px;
            width: 100%;
            text-align: center;
        }}
        .dl-game-name {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }}
        .qr-resource-title {{
            color: #e94560;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }}
        .dl-provider-badge {{
            display: inline-block;
            background: #16213e;
            color: #64b5f6;
            font-size: 0.85rem;
            font-weight: 600;
            padding: 4px 14px;
            border-radius: 20px;
            margin-bottom: 24px;
        }}
        .qr-code {{
            display: flex;
            justify-content: center;
            margin-bottom: 16px;
        }}
        .qr-code img {{
            width: 220px;
            height: 220px;
            border-radius: 10px;
            background: #fff;
            padding: 10px;
            image-rendering: pixelated;
        }}
        .qr-tip {{
            color: #999;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-bottom: 20px;
        }}
        .qr-tip svg {{ flex-shrink: 0; }}
        .dl-info {{
            text-align: left;
            margin: 0 auto 20px;
            max-width: 280px;
        }}
        .dl-info-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid #2a2a40;
            font-size: 0.9rem;
        }}
        .dl-info-label {{
            color: #888;
        }}
        .dl-info-value {{
            color: #e0e0e0;
            font-weight: 500;
        }}
        .extract-code {{
            font-family: "SF Mono", "Cascadia Code", "Consolas", monospace;
            background: #0f0f1a;
            padding: 2px 10px;
            border-radius: 4px;
            color: #ffd54f;
            letter-spacing: 0.1em;
        }}
        .dl-instructions {{
            background: #0f0f1a;
            border-radius: 8px;
            padding: 16px;
            text-align: left;
            font-size: 0.85rem;
            color: #aaa;
            line-height: 1.7;
        }}
        .dl-instructions ol {{
            padding-left: 20px;
        }}
        .dl-instructions li {{
            margin-bottom: 6px;
        }}
        .back-link {{
            margin-top: 24px;
            color: #777;
            font-size: 0.85rem;
            text-decoration: none;
            transition: color 0.2s;
        }}
        .back-link:hover {{ color: #e94560; }}
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="logo">??<span>??</span></a>
    </div>
    <div class="dl-card">
        <h1 class="dl-game-name">{game_title}</h1>
        {resource_title_html}
        <span class="dl-provider-badge">{provider_name}</span>
        <div class="qr-code">
            <img src="/api/download/qr/{token_str}" alt="?????" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22220%22 height=%22220%22><rect width=%22220%22 height=%22220%22 fill=%22%23f0f0f0%22/><text x=%22110%22 y=%22115%22 text-anchor=%22middle%22 font-size=%2214%22 fill=%22%23999%22>????</text></svg>'">
        </div>
        <p class="qr-tip">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                <line x1="12" y1="18" x2="12.01" y2="18"/>
            </svg>
            ????????????
        </p>
        <div class="dl-info">
            <div class="dl-info-row">
                <span class="dl-info-label">??</span>
                <span class="dl-info-value">{provider_name}</span>
            </div>
            {provider_info}
        </div>
        <div class="dl-instructions">
            <ol>
                <li>???????????</li>
                <li>??????????????</li>
                {"<li>????? <strong>" + extract_code + "</strong> ????</li>" if extract_code else ""}
            </ol>
        </div>
    </div>
    <a href="/" class="back-link">&larr; ????</a>
</body>
</html>"""


def _render_error_page(message: str) -> str:
    msg = _html_esc(message)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>?? - {SITE_NAME}</title>
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                         "Microsoft YaHei", sans-serif;
            background: #0f0f1a;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            text-align: center;
        }}
        .header {{ margin-bottom: 30px; }}
        .header .logo {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #fff;
            text-decoration: none;
        }}
        .header .logo span {{ color: #e94560; }}
        .error-msg {{
            color: #e94560;
            font-size: 1.1rem;
            margin-bottom: 20px;
        }}
        .back-link {{
            color: #777;
            font-size: 0.85rem;
            text-decoration: none;
        }}
        .back-link:hover {{ color: #e94560; }}
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="logo">??<span>??</span></a>
    </div>
    <p class="error-msg">{msg}</p>
    <a href="/" class="back-link">&larr; ????</a>
</body>
</html>"""
