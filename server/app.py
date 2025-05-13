import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import pandas as pd

app = Flask(__name__)
CORS(app)

def parse_energy_json(file_path):
    """
    Parse JSON file with energy data where:
    - 'epochs' is a list of timestamps
    - Each region (like 'japan') contains energy sources as keys
    - Each energy source (like 'nuclear') contains a list of values matching epochs
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Initialize list to store transformed data
        transformed_data = []
        
        # Get epochs array and regions
        epochs = data.get('epochs', [])
        regions = [key for key in data.keys() if key != 'epochs']
        
        # For each timestamp in epochs
        for idx, epoch in enumerate(epochs):
            for region in regions:
                region_data = data[region]  # This is a dictionary like {nuclear: [values], thermal: [values]}
                
                # Check if region_data is actually a dictionary
                if not isinstance(region_data, dict):
                    #print(f"Warning: data['{region}'] is not a dictionary, skipping")
                    continue
            
                # Create base entry for this timestamp and region
                entry = {
                    'date': datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S'),
                    'region': region
                }
                
                # Define energy types to exclude
                excluded_energy_types = ['regional_in', 'regional_out']

                # Add all energy values for this timestamp
                for energy_type in region_data.keys():
                    # Skip excluded energy types
                    if energy_type in excluded_energy_types:
                        continue
                    
                    # Make sure energy data is a list
                    if not isinstance(region_data[energy_type], list):
                        #print(f"Error: region_data['{energy_type}'] is not a list, it's a {type(region_data[energy_type])}")
                        continue
                        
                    # Make sure we don't go out of bounds
                    if idx < len(region_data[energy_type]):
                        if (energy_type == 'spot_price'):
                          entry[energy_type] = region_data[energy_type][idx]
                        else:
                          entry[energy_type] = region_data[energy_type][idx] / 1000
                
                transformed_data.append(entry)
        
        return transformed_data
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return []
    
def categorize_energy_sources():
    """
    Define energy source categorization
    """
    return {
        'renewable': [
          "hydropower",
          "geothermal",
          "bioenergy",
          "solar",
          "wind",
          "pumping_up",
          "pumping_down",
          "battery_charge",
          "battery_generate"
        ],
        'non_renewable': [
          "nuclear",
          "thermal_lng",
          "thermal_coal",
          "thermal_oil",
          "thermal_others",
          "others"
        ]
    }

def transform_to_categories(data):
    """
    Transform data by categorizing into renewable and non-renewable
    """
    # Convert to DataFrame for easier processing
    df = pd.DataFrame(data)
    
    # Get category for each energy source
    categories = categorize_energy_sources()
    
    # Initialize renewable and non-renewable columns
    df['renewable'] = 0
    df['non_renewable'] = 0
    
    # Sum values by category
    for energy_type in df.columns:
        if energy_type in categories['renewable']:
            # Add the values to the renewable category, handling NaN
            df['renewable'] += df[energy_type].fillna(0)
        elif energy_type in categories['non_renewable']:
            # Add the values to the non-renewable category, handling NaN
            df['non_renewable'] += df[energy_type].fillna(0)
  
    return df

def aggregate_by_month(df):
    """
    Aggregate data by month.
    Filters out incomplete months only if multiple months are present.
    Returns DataFrame with format:
    {date_id: datetime object, type: 'renewable'/'non_renewable', value: total}
    """
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Create a month column by truncating to first day of month
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    
    # Count unique months in the dataset
    unique_months = df['month'].unique()
    num_months = len(unique_months)
    
    # Only filter incomplete months if there's more than one month
    if num_months > 1:
        # Count days per month and region
        days_per_month = df.groupby(['month', 'region'])['date'].apply(
            lambda x: len(x.dt.date.unique())
        ).reset_index(name='day_count')
        
        # Determine the expected number of days for each month
        def expected_days(month_timestamp):
            year = month_timestamp.year
            month = month_timestamp.month
            import calendar
            return calendar.monthrange(year, month)[1]
        
        days_per_month['expected_days'] = days_per_month['month'].apply(expected_days)
        days_per_month['completeness'] = days_per_month['day_count'] / days_per_month['expected_days']
        
        # Filter for complete months
        complete_months = days_per_month[days_per_month['completeness'] == 1]
        complete_month_regions = list(zip(complete_months['month'], complete_months['region']))
        
        # Filter the dataframe to only include complete months
        df_filtered = df[df.apply(lambda row: (row['month'], row['region']) in complete_month_regions, axis=1)]
        
        # Use filtered data only if we still have data left
        if not df_filtered.empty:
            df = df_filtered
    
    # Group by month and region
    monthly = df.groupby(['month', 'region']).agg({
        'renewable': 'sum',
        'non_renewable': 'sum'
    }).reset_index()
    
    # Reshape using melt
    monthly_melted = pd.melt(
        monthly, 
        id_vars=['month', 'region'],
        value_vars=['renewable', 'non_renewable'],
        var_name='type',
        value_name='value'
    )
    
    # Rename month column to date_id
    monthly_melted = monthly_melted.rename(columns={'month': 'date_id'})
    
    return monthly_melted
  
# New function to handle different aggregation levels
def aggregate_data_by_level(df, aggregation):
    """
    Aggregate data based on the specified level: hourly, daily, weekly, or monthly
    With spot_price averaged instead of summed
    """
    # Make a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Define energy sources to aggregate (excluding metadata columns)
    exclude_cols = ['date', 'region']
    energy_cols = [col for col in df_copy.columns if col not in exclude_cols]
    
    # Separate spot_price from other energy columns
    sum_cols = [col for col in energy_cols if col != 'spot_price']
    
    # Apply appropriate time-based aggregation
    if aggregation == 'hourly':
        # No aggregation needed, already at hourly level
        return df_copy
    
    elif aggregation == 'daily':
        # Truncate to day
        df_copy['date_group'] = df_copy['date'].dt.floor('D')
        
    elif aggregation == 'weekly':
        # Truncate to week start (Monday)
        df_copy['date_group'] = df_copy['date'].dt.to_period('W').dt.start_time
        
    elif aggregation == 'monthly':
        # Truncate to month start
        df_copy['date_group'] = df_copy['date'].dt.to_period('M').dt.start_time
    
    else:
        # Default to hourly if invalid aggregation level
        print(f"Warning: Unknown aggregation level '{aggregation}', defaulting to hourly")
        return df_copy
    
    # Create a dictionary of aggregation functions for each column
    agg_dict = {col: 'sum' for col in sum_cols}
    
    # Add average for spot_price if it exists in the dataframe
    if 'spot_price' in df_copy.columns:
        agg_dict['spot_price'] = 'mean'
    
    # Group by the truncated date and region, applying different aggregations
    grouped = df_copy.groupby(['date_group', 'region']).agg(agg_dict).reset_index()
    
    # Rename date_group back to date for consistency
    grouped.rename(columns={'date_group': 'date'}, inplace=True)
    
    print(f"Aggregated data to {aggregation} level: {len(df_copy)} → {len(grouped)} records")
    
    return grouped

@app.route('/')
def root():
    return send_from_directory('../client/dist', 'index.html')

# Path for the rest of the static files (JS/CSS)
@app.route('/<path:path>')
def assets(path):
    return send_from_directory('../client/dist', path)

# Update the get_energy_data route in your Flask app
@app.route('/api/data', methods=['GET'])
def get_energy_data():
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        region = request.args.get('region')
        aggregation = request.args.get('aggregation', 'hourly')  # Default to hourly if not specified
        
        print(f"Received parameters: start_date={start_date}, end_date={end_date}, region={region}, aggregation={aggregation}")
        
        # Convert dates to datetime objects for comparison
        start_date_dt = pd.to_datetime(start_date) if start_date else None
        end_date_dt = pd.to_datetime(end_date) if end_date else None
        
        # Determine which files to load based on date ranges
        files_to_load = []

        # Add 2022 file if start_date is in 2022 or if no start_date specified
        if not start_date_dt or start_date_dt.year <= 2022:
            files_to_load.append('./data/2022/power-data.json')

        # Add 2023 file if start_date is in 2023 or if no start_date specified
        if not start_date_dt or start_date_dt.year <= 2023:
            files_to_load.append('./data/2023/power-data.json')
            
        # Add 2024 file if end_date is in 2024 or if no end_date specified
        if not end_date_dt or end_date_dt.year >= 2024:
            files_to_load.append('./data/2024/power-data.json')
        
        print(f"Loading data from files: {files_to_load}")
        
        # Load and combine data from all required files
        all_data = []
        for file_path in files_to_load:
            try:
                file_data = parse_energy_json(file_path)
                if file_data:
                    all_data.extend(file_data)
                    print(f"Loaded {len(file_data)} records from {file_path}")
                else:
                    print(f"No data found in {file_path}")
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        if not all_data:
            return jsonify({'error': 'Failed to load data from any file'}), 500
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        print(f"Combined DataFrame size before filtering: {len(df)}")
        
        # Apply filters
        if start_date_dt:
            df = df[df['date'] >= start_date_dt]
            print(f"DataFrame size after start_date filter: {len(df)}")
        
        if end_date_dt:
            df = df[df['date'] < end_date_dt]
            print(f"DataFrame size after end_date filter: {len(df)}")
        
        if region:
            print(f"Filtering by region: {region}")
            df = df[df['region'] == region]
            print(f"DataFrame size after region filter: {len(df)}")

        # Check if we have any data left after filtering
        if len(df) == 0:
            print("WARNING: No data left after filtering!")
            return jsonify({
                'type': {'daily': '[]'},
                'categorized': {'monthly': []}
            })


        # Apply aggregation based on the requested level
        df_aggregated = aggregate_data_by_level(df, aggregation)
        #print(start_date_dt, end_date_dt, df.tail(5), df_aggregated)
        
        # Continue with transformations for categorized data
        cat_df = transform_to_categories(df)
        monthly_data = aggregate_by_month(cat_df)
        
        return jsonify({
            'type': {
                'daily': df_aggregated.to_json(orient='records', date_format='iso')
            },
            'categorized': {
                'monthly': monthly_data.to_json(orient='records', date_format='iso')
            }
        })
            
    except Exception as e:
        print(f"Error in API: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)