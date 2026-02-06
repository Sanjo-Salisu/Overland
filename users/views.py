# users/views.py

from django.shortcuts import render
from django.core.files import File
from io import BytesIO
import qrcode
import cv2
import numpy as np
import json

from .forms import CustomerRegistrationForm
from .models import Customer

# ===============================
# OpenCV QR scan helper function
# ===============================
def decode_qr(image_file):
    """
    Safely decode a QR code from an uploaded image.
    Returns the QR data string (JSON) or None if decoding fails.
    """
    if not image_file:
        return None

    # Read file into bytes
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

    return data.strip()  # remove any whitespace or newlines


# ===============================
# Customer Registration View
# ===============================
def register_customer(request):
    """
    Handles customer registration and generates a QR code
    containing all customer info.
    """
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)

            # Prepare data for QR code
            customer_data = {
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "address": customer.address,
            }
            qr_data = json.dumps(customer_data, ensure_ascii=False)

            # Use QRCode object for precise encoding
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Save QR code image to customer.qr_code field
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
    Handles QR code uploads, decodes them, and displays
    customer information.
    """
    customer_data = None
    message = ''

    if request.method == 'POST':
        qr_image = request.FILES.get('qr_image')

        if qr_image:
            qr_text = decode_qr(qr_image)

            if qr_text:
                try:
                    customer_data = json.loads(qr_text)
                except json.JSONDecodeError:
                    message = "Invalid QR code data."
            else:
                message = "No QR code detected or image is invalid."
        else:
            message = "Please upload a valid image."

    # Always return a response (even for GET requests)
    return render(
        request,
        'users/scan_qr.html',
        {'customer_data': customer_data, 'message': message}
    )
