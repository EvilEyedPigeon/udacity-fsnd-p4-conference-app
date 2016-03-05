import endpoints
from conference import ConferenceApi
from session import SessionApi

# Register APIs
api = endpoints.api_server([ConferenceApi, SessionApi])
