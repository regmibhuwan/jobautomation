import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from typing import cast

# API base URL (configurable for deployment)
api_base = os.getenv("API_BASE_URL")
if not api_base:
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    if render_external_url:
        api_base = render_external_url.rstrip("/")

API_BASE = api_base or "http://localhost:8000"

st.set_page_config(
    page_title="Tech Job Automation Dashboard",
    page_icon="💻",
    layout="wide"
)

st.title("💻 Tech Job Automation Dashboard")

# Sidebar for navigation
page = st.sidebar.selectbox("Navigate", ["Jobs", "Applications", "Resume Upload", "Companies", "Automation"])

if page == "Jobs":
    st.header("💻 Tech Job Listings")
    st.info("🔍 Showing only tech jobs (Software Engineer, Developer, Data Scientist, etc.)")
    
    # Fetch jobs from API
    try:
        response = requests.get(f"{API_BASE}/jobs")
        if response.status_code == 200:
            jobs = response.json()
            
            if jobs:
                # Create DataFrame for better display
                df: pd.DataFrame = pd.DataFrame(jobs)
                
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    companies = ["All"] + list(df['company'].unique())
                    selected_company = st.selectbox("Company", companies)
                
                with col2:
                    statuses = ["All"] + list(df['status'].unique())
                    selected_status = st.selectbox("Status", statuses)
                
                with col3:
                    limit = st.slider("Number of jobs", 5, 50, 20)
                
                # Filter data
                filtered_df = cast(pd.DataFrame, df.copy())
                if selected_company != "All":
                    filtered_df = filtered_df[filtered_df['company'] == selected_company]
                if selected_status != "All":
                    filtered_df = filtered_df[filtered_df['status'] == selected_status]
                
                filtered_jobs_df = cast(pd.DataFrame, filtered_df)
                filtered_jobs = filtered_jobs_df.head(limit).to_dict(orient="records")

                # Display jobs
                for job in filtered_jobs:
                    with st.expander(f"{job['title']} - {job['company']}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Location:** {job['location']}")
                            st.write(f"**Status:** {job['status']}")
                            st.write(f"**Posted:** {job['date_posted']}")
                            st.write(f"**URL:** [View Job]({job['url']})")
                        with col2:
                            if st.button(f"Apply", key=f"apply_{job['id']}"):
                                try:
                                    apply_response = requests.post(f"{API_BASE}/jobs/{job['id']}/apply")
                                    if apply_response.status_code == 200:
                                        st.success("Applied successfully!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {apply_response.json().get('detail', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Error applying: {str(e)}")
            else:
                st.info("No tech jobs found. Run the scrapers to collect tech job data.")
        else:
            st.error(f"Error fetching jobs: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

elif page == "Applications":
    st.header("📝 Applications")
    
    try:
        response = requests.get(f"{API_BASE}/applications")
        if response.status_code == 200:
            applications = response.json()
            
            if applications:
                df = pd.DataFrame(applications)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No applications found.")
        else:
            st.error(f"Error fetching applications: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

elif page == "Resume Upload":
    st.header("📄 Resume Upload & Parsing")
    
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=['pdf', 'docx'],
        help="Upload a PDF or DOCX resume to extract skills and experience"
    )
    
    if uploaded_file is not None:
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size} bytes")
        
        if st.button("Parse Resume"):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(f"{API_BASE}/upload-resume", files=files)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success("Resume parsed successfully!")
                    
                    # Display parsed data
                    parsed_data = result['parsed_data']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:  
                        st.subheader("Skills Found")
                        if parsed_data['skills']:
                            for skill in parsed_data['skills']:
                                st.write(f"• {skill}")
                        else:
                            st.write("No skills detected")
                    
                    with col2:
                        st.subheader("Experience")
                        if parsed_data['experience_years']:
                            st.write(f"**Years of Experience:** {parsed_data['experience_years']}")
                        else:
                            st.write("Experience not detected")
                    
                    if parsed_data['education']:
                        st.subheader("Education")
                        for edu in parsed_data['education']:
                            st.write(f"• {edu}")
                    
                    if parsed_data['contact']:
                        st.subheader("Contact Information")
                        for key, value in parsed_data['contact'].items():
                            st.write(f"**{key.title()}:** {value}")
                
                else:
                    st.error(f"Error parsing resume: {response.json().get('detail', 'Unknown error')}")
            
            except Exception as e:
                st.error(f"Error uploading resume: {str(e)}")

elif page == "Companies":
    st.header("🏢 Companies")
    
    try:
        response = requests.get(f"{API_BASE}/companies")
        if response.status_code == 200:
            companies = response.json()
            
            if companies:
                df = pd.DataFrame(companies)
                st.dataframe(df, use_container_width=True)
                
                # Create a simple chart
                st.subheader("Jobs by Company")
                st.bar_chart(df.set_index('company')['count'])
            else:
                st.info("No company data found.")
        else:
            st.error(f"Error fetching companies: {response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")

elif page == "Automation":
    st.header("🤖 Tech Job Application Automation")
    
    # Get automation status
    try:
        status_response = requests.get(f"{API_BASE}/automation/status")
        if status_response.status_code == 200:
            status_data = status_response.json()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Pending Applications", status_data['pending_applications'])
            
            with col2:
                if st.button("Run Automation", type="primary"):
                    with st.spinner("Running automation..."):
                        try:
                            run_response = requests.post(f"{API_BASE}/automation/run", params={"max_applications": 3})
                            if run_response.status_code == 200:
                                result = run_response.json()
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(f"Error: {run_response.json().get('detail', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error running automation: {str(e)}")
            
            # Show pending jobs
            if status_data['jobs']:
                st.subheader("Pending Applications")
                for job in status_data['jobs']:
                    with st.expander(f"{job['title']} - {job['company']}"):
                        st.write(f"**Job ID:** {job['id']}")
                        st.write(f"**URL:** [View Job]({job['url']})")
            else:
                st.info("No pending applications found.")
        else:
            st.error(f"Error fetching automation status: {status_response.status_code}")
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
    
    # Automation settings
    st.subheader("Automation Settings")
    st.info("""
    **Current Features:**
    - ✅ Tech job filtering (Software Engineer, Developer, Data Scientist, etc.)
    - ✅ Uber tech job application automation
    - ✅ Resume data extraction and form filling
    - ✅ Application tracking and status updates
    - ⏳ Additional companies (coming soon)
    
    **How it works:**
    1. Upload your resume to extract personal information
    2. The system automatically fills application forms for tech jobs
    3. Applications are tracked and status is updated
    4. Results are logged for review
    """)

# Footer
st.markdown("---")
st.markdown("**Tech Job Automation System** - Built with FastAPI and Streamlit")
