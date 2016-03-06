"""Wishlist App Engine data & ProtoRPC models."""

from protorpc import messages
from google.appengine.ext import ndb

from models.session import Session


class Wishlist(ndb.Model):
    """Wishlist -- Wishlist object"""
    sessionKeys = ndb.KeyProperty(kind = Session, repeated = True)

class WishlistForm(messages.Message):
    """WishlistForm -- Wishlist message"""
    sessionKeys = messages.StringField(1, repeated = True)
