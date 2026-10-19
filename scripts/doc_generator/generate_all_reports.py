import os
import sys

# Ensure root is in sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from scripts.doc_generator.build_prd import generate_prd_en, generate_prd_hi
from scripts.doc_generator.build_srs import generate_srs_en, generate_srs_hi
from scripts.doc_generator.build_architecture import generate_arch_en, generate_arch_hi
from scripts.doc_generator.build_ui_ux import generate_ui_ux_en, generate_ui_ux_hi
from scripts.doc_generator.build_dev_guide import generate_dev_guide_en, generate_dev_guide_hi

def generate_all():
    reports_dir = os.path.join(WORKSPACE_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    docs_to_generate = [
        ("1_PRD_DocMindX_AI_EN.docx", generate_prd_en),
        ("1_PRD_DocMindX_AI_HI.docx", generate_prd_hi),
        ("2_SRS_DocMindX_AI_EN.docx", generate_srs_en),
        ("2_SRS_DocMindX_AI_HI.docx", generate_srs_hi),
        ("3_Architecture_DocMindX_AI_EN.docx", generate_arch_en),
        ("3_Architecture_DocMindX_AI_HI.docx", generate_arch_hi),
        ("4_UI_UX_Design_DocMindX_AI_EN.docx", generate_ui_ux_en),
        ("4_UI_UX_Design_DocMindX_AI_HI.docx", generate_ui_ux_hi),
        ("5_Development_Guide_DocMindX_AI_EN.docx", generate_dev_guide_en),
        ("5_Development_Guide_DocMindX_AI_HI.docx", generate_dev_guide_hi),
    ]

    print("================================================================================")
    print("DOCMINDX AI — GENERATING ALL 10 FORMAL WORD (DOCX) DOCUMENTATION ARTIFACTS")
    print(f"Output Directory: {reports_dir}")
    print("================================================================================")

    generated_files = []
    for filename, generator_fn in docs_to_generate:
        target_path = os.path.join(reports_dir, filename)
        print(f"Generating: {filename}...")
        generator_fn(target_path)
        file_size = os.path.getsize(target_path)
        print(f"  -> Successfully generated ({file_size / 1024:.2f} KB)")
        generated_files.append((filename, file_size))

    print("\n================================================================================")
    print("ALL 10 DOCUMENTATION ARTIFACTS GENERATED SUCCESSFULLY!")
    print("================================================================================")
    for fn, sz in generated_files:
        print(f" • {fn} ({sz / 1024:.2f} KB)")

if __name__ == "__main__":
    generate_all()
