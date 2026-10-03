import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "SwiftCargo/1.0 (contact: admin@swiftcargo.local)"


def geocode(address):
    """
    Look up an address string and return (lat, lng) or (None, None).
    Uses OpenStreetMap's free Nominatim API — no key required.
    """
    if not address or not address.strip():
        return None, None

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None, None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        print(f"[geocode] Failed for '{address}': {e}")
        return None, None