"""Application entry point and development server.

This script starts the Quart development server. For production use,
use an ASGI server like Hypercorn or Uvicorn:

    hypercorn run:app --bind 0.0.0.0:5000
    uvicorn run:app --host 0.0.0.0 --port 5000
"""

import asyncio

from dotenv import load_dotenv

from app import create_app
from app.config import settings

# Load environment variables
load_dotenv()


async def main():
    """Create and run the application."""
    app = await create_app()
    return app


app = asyncio.run(main())

if __name__ == "__main__":
    app.run(host=settings.host, port=settings.port, debug=settings.debug)
