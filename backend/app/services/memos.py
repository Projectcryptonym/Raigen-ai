import os
import httpx
from typing import List, Dict, Optional

BASE = os.getenv("MEMOS_URL", "http://localhost:7000")
KEY = os.getenv("MEMOS_API_KEY", "")

async def _post(path: str, json_data: dict):
    """Make POST request to MemOS API"""
    headers = {"Authorization": f"Bearer {KEY}"} if KEY else {}
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}{path}", json=json_data, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()

async def a_store(kind: str, text: str, meta: dict) -> str:
    """Async version of memory store"""
    try:
        data = await _post("/mem/store", {"kind": kind, "text": text, "meta": meta})
        return data.get("id", "mem_stub")
    except Exception as e:
        print(f"[memos] Store failed: {e}")
        return f"mem_{kind}_stub"

def memory_store(kind: str, text: str, meta: dict) -> str:
    """Sync wrapper for memory store"""
    import anyio
    return anyio.run(a_store, kind, text, meta)

async def a_search(query: str, k: int = 8) -> List[Dict]:
    """Async version of memory search"""
    try:
        data = await _post("/mem/search", {"query": query, "k": k})
        return data.get("results", [])
    except Exception as e:
        print(f"[memos] Search failed: {e}")
        return []

def memory_search(query: str, k: int = 8) -> List[Dict]:
    """Sync wrapper for memory search"""
    import anyio
    return anyio.run(a_search, query, k)

class MemOSClient:
    def __init__(self, base_url: str = BASE, api_key: Optional[str] = KEY):
        self.base_url = base_url
        self.api_key = api_key

    def store(self, kind: str, text: str, meta: Dict) -> str:
        return memory_store(kind, text, meta)

    def search(self, query: str, k: int = 8) -> List[Dict]:
        return memory_search(query, k)

    def thread(self, user_id: str, topic: str, k_recent: int = 10) -> List[Dict]:
        return []

    def patterns(self, user_id: str, weeks: int = 4) -> Dict:
        return {"adherence_trend": None, "trigger_events": [], "mood_trend": None, "common_blockers": []}

mem_client = MemOSClient() 