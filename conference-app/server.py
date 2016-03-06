import endpoints

from api.conference import ConferenceApi
from api.session import SessionApi
from api.wishlist import WishlistApi

# Register APIs
api = endpoints.api_server([ConferenceApi, SessionApi, WishlistApi])
