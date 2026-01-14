import requests
from datetime import datetime, timedelta
import time
from PIL import Image, ImageDraw
import pytz
import os
import json
from config import *
from extra import *

attemps = 0

from generate_header import generate_header
from generate_footer import generate_footer

cords = (lat, lon)

data = readStorage()

# Function to fetch weather data
def fetch_weather_data():
    # Fetch weather data from weather.gov
    temp_data = readStorage()

    weather_data = None
    forecast_url = None
    forecast_data = None
    max_retries = 1
    retry_delay = 10  # seconds

    if (
        temp_data is not None
        and objectHasKey(data, "high_temp")
        and objectHasKey(data, "high_temp")
        and temp_data["cords"] == [lat, lon]
    ):
        forecast_url = temp_data["forecast_url"]

    if forecast_url is None:
        # Initial request to get forecast URL
        for attempt in range(max_retries):
            try:
                weather_url = f"https://api.weather.gov/points/{lat},{lon}/"
                weather_response = requests.get(weather_url, timeout=10)

                # Check if the response was successful
                weather_response.raise_for_status()

                weather_data = weather_response.json()
                forecast_url = weather_data["properties"]["forecast"]
                addToStorage({"forecast_url": forecast_url, "cords": [lat, lon]})
                break
            except requests.exceptions.RequestException as e:
                print(
                    f"Error fetching weather data (attempt {attempt+1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Failed to fetch weather data after multiple attempts.")
                    if temp_data is not None and objectHasKey(
                        temp_data, "forecast_url"
                    ):
                        print("Using previously cached forecast URL")
                        forecast_url = temp_data["forecast_url"]
                    else:
                        raise Exception(
                            "Could not get forecast URL and no cached data available"
                        )

    # Get forecast data
    try:
        forecast_response = requests.get(forecast_url, timeout=10)  # type: ignore
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching forecast data: {e}")
        # Try to use cached data if available
        if os.path.exists("output/weather_data.json"):
            print("Using cached weather data")
            with open("output/weather_data.json", "r") as json_file:
                cached_data = json.load(json_file)
                forecast_data = cached_data["forecast"]
        else:
            raise Exception("Could not get forecast data and no cached data available")

    # Convert forecast temperatures to Fahrenheit if necessary
    if forecast_data:
        for period in forecast_data["properties"]["periods"]:
            if period["temperatureUnit"] == "C":
                period["temperature"] = celsius_to_fahrenheit(period["temperature"])
                period["temperatureUnit"] = "F"

    # Get current weather observations
    try:
        current_weather = requests.get(
            f"https://api.weather.gov/stations/{wx_obs_station}/observations/latest",
            timeout=10,
        )
        current_weather.raise_for_status()
        current_weather_data = current_weather.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching current weather data: {e}")
        # Try to use cached data if available
        if os.path.exists("output/weather_data.json"):
            print("Using cached current weather data")
            with open("output/weather_data.json", "r") as json_file:
                cached_data = json.load(json_file)
                current_weather_data = cached_data["current_weather"]
        else:
            raise Exception(
                "Could not get current weather data and no cached data available"
            )

    # Convert current temperature to Fahrenheit if necessary
    for key, value in current_weather_data["properties"].items():
        if (
            isinstance(value, dict)
            and "unitCode" in value
            and value["unitCode"] == "wmoUnit:degC"
            and value["value"] is not None
        ):
            value["value"] = celsius_to_fahrenheit(value["value"])
            value["unitCode"] = "wmoUnit:degF"
        if (
            isinstance(value, dict)
            and "unitCode" in value
            and value["unitCode"] == "wmoUnit:km_h-1"
            and value["value"] is not None
        ):
            value["value"] = round(value["value"] * 0.621371)
            value["unitCode"] = "wmoUnit:mph"

    json_data = {"forecast": forecast_data, "current_weather": current_weather_data}
    return json_data


# Function to generate PNG image
def generate_weather_image(weather_data):
    forecast_day = weather_data["forecast"]["properties"]["periods"][0]
    forecast_night = weather_data["forecast"]["properties"]["periods"][1]
    forecast_day2 = weather_data["forecast"]["properties"]["periods"][2]
    forecast_night2 = weather_data["forecast"]["properties"]["periods"][3]

    high_temp = forecast_day["temperature"]
    low_temp = forecast_night["temperature"]
    current_temp = weather_data["current_weather"]["properties"]["temperature"]["value"]

    print(f"High: {high_temp}°F, Low: {low_temp}°F, Current: {current_temp}°F")

    utc_time = datetime.strptime(
        weather_data["current_weather"]["properties"]["timestamp"],
        "%Y-%m-%dT%H:%M:%S%z",
    )
    tz = pytz.timezone(timezone)
    tz_time = utc_time.astimezone(tz)
    time = tz_time.strftime("%I:%M %p %m/%d/%Y")

    day1Risk = SPCRiskInArea(1)
    day2Risk = SPCRiskInArea(2)

    # Gets the background image
    background = Image.open(file)

    if background.size[0] > max_width:
        raise Exception(
            "Image is too wide. Please use an image with a width of "
            + str(max_width)
            + "px or less.\n"
            + "Current width: "
            + str(background.size[0])
            + "px"
        )

    size = (
        int(background.size[0] * width_multiplier),
        background.size[1] + 2 * header_height,
    )

    # Create an image with PIL
    img = Image.new("RGB", size, color=background_color)

    width = img.size[0]
    height = img.size[1]

    if center_image:
        img.paste(
            background, ((width - background.size[0]) // 2, header_height), background
        )
    else:
        img.paste(background, (0, header_height), background)

    generate_header(header_text)
    generate_footer(time, datetime.now().strftime("%I:%M %p %m/%d/%Y"))

    d = ImageDraw.Draw(img)
    font_size = 20
    spacing = 10

    img.paste(Image.open("output/header.png"), (0, 0))
    img.paste(Image.open("output/footer.png"), (0, height - header_height))

    s = header_height + 10

    image_title = "Today's Forecast"

    last_updated = datetime.strptime(
        weather_data["current_weather"]["properties"]["timestamp"],
        "%Y-%m-%dT%H:%M:%S%z",
    )

    next_update = last_updated + timedelta(hours=2)
    sleep_time = (next_update - datetime.now(pytz.utc)).total_seconds()

    # Check if high is less than or equal to low
    # If high < low, then it's image_night
    # so we must shift the forecast data
    original_high_temp = high_temp  # Save original before modification
    original_forecast_day = forecast_day  # Save original forecast day

    if high_temp <= low_temp:
        image_title = image_night
        forecast_day = {"temperature": -1, "shortForecast": "N/A"}
        forecast_night = weather_data["forecast"]["properties"]["periods"][0]
        forecast_day2 = weather_data["forecast"]["properties"]["periods"][1]
        forecast_night2 = weather_data["forecast"]["properties"]["periods"][2]
        high_temp = forecast_day["temperature"]
        low_temp = forecast_night["temperature"]

    wind_gusts = f"Wind Gust: {weather_data['current_weather']['properties']['windGust']['value']} mph"
    if weather_data["current_weather"]["properties"]["windGust"]["value"] is None:
        wind_gusts = "Wind Gust: N/A"

    feels_like = weather_data["current_weather"]["properties"]["heatIndex"]["value"]
    if feels_like is None:
        feels_like = weather_data["current_weather"]["properties"]["windChill"]["value"]

    if feels_like is None:
        feels_like = "Missing"

    # Handle long wording to fit onto the frame
    # if forecast_day["shortForecast"] == "Slight Chance Showers And Thunderstorms":
    #     forecast_day["shortForecast"] = "Slight Chance of Thunderstorms"
    # if len(forecast_day["shortForecast"]) > 26:
    #     forecast_day["shortForecast"] = (forecast_day["shortForecast"].split("then"))[0]

    forecast_day["shortForecast"] = correctText(forecast_day["shortForecast"])
    forecast_day2["shortForecast"] = correctText(forecast_day2["shortForecast"])

    print(len(forecast_day["shortForecast"]))

    text = [
        image_title,
        f"{forecast_day['shortForecast']}",
        f"High: {high_temp}°F",
        f"Low: {low_temp}°F",
        None,
        "Severe Risk",
        day1Risk,
        #"MDT",
        None,
        f"Observed Stats",
        f"{weather_data['current_weather']['properties']['textDescription']}",
        f"Temperature: {current_temp}°F",
        f"Feels Like: {feels_like}°F",
        f"Wind: {weather_data['current_weather']['properties']['windSpeed']['value']} mph",
        wind_gusts
    ]

    if sleep_time < 0:
        text.append(f"Outdated")

    for i in range(len(text)):
        if text[i] == "High: -1°F":
            if objectHasKey(data, "high_temp"):
                text[i] = f"High: {data['high_temp']}°F"
            else:
                text[i] = f"High: [Missing]"
        if text[i] == "N/A":
            if objectHasKey(data, "high_temp"):
                text[i] = data["shortForecast"]
            else:
                text[i] = "[Missing]"
        if text[i] == "Currently ":
            text[i] = "Currently Clear(?)"
        if text[i] == "Feels Like: Missing°F":
            text[i] = f"Feels Like: {current_temp}°F"

    for i in range(len(text)):
        fill_color = text_color
        if text[i] == "" or text[i] == None:
            continue

        if i > 0:
            if text[i].upper() in spc.keys():
                fill_color = spc[text[i].upper()]
                match text[i].upper():
                    case "TSTM":
                        text[i] = "Thunderstorm (<5%)"
                    case "MRGL":
                        text[i] = "Marginal (5%)"
                    case "SLGT":
                        text[i] = "Slight (15%)"
                    case "ENH":
                        text[i] = "Enhanced (30%)"
                    case "MDT":
                        text[i] = "Moderate (45%)"
                    case "HIGH":
                        text[i] = "High (60%)"
                    case "NONE":
                        text[i] = "None"
        y = s + (i) * font_size + spacing

        if i == 0:
            y = s

        if "outdated" in text[i].lower():
            fill_color = "red"

        d.text((10, y), text[i], fill=fill_color, font=font)

    text = [
        f"Tomorrow's Forecast",
        f"{forecast_day2['shortForecast']}",
        f"High: {forecast_day2['temperature']}°F",
        f"Low: {forecast_night2['temperature']}°F",
        None,
        "Severe Risk",
        day2Risk,
    ]

    for i in range(len(text)):
        fill_color = text_color
        if text[i] == "" or text[i] == None:
            continue

        if i > 0:
            if text[i].upper() in spc.keys():
                fill_color = spc[text[i].upper()]
                match text[i].upper():
                    case "TSTM":
                        text[i] = "Thunderstorm Risk (<5%)"
                    case "MRGL":
                        text[i] = "Marginal Risk (5%)"
                    case "SLGT":
                        text[i] = "Slight Risk (15%)"
                    case "ENH":
                        text[i] = "Enhanced Risk (30%)"
                    case "MDT":
                        text[i] = "Moderate Risk (45%)"
                    case "HIGH":
                        text[i] = "High Risk (60%)"
                    case "NONE":
                        text[i] = "None"

        x = width - getTextSize(text[i])[0] - 10
        y = s + (i) * font_size + spacing

        if i == 0:
            y = s

        d.text((x, y), text[i], fill=fill_color, font=font)

    if not loop:
        try:
            print(
                "Present Weather:"
                + ", ".join(
                    weather_data["current_weather"]["properties"]["presentWeather"]
                )
            )
            img.show()
        except:
            """"""

    if image_title != image_night:
        addToStorage(
            {
                "high_temp": original_high_temp,
                "shortForecast": original_forecast_day["shortForecast"],
            }
        )

    img.save("output/weather_forecast.png")


def SPCRiskInArea(day):
    try:
        url = f"https://www.spc.noaa.gov/products/outlook/day{day}otlk_cat.lyr.geojson"
        # https://www.spc.noaa.gov/products/outlook/day1otlk_cat.lyr.geojson
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        outlook_data = response.json()

        # Use cords variable and ensure numeric values
        check_lat = float(cords[0])
        check_lon = float(cords[1])
        
        print(f"Checking location: {check_lat}, {check_lon}")

        # Risk categories in order of severity (lowest to highest)
        risk_levels = ["TSTM", "MRGL", "SLGT", "ENH", "MDT", "HIGH"]
        highest_risk = None

        # Check each feature in the GeoJSON
        for feature in outlook_data.get("features", []):
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})

            risk_label = properties.get("LABEL", "").upper()

            if risk_label not in risk_levels:
                continue

            # Check if our coordinates are within this polygon
            if geometry.get("type") == "Polygon":
                coordinates = geometry.get("coordinates", [[]])
                if point_in_polygon(check_lat, check_lon, coordinates[0]):
                    if highest_risk is None or risk_levels.index(
                        risk_label
                    ) > risk_levels.index(highest_risk):
                        highest_risk = risk_label
            elif geometry.get("type") == "MultiPolygon":
                for polygon in geometry.get("coordinates", []):
                    if point_in_polygon(check_lat, check_lon, polygon[0]):
                        if highest_risk is None or risk_levels.index(
                            risk_label
                        ) > risk_levels.index(highest_risk):
                            highest_risk = risk_label
                        break

        if highest_risk is None:
            print("Location not in any risk area")
            return "None"
        
        return highest_risk

    except requests.exceptions.RequestException as e:
        print(f"Error fetching SPC outlook data: {e}")
        return "None"
    except Exception as e:
        print(f"Error processing SPC data: {e}")
        return "None"


def point_in_polygon(lat, lon, polygon) -> bool:
    inside = False
    n = len(polygon)

    # Convert lat/lon to float for comparison
    x, y = float(lon), float(lat)

    for i in range(n):
        j = (i + 1) % n
        xi, yi = polygon[i][0], polygon[i][1]
        xj, yj = polygon[j][0], polygon[j][1]

        # Check if point is on an edge (ray casting algorithm)
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside

    return inside


if __name__ == "__main__":
    # Always run once
    weather_data = fetch_weather_data()

    # Write weather_data to a file
    with open("output/weather_data.json", "w") as json_file:
        json.dump(weather_data, json_file, indent=4)

    generate_weather_image(weather_data)

    print("Image generated")
    print(
        "Latest Observation: https://api.weather.gov/stations/"
        + wx_obs_station
        + "/observations/latest"
    )
    print("Forecast: https://api.weather.gov/points/" + lat + "," + lon)

    last_updated = datetime.strptime(
        weather_data["current_weather"]["properties"]["timestamp"],
        "%Y-%m-%dT%H:%M:%S%z",
    )

    print(
        "Latest Observation Timestamp:", last_updated.strftime("%Y-%m-%d %H:%M:%S %Z")
    )

    next_update = last_updated + timedelta(hours=1)
    sleep_time = (next_update - datetime.now(pytz.utc)).total_seconds()

    if sleep_time < -(60 * 60 * 24):
        print("Observations are out of date by at least a whole day...")

    if not loop:
        exit()

    if sleep_time < 0:
        sleep_time = 60
    time.sleep(sleep_time)

    while True:
        weather_data = fetch_weather_data()
        last_updated = datetime.strptime(
            weather_data["current_weather"]["properties"]["timestamp"],
            "%Y-%m-%dT%H:%M:%S%z",
        )
        next_update = last_updated + timedelta(hours=1)
        sleep_time = (next_update - datetime.now(pytz.utc)).total_seconds()
        if sleep_time > 0:
            print("Releasing new image (it finally updated)...")
            generate_weather_image(weather_data)
            time.sleep(sleep_time)
        else:
            if attemps == 60:
                print("Forcing image to be generated again")
                attemps = 0
                generate_weather_image(weather_data)
            else:
                print("No new update (observations were not released via api)")
                time.sleep(60)
                attemps += 1
