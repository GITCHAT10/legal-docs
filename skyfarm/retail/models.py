from pydantic import BaseModel
from datetime import datetime
from typing import List

class SaleItem(BaseModel):
    product_id: str
    quantity: float
    price: float

class RetailSale(BaseModel):
    id: str
    store_id: str
    items: List[SaleItem]
    total_amount: float
    timestamp: datetime = datetime.now()

# In-memory storage
sales = {}

def record_sale(sale: RetailSale):
    sales[sale.id] = sale
    return sale
