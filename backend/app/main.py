from fastapi import FastAPI

from app.api.v1.internal.products import router as products_router

app = FastAPI(
    title="Credit Tracker API",
    version="0.1.0",
    description="Walking skeleton: Colombia credit card installment (cuota) calculation engine.",
)

app.include_router(products_router, prefix="/api/v1/internal")


@app.get("/health")
async def health():
    return {"status": "ok"}
