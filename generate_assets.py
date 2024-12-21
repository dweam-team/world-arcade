import os
from PIL import Image
import requests
from io import BytesIO

# Create assets directory
os.makedirs('assets', exist_ok=True)

# Use Apple's cloud emoji
emoji_url = "https://em-content.zobj.net/source/apple/354/cloud_2601-fe0f.png"

# Download and open the emoji image
response = requests.get(emoji_url)
source_image = Image.open(BytesIO(response.content))

# Convert to RGBA if not already
source_image = source_image.convert('RGBA')

# Generate different sizes
sizes = [16, 32, 48, 64, 128, 256]
images = []

for size in sizes:
    # Create a new image with the desired size
    resized = source_image.resize((size, size), Image.Resampling.LANCZOS)
    output_path = f'assets/icon_{size}.png'
    resized.save(output_path)
    images.append(resized)

# Create ICO file with all sizes
images[0].save('assets/icon.ico', format='ICO', sizes=[(size, size) for size in sizes], append_images=images[1:])
