from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=50, unique=True, null=True, blank=True)
    # Mahsulotning ichki qisqa kodi (masalan: 101, 102)
    internal_code = models.CharField(max_length=10, unique=True, null=True, blank=True) 
    price = models.DecimalField(max_digits=10, decimal_places=2) # 1 kg yoki 1 dona narxi
    stock = models.DecimalField(max_digits=10, decimal_places=3, default=0) # Umumiy kg yoki dona soni
    is_weight = models.BooleanField(default=False) # Bu mahsulot kg-da sotiladimi?

    def __str__(self):
        return f"{self.name} ({self.internal_code})"

class Sale(models.Model):
    cashier = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    PAYMENT_CHOICES = [
        ('cash', 'Naqd'),
        ('card', 'Plastik karta'),
    ]
    # ... boshqa maydonlar ...
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default='cash')


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2)