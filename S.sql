-- === Clean, warning-free Crime Management schema for PostgreSQL ===
-- Drop & recreate public schema so script runs cleanly (WARNING: removes all objects in public)
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
SET search_path = public;

-- Create extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------
-- Support tables
-- -----------------------
CREATE TABLE userlogin (
  staffid         VARCHAR(50) PRIMARY KEY,
  full_name       VARCHAR(200),
  gender          VARCHAR(10),
  email           VARCHAR(200),
  phone           VARCHAR(50),
  address         VARCHAR(500),
  role            VARCHAR(50),
  password        VARCHAR(400),
  status          VARCHAR(20) DEFAULT 'Active',
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login      TIMESTAMP,
  other_meta      TEXT
);

CREATE TABLE complainant (
  complainant_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name            VARCHAR(200) NOT NULL,
  age             INTEGER,
  gender          VARCHAR(20),
  contact_no      VARCHAR(50),
  address         VARCHAR(500),
  occupation      VARCHAR(100),
  email           VARCHAR(200),
  registered_by   VARCHAR(50),
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE crime_type (
  crime_type_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  crime_name      VARCHAR(200) NOT NULL,
  description     TEXT,
  severity_level  VARCHAR(50),
  base_penalty_years INTEGER,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
  audit_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  actor_staffid   VARCHAR(50),
  action_type     VARCHAR(100),
  target_table    VARCHAR(100),
  target_id       VARCHAR(200),
  action_time     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  action_details  TEXT
);

CREATE TABLE notifications (
  notification_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  case_id         VARCHAR(50),
  staffid         VARCHAR(50),
  message         TEXT,
  notification_type VARCHAR(50),
  related_id      VARCHAR(100),
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_read         BOOLEAN DEFAULT FALSE
);

CREATE TABLE user_sessions (
  session_id      VARCHAR(200) PRIMARY KEY,
  staffid         VARCHAR(50),
  ip_address      VARCHAR(100),
  user_agent      VARCHAR(500),
  is_active       BOOLEAN DEFAULT TRUE,
  login_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_activity   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  session_timeout_minutes INTEGER DEFAULT 480,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  logout_time     TIMESTAMP
);

CREATE TABLE login_attempts (
  attempt_id      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  staffid         VARCHAR(50),
  ip_address      VARCHAR(100),
  user_agent      VARCHAR(500),
  attempt_result  VARCHAR(50),
  failure_reason  VARCHAR(400),
  attempt_time    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -----------------------
-- Core tables
-- -----------------------
CREATE TABLE case_table (
  case_id                 VARCHAR(50) PRIMARY KEY,
  complainant_id          INTEGER NOT NULL,
  crime_type_id           INTEGER NOT NULL,
  case_title              VARCHAR(150) NOT NULL,
  description             TEXT,
  incident_datetime       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  incident_location       VARCHAR(250),
  priority                VARCHAR(15) DEFAULT 'Medium' CHECK (priority IN ('Low','Medium','High','Critical')),
  status                  VARCHAR(20) DEFAULT 'Reported' CHECK (status IN ('Reported','Assigned','Investigating','Closed')),
  nco_staffid             VARCHAR(50),
  cid_officer_staffid     VARCHAR(50),
  created_by              VARCHAR(50),
  created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  closed_at               TIMESTAMP,
  CONSTRAINT fk_case_complainant FOREIGN KEY (complainant_id) REFERENCES complainant(complainant_id) ON DELETE RESTRICT,
  CONSTRAINT fk_case_crimetype   FOREIGN KEY (crime_type_id) REFERENCES crime_type(crime_type_id) ON DELETE RESTRICT,
  CONSTRAINT fk_case_nco        FOREIGN KEY (nco_staffid) REFERENCES userlogin(staffid) ON DELETE SET NULL,
  CONSTRAINT fk_case_cid        FOREIGN KEY (cid_officer_staffid) REFERENCES userlogin(staffid) ON DELETE SET NULL
);

CREATE TABLE evidence (
  evidence_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  case_id            VARCHAR(50) NOT NULL,
  evidence_ref       VARCHAR(50) NOT NULL,
  evidence_type      VARCHAR(100),
  description        TEXT,
  collected_by       VARCHAR(50),
  collected_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status             VARCHAR(30) DEFAULT 'Collected' CHECK (status IN ('Collected','Under Analysis','Submitted','Archived')),
  stored_location    VARCHAR(150),
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP,
  CONSTRAINT fk_ev_case  FOREIGN KEY (case_id) REFERENCES case_table(case_id) ON DELETE CASCADE,
  CONSTRAINT fk_ev_user  FOREIGN KEY (collected_by) REFERENCES userlogin(staffid) ON DELETE SET NULL
);

CREATE TABLE investigation (
  investigation_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  case_id            VARCHAR(50) NOT NULL,
  investigation_note TEXT,
  investigator_staffid VARCHAR(50),
  created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP,
  CONSTRAINT fk_inv_case FOREIGN KEY (case_id) REFERENCES case_table(case_id) ON DELETE CASCADE,
  CONSTRAINT fk_inv_user FOREIGN KEY (investigator_staffid) REFERENCES userlogin(staffid) ON DELETE SET NULL
);

-- -----------------------
-- Utility functions (security)
-- -----------------------
CREATE OR REPLACE FUNCTION hash_password(p_password TEXT)
RETURNS TEXT LANGUAGE plpgsql AS $$
BEGIN
  RETURN encode(digest(p_password, 'sha256'), 'hex');
EXCEPTION WHEN OTHERS THEN
  RETURN p_password;
END;
$$;

CREATE OR REPLACE FUNCTION compare_password(p_password TEXT, p_hash TEXT)
RETURNS BOOLEAN LANGUAGE plpgsql AS $$
BEGIN
  RETURN hash_password(p_password) = p_hash;
EXCEPTION WHEN OTHERS THEN
  RETURN FALSE;
END;
$$;

CREATE OR REPLACE FUNCTION gen_token(p_len INTEGER DEFAULT 32)
RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE
  v_out TEXT := '';
  v_i INTEGER;
  v_chars TEXT := 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  v_idx INTEGER;
BEGIN
  FOR v_i IN 1..GREATEST(1, p_len) LOOP
    v_idx := floor(random() * length(v_chars))::int + 1;
    v_out := v_out || substr(v_chars, v_idx, 1);
  END LOOP;
  RETURN v_out;
END;
$$;

-- -----------------------
-- Trigger for case_id autogen
-- -----------------------
CREATE OR REPLACE FUNCTION trg_case_id_autogen_fn()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
  v_next_id INTEGER;
  v_prefix TEXT;
BEGIN
  IF NEW.case_id IS NULL OR trim(NEW.case_id) = '' THEN
    v_prefix := to_char(NOW(), 'YYYYMMDD');
    SELECT COALESCE(MAX(CAST(right(case_id,4) AS INTEGER)), 0) + 1 INTO v_next_id
      FROM case_table
      WHERE left(case_id,8) = v_prefix;
    NEW.case_id := v_prefix || '-' || lpad(v_next_id::text, 4, '0');
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_case_id_autogen
BEFORE INSERT ON case_table
FOR EACH ROW
EXECUTE FUNCTION trg_case_id_autogen_fn();

-- -----------------------
-- Procedures (no COMMIT inside; OUT params before defaults)
-- -----------------------

-- sp_create_case (p_priority moved last as default)
CREATE OR REPLACE PROCEDURE sp_create_case(
  p_complainant_id INTEGER,
  p_crime_type_id INTEGER,
  p_case_title VARCHAR,
  p_description TEXT,
  p_incident_location VARCHAR,
  p_created_by VARCHAR,
  p_priority VARCHAR DEFAULT 'Medium'
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_case_id VARCHAR(50);
BEGIN
  SELECT to_char(NOW(), 'YYYYMMDD') || '-' ||
         lpad((COALESCE(MAX(CAST(right(case_id,4) AS INTEGER)),0) + 1)::text,4,'0')
  INTO v_case_id
  FROM case_table
  WHERE left(case_id,8) = to_char(NOW(),'YYYYMMDD');

  IF v_case_id IS NULL THEN
    v_case_id := to_char(NOW(), 'YYYYMMDD') || '-0001';
  END IF;

  INSERT INTO case_table(case_id, complainant_id, crime_type_id, case_title, description, incident_location, priority, created_by)
  VALUES (v_case_id, p_complainant_id, p_crime_type_id, p_case_title, p_description, p_incident_location, p_priority, p_created_by);

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES (p_created_by, 'CREATE_CASE', 'case_table', v_case_id, CURRENT_TIMESTAMP, 'New case reported.');

  INSERT INTO notifications(case_id, staffid, message, notification_type, created_at)
  VALUES (v_case_id, p_created_by, 'Case ' || v_case_id || ' created successfully.', 'STATUS_CHANGE', CURRENT_TIMESTAMP);
END;
$$;

-- sp_update_case
CREATE OR REPLACE PROCEDURE sp_update_case(
  p_case_id VARCHAR,
  p_status VARCHAR,
  p_priority VARCHAR,
  p_updated_by VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE case_table
  SET status = p_status,
      priority = p_priority,
      updated_at = CURRENT_TIMESTAMP
  WHERE case_id = p_case_id;

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_updated_by, 'UPDATE_CASE', 'case_table', p_case_id, CURRENT_TIMESTAMP, 'Case updated. New status: ' || p_status || ', Priority: ' || p_priority);

  INSERT INTO notifications(case_id, staffid, message, notification_type, created_at)
  VALUES(p_case_id, p_updated_by, 'Case ' || p_case_id || ' updated successfully.', 'STATUS_CHANGE', CURRENT_TIMESTAMP);
END;
$$;

-- sp_add_evidence
CREATE OR REPLACE PROCEDURE sp_add_evidence(
  p_case_id VARCHAR,
  p_evidence_type VARCHAR,
  p_description TEXT,
  p_collected_by VARCHAR,
  p_stored_location VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_evidence_ref VARCHAR(50);
BEGIN
  v_evidence_ref := 'EV-' || to_char(NOW(),'YYYYMMDDHH24MISS') || '-' || gen_token(4);

  INSERT INTO evidence(case_id, evidence_ref, evidence_type, description, collected_by, stored_location, created_at)
  VALUES (p_case_id, v_evidence_ref, p_evidence_type, p_description, p_collected_by, p_stored_location, CURRENT_TIMESTAMP);

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_collected_by, 'ADD_EVIDENCE', 'evidence', p_case_id, CURRENT_TIMESTAMP, 'Evidence added to case ' || p_case_id);

  INSERT INTO notifications(case_id, staffid, message, notification_type, created_at)
  VALUES(p_case_id, p_collected_by, 'New evidence added for case ' || p_case_id, 'EVIDENCE_UPDATE', CURRENT_TIMESTAMP);
END;
$$;

-- sp_update_investigation
CREATE OR REPLACE PROCEDURE sp_update_investigation(
  p_investigation_id INTEGER,
  p_new_note TEXT,
  p_cid_officer VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE investigation
  SET investigation_note = p_new_note,
      updated_at = CURRENT_TIMESTAMP
  WHERE investigation_id = p_investigation_id;

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_cid_officer, 'UPDATE_INVESTIGATION', 'investigation', p_investigation_id::text, CURRENT_TIMESTAMP, 'Investigation updated.');
END;
$$;

-- sp_create_user
CREATE OR REPLACE PROCEDURE sp_create_user(
  p_staffid VARCHAR,
  p_full_name VARCHAR,
  p_gender VARCHAR,
  p_email VARCHAR,
  p_phone VARCHAR,
  p_address VARCHAR,
  p_role VARCHAR,
  p_password VARCHAR,
  p_created_by VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_hashed VARCHAR;
BEGIN
  v_hashed := hash_password(p_password);

  INSERT INTO userlogin (staffid, full_name, gender, email, phone, address, role, password, status, created_at)
  VALUES (p_staffid, p_full_name, p_gender, p_email, p_phone, p_address, p_role, v_hashed, 'Active', CURRENT_TIMESTAMP);

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(COALESCE(p_created_by, p_staffid), 'CREATE_USER', 'userlogin', p_staffid, CURRENT_TIMESTAMP, 'User created with role ' || p_role);
END;
$$;

-- sp_login: OUT params before defaults
CREATE OR REPLACE PROCEDURE sp_login(
  p_staffid VARCHAR,
  p_password VARCHAR,
  OUT p_session_id VARCHAR,
  OUT p_role_out VARCHAR,
  OUT p_result_out VARCHAR,
  p_ip_address VARCHAR DEFAULT NULL,
  p_user_agent VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_stored_hash VARCHAR;
  v_status VARCHAR;
  v_role VARCHAR;
  v_session VARCHAR;
BEGIN
  p_session_id := NULL;
  p_role_out := NULL;
  p_result_out := 'UNKNOWN';

  SELECT password, status, role INTO v_stored_hash, v_status, v_role
  FROM userlogin WHERE staffid = p_staffid;

  IF NOT FOUND THEN
    INSERT INTO login_attempts(staffid, ip_address, user_agent, attempt_result, failure_reason)
    VALUES(p_staffid, p_ip_address, p_user_agent, 'USER_NOT_FOUND', 'No such staff id');
    p_result_out := 'USER_NOT_FOUND';
    RETURN;
  END IF;

  IF v_status <> 'Active' THEN
    p_result_out := 'INACTIVE';
    RETURN;
  END IF;

  IF compare_password(p_password, v_stored_hash) THEN
    v_session := 'SES_' || p_staffid || '_' || to_char(NOW(),'YYYYMMDDHH24MISSFF3') || '_' || gen_token(8);

    INSERT INTO user_sessions(session_id, staffid, ip_address, user_agent, is_active, login_time, last_activity, session_timeout_minutes, created_at)
    VALUES(v_session, p_staffid, p_ip_address, p_user_agent, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 480, CURRENT_TIMESTAMP);

    INSERT INTO login_attempts(staffid, ip_address, user_agent, attempt_result)
    VALUES(p_staffid, p_ip_address, p_user_agent, 'SUCCESS');

    UPDATE userlogin SET last_login = CURRENT_TIMESTAMP WHERE staffid = p_staffid;

    p_session_id := v_session;
    p_role_out := v_role;
    p_result_out := 'SUCCESS';
  ELSE
    INSERT INTO login_attempts(staffid, ip_address, user_agent, attempt_result, failure_reason)
    VALUES(p_staffid, p_ip_address, p_user_agent, 'INVALID_CREDENTIALS', 'Wrong password');
    p_result_out := 'INVALID_CREDENTIALS';
  END IF;
END;
$$;

-- sp_logout
CREATE OR REPLACE PROCEDURE sp_logout(p_session_id VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE user_sessions SET is_active = FALSE, logout_time = CURRENT_TIMESTAMP WHERE session_id = p_session_id;
END;
$$;

-- sp_deactivate_user
CREATE OR REPLACE PROCEDURE sp_deactivate_user(p_staffid VARCHAR, p_admin VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE userlogin SET status = 'Inactive' WHERE staffid = p_staffid;
  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_admin, 'DEACTIVATE_USER', 'userlogin', p_staffid, CURRENT_TIMESTAMP, 'User deactivated by ' || p_admin);
END;
$$;

-- sp_activate_user
CREATE OR REPLACE PROCEDURE sp_activate_user(p_staffid VARCHAR, p_admin VARCHAR)
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE userlogin SET status = 'Active' WHERE staffid = p_staffid;
  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_admin, 'ACTIVATE_USER', 'userlogin', p_staffid, CURRENT_TIMESTAMP, 'User activated by ' || p_admin);
END;
$$;

-- sp_reset_password
CREATE OR REPLACE PROCEDURE sp_reset_password(p_staffid VARCHAR, p_new_password VARCHAR, p_admin VARCHAR)
LANGUAGE plpgsql
AS $$
DECLARE
  v_hash VARCHAR;
BEGIN
  v_hash := hash_password(p_new_password);
  UPDATE userlogin SET password = v_hash WHERE staffid = p_staffid;
  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_admin, 'RESET_PASSWORD', 'userlogin', p_staffid, CURRENT_TIMESTAMP, 'Password reset by ' || p_admin);
END;
$$;

-- sp_fetch_notifications (OUT before defaults)
CREATE OR REPLACE PROCEDURE sp_fetch_notifications(
  p_staffid VARCHAR,
  OUT p_cursor refcursor,
  p_only_unread INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
  OPEN p_cursor FOR
    SELECT notification_id, case_id, message, notification_type, related_id, created_at, is_read
    FROM notifications
    WHERE staffid = p_staffid
      AND (p_only_unread = 0 OR is_read = FALSE)
    ORDER BY created_at DESC;
END;
$$;

-- sp_mark_notifications_read
CREATE OR REPLACE PROCEDURE sp_mark_notifications_read(
  p_staffid VARCHAR,
  p_notification_id VARCHAR  -- single id or comma-separated ids
)
LANGUAGE plpgsql
AS $$
BEGIN
  IF position(',' in p_notification_id) > 0 THEN
    EXECUTE format('UPDATE notifications SET is_read = TRUE WHERE staffid = %L AND notification_id IN (%s)', p_staffid, p_notification_id);
  ELSE
    UPDATE notifications SET is_read = TRUE WHERE staffid = p_staffid AND notification_id = p_notification_id::INTEGER;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fn_unread_notification_count(p_staffid VARCHAR)
RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE
  v_cnt INTEGER;
BEGIN
  SELECT COUNT(*) INTO v_cnt FROM notifications WHERE staffid = p_staffid AND is_read = FALSE;
  RETURN v_cnt;
END;
$$;

-- sp_close_case
CREATE OR REPLACE PROCEDURE sp_close_case(
  p_case_id VARCHAR,
  p_closed_by VARCHAR,
  p_close_reason VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE case_table SET status = 'Closed', closed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE case_id = p_case_id;
  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_closed_by, 'CLOSE_CASE', 'case_table', p_case_id, CURRENT_TIMESTAMP, 'Case closed. Reason: ' || p_close_reason);
  INSERT INTO notifications(case_id, staffid, message, notification_type, created_at)
  VALUES(p_case_id, p_closed_by, 'Case ' || p_case_id || ' closed. Reason: ' || p_close_reason, 'STATUS_CHANGE', CURRENT_TIMESTAMP);
END;
$$;

-- sp_fetch_cases_paginated (OUT refcursor before default)
-- Fix for: "procedure OUT parameters cannot appear after one with a default value"

CREATE OR REPLACE PROCEDURE sp_fetch_cases_paginated(
  p_page         INTEGER,
  p_page_size    INTEGER,
  OUT p_cursor   refcursor,
  OUT p_total_rows INTEGER,
  p_status       VARCHAR DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_offset INTEGER := (GREATEST(1, p_page) - 1) * GREATEST(1, p_page_size);
BEGIN
  OPEN p_cursor FOR
    SELECT *
    FROM (
      SELECT c.*, ROW_NUMBER() OVER (ORDER BY created_at DESC) AS rn
      FROM case_table c
      WHERE p_status IS NULL OR c.status = p_status
    ) AS sub
    WHERE rn > v_offset AND rn <= v_offset + p_page_size;

  SELECT COUNT(*) INTO p_total_rows
  FROM case_table
  WHERE p_status IS NULL OR status = p_status;
END;
$$;

-- sp_get_dashboard_stats (OUT refcursor)
CREATE OR REPLACE PROCEDURE sp_get_dashboard_stats(OUT p_cursor refcursor)
LANGUAGE plpgsql
AS $$
BEGIN
  OPEN p_cursor FOR
    SELECT 'total_cases' metric, COUNT(*)::TEXT value FROM case_table
    UNION ALL
    SELECT 'open_cases', COUNT(*)::TEXT FROM case_table WHERE status <> 'Closed'
    UNION ALL
    SELECT 'closed_cases', COUNT(*)::TEXT FROM case_table WHERE status = 'Closed'
    UNION ALL
    SELECT 'evidence_count', COUNT(*)::TEXT FROM evidence
    UNION ALL
    SELECT 'unread_notifications', COUNT(*)::TEXT FROM notifications WHERE is_read = FALSE;
END;
$$;

-- sp_transfer_evidence
CREATE OR REPLACE PROCEDURE sp_transfer_evidence(
  p_evidence_id INTEGER,
  p_from_staffid VARCHAR,
  p_to_staffid VARCHAR,
  p_location VARCHAR,
  p_note VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_case VARCHAR(50);
BEGIN
  SELECT case_id INTO v_case FROM evidence WHERE evidence_id = p_evidence_id;

  UPDATE evidence
  SET stored_location = p_location,
      status = 'Under Analysis',
      updated_at = CURRENT_TIMESTAMP
  WHERE evidence_id = p_evidence_id;

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_from_staffid, 'TRANSFER_EVIDENCE', 'evidence', p_evidence_id::text, CURRENT_TIMESTAMP, 'Transferred from ' || p_from_staffid || ' to ' || p_to_staffid || '. Note: ' || COALESCE(p_note,'(none)'));

  INSERT INTO notifications(case_id, staffid, message, notification_type, related_id, created_at)
  VALUES(v_case, p_to_staffid, 'Evidence ' || p_evidence_id || ' transferred to you. Note: ' || COALESCE(p_note,'(none)'), 'EVIDENCE_UPDATE', p_evidence_id::text, CURRENT_TIMESTAMP);
END;
$$;

-- sp_create_crime_type
CREATE OR REPLACE PROCEDURE sp_create_crime_type(
  p_crime_name VARCHAR,
  p_description VARCHAR,
  p_severity VARCHAR,
  p_base_penalty_years INTEGER,
  p_admin VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_id INTEGER;
BEGIN
  INSERT INTO crime_type(crime_name, description, severity_level, base_penalty_years, created_at)
  VALUES(p_crime_name, p_description, p_severity, p_base_penalty_years, CURRENT_TIMESTAMP)
  RETURNING crime_type_id INTO v_id;

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_admin, 'CREATE_CRIME_TYPE', 'crime_type', v_id::text, CURRENT_TIMESTAMP, 'Created crime type ' || p_crime_name);
END;
$$;

-- sp_update_crime_type
CREATE OR REPLACE PROCEDURE sp_update_crime_type(
  p_crime_type_id INTEGER,
  p_crime_name VARCHAR,
  p_description VARCHAR,
  p_severity VARCHAR,
  p_base_penalty_years INTEGER,
  p_admin VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
  UPDATE crime_type
  SET crime_name = p_crime_name,
      description = p_description,
      severity_level = p_severity,
      base_penalty_years = p_base_penalty_years
  WHERE crime_type_id = p_crime_type_id;

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_admin, 'UPDATE_CRIME_TYPE', 'crime_type', p_crime_type_id::text, CURRENT_TIMESTAMP, 'Updated crime type.');
END;
$$;

-- sp_create_complainant
CREATE OR REPLACE PROCEDURE sp_create_complainant(
  p_name VARCHAR,
  p_age INTEGER,
  p_gender VARCHAR,
  p_contact_no VARCHAR,
  p_address VARCHAR,
  p_occupation VARCHAR,
  p_email VARCHAR,
  p_registered_by VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
  v_id INTEGER;
BEGIN
  INSERT INTO complainant(name, age, gender, contact_no, address, occupation, email, registered_by, created_at)
  VALUES(p_name, p_age, p_gender, p_contact_no, p_address, p_occupation, p_email, p_registered_by, CURRENT_TIMESTAMP)
  RETURNING complainant_id INTO v_id;

  INSERT INTO audit_log(actor_staffid, action_type, target_table, target_id, action_time, action_details)
  VALUES(p_registered_by, 'CREATE_COMPLAINANT', 'complainant', v_id::text, CURRENT_TIMESTAMP, 'Complainant created.');
END;
$$;

-- sp_search_case (prints via RAISE NOTICE)
CREATE OR REPLACE PROCEDURE sp_search_case(p_keyword VARCHAR)
LANGUAGE plpgsql
AS $$
DECLARE
  rec RECORD;
BEGIN
  FOR rec IN
    SELECT case_id, case_title, status, priority FROM case_table
    WHERE lower(case_title) LIKE '%' || lower(p_keyword) || '%'
       OR lower(description) LIKE '%' || lower(p_keyword) || '%'
  LOOP
    RAISE NOTICE 'Case: % | % | %', rec.case_id, rec.case_title, rec.status;
  END LOOP;
END;
$$;

-- -----------------------
-- Views & Indexes
-- -----------------------
CREATE OR REPLACE VIEW vw_case_summary AS
SELECT c.case_id, c.case_title, c.status, c.priority,
       u.full_name AS officer_name, ct.crime_name, co.name AS complainant_name,
       c.created_at
FROM case_table c
LEFT JOIN userlogin u ON c.nco_staffid = u.staffid
LEFT JOIN crime_type ct ON c.crime_type_id = ct.crime_type_id
LEFT JOIN complainant co ON c.complainant_id = co.complainant_id;

CREATE OR REPLACE VIEW vw_case_search AS
SELECT c.case_id, c.case_title, c.status, c.priority, c.incident_location, ct.crime_name, co.name AS complainant_name, c.created_at
FROM case_table c
LEFT JOIN crime_type ct ON c.crime_type_id = ct.crime_type_id
LEFT JOIN complainant co ON c.complainant_id = co.complainant_id;

CREATE INDEX idx_case_createdat ON case_table(created_at);
CREATE INDEX idx_case_status ON case_table(status);
CREATE INDEX idx_evidence_status ON evidence(status);
CREATE INDEX idx_notifications_staff_read ON notifications(staffid, is_read);

-- End of script
