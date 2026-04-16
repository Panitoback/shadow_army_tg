from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from api.auth import validate_init_data
from services.battle_service import get_battle_history, get_power_ranking, resolve_battle
from services.player_service import get_user_by_username

router = APIRouter()


def _check(result: dict) -> dict:
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


class AttackRequest(BaseModel):
    username: str = Field(min_length=1)


@router.post("/battle/attack")
async def attack(body: AttackRequest, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    attacker_id = user_data["id"]

    defender = get_user_by_username(body.username)
    if not defender:
        raise HTTPException(status_code=404, detail="Player not found")

    defender_id = defender[0]
    return _check(resolve_battle(attacker_id, defender_id))


@router.get("/battle/history")
async def history(x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    rows = get_battle_history(user_data["id"])
    return [
        {
            "id": row[0],
            "attacker": row[1],
            "defender": row[2],
            "winner_id": row[3],
            "attacker_power": row[4],
            "defender_power": row[5],
            "resources_stolen": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
        }
        for row in rows
    ]


@router.get("/battle/power")
async def power_ranking(x_init_data: str = Header(...)):
    validate_init_data(x_init_data)
    return get_power_ranking()
