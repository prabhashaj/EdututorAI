# frontend/pages/login.py
import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth_handler import AuthHandler

def render_login_page():
    """Render the login page"""
    st.set_page_config(
        page_title="EduTutor AI - Login",
        page_icon="🎓",
        layout="centered"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .login-header {
            text-align: center;
            color: #1f77b4;
            margin-bottom: 2rem;
        }
        .demo-section {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #eee;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize auth handler
    auth_handler = AuthHandler("http://localhost:8000/api")
    
    # Main login container
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="login-header">🎓 EduTutor AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Personalized Learning with AI</p>', unsafe_allow_html=True)
    
    # Login tabs
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Register"])
    
    with tab1:
        render_login_form(auth_handler)
    
    with tab2:
        render_register_form(auth_handler)
    
    # Demo section
    st.markdown('<div class="demo-section">', unsafe_allow_html=True)
    st.markdown("#### 🚀 Quick Demo Access")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👨‍🎓 Demo Student", use_container_width=True, type="secondary"):
            demo_login("student@demo.com", "student", "Demo Student")
    
    with col2:
        if st.button("👨‍🏫 Demo Educator", use_container_width=True, type="secondary"):
            demo_login("educator@demo.com", "educator", "Demo Educator")
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_login_form(auth_handler):
    """Render login form"""
    with st.form("login_form"):
        email = st.text_input("📧 Email", placeholder="Enter your email address")
        password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 2])
        with col2:
            login_button = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
        
        if login_button:
            if email and password:
                with st.spinner("Logging in..."):
                    result = auth_handler.login(email, password)
                    if result and 'user' in result and 'access_token' in result:
                        st.session_state.user = result['user']
                        st.session_state.access_token = result['access_token']
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials or server error. Please try again.")
            else:
                st.error("⚠️ Please fill in all fields")

def render_register_form(auth_handler):
    """Render registration form"""
    with st.form("register_form"):
        name = st.text_input("👤 Full Name", placeholder="Enter your full name")
        email = st.text_input("📧 Email", placeholder="Enter your email address")
        role = st.selectbox("👥 Role", ["student", "educator"])
        password = st.text_input("🔒 Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm your password")
        
        col1, col2 = st.columns([1, 2])
        with col2:
            register_button = st.form_submit_button("📝 Register", use_container_width=True, type="primary")
        
        if register_button:
            if all([name, email, password, confirm_password]):
                if password == confirm_password:
                    with st.spinner("Creating account..."):
                        result = auth_handler.register(email, name, role, password)
                        if result:
                            st.session_state.user = result['user']
                            st.session_state.access_token = result['access_token']
                            st.success("✅ Registration successful!")
                            st.rerun()
                        else:
                            st.error("❌ Registration failed")
                else:
                    st.error("⚠️ Passwords don't match")
            else:
                st.error("⚠️ Please fill in all fields")

def demo_login(email, role, name):
    """Handle demo login"""
    st.session_state.user = {
        "id": f"{role}_demo",
        "email": email,
        "role": role,
        "name": name
    }
    st.success(f"✅ Logged in as {name}")
    st.rerun()

if __name__ == "__main__":
    render_login_page()
