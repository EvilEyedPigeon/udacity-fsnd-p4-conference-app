from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models.conference import Conference
from models.speaker import Speaker
from models.session import Session
from models.session import SessionType
from models.session import SessionForm
from models.session import SessionForms
from models.session import _copySessionToForm, _copyFormToSession

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

from utils import getUserId

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID


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

@endpoints.api(name='session', version='v1', audiences=[ANDROID_AUDIENCE],
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class SessionApi(remote.Service):
    """Session API v0.1"""

    @endpoints.method(SESSION_POST_REQUEST, SessionForm,
            path='conference/{websafeConferenceKey}/session',
            http_method='POST',
            name='createSession')
    def createSession(self, request):
        """Create new session. Open only to the organizer of the conference."""
        return self._createSessionObject(request)

    @endpoints.method(SESSIONS_GET_REQUEST, SessionForms,
            path='conference/{websafeConferenceKey}/sessions',
            http_method='GET',
            name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Given a conference, return all sessions."""

        # Get Session object from request
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # Query sessions by ancestor conference
        sessions = Session.query(ancestor = conference.key)

        return SessionForms(
            items = [_copySessionToForm(s) for s in sessions]
        )

    @endpoints.method(SESSIONS_BY_TYPE_GET_REQUEST, SessionForms,
            path='conference/{websafeConferenceKey}/sessions/{typeOfSession}',
            http_method='GET',
            name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Given a conference, return all sessions of a specified type
        (e.g. lecture, keynote, workshop).
        """

        # Get Session object from request
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # Query sessions by anscestor and type property
        query = Session.query(ancestor = conference.key)
        sessions = query.filter(Session.typeOfSession == request.typeOfSession)

        return SessionForms(
            items = [_copySessionToForm(s) for s in sessions]
        )

    @endpoints.method(SESSIONS_BY_SPEAKER_GET_REQUEST, SessionForms,
            path='conference/sessions/{websafeSpeakerKey}',
            http_method='GET',
            name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Given a speaker, return all sessions given by this particular speaker,
        across all conferences.
        """
        try:
            speaker = ndb.Key(urlsafe = request.websafeSpeakerKey).get()
        except:
            speaker = None
        if not speaker:
            raise endpoints.NotFoundException(
                'No speaker found with key: %s' % request.websafeSpeakerKey)

        # Query sessions by speaker key property
        query = Session.query()
        sessions = query.filter(Session.speakerKey == speaker.key)

        return SessionForms(
            items = [_copySessionToForm(s) for s in sessions]
        )


    def _createSessionObject(self, request):
        """Create Session object, returning SessionForm/request."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # Trying to create a Key with an invalid value raises ProtocolBufferDecodeError.
        # Using from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
        # does not work, as a different ProtocolBufferDecodeError is raised.
        # See: https://github.com/googlecloudplatform/datastore-ndb-python/issues/143
        # Catching all exceptions for now...

        # Get Session object from request
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # Verify that the user is the conference organizer
        user_id = getUserId(user)
        if user_id != conference.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Allocate session ID and generate session key
        p_key = conference.key
        s_id = Conference.allocate_ids(size = 1, parent = p_key)[0]
        s_key = ndb.Key(Session, s_id, parent = p_key)

        # Create and store new session object
        session = _copyFormToSession(request)
        session.key = s_key # set the key since this is a new object
        session.put()

        # Check for featured speakers - delegate to a task
        if session.speakerKey:
            taskqueue.add(params={'websafeSpeakerKey': session.speakerKey.urlsafe(),
                'websafeConferenceKey': conference.key.urlsafe()},
                url='/tasks/set_feature_speaker'
            )

        # Return form back
        form = _copySessionToForm(session)
        return form
