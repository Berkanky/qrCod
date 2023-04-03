import streamlit as st
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import cv2
import io
from pyzbar.pyzbar import decode
import streamlit.components.v1 as components
import numpy as np
import requests
from bs4 import BeautifulSoup
from plyer import notification
# QR code generation function
def generate_qr(link, box_size, border, fill_color, back_color, icon_file, icon_size, icon_border):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    if back_color is None:
        # If back_color is None, set alpha channel to 0 (transparent)
        img.putalpha(0)

    if icon_file:
        icon = Image.open(icon_file).convert("RGBA").resize((icon_size, icon_size))
        img.paste(icon, (img.size[0] // 2 - icon.size[0] // 2, img.size[1] // 2 - icon.size[1] // 2), icon)
        if icon_border:
            border_width = int(icon_size * icon_border / 100)
            draw = ImageDraw.Draw(img)
            draw.rectangle((img.size[0] // 2 - icon.size[0] // 2 - border_width,
                            img.size[1] // 2 - icon.size[1] // 2 - border_width,
                            img.size[0] // 2 + icon.size[0] // 2 + border_width,
                            img.size[1] // 2 + icon.size[1] // 2 + border_width), outline=fill_color)

    return img

# Streamlit interface
st.set_page_config(page_title="QR Code Generator", page_icon=":sunglasses:")
st.title("QR Code Generator")

# User name input
user_name = st.text_input("Enter your name:")

# Link, box size and border input
input_link = st.text_input("Enter a link to generate a QR code:")
box_size = st.slider("Select box size:", 1, 20, 10)
border = st.slider("Select border size:", 0, 10, 4)

# Color options
color_option = st.selectbox("Select a color option:", ("Manual", "Palette"))

if color_option == "Manual":
    fill_color = st.text_input("Enter fill color (in hex format):", "#000000")
    back_color = st.text_input("Enter background color (in hex format):", "#FFFFFF")
else:
    fill_color = st.color_picker("Select fill color:", "#000000")
    back_color = st.color_picker("Select background color:", "#FFFFFF")

# Logo options
st.subheader("Logo options:")
icon_file = st.file_uploader("Select an image for the icon (optional):", type=["jpg", "jpeg", "png"])
if icon_file:
    icon_size = st.slider("Select icon size:", 10, 40, 20)
    icon_border = st.slider("Select icon border size (% of icon size):", 0, 50, 10)
else:
    icon_size = None
    icon_border = None

# Background color option
back_option = st.selectbox("Select a background option", ("White", "Transparent", "Custom"))

if back_option == "White":
    qr_img = generate_qr(input_link, box_size, border, fill_color, "#FFFFFF", icon_file, icon_size, icon_border)
elif back_option == "Transparent":
    qr_img = generate_qr(input_link, box_size, border, fill_color, None, icon_file, icon_size, icon_border)
else:
    custom_back_color = st.color_picker("Select custom background color:", "#000000")
    qr_img = generate_qr(input_link, box_size, border, fill_color, custom_back_color, icon_file, icon_size, icon_border)

if user_name:
    draw = ImageDraw.Draw(qr_img)
    font = ImageFont.truetype("arial.ttf", 30)
    text_width, text_height = draw.textsize(user_name, font=font)
    draw.text(((qr_img.size[0] - text_width) // 2, qr_img.size[1] - text_height - 10), user_name, fill=fill_color, font=font)

img_buffer = BytesIO()
qr_img.save(img_buffer, format="PNG", transparent=True)  # Set transparent=True for alpha channel
st.image(img_buffer, use_column_width=True)

def get_image_download_link(img, filename, text):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:file/png;base64,{img_str}" download="{filename}">{text}</a>'
    return href

# Generate download link for QR code image
download_link = get_image_download_link(qr_img, "qr_code.png", "Download QR Code")
st.markdown(download_link, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Choose an image to scan for QR codes", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Read the image file in bytes
    image_bytes = uploaded_file.read()

    # Load image using OpenCV
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), -1)

    # Try to decode QR codes in the image
    decoded_data = decode(image)
    if len(decoded_data) > 0:
        # If QR code is detected, print success message
        st.write("QR code detected!")
        # Draw a rectangle around the QR code on the image
        for data in decoded_data:
            x, y, w, h = data.rect
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), thickness=3)

            # If the QR code contains a URL, show a preview of the website
            for data in decoded_data:
                if data.type == "QRCODE" and data.data.startswith(b"http"):
                    st.write("Preview of the website in the QR code:")
                    st.write(data.data.decode())

                    # Use the requests library to get the HTML code of the website
                    try:
                        response = requests.get(data.data.decode())
                        soup = BeautifulSoup(response.content, "html.parser")
                        title = soup.title.string
                        description = soup.find("meta", attrs={"name": "description"})["content"]
                        st.write(title)
                        st.write(description)

                        # Get website image from "og:image" meta tag
                        image_url = soup.find("meta", property="og:image")["content"]
                        image_bytes = io.BytesIO(requests.get(image_url).content)
                        st.image(image_bytes)

                    except:
                        st.write("Failed to fetch website preview.")
    else:
        # If no QR code is detected, print error message
        st.write("No QR code detected.")





