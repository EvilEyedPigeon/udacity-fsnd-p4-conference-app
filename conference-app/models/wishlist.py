"""Wishlist App Engine data & ProtoRPC models."""

from protorpc import messages
from google.appengine.ext import ndb

from models.session import Session


#------ Model objects ---------------------------------------------------------

class Wishlist(ndb.Model):
    """Wishlist -- Wishlist object"""
    sessionKeys = ndb.KeyProperty(kind = Session, repeated = True)

    def to_form(self):
        """Convert Wishlist to WishlistForm."""
        return _copy_wishlist_to_form(self)

    @staticmethod
    def to_object(request):
        """Convert WishlistForm/request to Wishlist."""
        return _copy_form_to_wishlist(request)

class WishlistForm(messages.Message):
    """WishlistForm -- Wishlist message"""
    sessionKeys = messages.StringField(1, repeated = True)


#------ Mapping functions -----------------------------------------------------

def _copy_wishlist_to_form(wishlist):
    """Copy relevant fields from Wishlist to WishlistForm."""
    return WishlistForm(sessionKeys = [s_key.urlsafe() for s_key in wishlist.sessionKeys])

def _copy_form_to_wishlist(request):
    """Copy relevant fields from WishlistForm/request to Wishlist."""
    return Wishlist(sessionKeys = [ndb.Key(urlsafe = websafe_key) for websafe_key in request.sessionKeys])

#------------------------------------------------------------------------------
