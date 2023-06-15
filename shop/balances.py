from .models import Payment


def balance_user(request):
    balance = 'Авторизуйтесь!'
    if request.user.is_authenticated:
        balance = Payment.get_balance(request.user)
    return {'balance': balance}


def get_user_balance(request):
    bal = 'Авторизуйтесь!'
    if request.user.is_authenticated:
        bal = Payment.get_balance(request.user)
    return bal
