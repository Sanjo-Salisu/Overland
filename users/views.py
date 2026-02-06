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
# OpenCV QR scan function
# ===============================
def scan_qr(image_file):
    """Decode a QR code from an uploaded image safely."""
    if not image_file:
        return None

    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    if file_bytes.size == 0:
        return None

    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        return None

    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)

    if not data:
        return None

    return data  # Returns QR code string (JSON in our case)


# ===============================
# Customer Registration View
# ===============================
def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)

            # Prepare data to store in QR code (all customer info as JSON)
            customer_data = {
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "address": customer.address,
            }
            qr_data = json.dumps(customer_data)  # Convert dict to JSON string
            qr_img = qrcode.make(qr_data)

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
def scan_qr(request):
    customer_data = None
    message = ''

    if request.method == 'POST':
        qr_image = request.FILES.get('qr_image')

        if qr_image:
            qr_text = scan_qr(qr_image)  # Decode QR code

            if qr_text:
                try:
                    # Decode JSON string from QR code
                    customer_data = json.loads(qr_text)
                except json.JSONDecodeError:
                    message = "Invalid QR code data."
            else:
                message = "No QR code detected or image is invalid."
        else:
            message = "Please upload a valid image."

    return render(request, 'users/scan_qr.html', {'customer_data': customer_data, 'message': message})
