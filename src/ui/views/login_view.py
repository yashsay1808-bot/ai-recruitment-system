"""
Authentication view: a single card that toggles between Sign In and Sign Up.

Flow: Sign Up -> account saved -> back to Sign In with a confirmation banner -> user signs in.
Nothing here is rendered once a recruiter is authenticated.
"""

import re

import streamlit as st

from src.core.database import RecruitmentDatabase

MIN_PASSWORD_LENGTH = 8
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_AUTH_CSS = """
<style>
section[data-testid="stSidebar"], div[data-testid="stSidebarCollapsedControl"],
div[data-testid="stSidebarNav"], header[data-testid="stHeader"] { display: none !important; }
.block-container { max-width: 440px !important; padding-top: 9vh !important; }
.auth-brand { font-size: 0.95rem; font-weight: 600; color: var(--ob-text); letter-spacing: -0.01em; margin-bottom: 28px; }
.auth-title { font-size: 1.5rem; font-weight: 650; color: var(--ob-text); letter-spacing: -0.02em; margin: 0 0 4px 0; }
.auth-sub { font-size: 0.9rem; color: var(--ob-muted); margin: 0 0 20px 0; }
.auth-notice { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; border-radius: 8px;
  padding: 10px 14px; font-size: 0.88rem; margin-bottom: 18px; }
.st-key-auth_toggle button { white-space: nowrap; background: transparent !important; border: 0 !important; box-shadow: none !important;
  color: var(--ob-accent) !important; font-weight: 500; padding: 0 !important; min-height: 0 !important; }
.st-key-auth_toggle button p { color: var(--ob-accent) !important; }
.st-key-auth_toggle button:hover { text-decoration: underline; background: transparent !important; }
.auth-foot { text-align: center; color: var(--ob-muted); font-size: 0.88rem; }
</style>
"""

_SELF_SERVICE_ROLES = [
    role for role, level in RecruitmentDatabase.CLEARANCE_LEVELS.items() if level < 3
]


def _switch_mode(mode: str) -> None:
    st.session_state["auth_mode"] = mode
    st.session_state.pop("auth_notice", None)


def _render_sign_in(db: RecruitmentDatabase) -> None:
    st.markdown('<div class="auth-title">Sign in</div><div class="auth-sub">Welcome back.</div>', unsafe_allow_html=True)

    notice = st.session_state.pop("auth_notice", None)
    if notice:
        st.markdown(f'<div class="auth-notice">{notice}</div>', unsafe_allow_html=True)

    with st.form("sign_in_form", border=False):
        email = st.text_input("Email", placeholder="you@company.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)

    if submitted:
        if not email.strip() or not password:
            st.error("Enter your email and password.")
        else:
            recruiter = db.authenticate_recruiter(email, password)
            if recruiter:
                st.session_state["authenticated_recruiter"] = recruiter
                st.session_state.pop("auth_mode", None)
                st.rerun()
            else:
                st.error("Incorrect email or password.")


def _render_sign_up(db: RecruitmentDatabase) -> None:
    st.markdown('<div class="auth-title">Create your account</div><div class="auth-sub">It only takes a minute.</div>', unsafe_allow_html=True)

    with st.form("sign_up_form", border=False):
        name = st.text_input("Full name")
        email = st.text_input("Work email", placeholder="you@company.com")
        company = st.text_input("Company")
        role = st.selectbox("Role", _SELF_SERVICE_ROLES)
        password = st.text_input("Password", type="password", help=f"At least {MIN_PASSWORD_LENGTH} characters.")
        submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)

    if submitted:
        if not name.strip():
            st.error("Enter your full name.")
        elif not _EMAIL_RE.match(email.strip()):
            st.error("Enter a valid email address.")
        elif not company.strip():
            st.error("Enter your company.")
        elif len(password) < MIN_PASSWORD_LENGTH:
            st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        else:
            new_id = db.register_recruiter(
                name=name, email=email, password=password, company=company, role=role
            )
            if new_id:
                st.session_state["auth_mode"] = "signin"
                st.session_state["auth_notice"] = "Account created successfully. Please sign in with your credentials."
                st.rerun()
            else:
                st.error("An account with this email already exists.")


def render_recruiter_login_view(db: RecruitmentDatabase) -> None:
    """Renders the Sign In / Sign Up card. Only called for unauthenticated sessions."""
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)
    mode = st.session_state.get("auth_mode", "signin")

    st.markdown('<div class="auth-brand">AI Recruitment System</div>', unsafe_allow_html=True)

    with st.container(border=True):
        if mode == "signup":
            _render_sign_up(db)
        else:
            _render_sign_in(db)

    prompt, target, label = (
        ("Already have an account?", "signin", "Sign in")
        if mode == "signup"
        else ("Don't have an account?", "signup", "Sign up")
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    c_text, c_link = st.columns([1.5, 1], vertical_alignment="center", gap="small")
    with c_text:
        st.markdown(f'<div class="auth-foot" style="text-align:right;white-space:nowrap">{prompt}</div>', unsafe_allow_html=True)
    with c_link:
        st.button(label, key="auth_toggle", on_click=_switch_mode, args=(target,))
