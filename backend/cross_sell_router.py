from fastapi import APIRouter
from schemas.cross_sell import CrossSellRequest
from services.cross_sell_service import get_cross_sell

cross_sell_router = APIRouter(
    prefix="/cross-sell",
    tags=["cross-sell"]
)

@cross_sell_router.post("")
def cross_sell_endpoint(req: CrossSellRequest):
    products = [p.dict() for p in req.products]
    return get_cross_sell(products)
