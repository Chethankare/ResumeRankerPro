import streamlit as st
from models import User
import re

def show_login_form():
    """Display login form and handle authentication"""
    st.subheader("Login to Your Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if not email or not password:
            st.error("Please fill in all fields")
            return None
        
        user = User.get_by_email(email)
        if user and user.verify_password(password):
            st.session_state['authenticated'] = True
            st.session_state['user'] = {
                'id': user.id,
                'email': user.email,
                'company': user.company,
                'subscription_level': user.subscription_level
            }
            st.success("Login successful!")
            st.rerun()  # Changed from st.experimental_rerun()
        else:
            st.error("Invalid email or password")
    return None

def show_signup_form():
    """Display signup form and handle registration"""
    st.subheader("Create New Account")
    email = st.text_input("Email", key="signup_email")
    company = st.text_input("Company (Optional)")
    password = st.text_input("Password", type="password", key="signup_password")
    confirm_password = st.text_input("Confirm Password", type="password")
    
    if st.button("Sign Up"):
        if not email or not password:
            st.error("Email and password are required")
            return None
        
        if password != confirm_password:
            st.error("Passwords do not match")
            return None
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("Invalid email format")
            return None
        
        if User.get_by_email(email):
            st.error("Email already registered")
            return None
        
        user = User.create(email, password, company)
        st.session_state['authenticated'] = True
        st.session_state['user'] = {
            'id': user.id,
            'email': user.email,
            'company': user.company,
            'subscription_level': user.subscription_level
        }
        st.success("Account created successfully!")
        st.rerun()  # Changed from st.experimental_rerun()
    return None

def show_auth():
    """Main authentication flow"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if not st.session_state['authenticated']:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            show_login_form()
        with tab2:
            show_signup_form()
        return False
    return True

def logout():
    """Logout the current user"""
    st.session_state['authenticated'] = False
    st.session_state.pop('user', None)
    st.info("You have been logged out")
    st.rerun()  # Changed from st.experimental_rerun()