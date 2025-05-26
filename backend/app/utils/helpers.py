# app/utils/helpers.py
"""
도우미 함수들
"""

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import aiofiles  # type: ignore
except ImportError:
    aiofiles = None

from fastapi import UploadFile

from app.core.config import settings
from app.utils.logger import logger


async def save_upload_file(
    file: UploadFile, directory: str | None = None, filename: str | None = None
) -> str:
    """업로드된 파일 저장"""

    if aiofiles is None:
        raise ImportError("aiofiles is required for file operations")

    # 디렉토리 설정
    if directory is None:
        directory = settings.UPLOAD_DIR

    # 디렉토리 생성
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    # 파일명 생성
    if filename is None:
        # UUID를 사용한 고유 파일명 생성
        file_extension = Path(file.filename).suffix if file.filename else ""
        filename = f"{uuid.uuid4()}{file_extension}"

    file_path = dir_path / filename

    # 파일 저장
    async with aiofiles.open(file_path, "wb") as f:  # type: ignore
        content = await file.read()
        await f.write(content)

    logger.info(f"File saved: {file_path}")
    return str(file_path)


def generate_file_hash(file_path: str) -> str:
    """파일 해시 생성"""
    hash_md5 = hashlib.md5()
    path = Path(file_path)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """파일 확장자 검증"""
    if not filename:
        return False

    file_extension = Path(filename).suffix.lower()
    return file_extension in [ext.lower() for ext in allowed_extensions]


def get_file_size(file_path: str) -> int:
    """파일 크기 반환 (bytes)"""
    try:
        return Path(file_path).stat().st_size
    except OSError:
        return 0


def create_directory_if_not_exists(directory: str) -> None:
    """디렉토리 생성 (존재하지 않는 경우)"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def format_file_size(size_bytes: int) -> str:
    """파일 크기를 읽기 쉬운 형태로 변환"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size_float = float(size_bytes)
    while size_float >= 1024 and i < len(size_names) - 1:
        size_float /= 1024.0
        i += 1

    return f"{size_float:.1f}{size_names[i]}"


def generate_unique_id() -> str:
    """고유 ID 생성"""
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    """파일명 정화"""
    # 특수문자 제거 및 공백을 언더스코어로 변경
    import re

    filename = re.sub(r"[^\w\s-.]", "", filename)
    filename = re.sub(r"[-\s]+", "_", filename)
    return filename


def get_current_timestamp() -> datetime:
    """현재 타임스탬프 반환"""
    return datetime.utcnow()


def dict_to_camel_case(data: dict[str, Any]) -> dict[str, Any]:
    """딕셔너리 키를 camelCase로 변환"""

    def to_camel_case(snake_str: str) -> str:
        components = snake_str.split("_")
        return components[0] + "".join(x.capitalize() for x in components[1:])

    return {to_camel_case(key): value for key, value in data.items()}


def paginate_query_params(page: int = 1, size: int | None = None) -> dict[str, int]:
    """페이징 쿼리 파라미터 검증 및 정규화"""
    if size is None:
        size = settings.DEFAULT_PAGE_SIZE

    # 유효성 검사
    page = max(1, page)
    size = min(max(1, size), settings.MAX_PAGE_SIZE)

    offset = (page - 1) * size

    return {"page": page, "size": size, "offset": offset, "limit": size}
