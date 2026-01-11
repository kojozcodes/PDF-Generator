import os
import uuid
from datetime import date
from io import BytesIO

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
import qrcode
import cloudinary
import cloudinary.uploader
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

car_data = {
    "BYD": ["Sealion 7"],
    "Hyundai": ["Ioniq", "Tucson"],
    "Kia": ["EV6", "Niro EV", "Sportage", "Xeed"],
    "MG": ["MG-5", "MG-ZS"],
    "Nissan": ["Ariya", "Leaf"],
    "Polestar": ["Polestar 2"],
    "Skoda": ["Enyaq", "Octavia"],
    "Tesla": ["Model 3", "Model Y"],
    "Toyota": ["BZ4X", "Corolla", "Prius"],
    "Volkswagen": ["ID3", "ID4", "ID7", "ID-Buzz"]
}

# QR Code position constants (from testing)
QR_SIZE = 75
QR_X = 490
QR_Y = 741


def generate_qr_code(url, size=150):
    """Generate QR code image from URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to specified size
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Save to BytesIO
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer


def generate_certificate(
    test_date, tested_by, status,
    make, registration, model, first_registered, vin, mileage,
    battery, state_of_health,
    qr_code_buffer=None,
    output="certificate.pdf",
    template="certificate_bg_2.png"
):
    """Generate PDF certificate with optional QR code"""
    
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4  # 595 x 842 pts

    # Draw background if exists
    if os.path.exists(template):
        c.drawImage(template, 0, 0, width=width, height=height, mask="auto")

    # Draw QR code in specified position if provided
    if qr_code_buffer:
        # Save buffer to temp file for reportlab
        temp_qr = "temp_qr.png"
        with open(temp_qr, "wb") as f:
            f.write(qr_code_buffer.getvalue())
        
        c.drawImage(temp_qr, QR_X, QR_Y, width=QR_SIZE, height=QR_SIZE, mask="auto")
        
        # Clean up temp file
        if os.path.exists(temp_qr):
            os.remove(temp_qr)

    # Header row
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(90, height - 216, f"{test_date}")
    c.setFillColorRGB(1, 1, 1)
    c.drawString(270, height - 216, f"{tested_by}")

    # Status text
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(480, height - 215, f"{status}")

    # Vehicle details (black text)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(85, height - 354, f"{make}")
    c.drawString(405, height - 354, f"{registration}")
    c.drawString(85, height - 392, f"{model}")
    c.drawString(405, height - 392, f"{first_registered}")
    c.drawString(85, height - 431, f"{vin}")
    c.drawString(405, height - 432, f"{mileage}")

    c.setFont("Helvetica-Bold", 20)
    c.drawString(180, height - 585, f"{battery} kWh")

    # Progress bar for battery health
    bar_x = 180
    bar_y = height - 675
    bar_width = 300
    bar_height = 30
    
    # Clean state_of_health
    try:
        percent_value = int(str(state_of_health).replace("%", "").strip())
    except ValueError:
        percent_value = 0

    # Background bar (gray)
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.roundRect(bar_x, bar_y, bar_width, bar_height, radius=5, fill=1, stroke=1)

    # Progress fill
    if percent_value > 85:
        c.setFillColorRGB(0, 0.7, 0)  # green
    elif percent_value >= 65:
        c.setFillColorRGB(1, 0.65, 0)  # amber
    else:
        c.setFillColorRGB(0.9, 0, 0)  # red

    fill_width = (bar_width * percent_value) / 100
    c.roundRect(bar_x, bar_y, fill_width, bar_height, radius=5, fill=1, stroke=0)

    # Percentage text in white box
    c.setFillColorRGB(1, 1, 1)
    c.roundRect(bar_x + bar_width + 5, bar_y, 80, bar_height, radius=5, fill=1, stroke=1)
    
    c.setFont("Helvetica-Bold", 18)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(bar_x - 12.5 + bar_width + 60, bar_y + 8, f"{percent_value}%")

    c.save()
    return output


def upload_to_cloudinary(file_path, cloud_name, api_key, api_secret):
    """Upload file to Cloudinary and return public URL"""
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret
    )
    
    # Generate unique public ID
    unique_id = str(uuid.uuid4())
    
    # Upload file as raw resource
    response = cloudinary.uploader.upload(
        file_path,
        public_id=f"certificates/{unique_id}",
        resource_type="raw",
        overwrite=True
    )
    
    # Get the secure URL from response
    secure_url = response.get('secure_url', '')
    
    # If that doesn't work, try constructing URL manually
    if not secure_url:
        secure_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/certificates/{unique_id}.pdf"
    
    return secure_url, unique_id


# ----------------- STREAMLIT APP -----------------
st.set_page_config(
    page_title="Battery Health Certificate",
    page_icon="🔋",
    layout="centered"
)

st.title("🔋 Battery Health Certificate Generator")

# Cloudinary Configuration (from environment variables)
cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "")
api_key = os.getenv("CLOUDINARY_API_KEY", "")
api_secret = os.getenv("CLOUDINARY_API_SECRET", "")

cloudinary_configured = bool(cloud_name and api_key and api_secret)

# Form inputs
test_date = st.date_input("Test date", value=date.today()).strftime("%d/%m/%Y")
tested_by = st.text_input("Tested by", "")
make = st.selectbox("Make", sorted(car_data.keys()))
model = st.selectbox("Model", sorted(car_data[make]))
registration = st.text_input("Registration", "")
first_registered = st.date_input("First Registered", value=date(2021, 10, 28)).strftime("%d/%m/%Y")
vin = st.text_input("VIN", "")
mileage = st.text_input("Mileage", "")
battery = st.text_input("Battery (kWh)", "")

# State of Health as slider
state_of_health = st.slider("State of Health (%)", 0, 100, 90)

# Auto-calculate Battery Status
if state_of_health >= 85:
    status = "Excellent"
elif state_of_health >= 65:
    status = "Good"
else:
    status = "Bad"

st.info(f"**Battery Status:** {status}")

if st.button("Generate Certificate", type="primary"):
    if not cloudinary_configured:
        st.error("❌ Cloudinary credentials not configured. Please contact administrator.")
        st.stop()
    
    with st.spinner("Generating certificate..."):
        try:
            temp_filename = f"temp_cert_{uuid.uuid4()}.pdf"
            
            # Step 1: Generate initial PDF without QR
            generate_certificate(
                test_date, tested_by, status,
                make, registration, model, first_registered, vin, mileage,
                battery, state_of_health,
                qr_code_buffer=None,
                output=temp_filename
            )
            
            # Step 2: Upload to Cloudinary
            with st.spinner("Uploading to cloud..."):
                cert_url, cert_id = upload_to_cloudinary(
                    temp_filename, cloud_name, api_key, api_secret
                )
            
            # Step 3: Generate QR code with URL
            with st.spinner("Generating QR code..."):
                qr_buffer = generate_qr_code(cert_url)
            
            # Step 4: Regenerate PDF with QR code
            final_filename = f"certificate_{cert_id[:8]}.pdf"
            generate_certificate(
                test_date, tested_by, status,
                make, registration, model, first_registered, vin, mileage,
                battery, state_of_health,
                qr_code_buffer=qr_buffer,
                output=final_filename
            )
            
            # Step 5: Upload final version with QR
            with st.spinner("Finalizing..."):
                final_url, _ = upload_to_cloudinary(
                    final_filename, cloud_name, api_key, api_secret
                )
            
            # Clean up temp file
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            
            st.success("✅ Certificate generated successfully!")
            
            # Download button
            with open(final_filename, "rb") as f:
                st.download_button(
                    "⬇️ Download Certificate",
                    f,
                    file_name=final_filename,
                    mime="application/pdf"
                )
            
            # Clean up final file after download
            if os.path.exists(final_filename):
                os.remove(final_filename)
                    
        except Exception as e:
            st.error(f"❌ Error generating certificate: {str(e)}")
            st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
### 📧 Support
For issues or updates, contact: **hamza.ahmed.ws@gmail.com**
""")