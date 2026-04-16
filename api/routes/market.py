from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from api.auth import validate_init_data
from services.trading_service import buy_offer, cancel_offer, create_offer, get_active_offers

router = APIRouter()


def _check(result: dict) -> dict:
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


class SellRequest(BaseModel):
    resource: str
    amount: int = Field(gt=0)
    price_gold: int = Field(gt=0)


@router.get("/market")
async def list_offers(x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    user_id = user_data["id"]
    offers = get_active_offers()
    return [
        {
            "id": offer_id,
            "seller": username,
            "resource": resource,
            "amount": amount,
            "price_gold": price_gold,
            "is_mine": seller_id == user_id,
        }
        for offer_id, seller_id, username, resource, amount, price_gold in offers
    ]


@router.post("/market/sell")
async def sell(body: SellRequest, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    return _check(create_offer(user_data["id"], body.resource, body.amount, body.price_gold))


@router.post("/market/buy/{offer_id}")
async def buy(offer_id: int, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    return _check(buy_offer(user_data["id"], offer_id))


@router.delete("/market/{offer_id}")
async def cancel(offer_id: int, x_init_data: str = Header(...)):
    user_data = validate_init_data(x_init_data)
    return _check(cancel_offer(user_data["id"], offer_id))
