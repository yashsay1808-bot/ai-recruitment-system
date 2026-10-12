"""
SQLite Database Layer for Screening History, Job Management & Enterprise Recruiter Authorization
Stores Job Descriptions, Screening Sessions, Candidate Records,
RBAC Recruiter Profiles, Security Clearance Tokens, and Authentication Audit Logs.
"""

import sqlite3
import json
import os
import hashlib
import hmac
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime


class RecruitmentDatabase:
    """Manages SQLite storage for ATS jobs, sessions, candidates, and enterprise recruiter authentication."""

    # Authorized Corporate Keys required for new Recruiter Registration
    AUTHORIZED_REGISTRATION_KEYS = {
        "TECHCORP-AUTH-2026",
        "VKIT-HR-ACCESS-2026",
        "ENTERPRISE-RECRUITER-KEY",
        "ADMIN-ATS-ACCESS"
    }

    # Role-Based Access Control (RBAC) Clearance Levels
    CLEARANCE_LEVELS = {
        "Executive HR / Super Admin": 3,
        "Lead Technical Recruiter": 2,
        "Talent Acquisition Partner": 2,
        "Engineering Hiring Manager": 2,
        "Technical Interviewer / Reviewer": 1,
        "HR Business Partner": 1
    }

    def __init__(self, db_path: Optional[str] = None):
        # RECRUITMENT_DB_PATH lets tests and demos run against a throwaway database.
        self.db_path = db_path or os.environ.get("RECRUITMENT_DB_PATH", "recruitment_system.db")
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    _PBKDF2_ITERATIONS = 200_000

    @staticmethod
    def _hash_password(password: str, salt: str = "ats_recruiter_salt_2026") -> str:
        """Legacy salted SHA-256 hash; kept so accounts created before PBKDF2 can still sign in."""
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

    @classmethod
    def _hash_password_secure(cls, password: str) -> str:
        """Per-user random salt + PBKDF2-HMAC-SHA256. Stored as ``pbkdf2$iterations$salt$hash``."""
        salt = os.urandom(16).hex()
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), cls._PBKDF2_ITERATIONS)
        return f"pbkdf2${cls._PBKDF2_ITERATIONS}${salt}${digest.hex()}"

    @classmethod
    def _verify_password(cls, password: str, stored: str) -> bool:
        """Constant-time check against either the PBKDF2 format or the legacy SHA-256 digest."""
        if not stored:
            return False
        if stored.startswith("pbkdf2$"):
            try:
                _, iters, salt, expected = stored.split("$")
                digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iters))
            except ValueError:
                return False
            return hmac.compare_digest(digest.hex(), expected)
        return hmac.compare_digest(cls._hash_password(password), stored)

    def _init_db(self):
        """Initializes database schema, audit tables, and default seeds."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Recruiters Authentication & RBAC Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruiters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                company TEXT,
                role TEXT DEFAULT 'Talent Acquisition Partner',
                clearance_level INTEGER DEFAULT 2,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 2. Authentication & Security Audit Logs Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                event_type TEXT NOT NULL,
                status TEXT NOT NULL,
                clearance_level INTEGER,
                session_token TEXT,
                ip_simulated TEXT DEFAULT '192.168.1.100 (Secure Intranet)',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # 3. Job Descriptions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                department TEXT,
                min_experience REAL DEFAULT 0.0,
                required_skills TEXT,
                preferred_skills TEXT,
                description_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 4. Screening Sessions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                session_name TEXT NOT NULL,
                total_candidates INTEGER DEFAULT 0,
                shortlisted_count INTEGER DEFAULT 0,
                under_review_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                recruiter_email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES job_descriptions(id)
            )
            """)

            # 5. Candidate Screening Results Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                candidate_name TEXT,
                email TEXT,
                phone TEXT,
                overall_score REAL,
                rank_position INTEGER,
                decision TEXT,
                breakdown_json TEXT,
                gap_results_json TEXT,
                candidate_data_json TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES screening_sessions(id)
            )
            """)

            # Run Automatic Schema Migrations on Existing Tables
            try:
                cursor.execute("PRAGMA table_info(recruiters)")
                rec_cols = [r["name"] for r in cursor.fetchall()]
                if "clearance_level" not in rec_cols:
                    cursor.execute("ALTER TABLE recruiters ADD COLUMN clearance_level INTEGER DEFAULT 2")
                if "last_login" not in rec_cols:
                    cursor.execute("ALTER TABLE recruiters ADD COLUMN last_login TIMESTAMP")
                if "role" not in rec_cols:
                    cursor.execute("ALTER TABLE recruiters ADD COLUMN role TEXT DEFAULT 'Talent Acquisition Partner'")
                if "company" not in rec_cols:
                    cursor.execute("ALTER TABLE recruiters ADD COLUMN company TEXT DEFAULT 'Enterprise Hiring'")
            except Exception as e:
                print(f"Recruiter migration notice: {e}")

            try:
                cursor.execute("PRAGMA table_info(screening_sessions)")
                sess_cols = [r["name"] for r in cursor.fetchall()]
                if "recruiter_email" not in sess_cols:
                    cursor.execute("ALTER TABLE screening_sessions ADD COLUMN recruiter_email TEXT")
            except Exception as e:
                print(f"Session migration notice: {e}")

            conn.commit()

    # ------------------ Recruiter Authentication & Authorization ------------------
    def validate_auth_key(self, key: str) -> bool:
        """Validates if the provided Enterprise Access Key is authorized."""
        if not key:
            return False
        return key.strip().upper() in self.AUTHORIZED_REGISTRATION_KEYS

    def register_recruiter(
        self,
        name: str,
        email: str,
        password: str,
        company: str = "Enterprise Hiring",
        role: str = "Talent Acquisition Partner",
        auth_key: Optional[str] = None
    ) -> Optional[int]:
        """
        Registers a recruiter account with role clearance level.
        An access key is optional; if one is supplied it must be valid.
        """
        if auth_key is not None and not self.validate_auth_key(auth_key):
            self.log_auth_event(email, "REGISTRATION_ATTEMPT", "REJECTED_INVALID_AUTH_KEY", 0)
            return None

        cleaned_email = email.strip().lower()
        pwd_hash = self._hash_password_secure(password)
        clearance = min(self.CLEARANCE_LEVELS.get(role.strip(), 2), 2) if auth_key is None else self.CLEARANCE_LEVELS.get(role.strip(), 2)

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO recruiters (name, email, password_hash, company, role, clearance_level)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (name.strip(), cleaned_email, pwd_hash, company.strip(), role.strip(), clearance))
                conn.commit()
                rec_id = cursor.lastrowid

                self.log_auth_event(cleaned_email, "REGISTRATION_SUCCESS", "AUTHORIZED", clearance)
                return rec_id
        except sqlite3.IntegrityError:
            self.log_auth_event(cleaned_email, "REGISTRATION_ATTEMPT", "REJECTED_DUPLICATE_EMAIL", clearance)
            return None

    def authenticate_recruiter(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticates recruiter credentials, issues a unique session security token,
        and records an audit log.
        """
        cleaned_email = email.strip().lower()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, name, email, company, role, clearance_level, created_at, password_hash
            FROM recruiters
            WHERE email = ?
            """, (cleaned_email,))
            row = cursor.fetchone()

            if row and self._verify_password(password, row["password_hash"]):
                profile = dict(row)
                profile.pop("password_hash", None)
                # Generate unique cryptographically secure session authorization token
                sec_token = f"AUTH-SEC-{uuid.uuid4().hex[:8].upper()}-L{profile.get('clearance_level', 2)}"
                profile["session_token"] = sec_token
                profile["authenticated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Update last login
                cursor.execute("UPDATE recruiters SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (profile["id"],))
                conn.commit()

                # Audit Log
                self.log_auth_event(cleaned_email, "LOGIN_SUCCESS", "AUTHORIZED", profile.get("clearance_level", 2), sec_token)
                return profile
            else:
                self.log_auth_event(cleaned_email, "LOGIN_FAILED", "REJECTED_INVALID_CREDENTIALS", 0)
                return None

    def get_recruiter_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Finds recruiter profile by email address."""
        cleaned_email = email.strip().lower()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, name, email, company, role, clearance_level, created_at
            FROM recruiters
            WHERE email = ?
            """, (cleaned_email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def log_auth_event(
        self,
        email: str,
        event_type: str,
        status: str,
        clearance_level: int = 0,
        session_token: Optional[str] = None
    ):
        """Records an authorization security audit log into database."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO auth_audit_logs (email, event_type, status, clearance_level, session_token)
                VALUES (?, ?, ?, ?, ?)
                """, (email, event_type, status, clearance_level, session_token or "N/A"))
                conn.commit()
        except Exception:
            pass

    def get_auth_audit_logs(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves recent authorization audit logs for security oversight."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM auth_audit_logs ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # ------------------ Job Descriptions ------------------
    def create_job(
        self,
        title: str,
        department: str,
        min_experience: float,
        required_skills: List[str],
        preferred_skills: List[str],
        description_text: str
    ) -> int:
        """Saves a new Job Description to database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO job_descriptions (title, department, min_experience, required_skills, preferred_skills, description_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                title,
                department,
                min_experience,
                json.dumps(required_skills),
                json.dumps(preferred_skills),
                description_text
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Retrieves all saved Job Descriptions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC")
            rows = cursor.fetchall()
            jobs = []
            for r in rows:
                jobs.append({
                    "id": r["id"],
                    "title": r["title"],
                    "department": r["department"],
                    "min_experience": r["min_experience"],
                    "required_skills": json.loads(r["required_skills"] or "[]"),
                    "preferred_skills": json.loads(r["preferred_skills"] or "[]"),
                    "description_text": r["description_text"],
                    "created_at": r["created_at"]
                })
            return jobs

    def get_job_by_id(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves a specific Job Description by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_descriptions WHERE id = ?", (job_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "id": r["id"],
                "title": r["title"],
                "department": r["department"],
                "min_experience": r["min_experience"],
                "required_skills": json.loads(r["required_skills"] or "[]"),
                "preferred_skills": json.loads(r["preferred_skills"] or "[]"),
                "description_text": r["description_text"],
                "created_at": r["created_at"]
            }

    # ------------------ Screening Sessions ------------------
    def save_screening_session(
        self,
        job_id: int,
        session_name: str,
        evaluated_candidates: List[Dict[str, Any]],
        recruiter_email: Optional[str] = None
    ) -> int:
        """
        Saves an entire screening run with candidate breakdown, scores, and decisions.
        """
        total = len(evaluated_candidates)
        shortlisted = sum(1 for c in evaluated_candidates if c.get("overall_score", 0) >= 65.0)
        review = sum(1 for c in evaluated_candidates if 50.0 <= c.get("overall_score", 0) < 65.0)
        rejected = sum(1 for c in evaluated_candidates if c.get("overall_score", 0) < 50.0)
        avg_score = round(sum(c.get("overall_score", 0) for c in evaluated_candidates) / max(total, 1), 1)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO screening_sessions (job_id, session_name, total_candidates, shortlisted_count, under_review_count, rejected_count, avg_score, recruiter_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, session_name, total, shortlisted, review, rejected, avg_score, recruiter_email))
            session_id = cursor.lastrowid

            for cand in evaluated_candidates:
                score = cand.get("overall_score", 0.0)
                decision = "SHORTLISTED" if score >= 65.0 else ("UNDER_REVIEW" if score >= 50.0 else "REJECTED")
                c_data = cand.get("candidate_data", {})

                cursor.execute("""
                INSERT INTO candidate_results (session_id, candidate_name, email, phone, overall_score, rank_position, decision, breakdown_json, gap_results_json, candidate_data_json, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    cand.get("candidate_name", "Candidate"),
                    c_data.get("email", ""),
                    c_data.get("phone", ""),
                    score,
                    cand.get("rank", 1),
                    decision,
                    json.dumps(cand.get("breakdown", {})),
                    json.dumps(cand.get("gap_results", {})),
                    json.dumps(c_data),
                    ""
                ))

            conn.commit()
            return session_id

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Retrieves list of all screening sessions with Job details."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT s.*, j.title as job_title 
            FROM screening_sessions s
            LEFT JOIN job_descriptions j ON s.job_id = j.id
            ORDER BY s.created_at DESC
            """)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_session_candidates(self, session_id: int) -> List[Dict[str, Any]]:
        """Retrieves all candidate evaluations from a past screening session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM candidate_results WHERE session_id = ? ORDER BY rank_position ASC
            """, (session_id,))
            rows = cursor.fetchall()
            candidates = []
            for r in rows:
                candidates.append({
                    "id": r["id"],
                    "candidate_name": r["candidate_name"],
                    "email": r["email"],
                    "phone": r["phone"],
                    "overall_score": r["overall_score"],
                    "rank": r["rank_position"],
                    "decision": r["decision"],
                    "breakdown": json.loads(r["breakdown_json"] or "{}"),
                    "gap_results": json.loads(r["gap_results_json"] or "{}"),
                    "candidate_data": json.loads(r["candidate_data_json"] or "{}"),
                    "notes": r["notes"]
                })
            return candidates
