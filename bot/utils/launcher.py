import os
import glob
import asyncio
from itertools import cycle
from pyrogram import Client
from better_proxy import Proxy
from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions

global tg_clients

def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]
    return session_names

def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []
    return proxies

async def get_tg_clients() -> list[Client]:
    global tg_clients
    session_names = get_session_names()
    if not session_names:
        raise FileNotFoundError("No session files found")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]
    return tg_clients

async def process() -> None:
    session_names = get_session_names()
    
    if session_names:
        # Sessions found, start the clicker automatically
        logger.info(f"Found {len(session_names)} session(s), starting clicker...")
        tg_clients = await get_tg_clients()
        await run_tasks(tg_clients=tg_clients)
    else:
        # No sessions found, prompt to create one
        print("No session found. Please create a session.")
        await register_sessions()

async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
            )
        )
        for tg_client in tg_clients
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(process())
