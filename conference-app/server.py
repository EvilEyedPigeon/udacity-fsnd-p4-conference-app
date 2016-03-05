import endpoints

from api.conference import ConferenceApi
from api.session import SessionApi

# Register APIs
api = endpoints.api_server([ConferenceApi, SessionApi])
