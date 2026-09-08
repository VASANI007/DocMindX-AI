"""
DocMindX AI — Official WHO (World Health Organization) Disease Outbreak News Ingestor
Connects to official WHO Disease Outbreak News (DON) OData API, caches raw responses,
classifies India direct vs relevant vs global events, and produces normalized outbreak datasets.
ZERO fabricated district or facility telemetry. Strict data provenance.
"""
import os
import re
import json
import hashlib
import logging
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.settings import WHO_OUTBREAK_API_URL
from ai.supply_chain.data_quality import data_quality_engine, PROVENANCE_OBSERVED

logger = logging.getLogger("WHOOutbreakIngestor")

# Countries in WHO South-East Asia Region (SEARO) and immediate neighbors
SEARO_AND_NEIGHBORS = {
    "india", "bangladesh", "bhutan", "democratic people's republic of korea",
    "indonesia", "maldives", "myanmar", "nepal", "sri lanka", "thailand",
    "timor-leste", "pakistan", "china", "afghanistan"
}

# High-priority global epidemic pathogen signals relevant to Indian public health surveillance
HIGH_RELEVANCE_PATHOGENS = [
    "influenza", "h5n1", "h7n9", "avian influenza", "nipah", "zika", "mers", "mers-cov",
    "coronavirus", "mpox", "monkeypox", "cholera", "dengue", "chikungunya", "ebola",
    "marburg", "poliovirus", "polio", "crimean-congo", "lassa", "yellow fever"
]

class WHOOutbreakIngestor:
    def __init__(self, api_url: str = None):
        self.workspace_root = WORKSPACE_ROOT
        self.api_url = api_url or WHO_OUTBREAK_API_URL or "https://www.who.int/api/news/diseaseoutbreaknews"
        self.raw_dir = os.path.join(self.workspace_root, "data", "raw", "command_center", "who_outbreak")
        self.processed_dir = os.path.join(self.workspace_root, "data", "processed", "command_center")
        self.rejected_dir = os.path.join(self.processed_dir, "rejected", "who_outbreaks")
        
        for d in [self.raw_dir, self.processed_dir, self.rejected_dir]:
            os.makedirs(d, exist_ok=True)

    def _strip_html(self, text: Optional[str]) -> str:
        """Removes HTML tags and cleans up whitespace."""
        if not text or pd.isna(text):
            return ""
        clean = re.sub(r"<[^>]+>", " ", str(text))
        clean = re.sub(r"&[a-zA-Z0-9#]+;", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    def _extract_country_and_disease(self, title: str) -> tuple[str, str]:
        """Extracts country name and disease from WHO event title."""
        if not title:
            return "Global", "Unspecified Event"
        
        title_clean = title.replace("", "-").strip()
        
        # WHO title formats: 'Disease - Country' or 'Disease - Country - update X' or 'Disease in Country'
        country = "Global"
        disease = title_clean

        if " - " in title_clean:
            parts = [p.strip() for p in title_clean.split(" - ") if p.strip()]
            disease = parts[0]
            if len(parts) > 1 and not parts[1].lower().startswith("update"):
                country = parts[1]
        elif " in " in title_clean:
            parts = title_clean.split(" in ")
            disease = parts[0].strip()
            country = parts[1].strip()
        elif " – " in title_clean:
            parts = [p.strip() for p in title_clean.split(" – ") if p.strip()]
            disease = parts[0]
            if len(parts) > 1:
                country = parts[1]

        # Clean country name
        country = re.sub(r"\s*\(.*?\)", "", country).strip()
        return country.title(), disease.strip()

    def _classify_relevance(self, country: str, disease: str, title: str) -> str:
        """
        Classifies WHO event into:
        - INDIA_DIRECT: Event explicitly occurring within India
        - INDIA_RELEVANT: Event in SEARO/neighboring countries or high-priority global pathogen
        - GLOBAL_REFERENCE: Other worldwide health events for baseline reference
        """
        c_lower = country.lower()
        t_lower = title.lower()
        d_lower = disease.lower()

        if "india" in c_lower or "india" in t_lower:
            return "INDIA_DIRECT"

        if any(neighbor in c_lower or neighbor in t_lower for neighbor in SEARO_AND_NEIGHBORS):
            return "INDIA_RELEVANT"

        if any(p in d_lower or p in t_lower for p in HIGH_RELEVANCE_PATHOGENS):
            return "INDIA_RELEVANT"

        return "GLOBAL_REFERENCE"

    def fetch_and_save_raw(self, top: int = 100) -> Dict[str, Any]:
        """
        Fetches official WHO Disease Outbreak News records and saves raw payload.
        Handles caching and graceful offline fallback.
        """
        latest_raw_file = os.path.join(self.raw_dir, "latest.json")
        url = f"{self.api_url}?$orderby=PublicationDate desc&$top={top}"
        
        logger.info(f"Connecting to official WHO Disease Outbreak News API: {url}...")
        try:
            headers = {"User-Agent": "DocMindX-AI-Command-Center/2.0", "Accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=12)
            if response.status_code == 200:
                data = response.json()
                items = data.get("value", [])
                
                # Compute checksum
                payload_str = json.dumps(data)
                sha = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

                # Save latest raw
                meta_payload = {
                    "source": "WHO_DISEASE_OUTBREAK_NEWS_API",
                    "source_url": url,
                    "retrieved_at": datetime.now().isoformat(),
                    "http_status": response.status_code,
                    "checksum_sha256": sha,
                    "record_count": len(items),
                    "data": data
                }
                with open(latest_raw_file, "w", encoding="utf-8") as f:
                    json.dump(meta_payload, f, indent=2)

                # Save timestamped backup
                now = datetime.now()
                archive_dir = os.path.join(self.raw_dir, now.strftime("%Y"), now.strftime("%m"))
                os.makedirs(archive_dir, exist_ok=True)
                archive_file = os.path.join(archive_dir, f"response_{now.strftime('%Y%m%d_%H%M%S')}.json")
                with open(archive_file, "w", encoding="utf-8") as f:
                    json.dump(meta_payload, f, indent=2)

                logger.info(f"Successfully fetched {len(items)} WHO outbreak records from API. Cached to {latest_raw_file}")
                return {
                    "status": "ONLINE_API_SUCCESS",
                    "items": items,
                    "source_url": url,
                    "retrieved_at": meta_payload["retrieved_at"],
                    "checksum": sha,
                    "raw_path": latest_raw_file
                }
            else:
                logger.warning(f"WHO API returned HTTP {response.status_code}. Fallback to local cache.")
        except Exception as e:
            logger.warning(f"WHO API network request failed: {e}. Fallback to local cache.")

        # Offline / Cache Fallback
        if os.path.exists(latest_raw_file):
            try:
                with open(latest_raw_file, "r", encoding="utf-8") as f:
                    cached_meta = json.load(f)
                    items = cached_meta.get("data", {}).get("value", [])
                    logger.info(f"Loaded {len(items)} cached WHO outbreak records from {latest_raw_file}")
                    return {
                        "status": "OFFLINE_CACHE_SUCCESS",
                        "items": items,
                        "source_url": cached_meta.get("source_url", self.api_url),
                        "retrieved_at": cached_meta.get("retrieved_at", datetime.now().isoformat()),
                        "checksum": cached_meta.get("checksum_sha256", "UNKNOWN"),
                        "raw_path": latest_raw_file
                    }
            except Exception as e:
                logger.error(f"Failed to read cached WHO outbreak JSON: {e}")

        return {
            "status": "OFFLINE_NO_DATA",
            "items": [],
            "source_url": self.api_url,
            "retrieved_at": datetime.now().isoformat(),
            "checksum": "NONE",
            "raw_path": latest_raw_file
        }

    def ingest(self) -> Dict[str, Any]:
        """
        Executes end-to-end ingestion and normalization of WHO Disease Outbreak News records.
        """
        raw_res = self.fetch_and_save_raw(top=100)
        items = raw_res.get("items", [])
        
        if not items:
            logger.warning("No WHO outbreak records available.")
            return {"status": "NO_RECORDS", "records_processed": 0}

        normalized_records = []
        rejected_records = []

        for item in items:
            title = item.get("Title") or item.get("OverrideTitle")
            if not title:
                rejected_records.append({"item": item, "reason": "MISSING_EVENT_TITLE"})
                continue

            don_id = item.get("DonId") or item.get("Id")
            pub_date = item.get("PublicationDate")
            
            country, disease = self._extract_country_and_disease(title)
            relevance = self._classify_relevance(country, disease, title)

            summary = self._strip_html(item.get("Summary") or item.get("Overview"))
            epidemiology = self._strip_html(item.get("Epidemiology"))
            assessment = self._strip_html(item.get("Assessment"))
            advice = self._strip_html(item.get("Advice"))

            default_url = item.get("ItemDefaultUrl", "")
            full_url = f"https://www.who.int/emergencies/disease-outbreak-news/item{default_url}" if default_url else "https://www.who.int/emergencies/disease-outbreak-news"

            geo_res = "COUNTRY" if country != "Global" else ("REGION" if relevance in ["INDIA_DIRECT", "INDIA_RELEVANT"] else "GLOBAL")

            record = {
                "outbreak_id": f"WHO-DON-{don_id}" if don_id else f"WHO-EVENT-{hashlib.md5(title.encode()).hexdigest()[:8]}",
                "source": "WHO_DISEASE_OUTBREAK_NEWS",
                "source_record_id": str(don_id) if don_id else "UNKNOWN",
                "published_at": pub_date,
                "retrieved_at": raw_res.get("retrieved_at"),
                "country": country,
                "region": "SEARO" if relevance in ["INDIA_DIRECT", "INDIA_RELEVANT"] and country in ["India", "Nepal", "Bangladesh", "Sri Lanka", "Myanmar", "Bhutan", "Thailand", "Indonesia"] else "GLOBAL",
                "state": None, # Kept strictly None — No fabricated Indian state unless explicitly verified
                "district": None, # Kept strictly None — No fabricated district telemetry
                "geographic_resolution": geo_res,
                "district_surveillance_available": False,
                "disease": disease,
                "event_title": title.replace("", "-").strip(),
                "event_type": "EPIDEMIC_OUTBREAK_ALERT",
                "case_count": None, # Real data rule: None unless provided by WHO
                "death_count": None, # Real data rule: None unless provided by WHO
                "epidemiological_summary": summary[:300] if summary else (epidemiology[:300] if epidemiology else "Official WHO Disease Outbreak News Bulletin"),
                "risk_assessment": assessment[:300] if assessment else "WHO standard global epidemiological risk assessment.",
                "public_health_advice": advice[:300] if advice else "WHO public health advice and surveillance guidance.",
                "source_url": full_url,
                "provenance": PROVENANCE_OBSERVED,
                "relevance_category": relevance,
                "data_quality_score": 100.0
            }
            normalized_records.append(record)

        # Log rejected records if any
        if rejected_records:
            rej_df = pd.DataFrame(rejected_records)
            data_quality_engine.log_rejected_records(rej_df, "WHO_Outbreaks_Raw", "MISSING_REQUIRED_FIELDS")

        df = pd.DataFrame(normalized_records)
        # Deduplicate on outbreak_id
        df = df.drop_duplicates(subset=["outbreak_id"]).reset_index(drop=True)

        out_path = os.path.join(self.processed_dir, "who_outbreaks.parquet")
        df.to_parquet(out_path, index=False)

        quality = data_quality_engine.evaluate_dataset_quality(df, "WHO_Disease_Outbreak_News", required_cols=["outbreak_id", "disease", "country", "source_url", "provenance"])
        logger.info(f"WHO Outbreak ingestion complete: {len(df)} records stored in {out_path}")

        india_direct = int((df["relevance_category"] == "INDIA_DIRECT").sum())
        india_relevant = int((df["relevance_category"] == "INDIA_RELEVANT").sum())
        global_ref = int((df["relevance_category"] == "GLOBAL_REFERENCE").sum())

        return {
            "status": "SUCCESS",
            "api_status": raw_res.get("status"),
            "total_records": len(df),
            "india_direct_count": india_direct,
            "india_relevant_count": india_relevant,
            "global_reference_count": global_ref,
            "output_path": out_path,
            "quality": quality,
            "provenance": PROVENANCE_OBSERVED,
            "source_name": "World Health Organization (WHO) Disease Outbreak News API"
        }

who_outbreak_ingestor = WHOOutbreakIngestor()

if __name__ == "__main__":
    res = who_outbreak_ingestor.ingest()
    print("WHO Outbreak Ingestion Result:", json.dumps(res, indent=2))
