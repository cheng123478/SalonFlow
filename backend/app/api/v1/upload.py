"""文件上传接口（头像等）。"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.response import success

router = APIRouter(
    prefix="/upload",
    tags=["上传"],
    dependencies=[Depends(get_current_user)],
)

_UPLOAD_DIR = Path(settings.upload_dir).resolve()
_AVATAR_DIR = _UPLOAD_DIR / "avatars"

_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
_MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/avatar")
async def upload_avatar(file: UploadFile):
    """上传头像，返回可访问的相对 URL。"""
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/gif/webp 图片")

    data = await file.read()
    if len(data) > _MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in _ALLOWED_EXT:
        ext = "png"

    _AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    (_AVATAR_DIR / name).write_bytes(data)

    return success({"url": f"/uploads/avatars/{name}"}, "上传成功")