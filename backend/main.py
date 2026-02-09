# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

from customer import router as customer_router   
from items import router as items_router
from employees import router as employees_router
from login import router as login_router
from pricing_router import router as pricing_router
from shipping import router as shipping_router
from quotation import router as quotation_router
from utils.baht_text import baht_text
from cross_sell_router import cross_sell_router
from invoice_router import router as invoice_router
from item_update import router as item_update_router
from customer_analytics import router as customer_analytics_router
from api.router_sq import router as sq_router
from products_router import api_router
from special_price_request.router import router as special_price_request_router
from cache_refresh_router import router as cache_refresh_router

from config.config_external_api import CUSTOMER_API_KEY

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
import sys
import threading
import time

# Ensure logs are flushed immediately to stdout for Windows Console visibility
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Detect if running in frozen mode (PyInstaller)
if getattr(sys, 'frozen', False):
    # If _MEIPASS is defined, we are in onefile mode (or onedir with internal bundle logic)
    # But for standard onedir (which we use), resources are relative to the executable
    if hasattr(sys, "_MEIPASS"):
        BASE_DIR = sys._MEIPASS
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Smart Pricing API", version="1.0.0")

# โหลด template จาก backend ตรง ๆ
env = Environment(loader=FileSystemLoader(BASE_DIR))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for flexibility in offline/docker envs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotation_router, prefix="/api")
app.include_router(customer_router)
app.include_router(items_router,prefix="/api")
app.include_router(employees_router,prefix="/api")
app.include_router(login_router,prefix="/api")
app.include_router(pricing_router) # Router defines /api/pricing prefix internally
app.include_router(shipping_router) # Router defines /api/shipping prefix internally
app.include_router(cross_sell_router,prefix="/api")
app.include_router(invoice_router)
app.include_router(item_update_router, prefix="/api")
app.include_router(customer_analytics_router)
app.include_router(sq_router, prefix="/api")
app.include_router(api_router, prefix="/api")
app.include_router(special_price_request_router, prefix="/api")
app.include_router(cache_refresh_router)



# --- Print Endpoint (Root Level) ---
@app.post("/api/print/quotation")
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

# --- Static Files Serving (Fallback for Native App) ---
# When running as a native app (frozen) or if 'dist' exists nearby, serve frontend.
# In Docker, Nginx handles this, but this won't hurt as Nginx proxies /api and serves / itself.

dist_path = os.path.join(BASE_DIR, "dist")
if not os.path.exists(dist_path):
    # Try looking in the parent directory (development mode)
    dist_path = os.path.join(os.path.dirname(BASE_DIR), "frontend", "dist")

if os.path.exists(dist_path):
    print(f"Serving static files from: {dist_path}")
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_path, "assets")), name="assets")

    @app.get("/{catchall:path}")
    async def serve_react_app(catchall: str):
        # Allow API calls to pass through
        if (
            catchall.startswith("api/")
            or catchall.startswith("print/")
            or catchall.startswith("login")
        ):
            return Response(status_code=404)


        # Check if file exists in dist
        file_path = os.path.join(dist_path, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # Fallback to index.html for SPA routing
        return FileResponse(os.path.join(dist_path, "index.html"))

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# ========================================
# Background Email Checker Thread
# ========================================
def email_checker_background():
    """
    Background thread ที่ตรวจสอบ email ทุก 1 นาที
    รันอัตโนมัติเมื่อ FastAPI start
    """
    from special_price_request.email_reply_checker import check_email_replies
    
    CHECK_INTERVAL_MINUTES = 1  # ปรับได้ตามต้องการ
    
    print("\n" + "="*60)
    print("🚀 Email Checker Background Service Started")
    print(f"⏰ Checking emails every {CHECK_INTERVAL_MINUTES} minute(s)")
    print("="*60 + "\n")
    
    while True:
        try:
            check_email_replies()
        except Exception as e:
            print(f"❌ Error in email checker: {e}")
        
        # รอ N นาที
        time.sleep(CHECK_INTERVAL_MINUTES * 60)

@app.on_event("startup")
async def startup_event():
    """
    เริ่ม background thread เมื่อ FastAPI start
    """
    # Start email checker in background thread
    email_thread = threading.Thread(target=email_checker_background, daemon=True)
    email_thread.start()
    print("✅ Email checker thread started")

if __name__ == "__main__":
    import uvicorn
    # Enable logging for debugging
    # We use line buffering instead of redirecting to file, so the .bat pause can capture it.
    print("--- Starting Server ---")

    if not CUSTOMER_API_KEY:
        print("\n" + "="*60)
        print(" [WARNING] CUSTOMER_API_KEY is not set or empty!")
        print(" Please create a .env file with your API keys.")
        print("="*60 + "\n")

    # Pass the app object directly instead of the import string "main:app"
    # This prevents "Could not import module 'main'" errors in frozen (PyInstaller) environments
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False, log_level="info")


#uvicorn main:app --reload --port 8000
#npx prettier --write src
