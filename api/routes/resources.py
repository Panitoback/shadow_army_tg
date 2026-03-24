from fastapi import APIRouter, Header

from api.auth import validate_init_data
from services.recursos_service import get_resource_status, start_collection, collect_resource
from services.jugador_service import add_experience

router = APIRouter()


@router.get("/resources/status")
async def resource_status(x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    return get_resource_status(user_data["id"])


@router.post("/resources/{resource}/start")
async def start_resource(resource: str, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    return start_collection(user_data["id"], resource)


@router.post("/resources/{resource}/collect")
async def collect(resource: str, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    result = collect_resource(user_data["id"], resource)

    if result.get("collected"):
        leveled_up, new_level = add_experience(user_data["id"], result["xp"])
        result["leveled_up"] = leveled_up
        result["new_level"] = new_level

    return result
