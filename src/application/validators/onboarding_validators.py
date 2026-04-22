from domain.value_objects.enums import ProficiencyLevel


def validate_display_name(v: str) -> tuple[bool, str]:
    """Validate tên hiển thị: không rỗng, 1–50 ký tự."""
    if not v or not v.strip():
        return False, "Tên hiển thị không được để trống"
    if len(v.strip()) > 50:
        return False, "Tên hiển thị không được vượt quá 50 ký tự"
    return True, ""


def validate_cefr_level(v: str, field_name: str = "Trình độ") -> tuple[bool, str]:
    """Validate trình độ CEFR: phải là A1/A2/B1/B2/C1/C2."""
    try:
        ProficiencyLevel(v)
        return True, ""
    except ValueError:
        return False, f"{field_name} '{v}' không hợp lệ. Chỉ chấp nhận: A1, A2, B1, B2, C1, C2"


def validate_avatar_url(v: str) -> tuple[bool, str]:
    """Validate avatar URL: optional, nếu có phải dùng HTTPS."""
    if not v:
        return True, ""  # optional field
    if not v.startswith("https://"):
        return False, "URL ảnh đại diện phải dùng HTTPS"
    return True, ""
