# Spotiflood Dash App

A web application for creating musical sonifications from stream gauge data.

## Features

- **Gauge Selection**: Choose three USGS stream gauges from the Des Moines River Basin, or select from predefined trios
- **Time Period Selection**: Pick a date range (2010-2020) for the streamflow data
- **Tonal Mapping**: Assign different musical scales to each voice (gauge)
  - A Minor Pentatonic
  - C Major Pentatonic
  - C Major Diatonic
  - Chromatic
  - Arab Double Harmonic
- **Visualization**: See how your flow data maps to musical notes
- **MIDI Generation**: Create MIDI files from your selected parameters
- **Download**: Save generated MIDI files to use in your DAW or music player

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the app:
```bash
python app.py
```

2. Open your browser to: `http://localhost:8050`

3. Follow the workflow:
   - Select three gauges (or use a default trio)
   - Choose your time period
   - Select tonal mappings for each voice
   - Adjust note duration if desired
   - Click "Generate MIDI"
   - View the visualization
   - Download your MIDI file

## Default Trios

The app includes three predefined gauge combinations:

- **Raccoon River**: Root gauge 05484900 with upper gauges 05482300, 05483450
- **Upper Des Moines**: Root gauge 05482000 with upper gauges 05476750, 05479000
- **Lower Des Moines**: Root gauge 05490500 with upper gauges 05487470, 05488200

## Technical Details

- Each day of streamflow data is mapped to a musical note based on the selected scale
- Higher flows typically map to higher notes (can be inverted for voice 2 and 3)
- Note duration is adjustable (default: 0.2 seconds per day)
- Three voices create harmony from different gauges in the watershed
