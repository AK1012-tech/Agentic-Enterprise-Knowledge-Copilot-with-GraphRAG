from app.utils.config import Settings


def demo_identity(settings: Settings) -> dict[str, str]:
    return {"tenant_id": settings.demo_tenant_id, "user_id": settings.demo_user_id}

