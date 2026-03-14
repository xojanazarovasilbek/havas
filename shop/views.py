from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Product, Sale, SaleItem, Category
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
import json

# --- LOGIN/LOGOUT ---
def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'shop/login.html', {'error': 'Xato login yoki parol!'})
    return render(request, 'shop/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# --- KASSA ---
@login_required(login_url='login')
def kassa_page(request):
    return render(request, 'shop/kassa.html')

# MUHIM: Ham barcode, ham internal_code (ichki kod) bo'yicha qidirish
from django.http import JsonResponse
from django.db.models import Q  # <--- Buni albatta qo'shish kerak
from .models import Product

def get_product(request):
    # .strip() orqali koddagi tasodifiy bo'sh joylarni olib tashlaymiz
    query = request.GET.get('query', '').strip() 
    
    if not query:
        return JsonResponse({'status': 'error', 'message': 'Kod kiritilmadi'})
    
    try:
        # Qidiruv: Ham shtrix-kod, ham ichki kod bo'yicha
        # filter(...).first() orqali agar topilmasa None qaytarishini ta'minlaymiz
        product = Product.objects.filter(
            Q(barcode=query) | Q(internal_code=query)
        ).first()

        if product:
            return JsonResponse({
                'status': 'success',
                'id': product.id,
                'name': product.name,
                'price': float(product.price),
                # Agar is_weight maydoni bo'lmasa, default False qaytaradi
                'is_weight': getattr(product, 'is_weight', False) 
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Mahsulot topilmadi!'})
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@transaction.atomic
def complete_sale(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart = data.get('cart')
        payment_method = data.get('payment_method', 'cash') 
        
        try:
            sale = Sale.objects.create(
                cashier=request.user, 
                total_price=0,
                payment_method=payment_method
            )
            
            total_sum = 0
            for item in cart:
                product = Product.objects.get(id=item['id'])
                
                # Sotuv qatorini yaratish (qty endi float bo'lishi mumkin - 1.5 kg kabi)
                SaleItem.objects.create(
                    sale=sale,
                    product=product,
                    quantity=item['qty'],
                    price_at_sale=product.price
                )
                
                # Ombordan ayirish
                product.stock -= item['qty']
                product.save()
                
                total_sum += float(product.price) * float(item['qty'])
            
            sale.total_price = total_sum
            sale.save()
            
            return JsonResponse({'status': 'success', 'sale_id': sale.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

# --- DASHBOARD ---
@login_required(login_url='login')
def admin_dashboard(request):
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)
    
    today_sales = Sale.objects.filter(created_at__date=now.date())
    today_total = today_sales.aggregate(Sum('total_price'))['total_price__sum'] or 0
    
    # To'lov turlari bo'yicha ajratish
    today_cash = today_sales.filter(payment_method='cash').aggregate(Sum('total_price'))['total_price__sum'] or 0
    today_card = today_sales.filter(payment_method='card').aggregate(Sum('total_price'))['total_price__sum'] or 0
    today_click = today_sales.filter(payment_method='click').aggregate(Sum('total_price'))['total_price__sum'] or 0
    today_payme = today_sales.filter(payment_method='payme').aggregate(Sum('total_price'))['total_price__sum'] or 0

    weekly_total = Sale.objects.filter(created_at__gte=seven_days_ago).aggregate(Sum('total_price'))['total_price__sum'] or 0
    monthly_total = Sale.objects.filter(created_at__gte=now - timedelta(days=30)).aggregate(Sum('total_price'))['total_price__sum'] or 0

    chart_data = Sale.objects.filter(created_at__gte=seven_days_ago)\
        .annotate(date=TruncDate('created_at'))\
        .values('date')\
        .annotate(total=Sum('total_price'))\
        .order_by('date')

    dates = [data['date'].strftime("%d-%b") for data in chart_data]
    totals = [float(data['total']) for data in chart_data]

    top_products = SaleItem.objects.values('product__name').annotate(
        total_qty=Sum('quantity')
    ).order_by('-total_qty')[:5]

    low_stock = Product.objects.filter(stock__lt=10)
    categories = Category.objects.all()

    context = {
        'today_total': today_total,
        'today_cash': today_cash,
        'today_card': today_card,
        'today_click': today_click,
        'today_payme': today_payme,
        'weekly_total': weekly_total,
        'monthly_total': monthly_total,
        'top_products': top_products,
        'low_stock': low_stock,
        'categories': categories,
        'dates': json.dumps(dates),
        'totals': json.dumps(totals),
    }
    return render(request, 'shop/dashboard.html', context)

# --- MAHSULOT QO'SHISH ---
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        barcode = request.POST.get('barcode')
        internal_code = request.POST.get('internal_code') # Ichki kod (101)
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        category_id = request.POST.get('category')
        is_weight = request.POST.get('is_weight') == 'on' # Checkbox-dan keladi

        Product.objects.create(
            name=name,
            barcode=barcode,
            internal_code=internal_code,
            price=price,
            stock=stock,
            category_id=category_id,
            is_weight=is_weight
        )
        return redirect('dashboard')