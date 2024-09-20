from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import models



class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Listing(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_listings')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_listings')

    def __str__(self):
        return self.title


class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.bidder} bid {self.amount} on {self.listing}"


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user} on {self.listing}"


class Watchlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    listings = models.ManyToManyField(Listing)

    def __str__(self):
        return f"Watchlist for {self.user}"