import os
from datetime import date

import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

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


# Certificate generator
def generate_certificate(
    test_date, tested_by, status,
    make, registration, model, first_registered, vin, mileage,
    battery, state_of_health,
    output="certificate.pdf",
    template="certificate_bg.jpg"
):

    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4  # 595 x 842 pts

    # Draw background if exists
    if os.path.exists(template):
        c.drawImage(template, 0, 0, width=width, height=height, mask="auto")

    # Header row
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(1, 1, 1)
    c.drawString(80, height - 214, f"{test_date}")
    c.drawString(287, height - 214, f"{tested_by}")

    # Measure width of the status text
    text_width = stringWidth(status, "Helvetica-Bold", 14)

    # Pick background color based on status
    if status == "Excellent":
        c.setFillColorRGB(0, 0.7, 0)  # green
    elif status == "Good":
        c.setFillColorRGB(1, 0.65, 0)  # amber
    else:
        c.setFillColorRGB(0.9, 0, 0)  # red

    # Draw rectangle behind the text
    c.roundRect(504 - 2, (height - 214) - 5, text_width + 12, 14 + 6, radius=6, fill=1, stroke=0)

    # Now draw the text in white on top
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(1, 1, 1)  # white text
    c.drawString(507, height - 214, f"{status}")

    c.setFillColorRGB(0, 0, 0)
    c.drawString(80, height - 354, f"{make}")
    c.drawString(430, height - 354, f"{registration}")
    c.drawString(80, height - 392, f"{model}")
    c.drawString(430, height - 392, f"{first_registered}")
    c.drawString(80, height - 431, f"{vin}")
    c.drawString(430, height - 432, f"{mileage}")

    c.drawString(200, height - 551, f"{battery} kWh")

    # Gauge settings
    center_x, center_y = width / 2, height - 740
    radius = 65
    # Clean state_of_health string
    try:
        percent_value = int(str(state_of_health).replace("%", "").strip())
    except ValueError:
        percent_value = 0  # fallback if input is invalid

    # Draw background circle (light grey outline)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(20)
    c.circle(center_x, center_y, radius)

    # Pick color based on % thresholds
    if percent_value > 85:
        c.setStrokeColorRGB(0, 0.7, 0)  # green
    elif percent_value >= 65:
        c.setStrokeColorRGB(1, 0.65, 0)  # amber (orange)
    else:
        c.setStrokeColorRGB(0.9, 0, 0)  # red

    # Draw arc for percentage
    sweep_angle = 360 * (percent_value / 100)
    c.arc(center_x - radius, center_y - radius,
          center_x + radius, center_y + radius,
          startAng=90, extent=-int(sweep_angle))

    # Reset line width
    c.setLineWidth(1)

    # Draw percentage text inside circle
    c.setFont("Helvetica-Bold", 28)
    c.setFillColorRGB(1, 1, 1)  # white text
    c.drawCentredString(center_x, center_y - 10, f"{percent_value}%")

    # Big % centered
    c.setFont("Helvetica-Bold", 32)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(width/2, height - 750, f"{state_of_health}%")

    c.save()
    return output


# ----------------- STREAMLIT APP -----------------
st.set_page_config(
    page_title="Battery Health Certificate",   # Tab title
    page_icon="🔋",                            # Favicon (emoji or image file)
    layout="centered"                          # or "wide"
)

# -------------------------
# Streamlit UI - Main
# -------------------------

# Important Notice Alert
st.warning("""
### ⚠️ Important Notice
**Fiverr Account Suspension:** My Fiverr account has been permanently suspended due to a "suspicious clone account" issue. 
This is beyond my control, but I remain committed to supporting you.

**For continued support and updates, please contact me directly at:**  
📧 **hamza.ahmed.ws@gmail.com**

Thank you for your understanding and patience.
""")

st.title("🏡 Care Home Monthly Activities – Editable Preview & A3 PDF")

st.title("🔋 Battery Health Certificate Generator")

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

# Auto-calculate Battery Status from percentage
if state_of_health >= 85:
    status = "Excellent"
elif state_of_health >= 65:
    status = "Good"
else:
    status = "Bad"

if st.button("Generate Certificate"):
    filename = "certificate.pdf"
    generate_certificate(
        test_date, tested_by, status,
        make, registration, model, first_registered, vin, mileage,
        battery, state_of_health,
        output=filename
    )
    with open(filename, "rb") as f:
        st.download_button("⬇ Download Certificate", f, file_name=filename)
