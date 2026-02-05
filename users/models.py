from django.db import models
from django.urls import reverse

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)

    def __str__(self):
        return self.name

    def get_qr_code_path(self):
        return self.qr_code.url if self.qr_code else ''

