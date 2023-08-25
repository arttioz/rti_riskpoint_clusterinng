
"""
Developing Environment:
Python version: 3.8 or later
Required packages: pandas, numpy, sklearn

You can install the necessary packages with pip:
pip install pandas numpy sklearn

Please make sure that you have the correct version of Python and the necessary packages installed before running this script.
"""

# Import the necessary libraries
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

# Load the data
data = pd.read_excel('integration_final_bkk_no_person.xlsx')

# Convert 'DEAD_YEAR' column to the year of each case
data['Year'] = data['DEAD_YEAR']

# Convert 'Acc_lat' and 'Acc_long' to numeric type (float)
data['Acc_lat'] = pd.to_numeric(data['Acc_lat'], errors='coerce')
data['Acc_long'] = pd.to_numeric(data['Acc_long'], errors='coerce')

# Drop rows with non-numeric 'Acc_lat' and 'Acc_long'
data = data.dropna(subset=['Acc_lat', 'Acc_long'])

# Convert lat/long to radians
coords = np.radians(data[['Acc_lat', 'Acc_long']].values)

# Define the parameters for DBSCAN
kms_per_radian = 6371.0088
epsilon = 100 / 1000 / kms_per_radian # 100 meters

# Run DBSCAN on the data
db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine').fit(coords)

# Assign the cluster labels to the main_data DataFrame
data['cluster'] = db.labels_

# Calculate centroid of each cluster and add it to the DataFrame
centroids = data.groupby('cluster')[['Acc_lat', 'Acc_long']].mean().reset_index()
centroids.columns = ['cluster', 'Acc_lat_centroid', 'Acc_long_centroid']

# Merge centroids to the main data
data = pd.merge(data, centroids, on='cluster', suffixes=('', '_centroid'))

# Group by cluster and 'Year' to get unique events
unique_events = data.groupby(['cluster', 'Year'])['DEAD_CONSO_REPORT_ID'].nunique().reset_index()

# Get a mapping from 'DEAD_CONSO_REPORT_ID' to 'Year'
case_year_dict = data.set_index('DEAD_CONSO_REPORT_ID')['Year'].to_dict()

# Define a function to count the number of cases in each year for a given list of cases
def count_cases_in_years(case_list):
    # Create a dictionary to hold the counts for each year
    year_counts = {year: 0 for year in range(2555, 2566)}
    # For each case, increment the count for the corresponding year
    for case_id in case_list:
        year = case_year_dict[case_id]
        if year in year_counts:
            year_counts[year] += 1
    return year_counts

# Group by cluster to get risk points
risk_points = data.groupby('cluster')['DEAD_CONSO_REPORT_ID'].apply(list).reset_index()
risk_points.columns = ['cluster', 'case_list']

# Calculate the total number of cases for each year and add it to the DataFrame
for year in range(2555, 2566):
    risk_points[str(year)] = risk_points['case_list'].apply(lambda x: count_cases_in_years(x)[year])

# Count the total number of cases in each cluster
risk_points['count'] = risk_points['case_list'].apply(len)

# Merge risk_points with centroids
risk_points = pd.merge(risk_points, centroids, on='cluster')

# Create Google Maps URLs
risk_points['Google Maps URL'] = 'https://www.google.com/maps/search/?api=1&query=' + risk_points['Acc_lat_centroid'].astype(str) + ',' + risk_points['Acc_long_centroid'].astype(str)

# Export the risk points to an Excel file
risk_points.to_excel('risk_points.xlsx', index=False)
