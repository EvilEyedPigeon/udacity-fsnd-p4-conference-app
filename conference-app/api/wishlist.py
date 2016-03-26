import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

import settings
from models.session import SessionForms
from models.wishlist import WishlistForm
from services.wishlist import WishlistService


#------ Request objects -------------------------------------------------------
    
# Request for adding a session to or removing a session from the user's wishlist.
# Attributes:
#     websafeSessionKey: Session key (URL-safe)
WISHLIST_POST_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSessionKey = messages.StringField(1, required = True)
)


#------ API methods ------------------------------------------------------------

@endpoints.api(name = "wishlist", version = "v1",
    allowed_client_ids = settings.ALLOWED_CLIENT_IDS, 
    audiences = settings.AUDIENCES,
    scopes = settings.SCOPES)
class WishlistApi(remote.Service):
    """Wishlist API v0.1"""

    def __init__(self):
        self.wishlist_service = WishlistService()

    @endpoints.method(WISHLIST_POST_REQUEST, WishlistForm,
        path = "wishlist/{websafeSessionKey}",
        http_method = "POST",
        name = "addSessionToWishlist")
    def add_session_to_wishlist(self, request):
        """Add a session to the user's wishlist."""
        return self.wishlist_service.add_session_to_wishlist(
            request.websafeSessionKey)

    @endpoints.method(WISHLIST_POST_REQUEST, WishlistForm,
        path = "wishlist/{websafeSessionKey}",
        http_method = "DELETE",
        name = "deleteSessionInWishlist")
    def delete_session_in_wishlist(self, request):
        """Remove a session from the user's wishlist."""
        return self.wishlist_service.delete_session_in_wishlist(
            request.websafeSessionKey)

    @endpoints.method(message_types.VoidMessage, SessionForms,
        path = "wishlist",
        http_method = "GET",
        name = "getSessionsInWishlist")
    def get_sessions_in_wishlist(self, request):
        """Get list of sessions in users's wishlist."""
        return self.wishlist_service.get_sessions_in_wishlist()

#-------------------------------------------------------------------------------
