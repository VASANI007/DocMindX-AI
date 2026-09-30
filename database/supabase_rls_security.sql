-- ============================================================
-- DOCMINDX AI — SUPABASE POSTGRESQL RLS & RBAC HARDENING SCRIPT
-- Enforces Row Level Security (RLS) on all public tables,
-- removes UNRESTRICTED state in Supabase Security Advisor,
-- and grants least-privilege access across roles.
-- ============================================================

-- 1. ENABLE ROW LEVEL SECURITY ON ALL PUBLIC TABLES
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE otp_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE medicine_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE triage_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_analysis_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_facilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_demand ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_transfers ENABLE ROW LEVEL SECURITY;
ALTER TABLE command_center_model_runs ENABLE ROW LEVEL SECURITY;

-- 2. DROP EXISTING POLICIES (CLEAN IDEMPOTENT RE-APPLICATION)
DROP POLICY IF EXISTS service_role_all_users ON users;
DROP POLICY IF EXISTS users_select_own ON users;
DROP POLICY IF EXISTS users_update_own ON users;

DROP POLICY IF EXISTS service_role_all_family ON family_members;
DROP POLICY IF EXISTS family_select_own ON family_members;
DROP POLICY IF EXISTS family_insert_own ON family_members;
DROP POLICY IF EXISTS family_update_own ON family_members;
DROP POLICY IF EXISTS family_delete_own ON family_members;

DROP POLICY IF EXISTS service_role_all_conditions ON medical_conditions;
DROP POLICY IF EXISTS conditions_select_own ON medical_conditions;
DROP POLICY IF EXISTS conditions_insert_own ON medical_conditions;
DROP POLICY IF EXISTS conditions_update_own ON medical_conditions;
DROP POLICY IF EXISTS conditions_delete_own ON medical_conditions;

DROP POLICY IF EXISTS service_role_all_meds ON medications;
DROP POLICY IF EXISTS meds_select_own ON medications;
DROP POLICY IF EXISTS meds_insert_own ON medications;
DROP POLICY IF EXISTS meds_update_own ON medications;
DROP POLICY IF EXISTS meds_delete_own ON medications;

DROP POLICY IF EXISTS service_role_all_scans ON medical_scans;
DROP POLICY IF EXISTS scans_select_own ON medical_scans;
DROP POLICY IF EXISTS scans_insert_own ON medical_scans;
DROP POLICY IF EXISTS scans_update_own ON medical_scans;
DROP POLICY IF EXISTS scans_delete_own ON medical_scans;

DROP POLICY IF EXISTS service_role_all_otp ON otp_verifications;
DROP POLICY IF EXISTS service_role_all_audit ON security_audit_logs;

DROP POLICY IF EXISTS medicine_cache_read_public ON medicine_cache;
DROP POLICY IF EXISTS service_role_all_medicine_cache ON medicine_cache;

DROP POLICY IF EXISTS service_role_all_triage ON triage_history;
DROP POLICY IF EXISTS service_role_all_report_analysis ON report_analysis_history;

DROP POLICY IF EXISTS cc_sources_read_public ON command_center_sources;
DROP POLICY IF EXISTS service_role_all_cc_sources ON command_center_sources;

DROP POLICY IF EXISTS cc_facilities_read_public ON command_center_facilities;
DROP POLICY IF EXISTS service_role_all_cc_facilities ON command_center_facilities;

DROP POLICY IF EXISTS cc_inventory_read_public ON command_center_inventory;
DROP POLICY IF EXISTS service_role_all_cc_inventory ON command_center_inventory;

DROP POLICY IF EXISTS cc_demand_read_public ON command_center_demand;
DROP POLICY IF EXISTS service_role_all_cc_demand ON command_center_demand;

DROP POLICY IF EXISTS cc_alerts_read_public ON command_center_alerts;
DROP POLICY IF EXISTS service_role_all_cc_alerts ON command_center_alerts;

DROP POLICY IF EXISTS cc_predictions_read_public ON command_center_predictions;
DROP POLICY IF EXISTS service_role_all_cc_predictions ON command_center_predictions;

DROP POLICY IF EXISTS service_role_all_cc_transfers ON command_center_transfers;
DROP POLICY IF EXISTS service_role_all_cc_model_runs ON command_center_model_runs;

-- 3. REVOKE BROAD DEFAULT PRIVILEGES FROM ANON AND AUTHENTICATED
REVOKE ALL ON users FROM anon, authenticated, public;
REVOKE ALL ON family_members FROM anon, authenticated, public;
REVOKE ALL ON medical_conditions FROM anon, authenticated, public;
REVOKE ALL ON medications FROM anon, authenticated, public;
REVOKE ALL ON medical_scans FROM anon, authenticated, public;
REVOKE ALL ON otp_verifications FROM anon, authenticated, public;
REVOKE ALL ON security_audit_logs FROM anon, authenticated, public;
REVOKE ALL ON triage_history FROM anon, authenticated, public;
REVOKE ALL ON report_analysis_history FROM anon, authenticated, public;
REVOKE ALL ON command_center_transfers FROM anon, authenticated, public;
REVOKE ALL ON command_center_model_runs FROM anon, authenticated, public;

-- 4. GRANT LEAST-PRIVILEGE ACCESS
-- Server-side / Service / Postgres Roles have full management access
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;

-- Public / Anonymous / Authenticated Read-Only for Public Knowledge & Command Center Views
GRANT SELECT ON medicine_cache TO anon, authenticated;
GRANT SELECT ON command_center_sources TO anon, authenticated;
GRANT SELECT ON command_center_facilities TO anon, authenticated;
GRANT SELECT ON command_center_inventory TO anon, authenticated;
GRANT SELECT ON command_center_demand TO anon, authenticated;
GRANT SELECT ON command_center_alerts TO anon, authenticated;
GRANT SELECT ON command_center_predictions TO anon, authenticated;

-- 5. DEFINE GRANULAR ROW LEVEL SECURITY POLICIES

-- --- USERS TABLE ---
CREATE POLICY service_role_all_users ON users
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY users_select_own ON users
    FOR SELECT TO authenticated
    USING (id::text = auth.uid()::text OR email = (auth.jwt() ->> 'email'));

CREATE POLICY users_update_own ON users
    FOR UPDATE TO authenticated
    USING (id::text = auth.uid()::text OR email = (auth.jwt() ->> 'email'))
    WITH CHECK (id::text = auth.uid()::text OR email = (auth.jwt() ->> 'email'));

-- --- FAMILY MEMBERS TABLE (STRICT USER OWNERSHIP) ---
CREATE POLICY service_role_all_family ON family_members
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY family_select_own ON family_members
    FOR SELECT TO authenticated
    USING (user_id::text = auth.uid()::text);

CREATE POLICY family_insert_own ON family_members
    FOR INSERT TO authenticated
    WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY family_update_own ON family_members
    FOR UPDATE TO authenticated
    USING (user_id::text = auth.uid()::text)
    WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY family_delete_own ON family_members
    FOR DELETE TO authenticated
    USING (user_id::text = auth.uid()::text);

-- --- MEDICAL CONDITIONS TABLE (OWNERSHIP VIA FAMILY_MEMBERS) ---
CREATE POLICY service_role_all_conditions ON medical_conditions
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY conditions_select_own ON medical_conditions
    FOR SELECT TO authenticated
    USING (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

CREATE POLICY conditions_insert_own ON medical_conditions
    FOR INSERT TO authenticated
    WITH CHECK (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

CREATE POLICY conditions_update_own ON medical_conditions
    FOR UPDATE TO authenticated
    USING (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text))
    WITH CHECK (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

CREATE POLICY conditions_delete_own ON medical_conditions
    FOR DELETE TO authenticated
    USING (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

-- --- MEDICATIONS TABLE (OWNERSHIP VIA FAMILY_MEMBERS) ---
CREATE POLICY service_role_all_meds ON medications
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY meds_select_own ON medications
    FOR SELECT TO authenticated
    USING (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

CREATE POLICY meds_insert_own ON medications
    FOR INSERT TO authenticated
    WITH CHECK (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

CREATE POLICY meds_update_own ON medications
    FOR UPDATE TO authenticated
    USING (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text))
    WITH CHECK (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

CREATE POLICY meds_delete_own ON medications
    FOR DELETE TO authenticated
    USING (family_member_id IN (SELECT id FROM family_members WHERE user_id::text = auth.uid()::text));

-- --- MEDICAL SCANS TABLE (STRICT USER OWNERSHIP) ---
CREATE POLICY service_role_all_scans ON medical_scans
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY scans_select_own ON medical_scans
    FOR SELECT TO authenticated
    USING (user_id::text = auth.uid()::text);

CREATE POLICY scans_insert_own ON medical_scans
    FOR INSERT TO authenticated
    WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY scans_update_own ON medical_scans
    FOR UPDATE TO authenticated
    USING (user_id::text = auth.uid()::text)
    WITH CHECK (user_id::text = auth.uid()::text);

CREATE POLICY scans_delete_own ON medical_scans
    FOR DELETE TO authenticated
    USING (user_id::text = auth.uid()::text);

-- --- OTP VERIFICATIONS (SERVER-ONLY / ZERO DIRECT CLIENT ACCESS) ---
CREATE POLICY service_role_all_otp ON otp_verifications
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

-- --- SECURITY AUDIT LOGS (SERVER & ADMIN-ONLY) ---
CREATE POLICY service_role_all_audit ON security_audit_logs
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

-- --- MEDICINE CACHE (PUBLIC READ / SERVER WRITE) ---
CREATE POLICY medicine_cache_read_public ON medicine_cache
    FOR SELECT TO anon, authenticated, public USING (true);

CREATE POLICY service_role_all_medicine_cache ON medicine_cache
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

-- --- TRIAGE HISTORY & REPORT ANALYSIS (SERVER / OWNER CONTROLLED) ---
CREATE POLICY service_role_all_triage ON triage_history
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY service_role_all_report_analysis ON report_analysis_history
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

-- --- NATIONAL COMMAND CENTER TABLES (PUBLIC READ / ADMIN-SERVER WRITE) ---
CREATE POLICY cc_sources_read_public ON command_center_sources
    FOR SELECT TO anon, authenticated, public USING (true);
CREATE POLICY service_role_all_cc_sources ON command_center_sources
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY cc_facilities_read_public ON command_center_facilities
    FOR SELECT TO anon, authenticated, public USING (true);
CREATE POLICY service_role_all_cc_facilities ON command_center_facilities
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY cc_inventory_read_public ON command_center_inventory
    FOR SELECT TO anon, authenticated, public USING (true);
CREATE POLICY service_role_all_cc_inventory ON command_center_inventory
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY cc_demand_read_public ON command_center_demand
    FOR SELECT TO anon, authenticated, public USING (true);
CREATE POLICY service_role_all_cc_demand ON command_center_demand
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY cc_alerts_read_public ON command_center_alerts
    FOR SELECT TO anon, authenticated, public USING (true);
CREATE POLICY service_role_all_cc_alerts ON command_center_alerts
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY cc_predictions_read_public ON command_center_predictions
    FOR SELECT TO anon, authenticated, public USING (true);
CREATE POLICY service_role_all_cc_predictions ON command_center_predictions
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY service_role_all_cc_transfers ON command_center_transfers
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);

CREATE POLICY service_role_all_cc_model_runs ON command_center_model_runs
    FOR ALL TO postgres, service_role USING (true) WITH CHECK (true);
