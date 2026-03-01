from src.fingerprint import ArkoseBrowserFingerprint


def generate(original_ua,new_ua, original_bda, original_timestamp):
    fp = ArkoseBrowserFingerprint(original_bda, original_ua,original_timestamp)
    fp.update_timestamp_and_ua(new_ua)
    new_fp = fp.repackage()
    return new_fp


def forge_arkose_fingerprint(fp_from_db, new_ua):
    original_ua = fp_from_db["ua"]
    original_bda = fp_from_db["bda"]
    original_timestamp = int(fp_from_db["ts"])
    new_bda = generate(original_ua, new_ua,original_bda, original_timestamp)
    return new_bda