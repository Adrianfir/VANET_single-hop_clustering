import folium
import os
from PIL import Image
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from io import BytesIO


def save_img(sw_lat, sw_long,
             ne_lat, ne_long,
             se_lat, se_long,
             nw_lat, nw_long,
             zoom_out_value, name):

    """
    :param se_lat:
    :param se_long:
    :param nw_lat:
    :param nw_long:
    :param name: name of the image
    :param zoom_out_value: zoom amount
    :param sw_lat: minimum latitude
    :param ne_lat: maximum latitude
    :param sw_long: minimum longitude
    :param ne_long: maximum longitude
    :return: an image will be saved to the directory path
    """
    # Create a map object with specified bounds
    m = folium.Map(location=[(sw_lat + ne_lat) / 2, (sw_long + ne_long) / 2], zoom_start=zoom_out_value)
    folium.Polygon([(sw_lat, sw_long), (se_lat, se_long), (ne_lat, ne_long), (nw_lat, nw_long),
                    (sw_lat, sw_long)]).add_to(m)

    # Save the map as an HTML file
    map_file = "map.html"
    m.save(map_file)

    # Set up the options for the webdriver
    options = Options()
    options.headless = True  # Run the browser in headless mode (without opening a visible window)

    # Initialize the Firefox webdriver
    driver = webdriver.Firefox(options=options)

    # Open the map HTML file
    driver.get(f'file://{os.path.abspath(map_file)}')

    # change the zoom
    script = f"document.getElementsByClassName('leaflet-control')[0].style.transform = 'scale({1 / zoom_out_value})';"
    driver.execute_script(script)

    # Wait for the map to load (you can adjust the waiting time if needed)
    time.sleep(1)

    # Take a screenshot of the entire webpage (including the map)
    screenshot = driver.get_screenshot_as_png()

    # Save the screenshot as an image file with good resolution and in grayscale
    img = Image.open(BytesIO(screenshot))
    img = img.convert('L')  # Convert to grayscale
    img.save(name + '.png', 'PNG', quality=5000)

    # Close the Firefox window and quit the webdriver instance
    driver.quit()

    # Delete the temporary HTML file
    os.remove(map_file)


ne_lat = 43.977770
ne_long = -79.392738

sw_lat = 43.829375
sw_long = -79.454305

se_lat = 43.847194
se_long = -79.371203

nw_lat = 43.957412
nw_long = -79.485611

zoom = 12

image_name = "exported_map"
save_img(sw_lat, sw_long, ne_lat, ne_long, se_lat, se_long, nw_lat, nw_long, zoom, image_name)
