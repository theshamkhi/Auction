from decimal import Decimal
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required


from .forms import ListingForm
from .models import User, Listing, Category, Bid, Comment, Watchlist



def index(request):
    active_listings = Listing.objects.filter(is_active=True)
    return render(request, 'auctions/index.html', {'active_listings': active_listings})


def login_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            return redirect('index')
    else:
        form = ListingForm()
    return render(request, 'auctions/create_listing.html', {'form': form})


def categories(request):
    all_categories = Category.objects.all()
    return render(request, 'auctions/categories.html', {'all_categories': all_categories})

def category_listings(request, category_id):
    category = Category.objects.get(pk=category_id)
    active_listings = Listing.objects.filter(category=category, is_active=True)
    return render(request, 'auctions/category_listings.html', {'category': category, 'active_listings': active_listings})


@login_required
def watchlist(request):
    watchlist, created = Watchlist.objects.get_or_create(user=request.user)
    listings = watchlist.listings.all()
    return render(request, 'auctions/watchlist.html', {'listings': listings})

def remove_from_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    watchlist = Watchlist.objects.get(user=request.user)
    watchlist.listings.remove(listing)
    return redirect('watchlist')

def toggle_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    watchlist, created = Watchlist.objects.get_or_create(user=request.user)

    if listing in watchlist.listings.all():
        watchlist.listings.remove(listing)
    else:
        watchlist.listings.add(listing)

    return redirect('listing_detail', listing_id=listing_id)

def add_watchlist_count_to_context(request):
    watchlist_count = 0
    if request.user.is_authenticated:
        watchlist, created = Watchlist.objects.get_or_create(user=request.user)
        watchlist_count = watchlist.listings.count()
    return {'watchlist_count': watchlist_count}



@login_required
def listing_detail(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)

    in_watchlist = Watchlist.objects.filter(user=request.user, listings=listing).exists()

    current_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()

    starting_bid = listing.starting_bid

    # Handle adding/removing from watchlist
    if request.method == 'POST':
        if 'add_to_watchlist' in request.POST:
            if not in_watchlist:
                watchlist, created = Watchlist.objects.get_or_create(user=request.user)
                watchlist.listings.add(listing)
            else:
                watchlist = Watchlist.objects.get(user=request.user)
                watchlist.listings.remove(listing)
            return redirect('listing_detail', listing_id=listing_id)

    # Handle closing the auction
    if request.method == 'POST':
        if 'close_auction' in request.POST and listing.is_active:
            if request.user == listing.owner:
                highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
                if highest_bid:
                    listing.winner = highest_bid.bidder
                listing.is_active = False
                listing.save()

    # Handle bidding
    if request.method == 'POST':
        bid_amount_str = request.POST.get('bid_amount')
        if bid_amount_str:
            bid_amount = Decimal(bid_amount_str)

            if listing.is_active:
                if request.user != listing.owner:
                    if current_bid is None:
                        # There are no current bids, so check against the starting price
                        if bid_amount >= starting_bid:
                            bid = Bid(bidder=request.user, listing=listing, amount=bid_amount)
                            bid.save()
                            listing.current_bid = bid_amount
                            listing.save()
                            return redirect('listing_detail', listing_id=listing_id)
                        else:
                            error_message = "Your bid must be higher than the starting bid."
                    else:
                        # Check if the bid is higher than the current highest bid by at least $0.01
                        if bid_amount >= current_bid.amount + Decimal('0.01'):
                            bid = Bid(bidder=request.user, listing=listing, amount=bid_amount)
                            bid.save()
                            listing.current_bid = bid_amount
                            listing.save()
                            return redirect('listing_detail', listing_id=listing_id)
                        else:
                            error_message = "Your bid must be higher than the current bid."
                else:
                    error_message = "Owners of the listing cannot place bids."
            else:
                error_message = "This auction has ended."
        else:
            error_message = "Please enter a valid amount."
    else:
        error_message = None



    # Handle comments
    if request.method == 'POST':
        comment_text = request.POST.get('comment_text')
        if comment_text:
            comment = Comment(user=request.user, listing=listing, text=comment_text)
            comment.save()
            return redirect('listing_detail', listing_id=listing_id)

    comments = Comment.objects.filter(listing=listing)

    # Determine the winner if the auction is closed
    if not listing.is_active and listing.winner is None:
        highest_bid = Bid.objects.filter(listing=listing).order_by('-amount').first()
        if highest_bid:
            listing.winner = highest_bid.bidder
            listing.save()

    # Check if the current user is the winner
    is_winner = listing.winner == request.user if listing.winner else False

    return render(request, 'auctions/listing_detail.html', {
        'listing': listing,
        'in_watchlist': in_watchlist,
        'error_message': error_message,
        'current_bid': current_bid,
        'is_owner': request.user == listing.owner,
        'is_winner': is_winner,
        'comments': comments,
        'starting_bid': starting_bid,
    })

