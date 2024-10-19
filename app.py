from flask import Flask, render_template, request, jsonify  # Add render_template and jsonify
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import datetime
import os
from bs4 import BeautifulSoup
import requests
from apscheduler.schedulers.background import BackgroundScheduler
# from dotenv import load_dotenv
from supabase import create_client, Client

app = Flask(__name__)

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Scrape and insert
def scrape_and_insert():
    # URL of the page
    url = "https://services2.hdb.gov.sg/webapp/BP13BTOENQWeb/AR_Oct2024_BTO?strSystem=BTO"
    # Mimic a browser by setting the User-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Make a request to fetch the page content with headers
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all tables in the page
        tables = soup.find_all('table')

        # Extract and convert the tables to pandas DataFrames
        dfs = [pd.read_html(str(table))[0] for table in tables]

        # Display or save the DataFrames
        for i, df in enumerate(dfs):
            print(f"Table {i + 1}:")
            print(df)
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

    APPLICATION_PERIOD = '202410'

    PROJECT_TYPE = 'Community Care Apartments'
    for _, row in dfs[0].iterrows():
        supabase.table('bto_application').insert({
            'date': datetime.now().strftime("%Y%m%d"),
            'hour': datetime.now().strftime("%H"),
            'application_period': APPLICATION_PERIOD,
            'project': row['Town'],
            'project_type': PROJECT_TYPE,
            'flat_type': PROJECT_TYPE,
            'number_of_units': row['Number of Units'],
            'number_of_applicants': row['Number of Applicants'],
            'seniors_application_rate': row['Application Rate'],
            # 'first_timer_families_application_rate': row['Application Rate']['First-Timer Families'],
            # 'first_timer_singles_application_rate': row['Application Rate']['First-Timer Singles'],
            # 'second_timer_families_application_rate': row['Application Rate']['Second-Timer-Families']
        }).execute()

    PROJECT_TYPE = '2-room Flexi BTO flats'
    for _, row in dfs[1].iloc[:-1].iterrows():
        supabase.table('bto_application').insert({
            'date': datetime.now().strftime("%Y%m%d"),
            'hour': datetime.now().strftime("%H"),
            'application_period': APPLICATION_PERIOD,
            'project': row['Town']['Town'],
            'project_type': PROJECT_TYPE,
            'flat_type': PROJECT_TYPE,
            'number_of_units': row['Number of Units']['Number of Units'],
            'number_of_applicants': row['Number of Applicants']['Number of Applicants'],
            'seniors_application_rate': row['Application Rate']['Seniors'],
            'first_timer_families_application_rate': row['Application Rate']['First-Timer Families'],
            'first_timer_singles_application_rate': row['Application Rate']['First-Timer Singles'],
            'second_timer_families_application_rate': row['Application Rate']['Second-Timer Families']
        }).execute()

    PROJECT_TYPE = '3-room and bigger BTO flats'
    for _, row in dfs[2].iloc[:-1].iterrows():
        supabase.table('bto_application').insert({
            'date': datetime.now().strftime("%Y%m%d"),
            'hour': datetime.now().strftime("%H"),
            'application_period': APPLICATION_PERIOD,
            'project': row['Town']['Town'],
            'project_type': PROJECT_TYPE,
            'flat_type': row['Flat Type']['Flat Type'],
            'number_of_units': row['Number of Units']['Number of Units'],
            'number_of_applicants': row['Number of Applicants']['Number of Applicants'],
            # 'seniors_application_rate': row['Application Rate']['Seniors'],
            'first_timer_families_application_rate': row['Application Rate']['First-Timer Families'],
            # 'first_timer_singles_application_rate': row['Application Rate']['First-Timer Singles'],
            'second_timer_families_application_rate': row['Application Rate']['Second-Timer Families']
        }).execute()

# Start the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(scrape_and_insert, 'interval', hours=1)  # Schedule to run every hour
scheduler.start()

# data
# load_dotenv()
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_KEY")

response = supabase.table('bto_application').select('*').execute()
data = pd.DataFrame(response.data)
data['date_hour'] = data['date'].astype("string") + '_' + ["0" + i if int(i) < 10 else i for i in data['hour'].astype("string")]
df = pd.DataFrame(data)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot():
    # Plot 1: first_timer_families_application_rate
    fig = px.line(df, x="date_hour", y="first_timer_families_application_rate", color='project', title = 'First Timer Family Application Rate')
    
    # Plot 2: second_timer_families_application_rate
    fig2 = px.line(df, x="date_hour", y="second_timer_families_application_rate", color='project', title = 'Second Timer Families Application Rate')

    # Convert the figures to JSON
    graph_json1 = fig.to_json()
    graph_json2 = fig2.to_json()

    # Return both figures as JSON
    return jsonify({'graph1': graph_json1, 'graph2': graph_json2})

if __name__ == '__main__':
    app.run(debug=True)