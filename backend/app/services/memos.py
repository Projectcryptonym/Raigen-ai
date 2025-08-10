from typing import List, Dict, Optional

class MemOSClient:
    def __init__(self, base_url: str = "http://localhost:7000", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key

    def store(self, kind: str, text: str, meta: Dict) -> str:
        # TODO: POST to MemOS when available
        return "mem_" + kind

    def search(self, query: str, k: int = 8) -> List[Dict]:
        return []

    def thread(self, user_id: str, topic: str, k_recent: int = 10) -> List[Dict]:
        return []

    def patterns(self, user_id: str, weeks: int = 4) -> Dict:
        return {"adherence_trend": None, "trigger_events": [], "mood_trend": None, "common_blockers": []}

mem_client = MemOSClient()

def memory_store(kind: str, text: str, meta: Dict) -> str:
    return mem_client.store(kind, text, meta)

def memory_search(query: str, k: int = 8) -> List[Dict]:
    return mem_client.search(query, k) 