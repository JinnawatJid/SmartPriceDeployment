# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

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
from utils.baht_text import baht_text


from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
import sys
import logging

# --- LOGGING CONFIG (Ensure visible stdout in frozen app) ---
sys.stdout.reconfigure(line_buffering=True)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:    %(message)s')
logger = logging.getLogger(__name__)
# ------------------------------------------------------------

app = FastAPI(title="Smart Pricing API", version="1.0.0")

# --- BASE DIR SETUP (Dev vs Frozen) ---
if getattr(sys, 'frozen', False):
    # PyInstaller onedir mode:
    # In newer PyInstaller (v6+), bundled resources often live in `sys._MEIPASS` (_internal),
    # even in onedir mode. We check there first.
    if hasattr(sys, '_MEIPASS'):
        BASE_DIR = sys._MEIPASS
    else:
        # Fallback for older PyInstaller or if _MEIPASS is not used (resources at root)
        BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logger.info(f"Resolved BASE_DIR to: {BASE_DIR}")

# โหลด template จาก backend ตรง ๆ (หรือจาก unpacked bundle)
env = Environment(loader=FileSystemLoader(BASE_DIR))


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
       "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4000",
        "http://127.0.0.1:4000",
        "http://localhost:3200", # Native bundle default
        "http://127.0.0.1:3200",
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
app.include_router(pricing_router) # Note: pricing_router paths might need review if they don't have prefix
app.include_router(shipping_router)
app.include_router(glass_router,prefix="/api")
app.include_router(aluminium_router,prefix="/api")
app.include_router(cline_router,prefix="/api")
app.include_router(accessories_router,prefix="/api")
app.include_router(sealant_router,prefix="/api")
app.include_router(gypsum_router,prefix="/api")


@app.get("/api/health")
def root():
    return {"message": "Smart Pricing API connected"}

@app.post("/print/quotation")
def print_quotation(payload: dict):

    print("\n=== PRINT PAYLOAD ITEMS ===")
    for it in payload.get("items", []):
        print(it.get("code"), it.get("unit"))


    net_total = payload.get("netTotal", 0)
    payload["amountText"] = baht_text(net_total)
    
    template = env.get_template("quotation.html")

    html = template.render(q=payload)

    pdf = HTML(
        string=html,
        base_url=BASE_DIR   # ⭐ สำคัญ: ให้ WeasyPrint หา font / asset เจอ
    ).write_pdf()

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=quotation.pdf"
        }
    )

# --- Static Files & SPA Fallback ---
# Only verify static files exist if we are supposed to serve them (usually in prod bundle)
# In dev, we might run this file independently.
# However, if we bundle 'dist' into the executable/directory, we serve it.

# Check if 'dist' exists in BASE_DIR (bundled) or adjacent (dev structure check?)
# In the PyInstaller spec, we will put 'dist' inside the bundle root or a subdir.
# Let's assume we bundle the 'dist' folder into the root of the temp directory.
dist_dir = os.path.join(BASE_DIR, "dist")
logger.info(f"Checking for frontend at: {dist_dir}")

if os.path.exists(dist_dir):
    logger.info(f"Found frontend at {dist_dir}. Mounting static files.")
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        # Allow API calls to pass through if they weren't caught above
        if full_path.startswith("api/") or full_path.startswith("print/"):
             return Response("Not Found", status_code=404)

        # Check if a specific file was requested (e.g. favicon.ico)
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Otherwise serve index.html for SPA routing
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    logger.warning("Frontend dist directory NOT found. SPA routes will return 404.")

# Note: In production (frozen), the app is usually run via Uvicorn programmatically or direct entry.
# We will add a __main__ block for standalone execution if needed by PyInstaller.

if __name__ == "__main__":
    import uvicorn
    # Use port 3200 as requested for the batch deployment
    uvicorn.run(app, host="0.0.0.0", port=3200)
