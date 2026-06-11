import os
from dotenv import load_dotenv
load_dotenv()
import mercadopago

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

preference_data_1 = {
    "items": [{"title": "Test", "quantity": 1, "unit_price": 100}],
    "back_urls": {
        "success": "http://localhost:5173/success?pedido=123",
        "failure": "http://localhost:5173/failure",
        "pending": "http://localhost:5173/pending"
    },
    "auto_return": "approved"
}

preference_data_2 = {
    "items": [{"title": "Test", "quantity": 1, "unit_price": 100}],
    "back_urls": {
        "success": "http://localhost:5173/success",
        "failure": "http://localhost:5173/failure",
        "pending": "http://localhost:5173/pending"
    },
    "auto_return": "approved"
}

print("Testing with query parameters...")
res1 = sdk.preference().create(preference_data_1)
print(res1)

print("\nTesting WITHOUT query parameters...")
res2 = sdk.preference().create(preference_data_2)
print(res2)
