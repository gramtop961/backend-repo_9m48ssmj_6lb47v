import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from datetime import datetime, timezone

from database import db, create_document, get_documents
from schemas import Menuitem, Order, Payment, SCHEMAS

app = FastAPI(title="MessEase API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def serialize_doc(doc: dict):
    out = {**doc}
    if "_id" in out:
        out["id"] = str(out.pop("_id"))
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.astimezone(timezone.utc).isoformat()
    return out

@app.get("/")
def read_root():
    return {"message": "MessEase Backend Running"}

@app.get("/schema")
def get_schema():
    return {"collections": SCHEMAS}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["connection_status"] = "Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "❌ Not Connected"
    except Exception as e:
        response["database"] = f"⚠️ Error: {str(e)[:80]}"
    return response

# Menu Endpoints
@app.get("/menu")
def list_menu(limit: Optional[int] = 100, available_only: bool = True):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    query = {"is_available": True} if available_only else {}
    docs = get_documents("menuitem", query, limit)
    return [serialize_doc(d) for d in docs]

@app.post("/menu", status_code=201)
def add_menu_item(item: Menuitem):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    new_id = create_document("menuitem", item)
    return {"id": new_id}

# Orders
@app.get("/orders")
def list_orders(limit: Optional[int] = 50):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    docs = get_documents("order", {}, limit)
    return [serialize_doc(d) for d in docs]

@app.post("/order", status_code=201)
def create_order(order: Order):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    # basic validation of items and subtotal
    calc_subtotal = sum((i.get("qty", 1) * i.get("unit_price", 0.0)) for i in order.items)
    if round(calc_subtotal, 2) != round(order.subtotal, 2):
        raise HTTPException(status_code=400, detail="Subtotal mismatch")
    new_id = create_document("order", order)
    return {"id": new_id, "status": order.status}

# Payments
@app.get("/payments")
def list_payments(limit: Optional[int] = 50):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    docs = get_documents("payment", {}, limit)
    return [serialize_doc(d) for d in docs]

@app.post("/payment", status_code=201)
def create_payment(payment: Payment):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    # Mark paid_at for succeeded payments
    data = payment.model_dump()
    if data.get("status") == "succeeded" and not data.get("paid_at"):
        data["paid_at"] = datetime.now(timezone.utc)
    new_id = create_document("payment", data)
    # Optionally update the related order status to paid
    try:
        if payment.status == "succeeded":
            db["order"].update_one({"_id": ObjectId(payment.order_id)}, {"$set": {"status": "paid", "updated_at": datetime.now(timezone.utc)}})
    except Exception:
        pass
    return {"id": new_id}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
