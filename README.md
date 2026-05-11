                                     Weather Tracking Dashboard

A Python application that fetches real-time weather data from OpenWeatherMap API and displays it with history storage, analysis graphs, and multi-city tracking.

Features

Current Weather Tab
- Search weather by city name
- Display temperature, humidity, wind speed, pressure, feels like temperature
- Auto-refresh every 30 seconds (optional)
- Real-time data from OpenWeatherMap API

History Tab
- View all past weather searches
- Filter history by city name
- Export history to CSV file
- Clear history option
- Timestamp for each record

Analysis Tab
- View temperature, humidity, or wind speed trends
- Select specific city or view all cities combined
- Display average, minimum, maximum values
- Line graph with time-based trends
- Statistics cards for quick insights

Multi-City Tab
- Track up to 6 cities simultaneously
- Fetch weather for all cities at once
- Compare weather conditions side by side

Requirements

- Python 3.7 or higher
- customtkinter
- requests
- matplotlib

Installation

Install the required libraries:

pip install customtkinter requests matplotlib

API Key Setup

1. Go to https://openweathermap.org/api
2. Create a free account
3. Verify your email
4. Copy your API key from the dashboard

How to Run

python weather.py

API Key Configuration

Open the code file and replace the API key:

API_KEY = "your_api_key_here"

