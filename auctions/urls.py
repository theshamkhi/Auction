from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing", views.create_listing, name="create_listing"),
    path('categories/', views.categories, name='categories'),
    path('category/<int:category_id>/', views.category_listings, name='category_listings'),
    path('listing/<int:listing_id>/', views.listing_detail, name='listing_detail'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('toggle_watchlist/<int:listing_id>/', views.toggle_watchlist, name='toggle_watchlist'),
    path('remove_from_watchlist/<int:listing_id>/', views.remove_from_watchlist, name='remove_from_watchlist')
]
