import folium
from PIL import Image
from io import BytesIO
from selenium import webdriver
import os

# Create a map object
m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)

# Add marker to the map
folium.Marker(
    location=[45.5236, -122.6750],
    popup='Portland, OR',
    icon=folium.Icon(color='red', icon='info-sign')
).add_to(m)

# Save the map as an image file with good resolution
img_data = BytesIO()
m.save(img_data, close_file=False)
img_data.seek(0)

# Set the path to the geckodriver executable
geckodriver_path = r'/Users/pouyafirouzmakan/Desktop/VANET/geckodriver.exe'

# Add the path to the geckodriver executable to the system's PATH environment variable
os.environ['PATH'] += os.pathsep + geckodriver_path

# Create a Firefox webdriver instance
driver = webdriver.Firefox()

# Open a blank page in Firefox
driver.get('about:blank')

# Set the size of the Firefox window to match the size of the map image
driver.set_window_size(800, 800)

# Load the map image into Firefox
driver.execute_script("document.body.style.zoom='50%'")
driver.execute_script("document.body.style.margin='0'")
driver.execute_script("document.body.style.padding='0'")
driver.execute_script("document.body.style.overflow='hidden'")
driver.execute_script(f"document.body.innerHTML = '<img src=\"{img_data.getvalue().decode()}\" />'")

# Save the screenshot of the Firefox window as an image file with good resolution
screenshot = driver.get_screenshot_as_png()
img = Image.open(BytesIO(screenshot))
img.save('map.png', 'PNG', quality=100)

# Close the Firefox window and quit the webdriver instance
driver.close()
driver.quit()
