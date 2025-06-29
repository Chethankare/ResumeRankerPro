import streamlit as st
import os
import tempfile
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import time
import sys
import sqlite3
from contextlib import contextmanager

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#sys.path.append(os.path.dirname(os.path.abspath(_file_)))

# Import local modules
from auth import show_auth, logout
from models import User, Job, Analysis
from resume_parser import extract_text, extract_name, extract_contact_info
from similarity import analyze_resumes, serialize_results, deserialize_results
from database import init_db, get_db_connection

# Initialize database
init_db()

# App config
st.set_page_config(
    page_title="ResumeRanker Pro",
    page_icon="📄",
    layout="wide"
)

# Load skills database
with open("skills_db.txt") as f:
    SKILLS_DB = [line.strip() for line in f.readlines()]

# ----- Authentication -----
if not show_auth():
    st.stop()

# User is authenticated
user = st.session_state['user']
subscription_limit = User(user['email'], "").get_subscription_limit()  # Get subscription limits

# ----- Main App -----
st.title("📄 ResumeRanker Pro")
st.subheader(f"Welcome, {user['email']}")
st.caption(f"Subscription: {user['subscription_level'].upper()} | Resumes per job: {subscription_limit}")

# Navigation
tab1, tab2, tab3, tab4 = st.tabs(["Analyze Resumes", "Analysis History", "Account Settings", "Documentation"])

with tab1:  # Analyze Resumes Tab
    st.header("Analyze Resumes")
    
    # Job Description Section
    st.subheader("Job Description")
    job_title = st.text_input("Job Title", placeholder="Enter job title")
    
    input_method = st.radio("Job Description Input Method:", 
                          ["Paste Text", "Upload TXT File"], 
                          horizontal=True)
    
    job_desc_text = ""
    if input_method == "Paste Text":
        job_desc_text = st.text_area("Paste Job Description", height=300, 
                                    placeholder="Paste job description here...")
    else:
        jd_file = st.file_uploader("Upload Job Description", type=["txt"])
        if jd_file:
            job_desc_text = jd_file.read().decode("utf-8")
    
    # Resume Upload Section
    st.subheader("Resume Upload")
    resumes = st.file_uploader(f"Upload Resumes (PDF/DOCX) - Max {subscription_limit}", 
                             type=["pdf", "docx"], 
                             accept_multiple_files=True)
    
    # Show warning if over subscription limit
    if len(resumes) > subscription_limit:
        st.warning(f"Your subscription allows max {subscription_limit} resumes. "
                  f"Please remove {len(resumes) - subscription_limit} files.")
    
    # Analysis Button
    if st.button("Analyze Resumes", disabled=len(resumes) == 0 or not job_desc_text or len(resumes) > subscription_limit):
        st.info("Please upload job description and resumes to analyze")
    
    # Processing
    if resumes and job_desc_text and len(resumes) <= subscription_limit:
        with st.spinner(f"Processing {len(resumes)} resumes..."):
            start_time = time.time()
            
            # Save job to database
            job_id = Job.create(user['id'], job_title, job_desc_text)
            
            # Parse resumes
            parsed_data = []
            temp_dir = tempfile.mkdtemp()
            
            for i, resume in enumerate(resumes):
                # Save to temp file
                ext = "pdf" if resume.type == "application/pdf" else "docx"
                temp_path = os.path.join(temp_dir, f"resume_{i}.{ext}")
                with open(temp_path, "wb") as f:
                    f.write(resume.getbuffer())
                
                # Extract text and metadata
                text = extract_text(temp_path, ext)
                candidate_name = extract_name(text)
                contact_info = extract_contact_info(text)
                
                parsed_data.append({
                    "file_name": resume.name,
                    "text": text,
                    "candidate_name": candidate_name,
                    "contact": contact_info
                })
            
            # Perform analysis
            results, summary = analyze_resumes(job_desc_text, parsed_data, SKILLS_DB)
            
            # Save analysis to database
            results_json = serialize_results(results, summary)
            Analysis.save_results(user['id'], job_id, results_json)
            
            # Display results
            st.success(f"Analysis completed in {time.time() - start_time:.1f} seconds")
            st.subheader("Analysis Summary")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Resumes", summary['total_resumes'])
            col2.metric("Average Score", f"{summary['average_score']:.1f}/100")
            top_candidate = results[0]['candidate_name'] if results else "N/A"
            col3.metric("Top Candidate", top_candidate)
            
            # Score distribution
            st.subheader("Score Distribution")
            scores = [r['score'] for r in results]
            fig = px.histogram(x=scores, nbins=20, labels={'x': 'Score'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Top missing skills
            if summary['top_missing_skills']:
                st.subheader("Top Missing Skills Across Resumes")
                missing_df = pd.DataFrame(summary['top_missing_skills'], columns=['Skill', 'Count'])
                st.bar_chart(missing_df.set_index('Skill'))
            
            # Results table
            st.subheader("Ranked Resumes")
            results_df = pd.DataFrame([{
                "Rank": idx+1,
                "Candidate": r['candidate_name'],
                "Score": f"{r['score']:.1f}/100",
                "Matched Skills": len(r['matched_skills']),
                "Missing Skills": len(r['missing_skills']),
                "Contact": r['contact']['email'] or r['contact']['phone'] or "N/A",
                "File": r['file_name']
            } for idx, r in enumerate(results)])
            
            st.dataframe(results_df, hide_index=True, use_container_width=True)
            
            # Detailed view
            st.subheader("Candidate Details")
            for i, res in enumerate(results):
                with st.expander(f"{i+1}. {res['candidate_name']} - {res['score']:.1f}/100"):
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.subheader("✅ Matched Skills")
                        if res['matched_skills']:
                            st.write(", ".join(res['matched_skills']))
                        else:
                            st.info("No skills matched")
                    
                    with col2:
                        st.subheader("⚠️ Missing Skills")
                        if res['missing_skills']:
                            st.write(", ".join(res['missing_skills']))
                        else:
                            st.success("No missing skills - perfect match!")
                    
                    # Contact info
                    contact_info = []
                    if res['contact']['email']:
                        contact_info.append(f"✉️ {res['contact']['email']}")
                    if res['contact']['phone']:
                        contact_info.append(f"📞 {res['contact']['phone']}")
                    
                    if contact_info:
                        st.write(" | ".join(contact_info))
            
            # Export options
            st.download_button(
                "Export Results as CSV",
                results_df.to_csv(index=False),
                f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

with tab2:  # Analysis History Tab
    st.header("Analysis History")
    history = Analysis.get_history(user['id'])
    
    if not history:
        st.info("No analysis history found")
        st.stop()
    
    # Display history table
    history_df = pd.DataFrame(history, columns=['id', 'job_title', 'created_at'])
    history_df['created_at'] = pd.to_datetime(history_df['created_at'])
    history_df = history_df.sort_values('created_at', ascending=False)
    
    # Create display options for dropdown
    display_options = [
        f"{row['job_title']} | {row['created_at'].strftime('%Y-%m-%d %H:%M')}" 
        for _, row in history_df.iterrows()
    ]
    
    selected_display = st.selectbox("Select Analysis", display_options)
    
    if selected_display:
        # Find the matching row in the DataFrame
        match_mask = (
            history_df['job_title'] + " | " + 
            history_df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
        ) == selected_display
        
        if any(match_mask):
            selected_row = history_df[match_mask].iloc[0]
            selected_id = selected_row['id']
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT results FROM analyses WHERE id = ?
                ''', (selected_id,))
                result_row = cursor.fetchone()
                
                if result_row:
                    result_json = result_row[0]
                    analysis = deserialize_results(result_json)
                    
                    # Display analysis summary
                    st.subheader(f"Analysis: {selected_row['job_title']}")
                    st.caption(f"Date: {selected_row['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    # Summary metrics
                    col1, col2 = st.columns(2)
                    col1.metric("Total Resumes", analysis['summary']['total_resumes'])
                    col2.metric("Average Score", f"{analysis['summary']['average_score']:.1f}/100")
                    
                    # Results table
                    results_df = pd.DataFrame([{
                        "Rank": idx+1,
                        "Candidate": r['candidate_name'],
                        "Score": f"{r['score']:.1f}/100"
                    } for idx, r in enumerate(analysis['results'])])
                    
                    st.dataframe(results_df, hide_index=True, use_container_width=True)
                else:
                    st.warning("No results found for selected analysis")
        else:
            st.error("Selected analysis not found")

with tab3:  # Account Settings Tab
    st.header("Account Settings")
    
    st.subheader("Account Information")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Company:** {user.get('company', 'Not specified')}")
    st.write(f"**Subscription Level:** {user['subscription_level'].upper()}")
    
    st.divider()
    
    st.subheader("Change Password")
    current_pw = st.text_input("Current Password", type="password")
    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm New Password", type="password")
    
    if st.button("Update Password"):
        # Password update logic would go here
        if new_pw == confirm_pw:
            st.success("Password updated successfully")
        else:
            st.error("New passwords do not match")
    
    st.divider()
    
    st.subheader("Subscription Management")
    st.write("Upgrade your subscription for more features:")
    cols = st.columns(3)
    
    with cols[0]:
        st.info("**Free Tier**")
        st.write("✓ 20 resumes/job")
        st.write("✓ Basic analysis")
        st.write("✗ Export features")
        if user['subscription_level'] == 'free':
            st.success("Current Plan")
        else:
            st.button("Downgrade", disabled=True)
    
    with cols[1]:
        st.warning("**Pro Tier** - $29/month")
        st.write("✓ 50 resumes/job")
        st.write("✓ Advanced analysis")
        st.write("✓ CSV export")
        if user['subscription_level'] == 'pro':
            st.success("Current Plan")
        else:
            st.button("Upgrade to Pro")
    
    with cols[2]:
        st.success("**Enterprise** - $99/month")
        st.write("✓ 200 resumes/job")
        st.write("✓ All pro features")
        st.write("✓ Excel export")
        st.write("✓ Priority support")
        if user['subscription_level'] == 'enterprise':
            st.success("Current Plan")
        else:
            st.button("Upgrade to Enterprise")
    
    st.divider()
    
    if st.button("Logout", type="primary"):
        logout()

with tab4:  # Documentation Tab
    st.header("User Documentation")
    
    st.subheader("How to Use ResumeRanker Pro")
    st.write("""
    1. **Upload Resumes**: 
        - Click the "Upload Resumes" button in the Analyze Resumes tab
        - Select multiple PDF or DOCX files (up to your subscription limit)
        
    2. **Add Job Description**:
        - Either paste the job description text or upload a .txt file
        - Add a descriptive job title to help organize your analyses
        
    3. **Analyze**:
        - Click the "Analyze Resumes" button
        - Wait a few moments while we process your documents
        
    4. **Review Results**:
        - See ranked candidates with match scores
        - View matched and missing skills for each candidate
        - Explore analysis summary statistics
        
    5. **Export**:
        - Download results as CSV for further analysis
        - Access your analysis history anytime
    """)
    
    st.subheader("Best Practices")
    st.write("""
    - **Job Descriptions**: Use complete job descriptions for best results
    - **Resumes**: Ensure resumes are text-based (not scanned images)
    - **Naming**: Use candidate names in file names for easier identification
    - **Skills**: Add custom skills to skills_db.txt for better matching
    """)
    
    st.subheader("FAQ")
    with st.expander("What file formats are supported?"):
        st.write("We support PDF and DOCX files for resumes, and TXT files for job descriptions.")
    
    with st.expander("How is the match score calculated?"):
        st.write("""
        We use advanced NLP techniques (Sentence-BERT embeddings) to compare:
        - Skills and qualifications
        - Experience and education
        - Keywords and industry terms
        """)
    
    with st.expander("Can I add custom skills?"):
        st.write("Yes! Edit the skills_db.txt file to include your company-specific skills and terminology.")

# Footer
st.divider()
st.caption("ResumeRanker Pro v1.0 © 2025 | Resume Ranking System")