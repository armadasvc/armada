import requests

from config import IPQUALITYSCORE_API_KEY


def check_ip(proxy_url: str) -> dict:
    try:
        ip = requests.get(
            "https://api.ipify.org", proxies={"https": proxy_url}, timeout=10
        ).text
        return {"ip": ip}
    except Exception:
        return {"ip": None}


def check_quality(ip_address: str, quality_threshold: int = 70) -> dict:
    try:
        url = f"https://ipqualityscore.com/api/json/ip/{IPQUALITYSCORE_API_KEY}/{ip_address}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        fraud_score_inverted = 100 - resp.json()["fraud_score"]
    except Exception:
        return {
            "fraud_score_inverted": None,
            "quality_pass": False,
            "quality_threshold": quality_threshold,
        }

    return {
        "fraud_score_inverted": fraud_score_inverted,
        "quality_threshold": quality_threshold,
        "quality_pass": fraud_score_inverted > quality_threshold,
    }


def check_location(ip_address: str, expected_location: str) -> dict:
    try:
        resp = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        actual_tz = data.get("timezone", "")

        location_match = expected_location.lower() in actual_tz.lower()

        return {
            "actual_timezone": actual_tz,
            "expected_location": expected_location,
            "location_match": location_match,
        }
    except Exception as exc:
        return {"location_match": False, "error": str(exc)}


def run_checks(proxy_url, ip_address, verify_quality, verify_location, proxy_location, quality_threshold):
    result = {}
    passed = True

    if verify_quality:
        if ip_address:
            quality_result = check_quality(ip_address, quality_threshold)
            result["verify_quality"] = quality_result
            if not quality_result["quality_pass"]:
                passed = False
        else:
            result["verify_quality"] = {
                "fraud_score_inverted": None,
                "quality_pass": False,
                "error": "IP not resolved, cannot check quality",
            }
            passed = False

    if verify_location:
        if ip_address and proxy_location:
            location_result = check_location(ip_address, proxy_location)
            result["verify_location"] = location_result
            if not location_result["location_match"]:
                passed = False
        elif not proxy_location:
            result["verify_location"] = {
                "location_match": False,
                "error": "proxy_location parameter is required for location verification",
            }
            passed = False
        else:
            result["verify_location"] = {
                "location_match": False,
                "error": "IP not resolved, cannot check location",
            }
            passed = False

    return passed, result
