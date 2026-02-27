"""Application entry point and development server.

This script starts the Quart development server. For production use,
use Gunicorn’s native ASGI worker:

    gunicorn -k asgi app.main:app --reload --bind 0.0.0.0:5000
    # Gunicorn config file: see docs at
    # https://docs.gunicorn.org/en/stable/settings.html#configuration-file
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
