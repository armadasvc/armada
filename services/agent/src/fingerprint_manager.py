import requests
import os
import json


def get_value_or_default(value, default):
    """Return value if not None, otherwise return default."""
    return value if value is not None else default


def load_config(config):
    """Load configuration from file path or return dict as-is.

    Args:
        config: Either a file path (str) to a JSON file or a dict

    Returns:
        dict: The configuration dictionary
    """
    if isinstance(config, str):
        with open(config, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    return config


class FingerprintManager():
    def __init__(self,config_fingerprint=None):
        self.config_fingerprint = config_fingerprint
        self.antibot_vendor = "arkose"
        self.website = "X"
        self.collection_date_day = "01"
        self.collection_date_month = "01"
        self.collection_date_year = "1900"
        if self.config_fingerprint:
            self._parse_config_fingerprint()
    

    def _parse_config_fingerprint(self):
        self.config_fingerprint = load_config(self.config_fingerprint) if isinstance(self.config_fingerprint, str) else self.config_fingerprint
        self.antibot_vendor = get_value_or_default(self.config_fingerprint.get("antibot_vendor"), self.antibot_vendor)
        self.website = get_value_or_default(self.config_fingerprint.get("website"), self.website)
        self.collection_date_day = get_value_or_default(self.config_fingerprint.get("collection_date_day"), self.collection_date_day)
        self.collection_date_month = get_value_or_default(self.config_fingerprint.get("collection_date_month"), self.collection_date_month)
        self.collection_date_year = get_value_or_default(self.config_fingerprint.get("collection_date_year"), self.collection_date_year)

    
    def get_fingerprint(self,additional_data: dict= None):
        payload = self.config_fingerprint
        if additional_data:
            payload["additional_data"]=additional_data
        fp_provider_url = os.getenv("FINGERPRINT_PROVIDER_URL","http://localhost:5005")
        response = requests.get(fp_provider_url+"/get-fingerprint", json=payload)
        print(response.text)
        return response.text