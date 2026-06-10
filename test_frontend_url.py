import os
from dotenv import load_dotenv
load_dotenv()
from app.core.config import settings
print(settings.FRONTEND_URL)
