import pandas as pd
import numpy as np
from datetime import datetime

def process_temperature_data(input_file, county_name):
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    try:
        # First try YYYY-MM format
        df['date'] = pd.to_datetime(df['Variable observation date'], format='%Y-%m')
    except:
        try:
            # Try YYYY format
            df['date'] = pd.to_datetime(df['Variable observation date'], format='%Y')
        except:
            # Try extracting year from the date string
            df['date'] = pd.to_datetime(df['Variable observation date'].str[:4], format='%Y')
    
    # Extract year
    df['year'] = df['date'].dt.year
    
    # Calculate yearly averages
    yearly_avg = df.groupby('year')['Variable observation value'].mean().reset_index()
    
    # Create full range of years from 2000 to 2023
    full_range = pd.DataFrame({'year': range(2000, 2024)})
    
    # Merge with actual data
    merged = pd.merge(full_range, yearly_avg, on='year', how='left')
    
    # For missing years, use linear interpolation
    merged['Variable observation value'] = merged['Variable observation value'].interpolate(method='linear')
    
    # Create final dataframe with required format
    final_df = pd.DataFrame({
        'Location': county_name,
        'Year': merged['year'],
        'Temperature_Change': merged['Variable observation value']
    })
    
    return final_df

def find_temperature_file(county_folder, county_name):
    base_patterns = [
        f"{county_folder}/Projected max temperature change under RCP 2.6 (based on year 2006) in {county_name.split(',')[0]}.csv",
        f"{county_folder}/{county_name.split(',')[0]} Yearly Temp Change 2000-2024.csv",
        f"{county_folder}/temperature_data.csv"
    ]
    
    for pattern in base_patterns:
        try:
            pd.read_csv(pattern)
            return pattern
        except:
            continue
    
    raise FileNotFoundError(f"Could not find temperature file for {county_name}")

# Process Frederick County data
frederick_input = "Fredrick County, MD Data/Projected max temperature change under RCP 2.6 (based on year 2006) in Frederick County.csv"
frederick_output = "Fredrick County, MD Data/frederick_yearly_temp_2000_2023.csv"

frederick_df = process_temperature_data(frederick_input, "Frederick County, MD")
frederick_df.to_csv(frederick_output, index=False)
print("Processed Frederick County, MD")

# Process all other counties
counties = [
    ("Howard County, MD Data", "Howard County, MD"),
    ("Montgomery County, MD Data", "Montgomery County, MD"),
    ("Prince George's County, MD Data", "Prince George's County, MD"),
    ("Loudoun County, VA Data", "Loudoun County, VA"),
    ("Prince William County, VA Data", "Prince William County, VA"),
    ("Washington, DC Data", "Washington, DC")
]

for county_folder, county_name in counties:
    try:
        input_file = find_temperature_file(county_folder, county_name)
        output_file = f"{county_folder}/{county_name.split(',')[0].lower().replace(' ', '_')}_yearly_temp_2000_2023.csv"
        
        county_df = process_temperature_data(input_file, county_name)
        county_df.to_csv(output_file, index=False)
        print(f"Processed {county_name}")
    except Exception as e:
        print(f"Error processing {county_name}: {str(e)}")