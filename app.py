import pandas as pd
import numpy as np
import streamlit as st
import os
import matplotlib.pyplot as plt

# --- Function to categorize age into groups ---
def get_age_group(age):
    """Categorizes a given age into predefined age groups."""
    if pd.isna(age):
        return 'Unknown'
    try:
        age = int(age)
    except (ValueError, TypeError):
        return 'Unknown'
    
    if 0 <= age <= 14:
        return '0-14 Years'
    elif 15 <= age <= 49:
        return '15-49 Years'
    elif 50 <= age <= 64:
        return '50-64 Years'
    elif age >= 65:
        return '65+ Years'
    else:
        return 'Unknown'

# --- Main function to run the Streamlit app ---
def main():
    st.set_page_config(layout="wide")
    st.title("📊 Patient Event Dashboard")

    # --- Load Data ---
    file_path = 'Eventsnew_data.xlsx'
    if not os.path.exists(file_path):
        st.error(f"Error: The file '{file_path}' was not found.")
        st.info("Please upload the file to the same directory and try again.")
        return

    try:
        df = pd.read_excel(file_path)
        st.success("✅ Data loaded successfully!")
    except Exception as e:
        st.error(f"Error loading the Excel file: {e}")
        return

    # --- Data Processing ---
    df['Age Group'] = df['M&MCCoD Age'].apply(get_age_group)
    df['Event date'] = pd.to_datetime(df['Event date'], errors='coerce').dt.tz_localize(None)
    df['M&MCCoD_Alive_Date of Discharge'] = pd.to_datetime(df['M&MCCoD_Alive_Date of Discharge'], errors='coerce').dt.tz_localize(None)
    
    df.dropna(subset=['Event date', 'M&MCCoD_Alive_Date of Discharge'], inplace=True)
    
    df['length_of_stay_days'] = (df['Event date'] - df['M&MCCoD_Alive_Date of Discharge']).dt.total_seconds() / (24 * 3600)
    df['Month'] = df['Event date'].dt.to_period('M').astype(str)
    
    df['M&MCCoD_Alive_Primary diagnosis'] = df['M&MCCoD_Alive_Primary diagnosis'].astype(str).str.strip()
    df['Organisation unit name'] = df['Organisation unit name'].astype(str).str.strip()
    df['Age Group'] = df['Age Group'].astype(str).str.strip()
    df['Month'] = df['Month'].astype(str).str.strip()
    
    # --- Sidebar Filters ---
    st.sidebar.header("🔎 Filter Options")
    months = ['All'] + sorted(df['Month'].unique().tolist())
    diagnoses = ['All Diagnoses'] + sorted(df['M&MCCoD_Alive_Primary diagnosis'].unique().tolist())
    age_groups = ['All Age Groups'] + sorted(df['Age Group'].unique().tolist())
    org_units = ['All Units'] + sorted(df['Organisation unit name'].unique().tolist())
    
    selected_month = st.sidebar.selectbox("Select Month", months)
    selected_diagnosis = st.sidebar.selectbox("Select Diagnosis", diagnoses)
    selected_age_group = st.sidebar.selectbox("Select Age Group", age_groups)
    selected_organisation_unit = st.sidebar.selectbox("Select Organisation Unit", org_units)

    # --- Apply Filters ---
    filtered_patients = df.copy()
    if selected_month != 'All':
        filtered_patients = filtered_patients[filtered_patients['Month'] == selected_month]
    if selected_diagnosis != 'All Diagnoses':
        filtered_patients = filtered_patients[filtered_patients['M&MCCoD_Alive_Primary diagnosis'] == selected_diagnosis]
    if selected_age_group != 'All Age Groups':
        filtered_patients = filtered_patients[filtered_patients['Age Group'] == selected_age_group]
    if selected_organisation_unit != 'All Units':
        filtered_patients = filtered_patients[filtered_patients['Organisation unit name'] == selected_organisation_unit]

    # --- Display Filtered Patient Details ---
    st.subheader("🧾 Filtered Patient Details")
    if not filtered_patients.empty:
        patient_details = filtered_patients[['M&MCCoD Sex', 'M&MCCoD Age', 'Age Group',
                                             'M&MCCoD_Alive_Primary diagnosis', 'Organisation unit name',
                                             'length_of_stay_days']].copy()
        patient_details.index = np.arange(1, len(patient_details) + 1)
        st.dataframe(patient_details, use_container_width=True)
    else:
        st.warning("⚠️ No patients found for the selected criteria.")

    # --- Charts Section ---
    st.subheader("📊 Analysis & Visualizations")

    if not filtered_patients.empty:
        col1, col2 = st.columns(2)

        # 📈 Trend of patient volume over months
        with col1:
            st.markdown("**Trend of Patients Over Time**")
            monthly_trend = filtered_patients.groupby('Month').size()
            fig, ax = plt.subplots()
            monthly_trend.plot(kind="line", marker="o", ax=ax)
            ax.set_ylabel("Cases")
            ax.set_xlabel("Month")
            st.pyplot(fig)

        # 🥧 Age group distribution
        with col2:
            st.markdown("**Age Group Distribution**")
            age_dist = filtered_patients['Age Group'].value_counts()
            fig, ax = plt.subplots()
            ax.pie(age_dist, labels=age_dist.index, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            st.pyplot(fig)

        col3, col4 = st.columns(2)

        # 📊 Patient volume by organisation
        with col3:
            st.markdown("**Patient Volume by Organisation Unit**")
            org_counts = filtered_patients['Organisation unit name'].value_counts()
            fig, ax = plt.subplots()
            org_counts.plot(kind="bar", ax=ax, color="skyblue")
            ax.set_ylabel("Cases")
            st.pyplot(fig)

        # 📦 Length of stay distribution
        with col4:
            st.markdown("**Length of Stay Distribution**")
            fig, ax = plt.subplots()
            filtered_patients['length_of_stay_days'].dropna().plot(kind="hist", bins=20, ax=ax, color="orange", edgecolor="black")
            ax.set_xlabel("Length of Stay (days)")
            st.pyplot(fig)

        # 📦 Boxplot of length of stay by diagnosis
        st.markdown("**Length of Stay by Diagnosis (Boxplot)**")
        fig, ax = plt.subplots(figsize=(10,5))
        filtered_patients.boxplot(column="length_of_stay_days", by="M&MCCoD_Alive_Primary diagnosis", ax=ax, rot=90)
        ax.set_title("Length of Stay by Diagnosis")
        ax.set_ylabel("Days")
        st.pyplot(fig)

# --- Run main function ---
if __name__ == "__main__":
    main()
