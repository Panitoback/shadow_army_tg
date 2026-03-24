from fastapi import APIRouter, Header, HTTPException

from api.auth import validate_init_data
from services.player_service import get_user, get_inventory, get_ranking, register_user

router = APIRouter()


@router.get("/player/me")
async def get_my_profile(x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    user_id = user_data["id"]

    user = get_user(user_id)
    if not user:
        # Auto-register if the user opens the webapp without /start
        register_user(user_id, user_data.get("username") or user_data.get("first_name", ""))
        user = get_user(user_id)

    _, username, level, experience = user
    inv = get_inventory(user_id)
    wood, stone, water, food, gold = inv

    return {
        "id": user_id,
        "username": username,
        "level": level,
        "experience": experience,
        "xp_needed": level * 100,
        "inventory": {
            "wood": wood,
            "stone": stone,
            "water": water,
            "food": food,
            "gold": gold,
        },
    }


@router.get("/ranking")
async def get_player_ranking():
    ranking = get_ranking(limit=10)
    return [
        {"username": username, "level": level, "experience": experience}
        for username, level, experience in ranking
    ]
