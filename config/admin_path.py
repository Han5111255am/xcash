def normalize_admin_path(value: str | None) -> str:
    normalized = (value or "").strip().strip("/")
    if not normalized:
        return ""
    return normalized


def admin_route_prefix(admin_path: str) -> str:
    if not admin_path:
        return ""
    return f"{admin_path}/"
