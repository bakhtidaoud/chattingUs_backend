from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order, Listing, Payout, Conversation

@login_required
def dashboard_view(request):
    return render(request, 'web/dashboard.html')

@login_required
def chat_view(request):
    return render(request, 'web/chat.html')

@login_required
def saved_searches_view(request):
    return render(request, 'web/saved_searches.html')
