import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import pickle
import pretty_midi as pm
import base64
import io
from datetime import datetime
import requests

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Add MIDI player library - using soundfont-player for proper GM instrument support
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <script src="https://cdn.jsdelivr.net/npm/soundfont-player@0.12.0/dist/soundfont-player.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/@tonejs/midi@2.0.28/build/Midi.min.js"></script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Load data
def load_data():
    with open('../misc/dmrb.pickle', 'rb') as handle:
        dmrb = pickle.load(handle)
    
    df = pd.DataFrame()
    for gauge in dmrb:
        df[gauge] = pd.Series(dmrb[gauge])
    
    colsDrop = ['05476500','05476590','05476735','05478265','05480080','05480820',
                '05480930','05489490','05481510','05482315','05482430','05483318',
                '05483349','05483470','05484600']
    df.drop(columns=colsDrop, inplace=True)
    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)
    df = df.astype(float)
    
    return df, list(df.columns)

def get_usgs_site_info(site_numbers):
    """
    Fetch site information including lat/lon from USGS Water Services API
    
    Parameters:
    site_numbers: list of USGS site numbers (e.g., ['05476750', '05479000'])
    
    Returns:
    dict: {site_number: (lat, lon, name)}
    """
    # Join site numbers with commas
    sites_str = ','.join(site_numbers)
    
    # USGS Site Service endpoint
    url = f"https://waterservices.usgs.gov/nwis/site/?format=rdb&sites={sites_str}&siteOutput=expanded"
    
    print(f"Fetching gauge locations for {len(site_numbers)} sites from USGS API...")
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Error fetching USGS data: {response.status_code}")
            return {}
        
        # Parse the RDB format (tab-delimited with # comments)
        lines = response.text.split('\n')
        
        # Skip comment lines and find header
        data_lines = [line for line in lines if not line.startswith('#')]
        
        if len(data_lines) < 2:
            return {}
        
        # First line is headers, second is data types (skip), rest is data
        headers = data_lines[0].split('\t')
        
        # Find column indices
        site_no_idx = headers.index('site_no')
        lat_idx = headers.index('dec_lat_va')
        lon_idx = headers.index('dec_long_va')
        name_idx = headers.index('station_nm')
        
        # Parse data lines (skip first two: headers and format)
        site_info = {}
        for line in data_lines[2:]:
            if line.strip():
                parts = line.split('\t')
                if len(parts) > max(site_no_idx, lat_idx, lon_idx, name_idx):
                    site_no = parts[site_no_idx]
                    lat = float(parts[lat_idx]) if parts[lat_idx] else None
                    lon = float(parts[lon_idx]) if parts[lon_idx] else None
                    name = parts[name_idx]
                    
                    if lat and lon:
                        site_info[site_no] = (lat, lon, name)
        
        print(f"Successfully retrieved {len(site_info)} gauge locations")
        return site_info
    
    except Exception as e:
        print(f"Error fetching USGS site info: {e}")
        return {}

df, valid_gauges = load_data()

# Fetch gauge locations from USGS API
gauge_locations = get_usgs_site_info(valid_gauges)

# Frequency mappings
freqDict = {
    'Arab Double Harmonic': [130.81,138.59,164.81,174.61,196.00,207.65,246.94,261.63,
                             277.18,329.63,349.23,392.00,415.30,493.88,523.25],
    'Chromatic': [i for i in range(36,84)],
    'C Major Pentatonic': [48,50,52,55,57,60,62,64,67,69,72,74,76,79,81,84],
    'C Major Diatonic': [36,38,40,41,43,45,47,48,50,52,53,55,57,59,60,62,64,65,67,69,71,
                         72,74,76,77,79,81,84],
    'A Minor Pentatonic': [45,48,50,52,55,57,60,62,64,67,69,72,74,76,79,81,84]
}

# Default trios (root gage and upper gages)
default_trios = {
    'Raccoon River': {'root': '05484900', 'upper': ['05482300', '05483450']},
    'Upper Des Moines': {'root': '05482000', 'upper': ['05476750', '05479000']},
    'Lower Des Moines': {'root': '05490500', 'upper': ['05487470', '05488200']},
}

# MIDI Instruments (General MIDI program numbers)
midi_instruments = {
    0: 'Acoustic Grand Piano',
    1: 'Bright Acoustic Piano',
    2: 'Electric Grand Piano',
    3: 'Honky-tonk Piano',
    4: 'Electric Piano 1',
    5: 'Electric Piano 2',
    6: 'Harpsichord',
    7: 'Clavinet',
    8: 'Celesta',
    9: 'Glockenspiel',
    10: 'Music Box',
    11: 'Vibraphone',
    12: 'Marimba',
    13: 'Xylophone',
    14: 'Tubular Bells',
    15: 'Dulcimer',
    16: 'Drawbar Organ',
    17: 'Percussive Organ',
    18: 'Rock Organ',
    19: 'Church Organ',
    20: 'Reed Organ',
    21: 'Accordion',
    22: 'Harmonica',
    23: 'Tango Accordion',
    24: 'Acoustic Guitar (nylon)',
    25: 'Acoustic Guitar (steel)',
    26: 'Electric Guitar (jazz)',
    27: 'Electric Guitar (clean)',
    40: 'Violin',
    41: 'Viola',
    42: 'Cello',
    43: 'Contrabass',
    46: 'Orchestral Harp',
    47: 'Timpani',
    48: 'String Ensemble 1',
    49: 'String Ensemble 2',
    56: 'Trumpet',
    57: 'Trombone',
    58: 'Tuba',
    60: 'French Horn',
    64: 'Soprano Sax',
    65: 'Alto Sax',
    66: 'Tenor Sax',
    67: 'Baritone Sax',
    68: 'Oboe',
    69: 'English Horn',
    70: 'Bassoon',
    71: 'Clarinet',
    73: 'Flute',
    74: 'Recorder',
    75: 'Pan Flute',
    80: 'Lead 1 (square)',
    81: 'Lead 2 (sawtooth)',
    88: 'Pad 1 (new age)',
    89: 'Pad 2 (warm)',
    98: 'FX 3 (crystal)',
    99: 'FX 4 (atmosphere)',
}

# Helper functions from notebook
def freqMap(data, freq, log=True, inv=False, offset=0):
    if log:
        bins = np.linspace(np.log(data.min()), np.log(data.max()), len(freq)-1)
        digitized = np.digitize(np.log(data), bins)
    else:
        bins = np.linspace(data.min(), data.max(), len(freq)-1)
        digitized = np.digitize(data, bins)
    
    f = [freq[i] for i in digitized]
    return f

def make_track(note_list):
    track = [[note_list[0], 1]]
    for note in note_list[1:]:
        if note == track[-1][0]:
            track[-1][1] += 1
        else:
            track.append([note, 1])
    return track

# Function to create gauge map
def create_gauge_map(selected_gauges=None):
    """Create a map showing USGS gauge locations using OpenStreetMap"""
    if selected_gauges is None:
        selected_gauges = []
    
    # Prepare data for all valid gauges
    lats, lons, names, colors, sizes = [], [], [], [], []
    
    for gauge in valid_gauges:
        if gauge in gauge_locations:
            lat, lon, name = gauge_locations[gauge]
            lats.append(lat)
            lons.append(lon)
            names.append(f"{gauge}<br>{name}")
            
            # Color and size based on selection
            if gauge in selected_gauges:
                colors.append('#00D856')  # Green for selected
                sizes.append(15)
            else:
                colors.append('#1E90FF')  # Blue for unselected
                sizes.append(10)
    
    # Create OpenStreetMap using Scattermapbox
    fig = go.Figure(go.Scattermapbox(
        lon=lons,
        lat=lats,
        text=names,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=0.8
        ),
        hoverinfo='text',
    ))
    
    # Update layout for OpenStreetMap
    fig.update_layout(
        mapbox=dict(
            style='open-street-map',  # Use OpenStreetMap tiles
            center=dict(lat=41.5, lon=-93.5),
            zoom=7
        ),
        title='Des Moines River Basin USGS Gauges',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        autosize=True
    )
    
    return fig

# App layout
app.layout = html.Div([
    # Header with logo
    html.Div([
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Img(src='/assets/spotiflood-logo.svg', className='app-logo'),
                ], width=12, className='text-center'),
            ]),
            dbc.Row([
                dbc.Col([
                    html.H1("Stream Gauge Data Sonification", className="text-center"),
                    html.P("Transform streamflow data into music", className="text-center"),
                ], width=12),
            ]),
        ], fluid=True),
    ], className='app-header'),
    
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H4("1. Select Gauges"),
            
            # Default trios dropdown
            html.Label("Use Default Trio:"),
            dcc.Dropdown(
                id='default-trio-dropdown',
                options=[{'label': k, 'value': k} for k in default_trios.keys()],
                placeholder="Select a default trio (optional)",
                clearable=True
            ),
            
            html.Hr(),
            html.Label("Or select individual gauges:"),
            
            # Voice 1 (Root)
            html.Label("Voice 1 (Root Gage):"),
            dcc.Dropdown(
                id='gauge1-dropdown',
                options=[{'label': g, 'value': g} for g in valid_gauges],
                placeholder="Select gauge 1"
            ),
            
            # Voice 2
            html.Label("Voice 2:"),
            dcc.Dropdown(
                id='gauge2-dropdown',
                options=[{'label': g, 'value': g} for g in valid_gauges],
                placeholder="Select gauge 2"
            ),
            
            # Voice 3
            html.Label("Voice 3:"),
            dcc.Dropdown(
                id='gauge3-dropdown',
                options=[{'label': g, 'value': g} for g in valid_gauges],
                placeholder="Select gauge 3"
            ),
            
        ], width=6),
        
        dbc.Col([
            html.H4("Gauge Locations"),
            dcc.Graph(
                id='gauge-map',
                figure=create_gauge_map(),
                config={
                    'scrollZoom': True,
                    'displayModeBar': True,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                    'displaylogo': False
                },
                style={'height': '400px'}
            ),
        ], width=6),
    ], className="mb-4"),
    
    html.Hr(),
    
    dbc.Row([
        dbc.Col([
            html.H4("2. Select Time Period"),
            
            html.Label("Start Date:"),
            dcc.DatePickerSingle(
                id='start-date',
                min_date_allowed=datetime(2010, 10, 1),
                max_date_allowed=datetime(2020, 9, 30),
                initial_visible_month=datetime(2011, 10, 11),
                date=datetime(2011, 10, 11)
            ),
            
            html.Label("End Date:", className="mt-3"),
            dcc.DatePickerSingle(
                id='end-date',
                min_date_allowed=datetime(2010, 10, 1),
                max_date_allowed=datetime(2020, 9, 30),
                initial_visible_month=datetime(2019, 9, 30),
                date=datetime(2019, 9, 30)
            ),
            
        ], width=6),
    ], className="mb-4"),
    
    html.Hr(),
    
    html.H4("3. Tonal Mapping & Instruments", className="mb-3"),
    
    # Voice 1
    dbc.Row([
        dbc.Col([
            html.Label("Voice 1 Tonal Mapping:"),
            dcc.Dropdown(
                id='freq1-dropdown',
                options=[{'label': k, 'value': k} for k in freqDict.keys()],
                value='A Minor Pentatonic'
            ),
        ], width=6),
        
        dbc.Col([
            html.Label("Voice 1 Instrument:"),
            dcc.Dropdown(
                id='instrument1-dropdown',
                options=[{'label': f'{num}: {name}', 'value': num} for num, name in midi_instruments.items()],
                value=0,
                searchable=True
            ),
        ], width=6),
    ], className="mb-3"),
    
    # Voice 2
    dbc.Row([
        dbc.Col([
            html.Label("Voice 2 Tonal Mapping:"),
            dcc.Dropdown(
                id='freq2-dropdown',
                options=[{'label': k, 'value': k} for k in freqDict.keys()],
                value='C Major Pentatonic'
            ),
        ], width=6),
        
        dbc.Col([
            html.Label("Voice 2 Instrument:"),
            dcc.Dropdown(
                id='instrument2-dropdown',
                options=[{'label': f'{num}: {name}', 'value': num} for num, name in midi_instruments.items()],
                value=11,
                searchable=True
            ),
        ], width=6),
    ], className="mb-3"),
    
    # Voice 2 Inverted
    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Checkbox(
                    id='voice2-inverted',
                    value=True,
                    className="form-check-input me-2"
                ),
                html.Label("Voice 2 Inverted", className="form-check-label", style={'display': 'inline'}),
            ], className="d-flex align-items-center"),
        ], width=12),
    ], className="mb-3"),
    
    # Voice 3
    dbc.Row([
        dbc.Col([
            html.Label("Voice 3 Tonal Mapping:"),
            dcc.Dropdown(
                id='freq3-dropdown',
                options=[{'label': k, 'value': k} for k in freqDict.keys()],
                value='C Major Pentatonic'
            ),
        ], width=6),
        
        dbc.Col([
            html.Label("Voice 3 Instrument:"),
            dcc.Dropdown(
                id='instrument3-dropdown',
                options=[{'label': f'{num}: {name}', 'value': num} for num, name in midi_instruments.items()],
                value=12,
                searchable=True
            ),
        ], width=6),
    ], className="mb-3"),
    
    # Voice 3 Inverted
    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Checkbox(
                    id='voice3-inverted',
                    value=False,
                    className="form-check-input me-2"
                ),
                html.Label("Voice 3 Inverted", className="form-check-label", style={'display': 'inline'}),
            ], className="d-flex align-items-center"),
        ], width=12),
    ], className="mb-4"),
    
    html.Hr(),
    
    # Playback Settings
    dbc.Row([
        dbc.Col([
            html.H4("4. Playback Settings"),
            
            html.Label("Note Duration (seconds):"),
            dcc.Input(
                id='beat-length-input',
                type='number',
                value=0.2,
                min=0.05,
                max=2.0,
                step=0.05
            ),
            
        ], width=6),
    ], className="mb-4"),
    
    html.Hr(),
    
    dbc.Row([
        dbc.Col([
            dbc.Button("Generate MIDI", id="generate-btn", color="primary", size="lg", className="me-2"),
            dbc.Button("Download MIDI", id="download-btn", color="success", size="lg", disabled=True),
            dcc.Download(id="download-midi"),
        ], className="text-center mb-4"),
    ]),
    
    # Status message
    dbc.Row([
        dbc.Col([
            html.Div(id='status-message', className="text-center"),
        ]),
    ], className="mb-4"),
    
    # MIDI player controls (above graph)
    dbc.Row([
        dbc.Col([
            html.Div(id='midi-player'),
            html.Div(id='playback-status', className="text-center text-muted mt-2"),
        ], className="text-center"),
    ], className="mb-4"),
    
    # Visualization
    dbc.Row([
        dbc.Col([
            html.H4("Tonal Mapping Visualization"),
            dcc.Graph(
                id='visualization-graph',
                config={'responsive': False, 'displayModeBar': True},
                style={'height': '500px'}
            ),
        ]),
    ], className="mb-4"),
    
    # Hidden div to store MIDI data
    dcc.Store(id='midi-data-store'),
    
    ], fluid=True),  # Close Container
])  # Close outer Div


# Callback to update map when gauges are selected
@app.callback(
    Output('gauge-map', 'figure'),
    [Input('gauge1-dropdown', 'value'),
     Input('gauge2-dropdown', 'value'),
     Input('gauge3-dropdown', 'value')],
    prevent_initial_call=False
)
def update_map(gauge1, gauge2, gauge3):
    selected = [g for g in [gauge1, gauge2, gauge3] if g is not None]
    return create_gauge_map(selected)


# Callback to populate gauges from default trio selection
@app.callback(
    [Output('gauge1-dropdown', 'value'),
     Output('gauge2-dropdown', 'value'),
     Output('gauge3-dropdown', 'value')],
    Input('default-trio-dropdown', 'value'),
    prevent_initial_call=True
)
def update_from_trio(trio_name):
    if trio_name is None:
        return None, None, None
    
    trio = default_trios[trio_name]
    return trio['root'], trio['upper'][0], trio['upper'][1]


# Callback to generate MIDI
@app.callback(
    [Output('midi-data-store', 'data'),
     Output('status-message', 'children'),
     Output('download-btn', 'disabled'),
     Output('visualization-graph', 'figure')],
    Input('generate-btn', 'n_clicks'),
    [State('gauge1-dropdown', 'value'),
     State('gauge2-dropdown', 'value'),
     State('gauge3-dropdown', 'value'),
     State('start-date', 'date'),
     State('end-date', 'date'),
     State('freq1-dropdown', 'value'),
     State('freq2-dropdown', 'value'),
     State('freq3-dropdown', 'value'),
     State('instrument1-dropdown', 'value'),
     State('instrument2-dropdown', 'value'),
     State('instrument3-dropdown', 'value'),
     State('voice2-inverted', 'value'),
     State('voice3-inverted', 'value'),
     State('beat-length-input', 'value')],
    prevent_initial_call=True
)
def generate_midi(n_clicks, gauge1, gauge2, gauge3, start_date, end_date,
                  freq1_name, freq2_name, freq3_name, inst1, inst2, inst3,
                  voice2_inv, voice3_inv, beat_length):
    
    if not all([gauge1, gauge2, gauge3]):
        return None, dbc.Alert("Please select all three gauges!", color="warning"), True, {}
    
    try:
        # Get data for selected date range
        start = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        
        # Get frequency mappings
        freq1 = freqDict[freq1_name]
        freq2 = freqDict[freq2_name]
        freq3 = freqDict[freq3_name]
        
        # Invert if needed
        if voice2_inv:
            freq2 = freq2[::-1]
        if voice3_inv:
            freq3 = freq3[::-1]
        
        # Map flows to frequencies
        voice1_fm = freqMap(df[gauge1][start:end], freq1)
        voice2_fm = freqMap(df[gauge2][start:end].astype(np.float64), freq2)
        voice3_fm = freqMap(df[gauge3][start:end].astype(np.float64), freq3)
        
        # Create visualization
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=voice1_fm, mode='lines', name='Voice 1',
                                 line=dict(color='black', width=2)))
        fig.add_trace(go.Scatter(y=voice2_fm, mode='lines', name='Voice 2',
                                 line=dict(color='gray', width=1)))
        fig.add_trace(go.Scatter(y=voice3_fm, mode='lines', name='Voice 3',
                                 line=dict(color='lightgray', width=1)))
        fig.update_layout(
            title='Flow Data as MIDI Notes',
            xaxis_title='Days from beginning of selection',
            yaxis_title='Note Number',
            height=500,
            autosize=False,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        # Create MIDI file
        midi = pm.PrettyMIDI()
        instrument1 = pm.Instrument(program=inst1)
        instrument2 = pm.Instrument(program=inst2)
        instrument3 = pm.Instrument(program=inst3)
        
        # Create tracks
        for track, instrument in zip(
            [make_track(voice1_fm), make_track(voice2_fm), make_track(voice3_fm)],
            [instrument1, instrument2, instrument3]
        ):
            start_time = 0
            for note_info in track:
                end_time = start_time + beat_length * note_info[1]
                note = pm.Note(
                    velocity=100,
                    pitch=note_info[0],
                    start=start_time,
                    end=end_time
                )
                instrument.notes.append(note)
                start_time = end_time
        
        # Add instruments to MIDI
        midi.instruments.append(instrument1)
        midi.instruments.append(instrument2)
        midi.instruments.append(instrument3)
        
        # Save to bytes
        midi_io = io.BytesIO()
        midi.write(midi_io)
        midi_bytes = midi_io.getvalue()
        midi_b64 = base64.b64encode(midi_bytes).decode()
        
        success_msg = dbc.Alert(
            f"MIDI generated successfully! Duration: {len(voice1_fm)} days, "
            f"~{int(start_time)} seconds of audio.",
            color="success"
        )
        
        return midi_b64, success_msg, False, fig
        
    except Exception as e:
        error_msg = dbc.Alert(f"Error generating MIDI: {str(e)}", color="danger")
        return None, error_msg, True, {}


# Callback to download MIDI
@app.callback(
    Output('download-midi', 'data'),
    Input('download-btn', 'n_clicks'),
    State('midi-data-store', 'data'),
    State('gauge1-dropdown', 'value'),
    State('start-date', 'date'),
    State('end-date', 'date'),
    prevent_initial_call=True
)
def download_midi(n_clicks, midi_b64, gauge1, start_date, end_date):
    if midi_b64 is None:
        return None
    
    midi_bytes = base64.b64decode(midi_b64)
    
    # Generate filename
    start = pd.to_datetime(start_date).strftime('%Y%m%d')
    end = pd.to_datetime(end_date).strftime('%Y%m%d')
    filename = f"spotiflood_{gauge1}_{start}_{end}.mid"
    
    return dict(content=base64.b64encode(midi_bytes).decode(), filename=filename, base64=True)


# Callback to show MIDI player
@app.callback(
    Output('midi-player', 'children'),
    Input('midi-data-store', 'data'),
    prevent_initial_call=True
)
def show_midi_player(midi_b64):
    if midi_b64 is None:
        return None
    
    # Create a unique ID for this player instance
    player_id = f"midi-player-{hash(midi_b64) % 10000}"
    
    # Create player with embedded MIDI data
    return html.Div([
        html.H5("MIDI File Generated!", className="mb-3"),
        html.Div([
            dbc.Button("▶ Play", id="play-btn", color="success", size="lg", className="me-2"),
            dbc.Button("⏹ Stop", id="stop-btn", color="danger", size="lg"),
        ], className="text-center mb-3"),
        html.P("Use the controls above to play the MIDI in your browser, or download to use in your DAW.", 
               className="text-muted text-center"),
        # Hidden div to store MIDI data for JS
        html.Div(id='midi-data-for-player', **{'data-midi': midi_b64}, style={'display': 'none'})
    ])


# Clientside callback for play button
app.clientside_callback(
    """
    function(n_clicks, midi_b64) {
        if (!n_clicks || !midi_b64) {
            return "Ready to play";
        }
        
        // Stop any existing playback
        if (window.activeTimeout) {
            clearTimeout(window.activeTimeout);
        }
        if (window.scheduledNotes) {
            window.scheduledNotes.forEach(timeout => clearTimeout(timeout));
            window.scheduledNotes = [];
        }
        
        // Create audio context if needed
        if (!window.audioContext) {
            window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        // Decode base64 MIDI data
        const binaryString = atob(midi_b64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Parse MIDI file
        Midi.fromUrl(URL.createObjectURL(new Blob([bytes], {type: 'audio/midi'}))).then(midi => {
            window.scheduledNotes = [];
            const instruments = {};
            
            // GM instrument names mapping (simplified)
            const instrumentNames = {
                0: 'acoustic_grand_piano', 1: 'bright_acoustic_piano', 2: 'electric_grand_piano',
                3: 'honkytonk_piano', 4: 'electric_piano_1', 5: 'electric_piano_2',
                6: 'harpsichord', 7: 'clavinet', 8: 'celesta', 9: 'glockenspiel',
                10: 'music_box', 11: 'vibraphone', 12: 'marimba', 13: 'xylophone',
                14: 'tubular_bells', 15: 'dulcimer', 16: 'drawbar_organ', 17: 'percussive_organ',
                18: 'rock_organ', 19: 'church_organ', 20: 'reed_organ', 21: 'accordion',
                22: 'harmonica', 23: 'tango_accordion', 24: 'acoustic_guitar_nylon',
                25: 'acoustic_guitar_steel', 26: 'electric_guitar_jazz', 27: 'electric_guitar_clean',
                40: 'violin', 41: 'viola', 42: 'cello', 43: 'contrabass', 46: 'orchestral_harp',
                47: 'timpani', 48: 'string_ensemble_1', 49: 'string_ensemble_2',
                56: 'trumpet', 57: 'trombone', 58: 'tuba', 60: 'french_horn',
                64: 'soprano_sax', 65: 'alto_sax', 66: 'tenor_sax', 67: 'baritone_sax',
                68: 'oboe', 69: 'english_horn', 70: 'bassoon', 71: 'clarinet',
                73: 'flute', 74: 'recorder', 75: 'pan_flute', 80: 'lead_1_square',
                81: 'lead_2_sawtooth', 88: 'pad_1_new_age', 89: 'pad_2_warm',
                98: 'fx_3_crystal', 99: 'fx_4_atmosphere'
            };
            
            // Load instruments and schedule notes
            const loadPromises = midi.tracks.map((track, trackIndex) => {
                const program = track.instrument ? track.instrument.number : 0;
                const instrumentName = instrumentNames[program] || 'acoustic_grand_piano';
                
                return Soundfont.instrument(window.audioContext, instrumentName, {
                    soundfont: 'MusyngKite'
                }).then(instrument => {
                    instruments[trackIndex] = instrument;
                    
                    // Schedule all notes for this track
                    track.notes.forEach(note => {
                        const timeout = setTimeout(() => {
                            instrument.play(note.midi, window.audioContext.currentTime, {
                                duration: note.duration,
                                gain: note.velocity
                            });
                        }, note.time * 1000);
                        window.scheduledNotes.push(timeout);
                    });
                });
            });
            
            Promise.all(loadPromises).then(() => {
                // Auto-stop after MIDI duration
                window.activeTimeout = setTimeout(() => {
                    window.scheduledNotes = [];
                }, (midi.duration + 1) * 1000);
            });
        });
        
        return "Playing...";
    }
    """,
    Output('playback-status', 'children'),
    Input('play-btn', 'n_clicks'),
    State('midi-data-store', 'data'),
    prevent_initial_call=True
)


# Clientside callback for stop button
app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) {
            return "Ready to play";
        }
        
        // Clear all scheduled notes
        if (window.scheduledNotes) {
            window.scheduledNotes.forEach(timeout => clearTimeout(timeout));
            window.scheduledNotes = [];
        }
        
        // Clear auto-stop timeout
        if (window.activeTimeout) {
            clearTimeout(window.activeTimeout);
            window.activeTimeout = null;
        }
        
        return "Stopped";
    }
    """,
    Output('playback-status', 'children', allow_duplicate=True),
    Input('stop-btn', 'n_clicks'),
    prevent_initial_call=True
)


if __name__ == '__main__':
    app.run(debug=True, port=8050)
