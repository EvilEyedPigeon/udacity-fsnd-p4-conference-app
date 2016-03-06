from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

from models import Conference
from models.session import Session
from models.session import SessionType
from models.session import SessionForm
from models.session import SessionForms

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

#------ Requests objects ------------------------------------------------------
    
"""Request for creating or updating a session.

Attributes:
    SessionForm: Session inbound form
    websafeConferenceKey: Conference key (URL-safe)
"""
SESSION_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey = messages.StringField(1),
)

"""Request for getting all sessions in a conference.

Attributes:
    websafeConferenceKey: Conference key (URL-safe)
"""
SESSIONS_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required = True),
)

"""Request for getting all sessions of a given type in a conference.

Attributes:
    websafeConferenceKey: Conference key (URL-safe)
    typeOfSession: Type of session
"""
SESSIONS_BY_TYPE_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required = True),
    typeOfSession = messages.StringField(2, required = True)
)

"""Request for getting all sessions given by a speaker, across all conferences.

Attributes:
    speaker: Speaker name
"""
SESSIONS_BY_SPEAKER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    speaker = messages.StringField(1, required = True),
)

#-------------------------------------------------------------------------------

@endpoints.api(name='session', version='v1', audiences=[ANDROID_AUDIENCE],
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class SessionApi(remote.Service):
    """Session API v0.1"""

# - - - Sessions - - - - - - - - - - - - - - - - - - - -

    def _createSessionObject(self, request):
        """Create or update Session object, returning SessionForm/request."""
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # Trying to create a Key with an invalid value raises ProtocolBufferDecodeError.
        # Using from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
        # does not work, as a different ProtocolBufferDecodeError is raised.
        # See: https://github.com/googlecloudplatform/datastore-ndb-python/issues/143
        # Catching all exceptions for now...

        # get Session object from request; bail if not found
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # Copy SessionForm/ProtoRPC Message into dict
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        del data["websafeConferenceKey"] # keep only the session form

        # Allocate session ID and generate session key
        p_key = conference.key
        s_id = Conference.allocate_ids(size = 1, parent = p_key)[0]
        s_key = ndb.Key(Session, s_id, parent = p_key)
        data["key"] = s_key
        print "s_key:", s_key

        # Convert typeOfSession to string
        if data["typeOfSession"]:
            data["typeOfSession"] = str(data["typeOfSession"])

        # Create new session
        Session(**data).put()

        # Return form back
        form = SessionForm()
        for field in form.all_fields():
            if hasattr(request, field.name):
                setattr(form, field.name, getattr(request, field.name))
        return form

    @endpoints.method(SESSION_POST_REQUEST, SessionForm,
            path='conference/{websafeConferenceKey}/session',
            http_method='POST',
            name='createSession')
    def createSession(self, request):
        """Create new session."""
        return self._createSessionObject(request)


    @endpoints.method(SESSIONS_GET_REQUEST, SessionForms,
            path='conference/{websafeConferenceKey}/session',
            http_method='GET',
            name='getConferenceSessions')
    def getConferenceSessions(self, request):
        """Given a conference, return all sessions."""

        # get Session object from request; bail if not found
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # create ancestor query for all key matches for this conference
        sessions = Session.query(ancestor = conference.key)

        return SessionForms(
            items = [self._copySessionToForm(s) for s in sessions]
        )

    @endpoints.method(SESSIONS_BY_TYPE_GET_REQUEST, SessionForms,
            path='conference/{websafeConferenceKey}/session/{typeOfSession}',
            http_method='GET',
            name='getConferenceSessionsByType')
    def getConferenceSessionsByType(self, request):
        """Given a conference, return all sessions of a specified type
        (e.g. lecture, keynote, workshop).
        """

        # get Session object from request; bail if not found
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        query = Session.query(ancestor = conference.key)
        sessions = query.filter(Session.typeOfSession == request.typeOfSession)

        return SessionForms(
            items = [self._copySessionToForm(s) for s in sessions]
        )

    @endpoints.method(SESSIONS_BY_SPEAKER_GET_REQUEST, SessionForms,
            path='conference/session/{speaker}',
            http_method='GET',
            name='getSessionsBySpeaker')
    def getSessionsBySpeaker(self, request):
        """Given a speaker, return all sessions given by this particular speaker,
        across all conferences.
        """
        query = Session.query()
        sessions = query.filter(Session.speaker == request.speaker)

        return SessionForms(
            items = [self._copySessionToForm(s) for s in sessions]
        )


    def _copySessionToForm(self, session):
        """Copy relevant fields from Session to SessionForm."""
        form = SessionForm()
        for field in form.all_fields():
            if hasattr(session, field.name):
                if field.name == "typeOfSession":
                    # Convert session type string to Enum
                    if getattr(session, field.name):
                        setattr(form, field.name, getattr(SessionType, getattr(session, field.name)))
                elif field.name == "date":
                    # Convert Date to date string
                    setattr(form, field.name, str(getattr(session, field.name)))
                elif field.name == "startTime":
                    # Convert Time to time string
                    setattr(form, field.name, str(getattr(session, field.name)))
                else:
                    # Copy other fields
                    setattr(form, field.name, getattr(session, field.name))
        form.check_initialized()
        return form
