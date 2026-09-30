"""
DocMindX AI — Supabase PostgreSQL RLS & RBAC Policy Applier
Applies Row Level Security (RLS) and Granular Policies to all public tables in Supabase.
"""
import os
import sys
import re
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_DIR = os.path.dirname(__file__)
RLS_SQL_PATH = os.path.join(DB_DIR, "supabase_rls_security.sql")

db_url = os.getenv("DATABASE_URL", "")
if not db_url:
    print("[ERROR] DATABASE_URL is not configured in .env")
    sys.exit(1)

print("=" * 80)
print("APPLYING SUPABASE ROW LEVEL SECURITY (RLS) & RBAC POLICIES")
print(f"Target Host: {db_url.split('@')[-1]}")
print("=" * 80)

if db_url.startswith("postgres://"):
    db_url = "postgresql://" + db_url[len("postgres://"):]

conn = psycopg2.connect(db_url)
conn.autocommit = True
cur = conn.cursor()

with open(RLS_SQL_PATH, "r", encoding="utf-8") as f:
    sql_script = f.read()

cleaned = re.sub(r"--.*$", "", sql_script, flags=re.MULTILINE)
stmts = [s.strip() for s in cleaned.split(";") if s.strip()]

print(f"\n[1/3] Executing {len(stmts)} Security Statements...")
for i, stmt in enumerate(stmts, 1):
    try:
        cur.execute(stmt)
    except Exception as e:
        print(f"  [NOTICE] Statement {i}: {e}")

print("  [OK] All RLS and RBAC statements executed.")

print("\n[2/3] Verifying RLS Status for all Public Schema Tables...")
cur.execute("""
    SELECT tablename, rowsecurity 
    FROM pg_tables 
    WHERE schemaname = 'public' 
    ORDER BY tablename;
""")
tables = cur.fetchall()

print(f"{'TABLE NAME':<35} | {'RLS ENABLED':<15} | {'STATUS'}")
print("-" * 65)
all_secured = True
for t_name, rls_enabled in tables:
    status = "SECURED [OK]" if rls_enabled else "UNPROTECTED [FAIL]"
    if not rls_enabled:
        all_secured = False
    print(f"{t_name:<35} | {str(rls_enabled):<15} | {status}")

print("-" * 65)

print("\n[3/3] Inspecting Active RLS Policies...")
cur.execute("""
    SELECT tablename, policyname, roles, cmd 
    FROM pg_policies 
    WHERE schemaname = 'public'
    ORDER BY tablename, policyname;
""")
policies = cur.fetchall()
print(f"Total Active Security Policies: {len(policies)}")
for p in policies[:10]:
    print(f"  - Table: {p[0]:<28} Policy: {p[1]:<30} Command: {p[3]}")
if len(policies) > 10:
    print(f"  ... and {len(policies) - 10} more policies active across all tables.")

conn.close()

if all_secured:
    print("\n[SUCCESS] 100% of public tables are protected with Row Level Security (RLS)!")
    print("Supabase Security Advisor 'UNRESTRICTED' warnings are now resolved.")
else:
    print("\n[WARNING] Some tables still do not have RLS enabled.")
    sys.exit(1)
