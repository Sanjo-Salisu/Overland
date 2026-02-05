from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomerRegistrationForm
from .models import Customer
import qrcode
from io import BytesIO
from django.core.files import File
from pyzbar.pyzbar import decode
from PIL import Image

# Registration View
def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            
            # Generate QR code containing customer ID
            qr_data = str(customer.email)  # unique identifier
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

# QR Code Scanning View
def scan_qr(request):
    customer = None
    message = ''
    if request.method == "POST":
        qr_image = request.FILES.get('qr_image')
        if qr_image:
            img = Image.open(qr_image)
            decoded = decode(img)
            if decoded:
                qr_text = decoded[0].data.decode('utf-8')
                try:
                    customer = Customer.objects.get(email=qr_text)
                except Customer.DoesNotExist:
                    message = "No customer found with this QR code."
            else:
                message = "No QR code detected in the image."
        else:
            message = "Please upload an image."
    return render(request, 'users/scan_qr.html', {'customer': customer, 'message': message})

