from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

import settings
from models import QueryForms
from models.session import SessionForm
from models.session import SessionForms
from services.session import SessionService


#------ Request objects -------------------------------------------------------
    
# Request for creating or updating a session.
# Attributes:
#     SessionForm: Session inbound form
#     websafeConferenceKey: Conference key (URL-safe)
SESSION_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey = messages.StringField(1),
)

# Request for getting all sessions in a conference.
# Attributes:
#     websafeConferenceKey: Conference key (URL-safe)
SESSIONS_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required = True),
)

# Request for getting all sessions of a given type in a conference.
# Attributes:
#     websafeConferenceKey: Conference key (URL-safe)
#     typeOfSession: Type of session
SESSIONS_BY_TYPE_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required = True),
    typeOfSession = messages.StringField(2, required = True)
)

# Request for getting all sessions given by a speaker, across all conferences.
# Attributes:
#     websafeSpeakerKey: Speaker key (URL-safe)
SESSIONS_BY_SPEAKER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSpeakerKey = messages.StringField(1, required = True),
)


#------ API methods ------------------------------------------------------------

@endpoints.api(name = "session", version = "v1",
    allowed_client_ids = settings.ALLOWED_CLIENT_IDS, 
    audiences = settings.AUDIENCES,
    scopes = settings.SCOPES)
class SessionApi(remote.Service):
    """Session API v0.1"""

    def __init__(self):
        self.session_service = SessionService()

    @endpoints.method(SESSION_POST_REQUEST, SessionForm,
            path='conference/{websafeConferenceKey}/session',
            http_method='POST',
            name='createSession')
    def create_session(self, request):
        """Create new session. Open only to the organizer of the conference."""
        return self.session_service.create_session(
            request.websafeConferenceKey,
            request)

    @endpoints.method(SESSIONS_GET_REQUEST, SessionForms,
            path='conference/{websafeConferenceKey}/sessions',
            http_method='GET',
            name='getConferenceSessions')
    def get_conference_sessions(self, request):
        """Given a conference, return all sessions."""
        return self.session_service.get_conference_sessions(
            request.websafeConferenceKey)

    @endpoints.method(SESSIONS_BY_TYPE_GET_REQUEST, SessionForms,
            path='conference/{websafeConferenceKey}/sessions/{typeOfSession}',
            http_method='GET',
            name='getConferenceSessionsByType')
    def get_conference_sessions_by_type(self, request):
        """Given a conference, return all sessions of a specified type
        (e.g. lecture, keynote, workshop).
        """
        return self.session_service.get_conference_sessions_by_type(
            request.websafeConferenceKey,
            request.typeOfSession)

    @endpoints.method(SESSIONS_BY_SPEAKER_GET_REQUEST, SessionForms,
            path='conference/sessions/{websafeSpeakerKey}',
            http_method='GET',
            name='getSessionsBySpeaker')
    def get_sessions_by_speaker(self, request):
        """Given a speaker, return all sessions given by this particular speaker,
        across all conferences.
        """
        return self.session_service.get_sessions_by_speaker(
            request.websafeSpeakerKey)

    @endpoints.method(QueryForms, SessionForms,
            path='conference/sessions/query',
            http_method='POST',
            name='querySessions')
    def query_sessions(self, request):
        """(Experimental) Query for sessions."""
        return self.session_service.query_sessions(
            request)
