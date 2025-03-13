# UK Flood Monitoring Dashboard

A Streamlit-based dashboard that visualizes real-time flood monitoring data from the UK Environment Agency.

## Overview

This application provides an intuitive interface for accessing and visualizing water level and flow data from monitoring stations across the UK. Users can search and filter stations, view detailed station information, and analyze readings from the past 24 hours through interactive charts and data tables.

## Features

- **Station selection** with filtering by name, river, and status
- **Interactive visualization** of water level and flow readings
- **Data table view** with CSV export functionality
- **Station details** including location, river name, and operational status
- **Responsive design** for use on various devices

## Installation

### Prerequisites
- Python 3.7+

### Setup

1. Clone this repository or download the source code
2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv flood_env
   flood_env\Scripts\activate
   
   # macOS/Linux
   python -m venv flood_env
   source flood_env/bin/activate
   ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Ensure your virtual environment is activated
2. Run the Streamlit application:
   ```bash
   streamlit run flood_monitoring.py
   ```
3. The dashboard will open in your default web browser
4. Use the sidebar to search for and select a monitoring station
5. View the station's readings in the chart and data table

## Dependencies

- streamlit>=1.22.0
- pandas>=1.5.0
- requests>=2.28.0
- plotly>=5.13.0

## Data Source

This application uses Environment Agency flood and river level data from the real-time data API (Beta).

## Troubleshooting

- **No stations appear**: Check your internet connection. The application requires access to the Environment Agency API.
- **Chart shows no data**: Some stations may not have recent readings. Try selecting a different station.
- **Application crashes on startup**: Ensure all dependencies are correctly installed.

---

Created for educational and environmental monitoring purposes.