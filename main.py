import os
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

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
    percent_value = int(state_of_health)

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
st.title("🔋 Battery Health Certificate Generator")

test_date = st.text_input("Test date", "")
tested_by = st.text_input("Tested by", "")
status = st.text_input("Battery Status", "")

make = st.text_input("Make", "")
model = st.text_input("Model", "")
registration = st.text_input("Registration", "")
first_registered = st.text_input("First Registered", "")
vin = st.text_input("VIN", "")
mileage = st.text_input("Mileage", "")

battery = st.text_input("Battery (kWh)", "")
state_of_health = st.text_input("State of Health (%)", "")

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
