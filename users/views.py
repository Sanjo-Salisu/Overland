# users/views.py

from django.shortcuts import render
from django.core.files import File
from io import BytesIO
import qrcode
import cv2
import numpy as np
import json
import base64

from .forms import CustomerRegistrationForm
from .models import Customer

# ===============================
# OpenCV QR scan helper function
# ===============================
def decode_qr(image_file):
    """
    Decode a QR code from an uploaded image using OpenCV.
    Returns Base64 string (JSON encoded) or None if decoding fails.
    """
    if not image_file:
        return None

    # Read uploaded file into bytes
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    if file_bytes.size == 0:
        return None

    # Decode image using OpenCV
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        return None

    # Detect and decode QR code
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)

    if not data:
        return None

    return data.strip()  # remove whitespace or newlines


# ===============================
# Customer Registration View
# ===============================
def register_customer(request):
    """
    Handles customer registration and generates a QR code
    containing all customer info in Base64-encoded JSON.
    """
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)

            # Prepare JSON data
            customer_data = {
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "address": customer.address,
            }
            json_str = json.dumps(customer_data, ensure_ascii=False)

            # Encode JSON as Base64 for safe QR storage
            qr_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

            # Generate QR code
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Save QR code image
            buffer = BytesIO()
            qr_img.save(buffer, 'PNG')
            filename = f"{customer.email}_qr.png"
            customer.qr_code.save(filename, File(buffer), save=False)
            customer.save()

            return render(request, 'users/registration_success.html', {'customer': customer})
    else:
        form = CustomerRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


# ===============================
# QR Code Scanning View
# ===============================
def scan_qr_view(request):
    """
    Handles QR code uploads, decodes Base64 JSON, and displays
    customer information safely.
    """
    customer_data = None
    message = ''

    if request.method == 'POST':
        qr_image = request.FILES.get('qr_image')

        if qr_image:
            qr_text = decode_qr(qr_image)

            if qr_text:
                try:
                    # Decode Base64 back to JSON string
                    json_str = base64.b64decode(qr_text).decode('utf-8')
                    customer_data = json.loads(json_str)
                except Exception:
                    message = "Invalid QR code data."
            else:
                message = "No QR code detected or image is invalid."
        else:
            message = "Please upload a valid image."

    # Always return response (even GET)
    return render(request, 'users/scan_qr.html', {'customer_data': customer_data, 'message': message})
