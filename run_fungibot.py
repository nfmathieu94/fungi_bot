#!/usr/bin/python3

import asyncio
import os

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.io import ConsoleIO

from fungi_bot.agent import root_agent  # adjust if package name differs


APP_NAME = "FungiBotApp"
USER_ID = os.environ.get("FUNGI_USER_ID", "nmath020")


async def main() -> None:
    session_service = InMemorySessionService()

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
        # No memory_service – history is stored in analysis_history.duckdb instead
    )

    io = ConsoleIO()
    session_id = "fungibot-console-session"

    await runner.run(
        io=io,
        user_id=USER_ID,
        session_id=session_id,
    )


if __name__ == "__main__":
    asyncio.run(main())

