from django.contrib import admin
from .models import User, Category, Listing, Bid, Comment, Watchlist


admin.site.register(User)
admin.site.register(Category)
admin.site.register(Bid)
admin.site.register(Comment)
admin.site.register(Watchlist)


class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'starting_bid', 'current_bid', 'category', 'owner')

admin.site.register(Listing, ListingAdmin)
