import os
import csv
import pandas as pd
import numpy as np
from pathlib import Path

def process_file(file_path):
    """
    Process a CSV file to extract yearly averages and ensure data from 2000-2023
    """
    try:
        # Determine what kind of file we're processing based on the filename
        filename = os.path.basename(file_path)
        value_column = None
        if "AQI" in filename or "Air quality" in filename:
            value_column = "AQI"
            measure = "AQI"
        elif "PM2.5" in filename:
            value_column = "Value"
            measure = "PM2.5"
        elif "income" in filename:
            value_column = "Value" 
            measure = "Income"
        elif "employed" in filename or "employment" in filename:
            value_column = "Value"
            measure = "Employment"
        elif "Population" in filename:
            value_column = "Value"
            measure = "Population"
        elif "temperature" in filename or "Temp" in filename:
            value_column = "Value"
            measure = "Temperature"
        else:
            value_column = "Value"
            measure = "Value"
        
        # Extract county name from the path
        county_name = str(Path(file_path).parent).split('/')[-1].replace(' Data', '')
        
        # Read the CSV file
        print(f"Processing {file_path}...")
        try:
            df = pd.read_csv(file_path)
        except pd.errors.ParserError:
            # Sometimes CSV files might need different parsing settings
            df = pd.read_csv(file_path, engine='python')
            
        # Handle different file formats
        date_column = None
        if "Date" in df.columns:
            date_column = "Date"
        elif "Year" in df.columns:
            date_column = "Year"
        else:
            # If neither Date nor Year is found, look for a column that might contain dates
            for col in df.columns:
                if df[col].dtype == object:  # Check if column contains strings
                    sample = str(df[col].iloc[0]) if not df.empty else ""
                    if "-" in sample and len(sample) >= 8:  # Simple check for date-like strings
                        date_column = col
                        break
            
        if date_column is None:
            print(f"Could not find date column in {file_path}")
            return None
            
        # Extract year from the date column
        if date_column == "Year":
            df["Year"] = pd.to_numeric(df[date_column], errors='coerce')
        else:
            try:
                # Try to parse dates - handle different date formats
                df["Year"] = pd.to_datetime(df[date_column], errors='coerce').dt.year
            except:
                # If regular parsing fails, try to extract year from string
                df["Year"] = df[date_column].str.extract(r'(\d{4})').astype(float)
        
        # Drop rows with invalid years
        df = df.dropna(subset=["Year"])
        
        # Find the appropriate value column if not already determined
        if value_column not in df.columns:
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col != "Year" and col != date_column:
                    value_column = col
                    break
        
        if value_column not in df.columns:
            # Try to find a column with numeric values
            for col in df.columns:
                if col != "Year" and col != date_column:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        if not df[col].isna().all():
                            value_column = col
                            break
                    except:
                        continue
        
        if value_column is None:
            print(f"Could not find value column in {file_path}")
            return None
            
        # Calculate the mean value for each year
        yearly_mean = df.groupby("Year")[value_column].mean().reset_index()
        
        # Filter to include only years from 2000 to 2023
        yearly_mean = yearly_mean[(yearly_mean["Year"] >= 2000) & (yearly_mean["Year"] <= 2023)]
        
        # Create a complete dataframe with all years from 2000 to 2023
        all_years = pd.DataFrame({"Year": range(2000, 2024)})
        result_df = pd.merge(all_years, yearly_mean, on="Year", how="left")
        
        # Check if we have gaps that need to be filled
        if result_df[value_column].isna().any():
            # Use interpolation to fill gaps
            result_df[value_column] = result_df[value_column].interpolate(method='linear')
            
            # For any remaining NaN values (at the beginning or end), use extrapolation
            if result_df[value_column].isna().any():
                # Create a helper series with indices for extrapolation
                helper = pd.Series(result_df[value_column].values, index=result_df["Year"])
                # Fill forward
                helper = helper.fillna(method='ffill')
                # Fill backward
                helper = helper.fillna(method='bfill')
                result_df[value_column] = helper.values
        
        # Create the standardized output
        output_df = pd.DataFrame({
            "Location": county_name,
            "Year": result_df["Year"],
            measure: result_df[value_column]
        })
        
        # Generate output filename
        output_dir = os.path.dirname(file_path)
        output_filename = f"{measure.lower()}_yearly_2000_2023.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save the processed data
        output_df.to_csv(output_path, index=False)
        print(f"Saved processed data to {output_path}")
        
        return output_path
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None

def process_county_directory(county_dir):
    """
    Process all CSV files in a county directory
    """
    processed_files = []
    for root, _, files in os.walk(county_dir):
        for file in files:
            if file.endswith('.csv') and not file.endswith('_yearly_2000_2023.csv'):
                file_path = os.path.join(root, file)
                processed_file = process_file(file_path)
                if processed_file:
                    processed_files.append(processed_file)
    
    return processed_files

def main():
    # Base directory
    base_dir = os.path.dirname(os.path.realpath(__file__))
    
    # Counties to process (starting with Frederick and remaining counties)
    counties = [
        "Fredrick County, MD Data",
        "Howard County, MD Data",
        "Loudoun County, VA Data",
        "Montgomery County, MD Data",
        "Prince George's County, MD Data",
        "Prince William County, VA Data",
        "Washington, DC Data"
    ]
    
    # Process each county directory
    for county in counties:
        county_dir = os.path.join(base_dir, county)
        if os.path.exists(county_dir):
            print(f"\nProcessing {county}...")
            processed_files = process_county_directory(county_dir)
            print(f"Processed {len(processed_files)} files in {county}")
        else:
            print(f"County directory not found: {county_dir}")

if __name__ == "__main__":
    main()

import pandas as pd
import numpy as np
from datetime import datetime
import os

def process_county_data(input_file, county_name, data_type):
    """
    Process county data files into standardized yearly format
    Args:
        input_file: Path to input CSV file
        county_name: Name of the county
        data_type: Type of data (temperature, aqi, income, population)
    """
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    # Identify date and value columns based on data type
    date_cols = ['Date', 'Year', 'Variable observation date']
    value_cols = {
        'temperature': ['Temperature', 'Temperature_Change', 'Variable observation value'],
        'aqi': ['AQI', 'Air Quality Index'],
        'income': ['Income', 'Median Household Income'],
        'population': ['Population'],
        'employment': ['People Employed']
    }
    
    # Find the correct date column
    date_col = None
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col:
        raise ValueError(f"Could not find date column in {input_file}")
    
    # Find the correct value column
    value_col = None
    for col in value_cols.get(data_type, []):
        if col in df.columns:
            value_col = col
            break
    
    if not value_col:
        raise ValueError(f"Could not find value column for {data_type} in {input_file}")
    
    # Convert date to datetime
    try:
        df['date'] = pd.to_datetime(df[date_col])
    except:
        try:
            # Try extracting year from string
            df['date'] = pd.to_datetime(df[date_col].astype(str).str[:4], format='%Y')
        except:
            raise ValueError(f"Could not parse dates in {input_file}")
    
    # Extract year
    df['year'] = df['date'].dt.year
    
    # Calculate yearly averages
    yearly_avg = df.groupby('year')[value_col].mean().reset_index()
    
    # Create full range of years from 2000 to 2023
    full_range = pd.DataFrame({'year': range(2000, 2024)})
    
    # Merge with actual data
    merged = pd.merge(full_range, yearly_avg, on='year', how='left')
    
    # For missing years, use linear interpolation
    merged[value_col] = merged[value_col].interpolate(method='linear')
    
    # Create final dataframe with required format
    final_df = pd.DataFrame({
        'Location': county_name,
        'Year': merged['year'],
        data_type.capitalize(): merged[value_col]
    })
    
    return final_df

def process_all_counties(base_dir="."):
    """Process all data types for all counties"""
    counties = [
        ("FairFax County, VA Data", "Fairfax County, VA"),
        ("Fredrick County, MD Data", "Frederick County, MD"),
        ("Howard County, MD Data", "Howard County, MD"),
        ("Montgomery County, MD Data", "Montgomery County, MD"),
        ("Prince George's County, MD Data", "Prince George's County, MD"),
        ("Loudoun County, VA Data", "Loudoun County, VA"),
        ("Prince William County, VA Data", "Prince William County, VA"),
        ("Arlington County, VA Data", "Arlington County, VA"),
        ("Alexandria City, VA Data", "Alexandria City, VA")
    ]
    
    data_types = ['temperature', 'aqi', 'income', 'population', 'employment']
    
    for county_folder, county_name in counties:
        print(f"\nProcessing {county_name}...")
        
        for data_type in data_types:
            try:
                # Find relevant input file
                input_files = []
                for file in os.listdir(os.path.join(base_dir, county_folder)):
                    if any(keyword in file.lower() for keyword in [data_type, 'temp', 'aqi', 'household', 'employ']):
                        input_files.append(os.path.join(base_dir, county_folder, file))
                
                if not input_files:
                    print(f"No {data_type} file found for {county_name}")
                    continue
                
                # Process first matching file
                input_file = input_files[0]
                df = process_county_data(input_file, county_name, data_type)
                
                # Save processed data
                output_file = os.path.join(
                    base_dir,
                    county_folder, 
                    f"{county_name.split(',')[0].lower().replace(' ', '_')}_{data_type}_2000_2023.csv"
                )
                df.to_csv(output_file, index=False)
                print(f"Processed {data_type} data for {county_name}")
                
            except Exception as e:
                print(f"Error processing {data_type} data for {county_name}: {str(e)}")

if __name__ == "__main__":
    process_all_counties("The Effect of Urbanization on AQI in NOVA")