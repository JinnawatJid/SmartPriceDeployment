from pydantic import BaseModel
from typing import Optional, List

class CartProduct(BaseModel):
    productGroup: Optional[str] = None
    productSubGroup: Optional[str] = None

class CrossSellRequest(BaseModel):
    products: List[CartProduct]

class CrossSellItem(BaseModel):
    displayName: str
    ruleNo: int
    ruleType: str
    ruleGroup: Optional[str] = None
