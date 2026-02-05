# users/views.py

from django.shortcuts import render
from django.http import JsonResponse
from django.core.files import File
from io import BytesIO
from PIL import Image
import qrcode
import cv2
import numpy as np

from .forms import CustomerRegistrationForm
from .models import Customer

# ===============================
# OpenCV QR scan function
# ===============================
def scan_qr(image_file):
    # Convert uploaded file to OpenCV image
    file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Detect and decode QR code
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)

    return data  # Returns QR text or empty string


# ===============================
# Customer Registration View
# ===============================
def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            
            # Generate QR code containing customer email (unique identifier)
            qr_data = str(customer.email)
            qr_img = qrcode.make(qr_data)
            
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
    customer = None
    message = ''
    
    if request.method == "POST":
        qr_image = request.FILES.get('qr_image')
        if qr_image:
            qr_text = scan_qr(qr_image)  # OpenCV QR scan

            if qr_text:
                try:
                    customer = Customer.objects.get(email=qr_text)
                except Customer.DoesNotExist:
                    message = "No customer found with this QR code."
            else:
                message = "No QR code detected in the image."
        else:
            message = "Please upload an image."

    return render(request, 'users/scan_qr.html', {'customer': customer, 'message': message})
