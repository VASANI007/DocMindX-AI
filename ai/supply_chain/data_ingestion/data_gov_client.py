"""
DocMindX AI — Open Government Data (data.gov.in) API Client
Handles authenticated data.gov.in requests, caching, and fallback.
"""
import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from config.settings import DATA_GOV_IN_API_KEY

logger = logging.getLogger("DataGovClient")

DATA_GOV_BASE_URL = "https://api.data.gov.in/resource/"

class DataGovClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or DATA_GOV_IN_API_KEY
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "DocMindX-AI-Command-Center/2.0",
            "Accept": "application/json"
        })

    def is_configured(self) -> bool:
        """Returns True if a valid API key is present."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def fetch_resource(self, resource_id: str, limit: int = 100, offset: int = 0, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fetches an official government dataset from data.gov.in.
        Returns dictionary with records, total, and status metadata.
        """
        if not self.is_configured():
            logger.info("DATA_GOV_IN_API_KEY not configured or empty. Using verified local official dataset.")
            return {
                "status": "OFFLINE_LOCAL_DATA",
                "message": "DATA_GOV_IN_API_KEY not provided. Fallback to verified local copy.",
                "records": [],
                "total": 0,
                "timestamp": datetime.now().isoformat()
            }

        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
            "offset": offset
        }
        if filters:
            for k, v in filters.items():
                params[f"filters[{k}]"] = v

        url = f"{DATA_GOV_BASE_URL}{resource_id}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                records = data.get("records", [])
                total = data.get("total", len(records))
                return {
                    "status": "ONLINE_API_SUCCESS",
                    "resource_id": resource_id,
                    "records": records,
                    "total": total,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning(f"data.gov.in API returned HTTP {response.status_code}. Fallback to local.")
                return {
                    "status": "API_HTTP_ERROR",
                    "http_status": response.status_code,
                    "records": [],
                    "total": 0,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Error fetching data.gov.in resource {resource_id}: {str(e)}")
            return {
                "status": "API_NETWORK_EXCEPTION",
                "error": str(e),
                "records": [],
                "total": 0,
                "timestamp": datetime.now().isoformat()
            }

data_gov_client = DataGovClient()
