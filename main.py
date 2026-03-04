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
    obs_time = tz_time.strftime("%I:%M %p %m/%d/%Y")

    # SPC provides outlooks for Day 1 through Day 8; fetch what we need based on forecast length
    outlook_days = min(len(weather_data["forecast"]["properties"]["periods"]) // 2, 8)
    spc_risks = {}
    for day_num in range(1, outlook_days + 1):
        if day_num > 1:
            time.sleep(1)
        spc_risks[day_num] = SPCRiskInArea(day_num)

    # Create the image
    img = create_image()

    generate_header(header_text)
    generate_footer(obs_time, datetime.now().strftime("%I:%M %p %m/%d/%Y"))

    d = ImageDraw.Draw(img)
    font_size = 20
    spacing = 10

    img.paste(Image.open("output/header.png"), (0, 0))
    img.paste(Image.open("output/footer.png"), (0, getCorrectedHeight()))

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

    day1Risk = spc_risks.get(1, "NONE")
    day2Risk = spc_risks.get(2, "NONE")

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

        x = img.size[0] - getTextSize(text[i])[0] - 10
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

def generate_seven_day_forecast(weather_data):
    periods = weather_data["forecast"]["properties"]["periods"]

    outlook_days = min(len(periods) // 2, 8)
    spc_risks = {}
    for day_num in range(1, outlook_days + 1):
        if day_num > 1:
            time.sleep(1)
        spc_risks[day_num] = SPCRiskInArea(day_num)

    def risk_to_percent(risk: str | None) -> str:
        mapping = {
            "TSTM": "<5%",
            "MRGL": "5%",
            "SLGT": "15%",
            "ENH": "30%",
            "MDT": "45%",
            "HIGH": "60%",
            "NONE": "0%",
        }
        if not risk:
            return "N/A"
        # Day 4-8 already returns a percentage string like "15%"
        if risk.endswith("%"):
            return risk
        risk_upper = risk.upper()
        return mapping.get(risk_upper, risk_upper)

    def risk_color(percent_str: str):
        """Return a fill color based on the risk percentage."""
        if percent_str == "N/A" or percent_str == "None":
            return (169, 169, 169)  # gray
        is_less_than = "<" in percent_str
        try:
            val = int(percent_str.replace("%", "").replace("<", ""))
        except ValueError:
            return text_color
        if val <= 0:
            return (169, 169, 169)       # gray  – NONE
        elif is_less_than or val < 5:
            return spc.get("TSTM", (194, 232, 194))
        elif val <= 5:
            return spc.get("MRGL", (131, 197, 131))
        elif val <= 15:
            return spc.get("SLGT", (246, 246, 138))
        elif val <= 30:
            return spc.get("ENH", (228, 194, 133))
        elif val <= 45:
            return spc.get("MDT", (226, 125, 129))
        else:
            return spc.get("HIGH", (253, 127, 251))

    def risk_name(percent_str: str) -> str:
        """Map a risk percentage to a categorical name."""
        if percent_str == "N/A" or percent_str == "None":
            return "None"
        is_less_than = "<" in percent_str
        try:
            val = int(percent_str.replace("%", "").replace("<", ""))
        except ValueError:
            return percent_str
        if val <= 0:
            return "None"
        elif is_less_than or val < 5:
            return "Thunderstorm"
        elif val <= 5:
            return "Marginal"
        elif val <= 15:
            return "Slight"
        elif val <= 30:
            return "Enhanced"
        elif val <= 45:
            return "Moderate"
        else:
            return "High"

    days = []
    for idx, period in enumerate(periods):
        if not period.get("isDaytime"):
            continue

        low_temp = None
        for follow in periods[idx + 1 :]:
            if not follow.get("isDaytime"):
                low_temp = follow.get("temperature")
                break

        day_label = period.get("name", "Day").split(" ")[0]
        if day_label == "This":
            day_label = "Today"

        days.append(
            {
                "label": day_label,
                "high": period.get("temperature"),
                "low": low_temp,
                "short": correctText(period.get("shortForecast", "")),
            }
        )

        if len(days) == 7:
            break

    if not days:
        print("No forecast data available to generate seven day forecast.")
        return

    # Add the severe risk value per SPC Day 1-8 where available
    for idx, day in enumerate(days):
        day_num = idx + 1
        if day_num in spc_risks:
            day["risk"] = risk_to_percent(spc_risks[day_num])
        else:
            day["risk"] = "N/A"
        day["risk_name"] = risk_name(day["risk"])

    columns = ["Day", "High", "Low", "Forecast", "Severe Risk", "Risk Level"]

    temp_img = Image.new("RGB", (10, 10))
    temp_draw = ImageDraw.Draw(temp_img)

    def text_width(text: str) -> int:
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        return int(bbox[2] - bbox[0])

    col_widths = [text_width(col) for col in columns]
    for day in days:
        col_widths[0] = max(col_widths[0], text_width(str(day["label"])))
        col_widths[1] = max(col_widths[1], text_width(f"{day['high']}°F"))
        low_text = f"{day['low']}°F" if day["low"] is not None else "N/A"
        col_widths[2] = max(col_widths[2], text_width(low_text))
        col_widths[3] = max(col_widths[3], text_width(day["short"]))
        col_widths[4] = max(col_widths[4], text_width(day["risk"]))
        col_widths[5] = max(col_widths[5], text_width(day["risk_name"]))

    padding_x = 10
    padding_y = spacing
    col_spacing = 15

    table_content_width = padding_x * 2 + col_spacing * (len(columns) - 1) + sum(col_widths)
    row_height = font_size + spacing
    title_row_height = row_height
    table_height = (len(days) + 1) * row_height  # +1 for column titles
    body_height = padding_y * 2 + title_row_height + table_height

    # Compute timestamps for footer
    utc_time = datetime.strptime(
        weather_data["current_weather"]["properties"]["timestamp"],
        "%Y-%m-%dT%H:%M:%S%z",
    )
    tz = pytz.timezone(timezone)
    tz_time = utc_time.astimezone(tz)
    obs_time = tz_time.strftime("%I:%M %p %m/%d/%Y")
    gen_time = datetime.now().strftime("%I:%M %p %m/%d/%Y")

    img_width = table_content_width
    img_height = header_height + body_height + header_height  # header + body + footer

    img = create_backgroundless_image((img_width, img_height))
    d = ImageDraw.Draw(img)

    # Draw header bar
    d.rectangle([(0, 0), (img_width, header_height)], fill=header_color)
    hdr_bbox = d.textbbox((0, 0), header_text, font=header_font)
    hdr_tw = hdr_bbox[2] - hdr_bbox[0]
    hdr_th = hdr_bbox[3] - hdr_bbox[1]
    d.text(((img_width - hdr_tw) // 2, (header_height - hdr_th) // 2), header_text, fill=text_color, font=header_font)

    # Draw footer bar
    footer_y = img_height - header_height
    footer_text = f"Current Conditions as of {obs_time} | Generated: {gen_time}"
    d.rectangle([(0, footer_y), (img_width, img_height)], fill=footer_color)
    ftr_bbox = d.textbbox((0, 0), footer_text, font=footer_font)
    ftr_tw = ftr_bbox[2] - ftr_bbox[0]
    ftr_th = ftr_bbox[3] - ftr_bbox[1]
    d.text(((img_width - ftr_tw) // 2, footer_y + (header_height - ftr_th) // 2), footer_text, fill="white", font=footer_font)

    y = header_height + padding_y
    d.text((padding_x, y), "Seven Day Forecast", fill=text_color, font=font)
    y += title_row_height

    x_positions = [padding_x]
    for width in col_widths[:-1]:
        x_positions.append(x_positions[-1] + width + col_spacing)

    # Column titles
    for idx, col in enumerate(columns):
        d.text((x_positions[idx], y), col, fill=text_color, font=font)
    y += row_height

    # Rows
    for day in days:
        low_text = f"{day['low']}°F" if day["low"] is not None else "N/A"
        values = [day["label"], f"{day['high']}°F", low_text, day["short"], day["risk"], day["risk_name"]]
        for idx, val in enumerate(values):
            fill = risk_color(day["risk"]) if idx in (4, 5) else text_color
            d.text((x_positions[idx], y), str(val), fill=fill, font=font)
        y += row_height

    img.save("output/seven_day_weather_forecast.png")


def SPCRiskInArea(day, _retry=True):
    try:
        if day <= 3:
            url = f"https://www.spc.noaa.gov/products/outlook/day{day}otlk_cat.lyr.geojson"
        else:
            # Day 4-8 probabilistic outlooks
            url = f"https://www.spc.noaa.gov/products/exper/day4-8/day{day}prob.nolyr.geojson"

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
        highest_prob = 0.0  # For Day 4-8 probabilistic data

        # Check each feature in the GeoJSON
        for feature in outlook_data.get("features", []):
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})

            risk_label = properties.get("LABEL", "").strip()

            # Day 4-8 uses probabilistic labels like "0.15" instead of categorical
            is_prob = False
            prob_value = 0.0
            try:
                prob_value = float(risk_label)
                is_prob = True
            except (ValueError, TypeError):
                pass

            if not is_prob and risk_label.upper() not in risk_levels:
                continue

            # Check if our coordinates are within this polygon
            in_area = False
            if geometry.get("type") == "Polygon":
                coordinates = geometry.get("coordinates", [[]])
                in_area = point_in_polygon(check_lat, check_lon, coordinates[0])
            elif geometry.get("type") == "MultiPolygon":
                for polygon in geometry.get("coordinates", []):
                    if point_in_polygon(check_lat, check_lon, polygon[0]):
                        in_area = True
                        break

            if in_area:
                if is_prob:
                    if prob_value > highest_prob:
                        highest_prob = prob_value
                        highest_risk = f"{int(prob_value * 100)}%"
                else:
                    cat = risk_label.upper()
                    if highest_risk is None or (
                        cat in risk_levels
                        and (highest_risk not in risk_levels or risk_levels.index(cat) > risk_levels.index(highest_risk))
                    ):
                        highest_risk = cat

        if highest_risk is None:
            print("Location not in any risk area")
            return "NONE"

        return highest_risk

    except requests.exceptions.RequestException as e:
        print(f"Error fetching SPC outlook data: {e}")
        if _retry:
            print(f"Retrying Day {day} in 1s...")
            time.sleep(1)
            return SPCRiskInArea(day, _retry=False)
        return "NONE"
    except Exception as e:
        print(f"Error processing SPC data: {e}")
        if _retry:
            print(f"Retrying Day {day} in 1s...")
            time.sleep(1)
            return SPCRiskInArea(day, _retry=False)
        return "NONE"


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
    generate_seven_day_forecast(weather_data)

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
            print("Updating image...")
            generate_weather_image(weather_data)
            generate_seven_day_forecast(weather_data)
            time.sleep(sleep_time)
        else:
            if attemps == 60:
                print("Forcing image to be generated again")
                attemps = 0
                generate_weather_image(weather_data)
                generate_seven_day_forecast(weather_data)

            else:
                print("No new update (observations were not released via api)")
                time.sleep(60)
                attemps += 1
