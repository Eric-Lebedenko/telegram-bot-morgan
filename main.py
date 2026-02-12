from __future__ import annotations

import argparse
import asyncio

from telegram_app import run_telegram
from discord_app import run_discord


async def main() -> None:
    parser = argparse.ArgumentParser(description='Unified Telegram + Discord investment bot')
    parser.add_argument('--telegram', action='store_true', help='Run Telegram bot')
    parser.add_argument('--discord', action='store_true', help='Run Discord bot')
    args = parser.parse_args()

    tasks = []
    if args.telegram or (not args.telegram and not args.discord):
        tasks.append(asyncio.create_task(asyncio.to_thread(run_telegram)))
    if args.discord or (not args.telegram and not args.discord):
        tasks.append(asyncio.create_task(run_discord()))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
