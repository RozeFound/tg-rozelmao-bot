from typing import AsyncGenerator
from aiohttp import request

class Stats:

    @staticmethod
    async def get_stats(group_id: str) -> dict:
        url = f"https://grstats.me/api/chat/{group_id}"
        async with request('GET', url) as response:
            return (await response.json()).get("res")

    @staticmethod
    async def get_top_words(group_id: str) -> AsyncGenerator:
        stats = await Stats.get_stats(group_id)
        for word in stats.get("top_words", []):
            yield word[0], word[1]
