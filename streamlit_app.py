import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from geopy.distance import geodesic
from joblib import Parallel, delayed

def fuzzy_match(row1, row2):
    name_similarity = fuzz.ratio(str(row1['CUSTOMER NAME']), str(row2['CUSTOMER NAME'])) / 100
    address_similarity = fuzz.ratio(str(row1['ADDRESS']), str(row2['ADDRESS'])) / 100
    mobile_similarity = fuzz.ratio(str(row1['MOBILE']), str(row2['MOBILE'])) / 100
    
    coords1 = (row1['latitude'], row1['longitude'])
    coords2 = (row2['latitude'], row2['longitude'])
    geo_distance = geodesic(coords1, coords2).km
    geo_similarity = max(0, 1 - geo_distance / 100)
    
    average_similarity = (name_similarity + address_similarity + mobile_similarity + geo_similarity) / 4
    return average_similarity

def check_duplicates(i, row1, group):
    duplicates = []
    for j, row2 in group.iterrows():
        if i >= j:
            continue
        similarity_score = fuzzy_match(row1, row2)
        if similarity_score >= 0.95:
            duplicate_pair = pd.concat([row1, row2], axis=1).T
            duplicates.append(duplicate_pair)
    return duplicates

st.title("Duplicate Customer Finder")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xls", "xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("### Preview of Uploaded Data")
    st.dataframe(df.head())
    
    if st.button("Find Duplicates"):
        duplicates = []
        for sector, group in df.groupby('SECTOR'):
            sector_duplicates = Parallel(n_jobs=-1)(delayed(check_duplicates)(i, row1, group)
                                                     for i, row1 in group.iterrows())
            duplicates.extend([item for sublist in sector_duplicates for item in sublist])
        
        if duplicates:
            duplicates_df = pd.concat(duplicates, ignore_index=True)
            st.write("### Detected Duplicates")
            st.dataframe(duplicates_df.head())
            
            # Allow user to download results
            output_file = "customer_duplicates_95.xlsx"
            duplicates_df.to_excel(output_file, index=False)
            
            with open(output_file, "rb") as file:
                st.download_button(
                    label="Download Excel File",
                    data=file,
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.write("No duplicates found.")