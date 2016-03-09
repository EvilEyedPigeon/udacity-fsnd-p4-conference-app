import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

from models import ConflictException
from models.profile import Profile
from models.session import Session
from models.session import SessionForms
from models.session import _copySessionToForm
from models.wishlist import Wishlist
from models.wishlist import WishlistForm

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

from utils import getUserId

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID


#------ Request objects -------------------------------------------------------
    
"""Request for adding a session to the user's wishlist.

Attributes:
    websafeSessionKey: Session key (URL-safe)
"""
WISHLIST_POST_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey = messages.StringField(1, required = True)
)


#------ API methods ------------------------------------------------------------

@endpoints.api(name='wishlist', version='v1', audiences=[ANDROID_AUDIENCE],
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class WishlistApi(remote.Service):
    """Wishlist API v0.1"""

    @endpoints.method(WISHLIST_POST_REQUEST, WishlistForm,
        path = "wishlist/{websafeSessionKey}",
        http_method = "POST",
        name = "addSessionToWishlist")
    def addSessionToWishlist(self, request):
        """Add a session to the user's wishlist."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # Get user wishlist
        wishlist = self._getUserWishList(user)

        # Check that session is not already in the list
        session_key = ndb.Key(urlsafe = request.websafeSessionKey)
        if session_key in wishlist.sessionKeys:
            raise ConflictException("Session already in wishlist")

        # Add to list
        wishlist.sessionKeys.append(session_key)
        wishlist.put()

        # Return list of session keys
        return WishlistForm(sessionKeys = [s_key.urlsafe() for s_key in wishlist.sessionKeys])

    @endpoints.method(WISHLIST_POST_REQUEST, WishlistForm,
        path = "wishlist/{websafeSessionKey}",
        http_method = "DELETE",
        name = "deleteSessionInWishlist")
    def deleteSessionInWishlist(self, request):
        """Remove a session from the user's wishlist."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # Get user wishlist
        wishlist = self._getUserWishList(user)

        # Check that session is not already in the list
        session_key = ndb.Key(urlsafe = request.websafeSessionKey)
        if session_key not in wishlist.sessionKeys:
            raise ConflictException("Session not in wishlist")

        # Add to list
        wishlist.sessionKeys.remove(session_key)
        wishlist.put()

        # Return list of session keys
        return WishlistForm(sessionKeys = [s_key.urlsafe() for s_key in wishlist.sessionKeys])

    @endpoints.method(message_types.VoidMessage, SessionForms,
        path = "wishlist",
        http_method = "GET",
        name = "getSessionsInWishlist")
    def getSessionsInWishlist(self, request):
        """Get list of sessions in users's wishlist."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # Get user wishlist
        wishlist = self._getUserWishList(user)

        # Get sessions in wishlist
        sessions = ndb.get_multi(wishlist.sessionKeys)

        # Return list of session
        return SessionForms(
            items = [_copySessionToForm(s) for s in sessions]
        )

    def _getUserWishList(self, user):
        """Get user wishlist (creates a new empty list if it does not exist)."""

        # Get list
        user_id = getUserId(user)
        p_key = ndb.Key(Profile, user_id)
        wishlist = Wishlist.query(ancestor = p_key).get()

        # Init list if it does not exist
        if not wishlist:
            wl_id = Wishlist.allocate_ids(size = 1, parent = p_key)[0]
            wl_key = ndb.Key(Wishlist, wl_id, parent = p_key)
            wishlist = Wishlist(key = wl_key)
            wishlist.put()

        return wishlist

#-------------------------------------------------------------------------------
