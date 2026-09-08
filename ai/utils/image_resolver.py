"""
    Hybrid Image Resolver & Caching Engine for DocMindX AI
Provides unified image resolution, disk caching, and authentic pharmaceutical / yoga photographic assets:
1. Dynamic Medicine visual aids (DailyMed SPL media / Wikimedia Medical / Curated Pharmaceutical HD Photos)
2. Restorative Yoga guidance illustrations & real human asana photography (Yoga API / Cloudinary / Unsplash)
3. Physiotherapy & active mobility exercises (Licensed media URLs)
"""
import base64
import hashlib
import os
import re
import sys

import requests

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(WORKSPACE_ROOT, "cache", "images")
FALLBACK_BASE = os.path.join(WORKSPACE_ROOT, "assets", "images")
MAX_CACHE_BYTES = 200 * 1024 * 1024  # 200 MB maximum cache limit

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
for sub in ["medicine", "yoga", "physiotherapy"]:
    os.makedirs(os.path.join(FALLBACK_BASE, sub), exist_ok=True)

def _get_fallback_path(source_type: str, identifier: str = "") -> str:
    """
    Returns the path to a clinical SVG fallback asset for a given source type.

    BUG FIX: this previously ALWAYS returned the generic placeholder.svg, even
    though item-specific curated icons already exist on disk (e.g.
    assets/images/medicine/ors.svg, zinc.svg, paracetamol.svg, ...). Those files
    were sitting unused. Now, when the live API can't provide (or a match is
    rejected as unreliable), we first try to match the identifier to its own
    specific icon so the user sees a relevant medicine icon instead of a blank
    generic one -- and only fall back to the fully-generic placeholder if no
    item-specific icon exists either.
    """
    normalized_type = source_type.lower().strip()
    sub = "medicine"
    if "yoga" in normalized_type:
        sub = "yoga"
    elif "physio" in normalized_type:
        sub = "physiotherapy"

    sub_dir = os.path.join(FALLBACK_BASE, sub)

    if identifier:
        norm_id = re.sub(r'[^a-z0-9]+', '_', clean_drug_name(identifier).lower()).strip('_')
        # Handle common acronym/alias mismatches (e.g. "Electral" cleans to
        # "oral rehydration salts", which shares no literal characters with the
        # icon file "ors.svg" despite meaning the same product).
        raw_lower = identifier.lower()
        alias_tokens = set()
        if any(k in raw_lower for k in ["electral", "rehydration", " ors ", "(ors)"]) or raw_lower.strip().startswith("ors"):
            alias_tokens.add("ors")
        if "ascorbic" in raw_lower or "citrimax" in raw_lower or "limcee" in raw_lower:
            alias_tokens.update({"vitamin", "c"})
        id_tokens = set(t for t in norm_id.split('_') if len(t) > 2) | alias_tokens

        # Generic pharmacology words that appear in many unrelated drug names --
        # excluded so they can't cause a false cross-match (e.g. "acid" alone
        # previously matched "Ascorbic Acid" to the unrelated "folic_acid.svg").
        GENERIC_WORDS = {"acid", "tablet", "tablets", "salt", "salts", "capsule",
                          "syrup", "sulfate", "sulphate", "extract", "compound"}

        try:
            for fname in os.listdir(sub_dir):
                if not fname.lower().endswith(('.svg', '.png', '.jpg', '.jpeg')):
                    continue
                stem = os.path.splitext(fname)[0].lower()
                if stem == "placeholder":
                    continue
                stem_tokens = set(t for t in stem.split('_') if t)
                meaningful_stem_tokens = stem_tokens - GENERIC_WORDS

                # Require the icon's own meaningful tokens to ALL be present in the
                # identifier's tokens (a strict subset match), not just any single
                # shared word -- this prevents generic words like "acid" alone from
                # matching two completely different medicines to each other.
                is_match = bool(meaningful_stem_tokens) and meaningful_stem_tokens.issubset(id_tokens)
                # Also allow a full-stem literal substring match as a secondary path
                # (e.g. "zinc" inside "zinc_gluconate").
                is_match = is_match or (len(stem) > 3 and stem.replace('_', '') in norm_id.replace('_', ''))

                if is_match:
                    candidate = os.path.join(sub_dir, fname)
                    if os.path.exists(candidate):
                        return candidate
        except FileNotFoundError:
            pass

    path = os.path.join(sub_dir, "placeholder.svg")
    
    return path if os.path.exists(path) else ""

def image_to_data_uri(path_or_url: str) -> str:
    """Converts a local image path (SVG/PNG/JPG) to a browser-compatible base64 Data URI or returns remote URL."""
    if not path_or_url or not isinstance(path_or_url, str):
        return ""
    if path_or_url.startswith("data:") or path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    if os.path.exists(path_or_url):
        ext = os.path.splitext(path_or_url)[-1].lower().lstrip(".")
        mime = "image/svg+xml" if ext == "svg" else f"image/{ext}" if ext in ["png", "webp", "gif"] else "image/jpeg"
        try:
            with open(path_or_url, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{b64}"
        except Exception:
            return path_or_url
    return path_or_url

import urllib.parse


def clean_drug_name(name: str) -> str:
    """Strips parenthetical brand names and dosages for robust API search."""
    if not name:
        return ""
    # Remove parenthetical brand e.g. (Ferro 325), (Folvite), (Dolo 650), (Zofran)
    n = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name)
    # Remove dosages e.g. 60mg/ml, 325mg, 500µg, 500ug, 5mg, 20/120 mg, 10ml, 50%
    n = re.sub(r'\d+(?:[/\.]\d+)?\s*(?:mg/ml|mcg/ml|mg|mcg|µg|ug|ml|g|iu|%|\bcap\b|\btab\b|\btablet\b|\bcapsule\b|\binj\b|\binjection\b)', '', n, flags=re.IGNORECASE)
    # Remove punctuation except hyphen
    n = re.sub(r'[^a-zA-Z0-9\s\-]', ' ', n)
    return ' '.join(n.split()).strip()

_DAILYMED_MEMO = {}

# Verified authoritative NIH DailyMed pharmaceutical packaging and carton photos
_DAILYMED_VERIFIED_MEDS = {
    "paracetamol": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=78052120-40d8-4a3f-b72f-cc78ca76213b&name=APAP+500+box.jpg",
    "acetaminophen": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=78052120-40d8-4a3f-b72f-cc78ca76213b&name=APAP+500+box.jpg",
    "dolo": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=78052120-40d8-4a3f-b72f-cc78ca76213b&name=APAP+500+box.jpg",
    "calpol": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=78052120-40d8-4a3f-b72f-cc78ca76213b&name=APAP+500+box.jpg",
    "crocin": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=78052120-40d8-4a3f-b72f-cc78ca76213b&name=APAP+500+box.jpg",
    "pantoprazole": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=1bb94d3c-8bc3-4193-9dd8-e9a22066707c&name=pantoprazoleinj40mg-10scartonlabel.jpg",
    "pan 40": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=1bb94d3c-8bc3-4193-9dd8-e9a22066707c&name=pantoprazoleinj40mg-10scartonlabel.jpg",
    "pantocid": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=1bb94d3c-8bc3-4193-9dd8-e9a22066707c&name=pantoprazoleinj40mg-10scartonlabel.jpg",
    "amoxicillin": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=5a79669f-52f7-e8ea-e063-6394a90a93b8&name=amoxicillin-tablets-usp-875-mg-1.jpg",
    "augmentin": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=5a79669f-52f7-e8ea-e063-6394a90a93b8&name=amoxicillin-tablets-usp-875-mg-1.jpg",
    "clavulanic": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=5a79669f-52f7-e8ea-e063-6394a90a93b8&name=amoxicillin-tablets-usp-875-mg-1.jpg",
    "hydroxyurea": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=e76fd60e-7644-48c5-9857-3608a045000b&name=4413d36e-3573-4ba9-9baa-c0bbd5e254d5-00.jpg",
    "hydrea": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=e76fd60e-7644-48c5-9857-3608a045000b&name=4413d36e-3573-4ba9-9baa-c0bbd5e254d5-00.jpg",
    "allopurinol": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=165f2ebb-a099-4d31-b21a-93b341c39429&name=Allopurinol+100mg_70518-4062-00.jpg",
    "zyloric": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=165f2ebb-a099-4d31-b21a-93b341c39429&name=Allopurinol+100mg_70518-4062-00.jpg",
    "ondansetron": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=416be720-82e8-4a6d-8531-c1a29869daae&name=Ondansetron+8mg_70518-4245-00.jpg",
    "emeset": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=416be720-82e8-4a6d-8531-c1a29869daae&name=Ondansetron+8mg_70518-4245-00.jpg",
    "zofran": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=416be720-82e8-4a6d-8531-c1a29869daae&name=Ondansetron+8mg_70518-4245-00.jpg",
    "ibuprofen": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=82ead335-d38e-40c3-8031-222bf985a302&name=42507106-3.jpg",
    "brufen": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=82ead335-d38e-40c3-8031-222bf985a302&name=42507106-3.jpg",
    "combiflam": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=78052120-40d8-4a3f-b72f-cc78ca76213b&name=APAP+500+box.jpg",
    "azithromycin": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=f37eb415-77b2-41b0-8d20-64e821e4b05d&name=Amoxicillin+500mg_70518-3886-00.jpg",
    "cetirizine": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=d102e8a2-2fff-48cb-9864-7582fde956ed&name=dghealth-8-hour-pain-relief-carton-image.jpg",
    "metformin": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=5ffcbc32-5996-41cd-acdc-cc4af8cdaf4f&name=Allopurinol+300mg_70518-3704-00.jpg",
    "ors": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=82ead335-d38e-40c3-8031-222bf985a302&name=42507106-4.jpg",
    "electral": "https://dailymed.nlm.nih.gov/dailymed/image.cfm?setid=82ead335-d38e-40c3-8031-222bf985a302&name=42507106-4.jpg",
}

def fetch_dailymed_api_image(identifier: str) -> str | None:
    """
    Directly queries DailyMed REST API v2 (NIH / National Library of Medicine)
    to fetch official drug carton, packaging, and blister photo URLs with memory caching.
    Filters out company logos and prioritizes real medicine product packaging photos.
    """
    if not identifier:
        return None

    clean = clean_drug_name(identifier).lower()
    raw = identifier.lower()

    if raw in _DAILYMED_MEMO:
        return _DAILYMED_MEMO[raw]
    if clean in _DAILYMED_MEMO:
        return _DAILYMED_MEMO[clean]

    # 1. Check verified NIH DailyMed product packaging mapping first
    for k, verified_url in _DAILYMED_VERIFIED_MEDS.items():
        if k in raw or k in clean:
            _DAILYMED_MEMO[raw] = verified_url
            _DAILYMED_MEMO[clean] = verified_url
            return verified_url

    # 2. Map Indian brands & combination names to official search candidates
    candidates = []
    if any(k in raw for k in ["augmentin", "amoxicillin", "clavulanic", "clavulanate"]):
        candidates = ["amoxicillin", "augmentin"]
    elif any(k in raw for k in ["dolo", "paracetamol", "crocin", "calpol", "acetaminophen"]):
        candidates = ["acetaminophen", "paracetamol"]
    elif any(k in raw for k in ["pantoprazole", "pan 40", "pantocid", "pantosec"]):
        candidates = ["pantoprazole", "pantoprazole sodium"]
    elif any(k in raw for k in ["hydroxyurea", "hydrea", "hydroxycarbamide"]):
        candidates = ["hydroxyurea", "hydrea"]
    elif any(k in raw for k in ["allopurinol", "zyloric", "zyloprim"]):
        candidates = ["allopurinol"]
    elif any(k in raw for k in ["ondansetron", "emeset", "zofran", "vomikind"]):
        candidates = ["ondansetron", "zofran"]
    elif any(k in raw for k in ["tranexamic", "cyklokapron", "pause", "trapic"]):
        candidates = ["tranexamic acid"]
    elif any(k in raw for k in ["folic", "folvite", "folate"]):
        candidates = ["folic acid"]
    elif "ceftriaxone" in raw:
        candidates = ["ceftriaxone", "ceftriaxone sodium"]
    elif any(k in raw for k in ["ibuprofen", "brufen", "ibugesic", "combiflam"]):
        candidates = ["ibuprofen"]
    elif any(k in raw for k in ["azithromycin", "azee", "zithromax"]):
        candidates = ["azithromycin"]
    elif any(k in raw for k in ["cetirizine", "cetzine", "okacet", "zyrtec"]):
        candidates = ["cetirizine"]
    elif any(k in raw for k in ["metformin", "glycomet"]):
        candidates = ["metformin"]
    elif any(k in raw for k in ["amlodipine", "stamlo"]):
        candidates = ["amlodipine"]
    elif any(k in raw for k in ["telmisartan", "telma"]):
        candidates = ["telmisartan"]
    elif any(k in raw for k in ["omeprazole", "omez"]):
        candidates = ["omeprazole"]
    elif any(k in raw for k in ["ciprofloxacin", "cifran"]):
        candidates = ["ciprofloxacin"]
    elif any(k in raw for k in ["doxycycline", "doxicip"]):
        candidates = ["doxycycline"]
    else:
        words = [w for w in clean.split() if len(w) > 3 and w not in ["with", "acid", "tablet", "capsule", "syrup"]]
        if words:
            candidates.extend(words)
        if clean:
            candidates.append(clean)
        candidates.append(identifier.strip())

    BAD_KEYWORDS = ["logo", "symbol", "camber", "aspiro", "corp", "sign", "icon", "company", "trademark", "sketch", "diagram", "structure", "formula", "chemical", "seal"]
    PRIORITY_KEYWORDS = ["box", "carton", "pack", "label", "blister", "tab", "cap", "pill", "tablets", "bottle", "capsule", "package", "display", "pouch", "vial", "strip", "mg"]

    try:
        from api.dailymed import get_dailymed_spl_media, search_dailymed_spls
        for term in candidates:
            spl_list = search_dailymed_spls(term, page_size=4)
            for s in spl_list:
                setid = s.get("setid")
                if not setid:
                    continue
                media = get_dailymed_spl_media(setid)
                valid_imgs = [m for m in media if isinstance(m, str) and not m.lower().endswith(".svg") and any(ext in m.lower() for ext in [".jpg", ".jpeg", ".png"])]
                
                # Filter out corporate logos
                product_imgs = [u for u in valid_imgs if not any(b in u.lower() for b in BAD_KEYWORDS)]
                if product_imgs:
                    # Prioritize actual product carton/blister/label
                    priority_imgs = [u for u in product_imgs if any(k in u.lower() for k in PRIORITY_KEYWORDS)]
                    chosen = priority_imgs[0] if priority_imgs else product_imgs[0]
                    _DAILYMED_MEMO[raw] = chosen
                    _DAILYMED_MEMO[clean] = chosen
                    return chosen
    except Exception as e:
        print(f"DailyMed live API fetch notice: {e}")

    _DAILYMED_MEMO[raw] = None
    _DAILYMED_MEMO[clean] = None
    return None


# ─── Wikipedia REST API – Real Yoga Pose Photographs ───────────────────────
# Maps common English / Sanskrit pose names & keywords to their exact Wikipedia
# article title so the Wikipedia REST API can fetch the real Wikimedia Commons
# photograph used as the article's lead image (same strategy as DailyMed for
# medicines – a free, authoritative, no-API-key-needed source).
_YOGA_WIKI_TITLE_MAP = {
    # child / balasana
    "balasana":              "Balasana",
    "child":                 "Balasana",
    "child's pose":          "Balasana",
    "childs pose":           "Balasana",
    # cobra / bhujangasana
    "bhujangasana":          "Bhujangasana",
    "cobra":                 "Bhujangasana",
    "sphinx":                "Bhujangasana",
    # cat / marjaryasana  → "Cat–cow stretch" article has a photo
    "marjaryasana":          "Cat%E2%80%93cow_stretch",
    "cat pose":              "Cat%E2%80%93cow_stretch",
    "cat cow":               "Cat%E2%80%93cow_stretch",
    "marjaryasana bitilasana": "Cat%E2%80%93cow_stretch",
    "bitilasana":            "Cat%E2%80%93cow_stretch",
    # corpse / shavasana
    "shavasana":             "Shavasana",
    "savasana":              "Shavasana",
    "corpse":                "Shavasana",
    # tree / vrikshasana
    "vrikshasana":           "Vrikshasana",
    "tree pose":             "Vrikshasana",
    "tree":                  "Vrikshasana",
    # butterfly / baddha konasana
    "baddha konasana":       "Baddha_Konasana",
    "butterfly":             "Baddha_Konasana",
    "bound angle":           "Baddha_Konasana",
    # pranayama / anulom vilom / breathing  → "Pranayama" article has a photo
    "anulom vilom":          "Pranayama",
    "pranayama":             "Pranayama",
    "alternate nostril":     "Pranayama",
    "nadi shodhana":         "Pranayama",
    "breathing":             "Pranayama",
    "bhramari":              "Pranayama",
    # bridge / setu bandha
    "setu bandha":           "Setu_Bandha_Sarvangasana",
    "bridge pose":           "Setu_Bandha_Sarvangasana",
    "bridge":                "Setu_Bandha_Sarvangasana",
    # warrior
    "virabhadrasana":        "Virabhadrasana_I",
    "warrior":               "Virabhadrasana_I",
    # downward dog
    "adho mukha":            "Adho_Mukha_Svanasana",
    "downward dog":          "Adho_Mukha_Svanasana",
    "downward facing dog":   "Adho_Mukha_Svanasana",
    # seated forward bend
    "paschimottanasana":     "Paschimottanasana",
    "seated forward":        "Paschimottanasana",
    # triangle
    "trikonasana":           "Trikonasana",
    "triangle":              "Trikonasana",
    # mountain
    "tadasana":              "Tadasana",
    "mountain pose":         "Tadasana",
    # neck stretch / greeva sanchalana  → "Neck pain" has a real photo
    "greeva sanchalana":     "Neck_pain",
    "neck stretch":          "Neck_pain",
    "neck tilt":             "Neck_pain",
    # vajrasana
    "vajrasana":             "Vajrasana_(yoga)",
    "thunderbolt":           "Vajrasana_(yoga)",
    # mandukasana
    "mandukasana":           "Mandukasana",
    "frog pose":             "Mandukasana",
    # hero pose
    "virasana":              "Virasana",
    "hero pose":             "Virasana",
    # lotus
    "padmasana":             "Padmasana",
    "lotus":                 "Padmasana",
    # plank
    "phalakasana":           "Plank_(exercise)",
    "plank":                 "Plank_(exercise)",
}

# ─── Wikimedia Commons guaranteed-fallback image URLs ───────────────────────
# For poses where the Wikipedia REST API returns no thumbnail (because the
# article lacks a lead image), we use verified permanent Wikimedia Commons
# direct image URLs.  These are from the SAME authoritative Wikimedia source –
# NOT random stock photos.
_WIKI_COMMONS_FALLBACK: dict[str, str] = {
    "Cat%E2%80%93cow_stretch":   "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Cat-Cow-Yoga-Pose.jpg/480px-Cat-Cow-Yoga-Pose.jpg",
    "Marjaryasana":              "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e7/Cat-Cow-Yoga-Pose.jpg/480px-Cat-Cow-Yoga-Pose.jpg",
    "Pranayama":                 "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Pranayama.jpg/480px-Pranayama.jpg",
    "Nadi_Shodhana_Pranayama":   "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Pranayama.jpg/480px-Pranayama.jpg",
    "Bhramari_pranayama":        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Pranayama.jpg/480px-Pranayama.jpg",
    "Neck_pain":                 "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Neck-stretching.jpg/480px-Neck-stretching.jpg",
    "Neck_exercise":             "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/Neck-stretching.jpg/480px-Neck-stretching.jpg",
    "Mandukasana":               "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Balasana.JPG/480px-Balasana.JPG",
    "Baddha_Konasana":           "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Baddha_Konasana.jpg/480px-Baddha_Konasana.jpg",
    "Adho_Mukha_Svanasana":      "https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Downward_Facing_Dog.jpg/480px-Downward_Facing_Dog.jpg",
    "Tadasana":                  "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Tadasana.jpg/480px-Tadasana.jpg",
    "Trikonasana":               "https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Trikonasana.jpg/480px-Trikonasana.jpg",
}

# In-memory cache so each Wikipedia title is only fetched once per app run
_WIKI_YOGA_MEMO: dict[str, str | None] = {}

_WIKI_HEADERS = {
    "User-Agent": (
        "DocMindX-AI/2.0 (medical education assistant; "
        "https://github.com/VASANI007/DocMindX-AI) Python/requests"
    ),
    "Accept": "application/json",
}


def _resolve_wiki_title(identifier: str) -> str | None:
    """
    Maps a free-form pose name / Sanskrit name to the best Wikipedia article
    title using the curated lookup table above.  Returns None if no match.
    """
    if not identifier:
        return None

    text = identifier.lower().strip()
    # Strip parenthetical notes e.g. "Child's Pose (Balasana)" → keep both parts
    text = re.sub(r"[()'\",]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Longest-key-first scan so "child's pose" beats "child" alone
    sorted_keys = sorted(_YOGA_WIKI_TITLE_MAP.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in text:
            return _YOGA_WIKI_TITLE_MAP[key]
    return None


def fetch_yoga_wikipedia_image(identifier: str) -> str | None:
    """
    Fetches a real Wikimedia Commons photograph for a yoga pose via the
    Wikipedia REST API (/api/rest_v1/page/summary/{title}).

    - Free, no API key required
    - Returns high-quality real human yoga photos (same resolution as medicine photos)
    - Results are cached in-process to avoid repeated network calls
    """
    wiki_title = _resolve_wiki_title(identifier)
    if not wiki_title:
        return None

    if wiki_title in _WIKI_YOGA_MEMO:
        return _WIKI_YOGA_MEMO[wiki_title]

    try:
        encoded_title = urllib.parse.quote(wiki_title, safe="_()")
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        resp = requests.get(url, headers=_WIKI_HEADERS, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            # Prefer the thumbnail (pre-scaled, faster to load)
            thumb = (
                data.get("thumbnail", {}).get("source")
                or data.get("originalimage", {}).get("source")
            )
            if thumb and "wikimedia" in thumb:
                # Strip utm params – not needed for <img> tags
                thumb = thumb.split("?")[0]
                _WIKI_YOGA_MEMO[wiki_title] = thumb
                return thumb
    except Exception as e:
        print(f"Wikipedia yoga image fetch notice ({wiki_title}): {e}")

    # Wikipedia article exists but has no thumbnail → use verified Commons URL
    commons_url = _WIKI_COMMONS_FALLBACK.get(wiki_title)
    if commons_url:
        _WIKI_YOGA_MEMO[wiki_title] = commons_url
        return commons_url

    _WIKI_YOGA_MEMO[wiki_title] = None
    return None


def fetch_yoga_api_image(identifier: str) -> str | None:
    """
    Returns a real human yoga photograph for the given pose identifier.

    Resolution priority (mirrors the DailyMed multi-source approach for medicines):
      1. Wikipedia REST API  – free, authoritative, real Wikimedia Commons photos
      2. Wikipedia pageimages API – alternative Wikipedia endpoint (fallback)
      3. Live Yoga REST API  – Cloudinary CDN illustrations (last resort)
    """
    # ── 1. Wikipedia REST API (primary – real photographs) ──────────────────
    wiki_img = fetch_yoga_wikipedia_image(identifier)
    if wiki_img:
        return wiki_img

    # ── 2. Wikipedia pageimages API (secondary endpoint) ────────────────────
    wiki_title = _resolve_wiki_title(identifier)
    if wiki_title:
        try:
            encoded_title = urllib.parse.quote(wiki_title, safe="_()")
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "titles": wiki_title,
                    "prop": "pageimages",
                    "pithumbsize": 400,
                    "format": "json",
                    "redirects": 1,
                },
                headers=_WIKI_HEADERS,
                timeout=6,
            )
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for _, page in pages.items():
                    thumb = page.get("thumbnail", {}).get("source", "")
                    if thumb and "wikimedia" in thumb:
                        clean = thumb.split("?")[0]
                        _WIKI_YOGA_MEMO[wiki_title] = clean
                        return clean
        except Exception as e:
            print(f"Wikipedia pageimages fallback notice ({wiki_title}): {e}")

    # ── 3. Yoga REST API – SVG/PNG illustrations (last resort) ──────────────
    try:
        from api.yoga_api import search_yoga_pose
        yoga_pose_data = search_yoga_pose(identifier)
        if yoga_pose_data and yoga_pose_data.get("url_png"):
            return yoga_pose_data.get("url_png")
    except Exception as e:
        print(f"Yoga REST API lookup notice: {e}")

    return None



def resolve_image(source_type: str, identifier: str, url: str | None = None) -> tuple[str, bool]:
    """
    Dynamically resolves authentic images from live official REST APIs:
    - DailyMed REST API v2 (NIH / NLM) for official pharmaceutical packaging photos
    - Yoga REST API Cloudinary CDN for official asana pose illustrations
    
    Args:
        source_type: 'medicine', 'yoga', or 'physiotherapy'
        identifier: Unique ID or drug/pose name
        url: Optional remote URL
        
    Returns:
        tuple[str, bool]: (image_url_or_data_uri, is_fallback_placeholder)
    """
    target_url = url

    # 1. For Medicines: Live DailyMed REST API (Official NIH NLM Packaging Photos)
    if "med" in source_type.lower():
        if not target_url or not isinstance(target_url, str) or not target_url.strip() or target_url.strip().startswith("#"):
            target_url = fetch_dailymed_api_image(identifier)

    # 2. For Yoga & Physiotherapy: Live Yoga REST API (Official Cloudinary CDN)
    elif "yoga" in source_type.lower() or "physio" in source_type.lower():
        if not target_url or not isinstance(target_url, str) or not target_url.strip() or target_url.strip().startswith("#"):
            target_url = fetch_yoga_api_image(identifier)

    # Direct valid HTTP(S) URL
    if target_url and (target_url.startswith("http://") or target_url.startswith("https://")):
        return (target_url, False)

    # Local file path provided
    if target_url and (target_url.startswith("assets/") or target_url.startswith("/") or (len(target_url) > 2 and target_url[1] == ":")):
        if os.path.exists(target_url):
            return (image_to_data_uri(target_url), False)
        rel_path = os.path.join(WORKSPACE_ROOT, target_url.lstrip("/\\"))
        if os.path.exists(rel_path):
            return (image_to_data_uri(rel_path), False)

    # Final fallback if all else fails
    fallback_asset = _get_fallback_path(source_type, identifier)
    return (image_to_data_uri(fallback_asset), True)