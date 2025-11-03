from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# MessEase Schemas (each class name lowercased -> collection name)

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: Literal["student", "admin"] = Field("student", description="User role")
    is_active: bool = Field(True, description="Whether user is active")

class Menuitem(BaseModel):
    title: str = Field(..., description="Dish name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in INR")
    is_available: bool = Field(True, description="Availability for today")
    category: Optional[str] = Field(None, description="Breakfast/Lunch/Dinner/Snacks")

class Order(BaseModel):
    user_email: str = Field(..., description="Email of the student placing the order")
    items: List[dict] = Field(..., description="List of ordered items with qty and price")
    # items: [{ menuitem_id: str, title: str, qty: int, unit_price: float, line_total: float }]
    subtotal: float = Field(..., ge=0)
    status: Literal["pending", "paid", "cancelled"] = Field("pending")

class Payment(BaseModel):
    order_id: str = Field(..., description="Related order id")
    amount: float = Field(..., ge=0)
    currency: Literal["INR", "USD"] = Field("INR")
    provider: Literal["stripe", "cash", "upi"] = Field("stripe")
    status: Literal["succeeded", "failed", "pending"] = Field("pending")
    paid_at: Optional[datetime] = Field(None)

# Optional: simple schema registry for /schema endpoint consumers
SCHEMAS = {
    "user": User.model_json_schema(),
    "menuitem": Menuitem.model_json_schema(),
    "order": Order.model_json_schema(),
    "payment": Payment.model_json_schema(),
}
