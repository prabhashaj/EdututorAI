import requests
import streamlit as st

class AuthHandler:
    """Handles authentication for EduTutor AI frontend."""
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url

    def login(self, email: str, password: str):
        """Authenticate user and store token in session state."""
        try:
            st.write(f"Attempting to log in with email: {email}")
            response = requests.post(
                f"{self.api_base_url}/auth/login",
                json={"email": email, "password": password}
            )
            st.write(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                st.session_state["access_token"] = data.get("access_token")
                st.session_state["user"] = data.get("user")
                # Return the complete data with user and token
                return data
            else:
                try:
                    error_detail = response.json()
                    st.error(f"Login failed: {error_detail}")
                except:
                    st.error(f"Login failed: {response.text}")
                # Return None on failure
                return None
        except Exception as e:
            st.error(f"Login error: {str(e)}")
            # Return None on exception
            return None

    def logout(self):
        """Clear user session."""
        st.session_state.pop("access_token", None)
        st.session_state.pop("user", None)

    def is_authenticated(self) -> bool:
        """Check if user is logged in."""
        return "access_token" in st.session_state and "user" in st.session_state

    def get_current_user(self):
        """Get current user info from session."""
        return st.session_state.get("user")

    def register(self, email, name, role, password):
        """Register a new user."""
        try:
            response = requests.post(
                f"{self.api_base_url}/auth/register",
                json={
                    "email": email,
                    "name": name,
                    "role": role,
                    "password": password
                }
            )
            if response.status_code == 201:
                # Registration successful
                data = response.json()
                return data  # Return the data on success
            else:
                # Registration failed for reasons other than exception
                st.error("❌ Registration failed: " + response.text)
                return None
        except Exception as e:
            # Handle connection errors or other exceptions
            st.error(f"❌ Registration error: {str(e)}")
            return None
