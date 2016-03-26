from google.appengine.ext import ndb

from models import ConflictException
from models.profile import Profile
from models.session import SessionForms
from models.session import _copySessionToForm
from models.wishlist import Wishlist
from models.wishlist import WishlistForm

from services import BaseService
from services import login_required


class WishlistService(BaseService):
    """Wishlist Service v0.1"""

    @login_required
    def add_session_to_wishlist(self, websafe_session_key):
        """Add a session to the user's wishlist.

        Args:
            websafe_session_key (string)

        Returns:
            WishlistForm with the updated wishlist
        """
        # Get user wishlist
        wishlist = self._get_user_wish_list()

        # Check that session is not already in the list
        session_key = ndb.Key(urlsafe = websafe_session_key)
        if session_key in wishlist.sessionKeys:
            raise ConflictException("Session already in wishlist")

        # Add session to list
        wishlist.sessionKeys.append(session_key)
        wishlist.put()

        # Return list of session keys
        return WishlistForm(sessionKeys = [s_key.urlsafe() for s_key in wishlist.sessionKeys])

    @login_required
    def delete_session_in_wishlist(self, websafe_session_key):
        """Remove a session from the user's wishlist.

        Args:
            websafe_session_key (string)

        Returns:
            WishlistForm with the updated wishlist
        """
        # Get user wishlist
        wishlist = self._get_user_wish_list()

        # Check that session is not already in the list
        session_key = ndb.Key(urlsafe = websafe_session_key)
        if session_key not in wishlist.sessionKeys:
            raise ConflictException("Session not in wishlist")

        # Delete session from list
        wishlist.sessionKeys.remove(session_key)
        wishlist.put()

        # Return list of session keys
        return WishlistForm(sessionKeys = [s_key.urlsafe() for s_key in wishlist.sessionKeys])

    @login_required
    def get_sessions_in_wishlist(self):
        """Get list of sessions in users's wishlist.

        Returns:
            SessionForms with all the sessions in the wishlist
        """
        # Get user wishlist
        wishlist = self._get_user_wish_list()

        # Get sessions in wishlist
        sessions = ndb.get_multi(wishlist.sessionKeys)

        # Return list of session
        return SessionForms(
            items = [_copySessionToForm(s) for s in sessions]
        )

    def _get_user_wish_list(self):
        """Get user wishlist (creates a new empty list if it does not exist)."""

        # Get list
        user_id = self.get_user_id()
        p_key = ndb.Key(Profile, user_id)
        wishlist = Wishlist.query(ancestor = p_key).get()

        # Init list if it does not exist
        if not wishlist:
            wl_id = Wishlist.allocate_ids(size = 1, parent = p_key)[0]
            wl_key = ndb.Key(Wishlist, wl_id, parent = p_key)
            wishlist = Wishlist(key = wl_key)
            wishlist.put()

        return wishlist
