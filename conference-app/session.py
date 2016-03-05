from datetime import datetime

import endpoints
from protorpc import messages
from protorpc import remote

from google.appengine.ext import ndb

from models import Conference
from models import Session
from models import SessionForm

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

SESSION_POST_REQUEST = endpoints.ResourceContainer(
    SessionForm,
    websafeConferenceKey = messages.StringField(1),
)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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

    # createSession(SessionForm, websafeConferenceKey)
    @endpoints.method(SESSION_POST_REQUEST, SessionForm,
            path='conference/{websafeConferenceKey}/session',
            http_method='POST',
            name='createSession')
    def createSession(self, request):
        """Create new session."""
        return self._createSessionObject(request)
