import endpoints

from api.conference import ConferenceApi
from api.speaker import SpeakerApi
from api.session import SessionApi
from api.wishlist import WishlistApi

# Register APIs
api = endpoints.api_server([ConferenceApi, SpeakerApi, SessionApi, WishlistApi])
