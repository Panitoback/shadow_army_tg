from enum import Enum

from fastapi import APIRouter, Header, HTTPException

from api.auth import validate_init_data
from services.resources_service import get_resource_status, start_collection, collect_resource
from services.player_service import add_experience

router = APIRouter()


class ResourceName(str, Enum):
    wood  = "wood"
    stone = "stone"
    water = "water"
    food  = "food"


def _check(result: dict) -> dict:
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/resources/status")
async def resource_status(x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    return get_resource_status(user_data["id"])


@router.post("/resources/{resource}/start")
async def start_resource(resource: ResourceName, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    return _check(start_collection(user_data["id"], resource.value))


@router.post("/resources/{resource}/collect")
async def collect(resource: ResourceName, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    result = _check(collect_resource(user_data["id"], resource.value))

    if result.get("collected"):
        leveled_up, new_level = add_experience(user_data["id"], result["xp"])
        result["leveled_up"] = leveled_up
        result["new_level"] = new_level

    return result
