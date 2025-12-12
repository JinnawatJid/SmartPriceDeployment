# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from customer import router as customer_router   
from items import router as items_router
from employees import router as employees_router
from login import router as login_router
from pricing_router import router as pricing_router
from shipping import router as shipping_router
from glass_router import router as glass_router
from aluminium_router import router as aluminium_router
from cline_router import router as cline_router
from accessories_router import router as accessories_router
from sealant_router import router as sealant_router
from gypsum_router import router as gypsum_router
from quotation import router as quotation_router
app = FastAPI(title="Smart Pricing API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:4000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotation_router, prefix="/api")
app.include_router(customer_router, prefix="/api")
app.include_router(items_router,prefix="/api")
app.include_router(employees_router,prefix="/api")
app.include_router(login_router,prefix="/api")
app.include_router(pricing_router)
app.include_router(shipping_router)
app.include_router(glass_router,prefix="/api")
app.include_router(aluminium_router,prefix="/api")
app.include_router(cline_router,prefix="/api")
app.include_router(accessories_router,prefix="/api")
app.include_router(sealant_router,prefix="/api")
app.include_router(gypsum_router,prefix="/api")


@app.get("/")
def root():
    return {"message": "Smart Pricing API connected"}


#uvicorn main:app --reload --port 4000

