# Forecast Image Generator

This project generates weather forecast images using data from the National Weather Service API. The generated images include a header, footer, and weather forecast details.

## Features

- Fetches weather data from the National Weather Service API
- Generates weather forecast images with headers and footers
- Supports custom fonts and colors
- Provides a simple web interface to view the generated images

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/Arch881010/forecast-image-generator.git
    cd forecast-image-generator
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

Edit the [config.py](config.py) file to customize the settings such as colors, fonts, and location details.

## Usage

1. Run the main script to generate the weather forecast image:
    ```sh
    python main.py
    ```
    Make sure to exit after the first image is generated, unless you want to open a new terminal/screen.

2. Start the Flask web server to view the generated images:
    ```sh
    python api.py
    ```

3. Open your web browser and navigate to `http://localhost:9999` to view the generated weather forecast image.

## File Structure

- [main.py](main.py): Main script to fetch weather data and generate images
- [api.py](api.py): Flask web server to serve the generated images
- [config.py](onfig.py): Configuration file for customizable settings
- [generate_header.py](generate_header.py): Script to generate the header image
- [generate_footer.py](generate_footer.py): Script to generate the footer image
- [make_transparent.py](make_transparent.py): A script that attempts to make images transparent (usage: `py make_transparent.py filePath`)
- [extra.py](extra.py): Additional utility functions
- [web_files](web_files): Contains HTML and JavaScript files for the web interface
- [output](output): Directory where generated images and data are saved
- [fonts](fonts): Directory containing font files
- [icons](icons): Directory containing icon files
- [transparent_icons](transparent_icons): Directory containing transparent icon files

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

# TODO

- [ ] Fix the image randomly being rotated 180 degrees after running `py make_transparent.py`