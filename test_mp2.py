import os
from dotenv import load_dotenv
load_dotenv()
import mercadopago

sdk = mercadopago.SDK(os.getenv("MP_ACCESS_TOKEN"))

preference_data = {
    "items": [{"title": "Test", "quantity": 1, "unit_price": 100}],
    "back_urls": {
        "success": "https://www.google.com/success",
        "failure": "https://www.google.com/failure",
        "pending": "https://www.google.com/pending"
    },
    "auto_return": "approved"
}

res = sdk.preference().create(preference_data)
print(res)
