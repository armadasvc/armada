from fastapi import FastAPI, HTTPException, Query

from checks import check_ip, run_checks
from config import IPQUALITYSCORE_API_KEY
from db import build_proxy_query, fetch_random_proxy

app = FastAPI()


@app.get("/fetch_proxy")
async def fetch_proxy(
    proxy_provider_name: str | None = Query(None),
    proxy_rotation_strategy: str | None = Query(None),
    proxy_type: str | None = Query(None),
    proxy_location: str | None = Query(None),
    verify_ip: bool | None = Query(None),
    verify_quality: bool | None = Query(None),
    verify_location: bool | None = Query(None),
    quality_threshold: int = Query(70),
    max_queries_number: int = Query(2),
):
    filters = {
        "proxy_provider_name": proxy_provider_name,
        "proxy_rotation_strategy": proxy_rotation_strategy,
        "proxy_type": proxy_type,
        "proxy_location": proxy_location,
    }

    query, params = build_proxy_query(filters)

    if verify_quality and not IPQUALITYSCORE_API_KEY:
        verify_quality = False

    need_checks = verify_ip or verify_quality or verify_location

    for attempt in range(1, max_queries_number + 1):
        try:
            proxy_url = fetch_random_proxy(query, params)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        if proxy_url is None:
            raise HTTPException(
                status_code=404, detail="No proxy found matching the given criteria"
            )

        result = {"proxy_url": proxy_url, "attempt": attempt}

        if not need_checks:
            return result

        ip_result = check_ip(proxy_url)
        result["verify_ip"] = ip_result
        ip_address = ip_result.get("ip")

        if not ip_address:
            continue

        passed, check_results = run_checks(
            proxy_url, ip_address, verify_quality, verify_location,
            proxy_location, quality_threshold,
        )
        result.update(check_results)

        if passed:
            return result

    raise HTTPException(
        status_code=404,
        detail=f"No proxy passed all checks after {max_queries_number} attempts",
    )
