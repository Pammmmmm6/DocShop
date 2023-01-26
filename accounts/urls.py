from accounts.views import signup, logout_user, login_user, profile, set_default_shipping_address, delete_adddress
from django.urls import path

app_name = 'accounts'

urlpatterns = [
    path('logout/', logout_user, name='logout'),
    path('profile/', profile, name='profile'),
    path('profile/set_default_shipping/<int:pk>', set_default_shipping_address, name='set-default-shipping'),
    path('login/', login_user, name='login'),
    path('signup/', signup, name='signup'),
    path('delete_address/<int:pk>/', delete_adddress, name='delete-address'),
]