import os
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime
import pandas as pd

# Define base and data directories for absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

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
        transformed_data = []
        epochs = data.get('epochs', [])
        regions = [key for key in data.keys() if key != 'epochs']
        for idx, epoch in enumerate(epochs):
            for region in regions:
                region_data = data.get(region, {})
                if not isinstance(region_data, dict):
                    continue
                entry = {
                    'date': datetime.fromtimestamp(epoch).strftime('%Y-%m-%d %H:%M:%S'),
                    'region': region
                }
                excluded_energy_types = ['regional_in', 'regional_out']
                for energy_type, values in region_data.items():
                    if energy_type in excluded_energy_types or not isinstance(values, list):
                        continue
                    if idx < len(values):
                        entry[energy_type] = values[idx] if energy_type == 'spot_price' else values[idx] / 1000
                transformed_data.append(entry)
        return transformed_data
    except Exception as e:
        app.logger.error(f"Error parsing JSON '{file_path}': {e}")
        return []

def categorize_energy_sources():
    return {
        'renewable': [
            "hydropower", "geothermal", "bioenergy", "solar", "wind",
            "pumping_up", "pumping_down", "battery_charge", "battery_generate"
        ],
        'non_renewable': [
            "nuclear", "thermal_lng", "thermal_coal",
            "thermal_oil", "thermal_others", "others"
        ]
    }

def transform_to_categories(data):
    df = pd.DataFrame(data)
    categories = categorize_energy_sources()
    df['renewable'] = 0
    df['non_renewable'] = 0
    for col in df.columns:
        if col in categories['renewable']:
            df['renewable'] += df[col].fillna(0)
        elif col in categories['non_renewable']:
            df['non_renewable'] += df[col].fillna(0)
    return df

def aggregate_by_month(df):
    if not pd.api.types.is_datetime64_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    unique_months = df['month'].unique()
    if len(unique_months) > 1:
        days_per_month = df.groupby(['month', 'region'])['date'].apply(
            lambda x: len(x.dt.date.unique())
        ).reset_index(name='day_count')
        def expected_days(ts):
            import calendar
            return calendar.monthrange(ts.year, ts.month)[1]
        days_per_month['expected_days'] = days_per_month['month'].apply(expected_days)
        complete = days_per_month[days_per_month['day_count'] == days_per_month['expected_days']]
        complete_set = set(zip(complete['month'], complete['region']))
        df = df[df.apply(lambda r: (r['month'], r['region']) in complete_set, axis=1)]
    monthly = df.groupby(['month', 'region']).agg({'renewable':'sum','non_renewable':'sum'}).reset_index()
    return pd.melt(monthly, id_vars=['month','region'], value_vars=['renewable','non_renewable'], var_name='type', value_name='value').rename(columns={'month':'date_id'})

def aggregate_data_by_level(df, aggregation):
    df_copy = df.copy()
    exclude = ['date','region']
    sum_cols = [c for c in df_copy.columns if c not in exclude and c!='spot_price']
    if aggregation == 'hourly':
        return df_copy
    if aggregation == 'daily':
        df_copy['date_group'] = df_copy['date'].dt.floor('D')
    elif aggregation == 'weekly':
        df_copy['date_group'] = df_copy['date'].dt.to_period('W').dt.start_time
    elif aggregation == 'monthly':
        df_copy['date_group'] = df_copy['date'].dt.to_period('M').dt.start_time
    else:
        df_copy['date_group'] = df_copy['date']
    agg_dict = {c:'sum' for c in sum_cols}
    if 'spot_price' in df_copy.columns:
        agg_dict['spot_price'] = 'mean'
    grouped = df_copy.groupby(['date_group','region']).agg(agg_dict).reset_index().rename(columns={'date_group':'date'})
    return grouped

@app.route('/')
def root():
    return send_from_directory(os.path.join(BASE_DIR, '../client/dist'), 'index.html')

@app.route('/<path:path>')
def assets(path):
    return send_from_directory(os.path.join(BASE_DIR, '../client/dist'), path)

@app.route('/api/data', methods=['GET'])
def get_energy_data():
    try:
        start = request.args.get('start_date')
        end = request.args.get('end_date')
        region = request.args.get('region')
        agg = request.args.get('aggregation','hourly')
        app.logger.info(f"Received parameters: start_date={start}, end_date={end}, region={region}, aggregation={agg}")
        start_dt = pd.to_datetime(start) if start else None
        end_dt = pd.to_datetime(end) if end else None
        files = []
        if not start_dt or start_dt.year <= 2022:
            files.append(os.path.join(DATA_DIR, '2022','power-data.json'))
        if not start_dt or start_dt.year <= 2023:
            files.append(os.path.join(DATA_DIR, '2023','power-data.json'))
        if not end_dt or end_dt.year >= 2024:
            files.append(os.path.join(DATA_DIR, '2024','power-data.json'))
        app.logger.info(f"Loading data from files: {files}")
        all_data = []
        for fp in files:
            if os.path.exists(fp):
                data_chunk = parse_energy_json(fp)
                app.logger.info(f"Loaded {len(data_chunk)} records from {fp}")
                all_data.extend(data_chunk)
            else:
                app.logger.warning(f"File not found: {fp}")
        if not all_data:
            return jsonify({'error':'No data found'}),500
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        if start_dt:
            df = df[df['date']>=start_dt]
        if end_dt:
            df = df[df['date']<end_dt]
        if region:
            df = df[df['region']==region]
        if df.empty:
            return jsonify({'type':{'daily':'[]'},'categorized':{'monthly':[]}})
        df_agg = aggregate_data_by_level(df,agg)
        cat_df = transform_to_categories(df)
        monthly_data = aggregate_by_month(cat_df)
        return jsonify({
            'type':{'daily':df_agg.to_json(orient='records',date_format='iso')},
            'categorized':{'monthly':monthly_data.to_json(orient='records',date_format='iso')}
        })
    except Exception as e:
        app.logger.error(f"Error in API: {e}")
        return jsonify({'error':str(e)}),500

if __name__=='__main__':
    app.run(debug=True)
