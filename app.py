import pandas as pd
import numpy as np
import streamlit as st
import os

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
    st.title("Patient Event Dashboard")

    # --- Load Data ---
    file_path = 'Eventsnew_data.xlsx'
    if not os.path.exists(file_path):
        st.error(f"Error: The file '{file_path}' was not found.")
        st.info("Please upload the file to the same directory and try again.")
        return

    try:
        df = pd.read_excel(file_path)
        st.success("Data loaded successfully!")
    except Exception as e:
        st.error(f"Error loading the Excel file: {e}")
        return

    # --- Data Processing and Cleaning ---
    df['Age Group'] = df['M&MCCoD Age'].apply(get_age_group)

    # Convert dates
    df['Event date'] = pd.to_datetime(df['Event date'], errors='coerce').dt.tz_localize(None)
    df['M&MCCoD_Alive_Date of Discharge'] = pd.to_datetime(df['M&MCCoD_Alive_Date of Discharge'], errors='coerce').dt.tz_localize(None)
    df.dropna(subset=['Event date', 'M&MCCoD_Alive_Date of Discharge'], inplace=True)

    # Length of stay
    df['length_of_stay_days'] = (
        (df['Event date'] - df['M&MCCoD_Alive_Date of Discharge']).dt.total_seconds() / (24 * 3600)
    )

    # Month column
    df['Month'] = df['Event date'].dt.to_period('M').astype(str)

    # Clean string columns
    df['M&MCCoD_Alive_Primary diagnosis'] = df['M&MCCoD_Alive_Primary diagnosis'].astype(str).str.strip()
    df['Organisation unit name'] = df['Organisation unit name'].astype(str).str.strip()
    df['Age Group'] = df['Age Group'].astype(str).str.strip()
    df['Month'] = df['Month'].astype(str).str.strip()

    # --- Sidebar Filters ---
    st.sidebar.header("Filter Options")

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
    st.subheader("Filtered Patient Details")
    if not filtered_patients.empty:
        patient_details = filtered_patients[[
            'M&MCCoD Sex',
            'M&MCCoD Age',
            'Age Group',
            'M&MCCoD_Alive_Primary diagnosis',
            'Organisation unit name',
            'length_of_stay_days'
        ]].copy()
        patient_details.index = np.arange(1, len(patient_details) + 1)
        st.dataframe(patient_details, use_container_width=True)
    else:
        st.warning("No patients found for the selected criteria.")

    # --- Charts based on filtered data ---
    st.subheader("Patient Volume by Month")
    patient_volume_by_month = filtered_patients.groupby('Month').size().reset_index(name='cases')
    if not patient_volume_by_month.empty:
        st.bar_chart(patient_volume_by_month.set_index('Month'))
    else:
        st.info("No data available for the selected filters to plot Patient Volume by Month.")

    st.subheader("Average Length of Stay by Diagnosis")
    if not filtered_patients.empty:
        avg_los_by_diagnosis = (
            filtered_patients
            .groupby('M&MCCoD_Alive_Primary diagnosis')['length_of_stay_days']
            .mean()
            .sort_values(ascending=False)
            .head(10)
        )
        if not avg_los_by_diagnosis.empty:
            st.bar_chart(avg_los_by_diagnosis)
        else:
            st.info("No data available for the selected filters to plot Average Length of Stay.")
    else:
        st.warning("No patients found for the selected criteria.")

# --- Run main function ---
if __name__ == "__main__":
    main()
