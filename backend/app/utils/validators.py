# app/utils/validators.py
"""
데이터 검증 유틸리티
"""

import re
from typing import Any

from app.core.exceptions import ValidationError


def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_phone_number(phone: str) -> bool:
    """전화번호 형식 검증 (한국 형식)"""
    # 010-1234-5678, 02-123-4567 등의 형식
    pattern = r"^(\d{2,3})-(\d{3,4})-(\d{4})$"
    return bool(re.match(pattern, phone))


def validate_password_strength(password: str) -> dict[str, Any]:
    """비밀번호 강도 검증"""
    errors = []

    if len(password) < 8:
        errors.append("비밀번호는 최소 8자 이상이어야 합니다.")

    if not re.search(r"[A-Z]", password):
        errors.append("비밀번호에는 대문자가 포함되어야 합니다.")

    if not re.search(r"[a-z]", password):
        errors.append("비밀번호에는 소문자가 포함되어야 합니다.")

    if not re.search(r"\d", password):
        errors.append("비밀번호에는 숫자가 포함되어야 합니다.")

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("비밀번호에는 특수문자가 포함되어야 합니다.")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "strength": "strong" if len(errors) == 0 else "weak",
    }


def validate_text_length(text: str, max_length: int = 1000) -> bool:
    """텍스트 길이 검증"""
    return len(text.strip()) <= max_length


def validate_node_id_format(node_id: str) -> bool:
    """노드 ID 형식 검증"""
    # 영문, 숫자, 언더스코어만 허용
    pattern = r"^[a-zA-Z0-9_]+$"
    return bool(re.match(pattern, node_id))


def validate_version_format(version: str) -> bool:
    """버전 형식 검증 (예: 1.0, 2.1.3)"""
    pattern = r"^\d+\.\d+(\.\d+)?$"
    return bool(re.match(pattern, version))


def validate_audio_duration(duration: float, max_duration: float = 300.0) -> bool:
    """오디오 지속 시간 검증 (초 단위)"""
    return 0 < duration <= max_duration


def validate_json_structure(data: Any, required_fields: list[str]) -> dict[str, Any]:
    """JSON 구조 검증"""
    if not isinstance(data, dict):
        return {"is_valid": False, "error": "데이터는 객체 형태여야 합니다."}

    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)

    if missing_fields:
        return {
            "is_valid": False,
            "error": f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}",
        }

    return {"is_valid": True}


class DataValidator:
    """데이터 검증 클래스"""

    @staticmethod
    def validate_scenario_node_config(node_type: str, config: dict[str, Any]) -> None:
        """시나리오 노드 설정 검증"""

        if node_type == "branch":
            # 분기 노드는 branches 필드가 필요
            if "branches" not in config:
                raise ValidationError("분기 노드에는 branches 설정이 필요합니다.")

            branches = config["branches"]
            if not isinstance(branches, list) or len(branches) == 0:
                raise ValidationError("branches는 비어있지 않은 배열이어야 합니다.")

            for branch in branches:
                if not isinstance(branch, dict):
                    raise ValidationError("각 branch는 객체여야 합니다.")

                required_branch_fields = ["key", "label", "target"]
                for field in required_branch_fields:
                    if field not in branch:
                        raise ValidationError(f"branch에 {field} 필드가 필요합니다.")

        elif node_type == "message":
            # 메시지 노드는 text 또는 voice_actor_id가 필요
            if "text" not in config and "voice_actor_id" not in config:
                raise ValidationError(
                    "메시지 노드에는 text 또는 voice_actor_id가 필요합니다."
                )

        elif node_type == "transfer":
            # 상담원 연결 노드는 target 설정이 필요
            if "target" not in config:
                raise ValidationError("상담원 연결 노드에는 target 설정이 필요합니다.")

    @staticmethod
    def validate_tts_settings(settings_dict: dict[str, Any]) -> None:
        """TTS 설정 검증"""

        # 속도 검증 (0.5 ~ 2.0)
        if "speed" in settings_dict:
            speed = settings_dict["speed"]
            if not isinstance(speed, int | float) or not (0.5 <= speed <= 2.0):
                raise ValidationError("속도는 0.5에서 2.0 사이의 값이어야 합니다.")

        # 톤 검증
        valid_tones = ["friendly", "professional", "calm", "energetic"]
        if "tone" in settings_dict:
            tone = settings_dict["tone"]
            if tone not in valid_tones:
                raise ValidationError(
                    f"톤은 다음 중 하나여야 합니다: {', '.join(valid_tones)}"
                )

        # 감정 검증
        valid_emotions = ["bright", "neutral", "sad", "happy", "excited"]
        if "emotion" in settings_dict:
            emotion = settings_dict["emotion"]
            if emotion not in valid_emotions:
                raise ValidationError(
                    f"감정은 다음 중 하나여야 합니다: {', '.join(valid_emotions)}"
                )
