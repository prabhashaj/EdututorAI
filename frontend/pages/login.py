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
    
    # Header
    st.markdown('<h1 class="login-header">🎓 EduTutor AI</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Personalized Learning with AI</p>', unsafe_allow_html=True)
    
    # Login form
    render_login_form(auth_handler)
    
    # Predefined accounts section
    st.markdown('<div class="demo-section">', unsafe_allow_html=True)
    st.markdown("#### 🔑 Demo Logins")
    st.info("Quick access to demo accounts:")
    
    # Create two columns for the predefined accounts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 👨‍🏫 Educator Demo")
        if st.button("👨‍🏫 Login as Educator", use_container_width=True, type="primary"):
            result = auth_handler.login("educator@edututor.ai", "educator123")
            if result:
                st.session_state.user = result.get('user')
                st.session_state.access_token = result.get('access_token')
                # Set default page for educator
                st.session_state.educator_page = "📝 Quiz Assignment"
                st.success("✅ Login successful!")
                st.rerun()
    
    with col2:
        st.markdown("##### 👨‍🎓 Student Demo")
        if st.button("👨‍🎓 Login as Student", use_container_width=True, type="secondary"):
            result = auth_handler.login("student@edututor.ai", "student123")
            if result:
                st.session_state.user = result.get('user')
                st.session_state.access_token = result.get('access_token')
                st.success("✅ Login successful!")
                st.rerun()

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
                        
                        # Set default page for educator
                        if result['user']['role'] == 'educator':
                            st.session_state.educator_page = "📝 Quiz Assignment"
                            
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials or server error. Please try again.")
            else:
                st.error("⚠️ Please fill in all fields")



if __name__ == "__main__":
    render_login_page()
