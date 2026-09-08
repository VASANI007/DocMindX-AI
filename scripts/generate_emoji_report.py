"""
Accurate, pure emoji scanner extracting only actual emojis into emoji.txt
"""
import os
import unicodedata
from collections import defaultdict

EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".streamlit", "node_modules", "venv", ".venv", "database"}
EXCLUDE_EXTS = {".png", ".jpg", ".jpeg", ".ico", ".pkl", ".joblib", ".pyc", ".pdf", ".zip", ".tar", ".gz", ".db"}

def is_true_emoji(char):
    cp = ord(char)
    # Filter out box drawing, degree symbol, geometric lines, and ascii
    if cp < 0x2000 or (0x2500 <= cp <= 0x257F) or cp in (0x00B0, 0x25CF, 0x2715, 0x25BA, 0x2197, 0x02F2, 0x0645, 0x02F9, 0x0482):
        return False

    # Standard true emoji ranges
    if (
        (0x1F300 <= cp <= 0x1FAFF) or  # Pictographs & Symbols
        (0x1F1E6 <= cp <= 0x1F1FF) or  # Flags (Regional Indicators)
        (0x1F600 <= cp <= 0x1F64F) or  # Emoticons
        (0x1F680 <= cp <= 0x1F6FF) or  # Transport & Map
        (0x2600 <= cp <= 0x27BF and cp not in (0x2715, 0x2665)) or  # Dingbats & misc symbols
        (0x2B50 <= cp <= 0x2B55) or    # Stars & colored shapes
        (0x231A <= cp <= 0x23F3)       # Watches, hourglasses
    ):
        return True

    return False

def extract_emojis_from_text(text):
    emojis = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # Check for Flag combinations (pair of regional indicators)
        if 0x1F1E6 <= ord(ch) <= 0x1F1FF and i + 1 < n and 0x1F1E6 <= ord(text[i+1]) <= 0x1F1FF:
            emojis.append(text[i:i+2])
            i += 2
            continue

        if is_true_emoji(ch):
            seq = ch
            while i + 1 < n and (ord(text[i+1]) in (0x200D, 0xFE0F, 0xFE0E) or (0x1F3FB <= ord(text[i+1]) <= 0x1F3FF) or is_true_emoji(text[i+1])):
                if text[i+1] in ('\n', '\r', ' ', '\t', '"', "'", '<', '>', '/', '{', '}', '(', ')', '[', ']'):
                    break
                seq += text[i+1]
                i += 1
            emojis.append(seq)
        i += 1
    return emojis

def scan_repository():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    emoji_counts = defaultdict(int)
    emoji_locations = defaultdict(list)
    total_files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in EXCLUDE_EXTS or fname in ("emoji.txt", "generate_emoji_report.py"):
                continue

            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root_dir)
            total_files_scanned += 1

            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_no, line in enumerate(f, start=1):
                        found_emojis = extract_emojis_from_text(line)
                        for em in found_emojis:
                            emoji_counts[em] += 1
                            if len(emoji_locations[em]) < 10:
                                emoji_locations[em].append(f"{rel_path}:{line_no}")
            except Exception:
                pass

    sorted_emojis = sorted(emoji_counts.items(), key=lambda x: x[1], reverse=True)

    output_lines = [
        "==================================================================",
        "          DocMindX AI — COMPLETE PROJECT EMOJI AUDIT REPORT",
        "==================================================================",
        f"Total Unique Emojis Used        : {len(sorted_emojis)}",
        f"Total Emoji Occurrences In Code : {sum(emoji_counts.values())}",
        f"Total Code & Config Files Scanned : {total_files_scanned}",
        "==================================================================\n",
        "SUMMARY LIST OF ALL UNIQUE EMOJIS:",
        " ".join([em for em, _ in sorted_emojis]),
        "\n------------------------------------------------------------------",
        "DETAILED BREAKDOWN BY EMOJI (Ranked by Frequency of Use):",
        "------------------------------------------------------------------"
    ]

    for idx, (em, count) in enumerate(sorted_emojis, start=1):
        names = []
        for char in em:
            try:
                if ord(char) not in (0xFE0F, 0xFE0E, 0x200D):
                    names.append(unicodedata.name(char))
            except Exception:
                pass
        name_str = " + ".join(names) if names else "EMOJI SEQUENCE"
        codepoints = " ".join([f"U+{ord(c):04X}" for c in em])
        locs = emoji_locations[em]
        loc_str = ", ".join(locs[:4])
        if len(locs) > 4:
            loc_str += f" and {count - 4} more places..."

        output_lines.append(f"{idx:2d}. [{em}] ({codepoints}) : Used {count} time(s)")
        output_lines.append(f"    Name        : {name_str}")
        output_lines.append(f"    Source Files: {loc_str}")
        output_lines.append("")

    output_lines.append("==================================================================")
    output_lines.append("END OF EMOJI AUDIT REPORT")
    output_lines.append("==================================================================")

    out_file = os.path.join(root_dir, "emoji.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"Done! Clean emoji.txt written with {len(sorted_emojis)} unique emojis ({sum(emoji_counts.values())} occurrences).")

if __name__ == "__main__":
    scan_repository()
