from fastapi import FastAPI

from app.api import leases, maintenance, payments, properties, tenants


app = FastAPI(title="Hearthside Property API", version="0.1.0")
app.include_router(properties.router)
app.include_router(tenants.router)
app.include_router(leases.router)
app.include_router(maintenance.router)
app.include_router(payments.router)


@app.get("/health")
def health():
    return {"status": "ok"}
