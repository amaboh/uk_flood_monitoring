import streamlit as st
import pandas as pd
import requests
import datetime
import plotly.express as px
import time

# Set page configuration
st.set_page_config(
    page_title="UK Flood Monitoring Dashboard",
    page_icon="🌊",
    layout="wide"
)

# Constants
API_BASE_URL = "https://environment.data.gov.uk/flood-monitoring"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# App title and description
st.title("UK Flood Monitoring Dashboard")
st.markdown("""
This dashboard provides real-time flood monitoring data from the UK Environment Agency.
Select a measurement station to view water level or flow readings over the last 24 hours.
""")

# Cache the stations data to avoid frequent API calls
@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_stations():
    """
    Fetch all measurement stations from the API
    
    Returns:
        pandas.DataFrame: DataFrame containing station information
    """
    try:
        response = requests.get(f"{API_BASE_URL}/id/stations", params={"_limit": 5000})
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant station data
        stations = []
        for item in data.get("items", []):
            # Only include stations with valid labels and references
            if "label" in item and "stationReference" in item:
                # Extract status from URI format if needed
                status = item.get("status", "Unknown")
                if isinstance(status, str) and "#" in status:
                    status = status.split("#")[-1]
                
                station_info = {
                    "id": item.get("stationReference", ""),
                    "label": item.get("label", ""),
                    "river": item.get("riverName", "Unknown"),
                    "town": item.get("town", "Unknown"),
                    "catchment": item.get("catchmentName", "Unknown"),
                    "lat": item.get("lat", None),
                    "long": item.get("long", None),
                    "status": status,
                    "measures": len(item.get("measures", []))
                }
                stations.append(station_info)
        
        # Create DataFrame and sort by station label
        df = pd.DataFrame(stations)
        return df.sort_values("label")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching stations: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_station_readings(station_id):
    """
    Fetch readings for a specific station over the last 24 hours
    
    Args:
        station_id (str): The station reference ID
        
    Returns:
        pandas.DataFrame: DataFrame containing station readings
    """
    # Calculate timestamp for 24 hours ago
    since_time = (datetime.datetime.now() - datetime.timedelta(hours=24)).isoformat()
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/id/stations/{station_id}/readings",
            params={"since": since_time, "_sorted": True}
        )
        response.raise_for_status()
        data = response.json()
        
        # Process the readings
        readings = []
        for item in data.get("items", []):
            # Extract measure information
            measure = item.get("measure", {})
            measure_id = ""
            if isinstance(measure, dict) and "@id" in measure:
                measure_id = measure.get("@id", "").split("/")[-1]
            
            reading = {
                "dateTime": item.get("dateTime", ""),
                "value": item.get("value", None),
                "parameter": measure.get("parameter", "Unknown") if isinstance(measure, dict) else "Unknown",
                "qualifier": measure.get("qualifier", "") if isinstance(measure, dict) else "",
                "unit": measure.get("unitName", "") if isinstance(measure, dict) else "",
                "measure_id": measure_id
            }
            readings.append(reading)
        
        df = pd.DataFrame(readings)
        
        # Convert datetime to pandas datetime format
        if not df.empty and "dateTime" in df.columns:
            df["dateTime"] = pd.to_datetime(df["dateTime"])
            
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching readings: {str(e)}")
        return pd.DataFrame()

# Main application
def main():
    # Load stations with a progress bar
    with st.spinner("Loading measurement stations..."):
        stations_df = fetch_stations()

    # If stations were successfully loaded
    if not stations_df.empty:
        st.success(f"Loaded {len(stations_df)} measurement stations")
        
        # Create a sidebar for station filtering and selection
        with st.sidebar:
            st.header("Station Selection")
            
            # Filter options
            st.subheader("Filter Stations")
            
            # Search by name
            search_query = st.text_input("Search by station name")
            
            # Filter by river
            rivers = stations_df["river"].dropna().unique()
            rivers = [r for r in rivers if r != "Unknown" and r != ""]
            all_rivers = sorted(["All Rivers"] + list(rivers))
            selected_river = st.selectbox("Filter by river", all_rivers)
            
            # Filter by status
            statuses = stations_df["status"].dropna().unique()
            statuses = [s for s in statuses if s != "Unknown"]
            all_statuses = ["All Statuses"] + list(statuses)
            selected_status = st.selectbox("Filter by status", all_statuses)
            
            # Apply filters
            filtered_df = stations_df.copy()
            
            if search_query:
                filtered_df = filtered_df[filtered_df["label"].str.contains(search_query, case=False, na=False)]
            
            if selected_river != "All Rivers":
                filtered_df = filtered_df[filtered_df["river"] == selected_river]
                
            if selected_status != "All Statuses":
                filtered_df = filtered_df[filtered_df["status"] == selected_status]
            
            # Show number of stations after filtering
            st.info(f"Showing {len(filtered_df)} stations")
            
            # If we have filtered stations, show them in a selectbox
            if not filtered_df.empty:
                station_options = [f"{row['label']} ({row['id']})" for _, row in filtered_df.iterrows()]
                selected_station_str = st.selectbox("Select a station", station_options)
                
                # Extract station ID from selected option
                selected_station_id = selected_station_str.split("(")[-1].strip(")")
                
                # Get the full details of the selected station
                selected_station = filtered_df[filtered_df["id"] == selected_station_id].iloc[0]
                
                # Display station details
                st.subheader("Station Details")
                st.write(f"**ID:** {selected_station['id']}")
                st.write(f"**River:** {selected_station['river']}")
                if selected_station['town'] != "Unknown":
                    st.write(f"**Town:** {selected_station['town']}")
                if selected_station['catchment'] != "Unknown":
                    st.write(f"**Catchment:** {selected_station['catchment']}")
                if selected_station['status'] != "Unknown":
                    status_color = "green" if selected_station['status'] == "Active" else "red"
                    st.write(f"**Status:** :{status_color}[{selected_station['status']}]")
                if selected_station['lat'] and selected_station['long']:
                    st.write(f"**Location:** {selected_station['lat']:.4f}, {selected_station['long']:.4f}")
                    st.write(f"[View on Map](https://www.google.com/maps/search/?api=1&query={selected_station['lat']},{selected_station['long']})")
                st.write(f"**Available Measures:** {selected_station['measures']}")
            else:
                st.warning("No stations match your filters. Please adjust your search criteria.")
                selected_station_id = None
        
        # Main area - display readings if a station is selected
        if 'selected_station_id' in locals() and selected_station_id:
            st.header(f"Readings for {selected_station['label']}")
            
            # Fetch and display the readings
            with st.spinner("Fetching station readings..."):
                readings_df = fetch_station_readings(selected_station_id)
            
            if not readings_df.empty:
                # Display a summary of the data
                st.write(f"Showing data from {readings_df['dateTime'].min().strftime(DATE_FORMAT)} to {readings_df['dateTime'].max().strftime(DATE_FORMAT)}")
                st.write(f"Total readings: {len(readings_df)}")
                
                # Group by parameter for multiple measures
                parameters = readings_df["parameter"].unique()
                
                # If there are multiple parameters, add a selector
                if len(parameters) > 1:
                    selected_param = st.selectbox("Select measurement type", parameters)
                    measure_df = readings_df[readings_df["parameter"] == selected_param]
                else:
                    # Just use the only parameter
                    selected_param = parameters[0]
                    measure_df = readings_df
                
                if not measure_df.empty:
                    # Get the qualifier and unit for this measure
                    qualifiers = measure_df["qualifier"].unique()
                    qualifier_str = ", ".join([q for q in qualifiers if q]) if len(qualifiers) > 0 and qualifiers[0] else "Standard"
                    unit = measure_df["unit"].iloc[0] if "unit" in measure_df.columns and not measure_df["unit"].iloc[0] == "" else "Units unknown"
                    
                    # Create column names for the chart
                    y_axis_title = f"{selected_param.capitalize()} ({unit})"
                    
                    # Create tabs for visualization and data
                    tab1, tab2 = st.tabs(["📈 Chart", "🔢 Data Table"])
                    
                    with tab1:
                        # Create plot
                        fig = px.line(
                            measure_df,
                            x="dateTime",
                            y="value",
                            title=f"{selected_param.capitalize()} - {qualifier_str} ({unit})"
                        )
                        
                        fig.update_layout(
                            xaxis_title="Time",
                            yaxis_title=y_axis_title,
                            hovermode="x unified",
                            height=500
                        )
                        
                        # Add range slider to the plot
                        fig.update_xaxes(rangeslider_visible=True)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add some statistics
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Latest Value", f"{measure_df['value'].iloc[0]:.2f} {unit}")
                        with col2:
                            st.metric("Average", f"{measure_df['value'].mean():.2f} {unit}")
                        with col3:
                            st.metric("Min", f"{measure_df['value'].min():.2f} {unit}")
                        with col4:
                            st.metric("Max", f"{measure_df['value'].max():.2f} {unit}")
                    
                    with tab2:
                        # Create a more readable table
                        table_df = measure_df[["dateTime", "value"]].copy()
                        table_df.columns = ["Date & Time", f"Value ({unit})"]
                        table_df = table_df.sort_values("Date & Time", ascending=False)
                        
                        # Add download button
                        csv = table_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "Download Data as CSV",
                            csv,
                            f"{selected_station_id}_{selected_param}_readings.csv",
                            "text/csv",
                            key=f"download_{selected_param}"
                        )
                        
                        # Show the table
                        st.dataframe(table_df, use_container_width=True)
                        
                else:
                    st.warning(f"No {selected_param} readings available for this station in the last 24 hours.")
            else:
                st.warning("No readings available for this station in the last 24 hours.")
    else:
        st.error("Failed to load stations data. Please try again later.")

    # Footer
    st.markdown("---")
    st.markdown("""
    **Data Source:** Environment Agency Real Time flood-monitoring API  
    This application uses Environment Agency flood and river level data from the real-time data API (Beta)
    """)
    
    # Add last updated time
    st.text(f"Last updated: {datetime.datetime.now().strftime(DATE_FORMAT)}")

# Run the main application
if __name__ == "__main__":
    main()