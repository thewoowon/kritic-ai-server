from decouple import config

DATABASE_URL = config("DATABASE_URL", default="sqlite+aiosqlite:///./app/db/mnm.db")
