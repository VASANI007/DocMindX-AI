"""
    MedlinePlus Genetics & Health Topics API Client (NIH / NLM)
Provides:
1. Specific Disease / Condition Genetics JSON endpoint
2. MedlinePlus Health Topics Web Search API (XML parser)
No API key required (Public NIH Service).
"""
import requests
import re
import xml.etree.ElementTree as ET

GENETICS_BASE_URL = "https://medlineplus.gov/download/genetics/condition"
SEARCH_BASE_URL = "https://wsearch.nlm.nih.gov/ws/query"

def slugify(text):
    """
    Convert disease title to MedlinePlus condition slug.
    e.g. 'Alzheimer disease' -> 'alzheimer-disease'
    """
    text = text.lower().strip()
    text = re.sub(r'[\(\)\,\'\"]', '', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def get_medlineplus_genetics_data(disease_name):
    """
    Fetch structured condition genetics information including genes, inheritance, and codes.
    """
    if not disease_name or not disease_name.strip():
        return None

    slug = slugify(disease_name)
    url = f"{GENETICS_BASE_URL}/{slug}.json"
    try:
        res = requests.get(url, timeout=7)
        if res.status_code == 200:
            data = res.json()
            
            # Extract related genes
            genes = []
            for g in data.get("related-gene-list", []):
                gene_obj = g.get("related-gene", {})
                if isinstance(gene_obj, dict) and "gene-symbol" in gene_obj:
                    genes.append(gene_obj["gene-symbol"])
                elif isinstance(g, str):
                    genes.append(g)

            # Extract inheritance patterns
            inheritance = []
            for inh in data.get("inheritance-pattern-list", []):
                if isinstance(inh, dict):
                    inheritance.append(inh.get("inheritance-pattern", ""))
                elif isinstance(inh, str):
                    inheritance.append(inh)

            # Extract synonyms
            synonyms = []
            for s in data.get("synonym-list", []):
                if isinstance(s, dict):
                    synonyms.append(s.get("synonym", ""))
                elif isinstance(s, str):
                    synonyms.append(s)

            # Extract descriptions
            descriptions = []
            for t in data.get("text-list", []):
                if isinstance(t, dict):
                    text_obj = t.get("text")
                    if isinstance(text_obj, dict):
                        html_text = text_obj.get("html", "")
                        clean_text = re.sub(r'<[^>]+>', ' ', html_text).strip()
                        if clean_text:
                            descriptions.append(clean_text)
                    elif isinstance(text_obj, str) and text_obj.strip():
                        clean_text = re.sub(r'<[^>]+>', ' ', text_obj).strip()
                        descriptions.append(clean_text)

            summary_text = descriptions[0][:500] if descriptions else "Comprehensive biomedical summary available on MedlinePlus."
            return {
                "disease_name": data.get("name", disease_name),
                "summary": summary_text,
                "related_genes": genes[:6],
                "inheritance_patterns": inheritance,
                "synonyms": synonyms[:6],
                "reviewed_date": data.get("reviewed", "Reviewed"),
                "published_date": data.get("published", "Current"),
                "source": "NIH MedlinePlus Genetics"
            }
    except Exception as e:
        print(f"MedlinePlus Genetics fetch note: {e}")

    return None

def search_medlineplus_topics(query, retmax=4):
    """
    Search MedlinePlus Health Topics Web Service.
    """
    if not query or not query.strip():
        return []

    try:
        params = {
            "db": "healthTopics",
            "term": query.strip(),
            "retmax": retmax,
            "tool": "DocMindX_ai"
        }
        res = requests.get(SEARCH_BASE_URL, params=params, timeout=7)
        if res.status_code == 200:
            root = ET.fromstring(res.text)
            documents = root.findall(".//document")
            results = []

            for doc in documents:
                title = ""
                snippet = ""
                url = doc.get("url", "https://medlineplus.gov")

                for content in doc.findall("content"):
                    name = content.get("name")
                    if name == "title":
                        title = re.sub(r'<[^>]+>', '', content.text or "")
                    elif name == "snippet" or name == "FullSummary":
                        snippet = re.sub(r'<[^>]+>', '', content.text or "")

                if title:
                    results.append({
                        "title": title,
                        "snippet": snippet[:250] if snippet else "NIH MedlinePlus clinical topic reference.",
                        "url": url
                    })
            return results
    except Exception as e:
        print(f"MedlinePlus Topics search note: {e}")

    return []
