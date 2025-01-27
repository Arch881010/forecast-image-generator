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


# Function to convert Celsius to Fahrenheit
def celsius_to_fahrenheit(celsius):
    return round((celsius * 9 / 5) + 32)


# Function to fetch weather data
def fetch_weather_data():
    # Fetch weather data from weather.gov
    temp_data = readStorage()

    weather_data = None
    forecast_url = None
    forecast_data = None

    if (
        temp_data is not None
        and objectHasKey(data, "high_temp")
        and objectHasKey(data, "high_temp")
        and temp_data["cords"] == [lat, lon]
    ):
        forecast_url = temp_data["forecast_url"]

    if forecast_url is None:
        weather_url = f"https://api.weather.gov/points/{lat},{lon}/"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()
        forecast_url = weather_data["properties"]["forecast"]
        addToStorage({"forecast_url": forecast_url, "cords": [lat, lon]})

    forecast_response = requests.get(forecast_url)
    forecast_data = forecast_response.json()

    # Convert forecast temperatures to Fahrenheit if necessary
    for period in forecast_data["properties"]["periods"]:
        if period["temperatureUnit"] == "C":
            period["temperature"] = celsius_to_fahrenheit(period["temperature"])
            period["temperatureUnit"] = "F"

    current_weather = requests.get(
        f"https://api.weather.gov/stations/{wx_obs_station}/observations/latest"
    )
    current_weather_data = current_weather.json()

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

    json = {"forecast": forecast_data, "current_weather": current_weather_data}

    return json


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
    font_path = os.path.join(os.path.dirname(__file__), "arial.ttf")
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
    # If high < low, then it's tonight's forecast
    # so we must shift the forecast data
    if high_temp <= low_temp:
        image_title = "Tonight's Forecast"
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

    text = [
        "Today's Forecast",
        f"{forecast_day['shortForecast']}",
        f"High: {high_temp}°F",
        f"Low: {low_temp}°F",
        None,
        f"Observed Stats",
        f"Currently {weather_data['current_weather']['properties']['textDescription']}",
        f"Temperature: {current_temp}°F",
        f"Feels Like: {feels_like}°F",
        f"Wind: {weather_data['current_weather']['properties']['windSpeed']['value']} mph",
        wind_gusts,
    ]

    if sleep_time < 0 or debug:
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
            text[i] = "Currently [Missing]"

    for i in range(len(text)):
        fill_color = text_color
        if text[i] == "" or text[i] == None:
            continue
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
        f"Severe Potential",
        f"WIP",
    ]

    for i in range(len(text)):
        if text[i] == "" or text[i] == None:
            continue
        x = width - getTextSize(text[i])[0] - 10
        y = s + (i) * font_size + spacing

        if i == 0:
            y = s

        d.text((x, y), text[i], fill=text_color, font=font)

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

    if image_title != "Tonight's Forecast":
        addToStorage(
            {"high_temp": high_temp, "shortForecast": forecast_day["shortForecast"]}
        )

    img.save("output/weather_forecast.png")


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
