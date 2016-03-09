import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb
from google.appengine.api import memcache

from models import ConflictException
from models import StringMessage
from models.conference import Conference
from models.speaker import Speaker
from models.speaker import SpeakerForm
from models.speaker import SpeakerForms
from models.session import Session
from models.session import SessionForms
from models.session import _copySessionToForm

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID

MEMCACHE_FEATURED_SPEAKER_KEY = "MEMCACHE_FEATURED_SPEAKER_KEY"


#------ Request objects -------------------------------------------------------

SPEAKERS_BY_CONF_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeConferenceKey = messages.StringField(1, required = True),
)

SESSIONS_BY_CONF_AND_SPEAKER_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,
    websafeSpeakerKey = messages.StringField(1, required = True),
    websafeConferenceKey = messages.StringField(2, required = True),
)


#------ API methods ------------------------------------------------------------

@endpoints.api(name='speaker', version='v1', audiences=[ANDROID_AUDIENCE],
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class SpeakerApi(remote.Service):
    """Speaker API v0.1"""

    @endpoints.method(SpeakerForm, SpeakerForm,
            path = "speaker",
            http_method = "POST",
            name = "createSpeaker")
    def createSpeaker(self, request):
        """Create new speaker."""
        return self._createSpeakerObject(request)

    @endpoints.method(message_types.VoidMessage, SpeakerForms,
            path = "speaker",
            http_method = "GET",
            name = "getSpeakers")
    def getSpeakers(self, request):
        """Get list of all speakers."""
        speakers = Speaker.query().fetch()
        return SpeakerForms(
            items = [self._copySpeakerToForm(s) for s in speakers]
        )

    @endpoints.method(SPEAKERS_BY_CONF_GET_REQUEST, SpeakerForms,
            path = "speaker/conference/{websafeConferenceKey}",
            http_method = "GET",
            name = "getConferenceSpeakers")
    def getConferenceSpeakers(self, request):
        """Given a conference, get the list of all speakers."""

        # Get Conference object from request
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # Get all sessions for the conference
        sessions = Session.query(ancestor = conference.key).fetch()

        # Only use valid keys and ignore duplicates
        speaker_keys = set([s.speakerKey for s in sessions if s.speakerKey])

        # Get the speakers
        speakers = ndb.get_multi(speaker_keys)

        return SpeakerForms(
            items = [self._copySpeakerToForm(s) for s in speakers]
        )

    @endpoints.method(SESSIONS_BY_CONF_AND_SPEAKER_GET_REQUEST, SessionForms,
            path = "speaker/{websafeSpeakerKey}/conference/{websafeConferenceKey}",
            http_method = "GET",
            name = "getSessionsByConferenceSpeaker")
    def getSessionsByConferenceSpeaker(self, request):
        """Given a speaker and a conference, return all sessions given by
        the speaker at the conference.
        """

        # Get Speaker object from request
        try:
            speaker = ndb.Key(urlsafe = request.websafeSpeakerKey).get()
        except:
            speaker = None
        if not speaker:
            raise endpoints.NotFoundException(
                'No speaker found with key: %s' % request.websafeSpeakerKey)

        # Get Conference object from request
        try:
            conference = ndb.Key(urlsafe = request.websafeConferenceKey).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % request.websafeConferenceKey)

        # Load sessions
        query = Session.query(ancestor = conference.key)
        sessions = query.filter(Session.speakerKey == speaker.key)

        return SessionForms(
            items = [_copySessionToForm(s) for s in sessions]
        )


    def _createSpeakerObject(self, request):
        """Create Speaker object, returning SpeakerForm/request."""
        
        # Check user
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException('Authorization required')

        # Validate fields
        if not request.name:
            raise endpoints.BadRequestException("Speaker 'name' field required")
        if not request.email:
            raise endpoints.BadRequestException("Speaker 'email' field required")

        # Check that speaker with same email does not exist
        speaker = Speaker.query(Speaker.email == request.email).get()
        if speaker:
            raise ConflictException("Speaker already exists with email: %s" % request.email)

        # Create new speaker
        data = {field.name: getattr(request, field.name) for field in request.all_fields()}
        del data["websafeKey"]
        speaker = Speaker(**data) # TODO: add function to get form from request
        speaker_key = speaker.put()

        # Returm form back
        form = self._copySpeakerToForm(speaker)
        return form

    def _copySpeakerToForm(self, speaker):
        """Copy relevant fields from Speaker to SpeakerForm."""
        form = SpeakerForm()
        for field in form.all_fields():
            if field.name == "websafeKey":
                # Set URL-safe key
                setattr(form, field.name, speaker.key.urlsafe())
            elif hasattr(speaker, field.name):
                # Copy other fields
                setattr(form, field.name, getattr(speaker, field.name))
        form.check_initialized()
        return form


    @staticmethod
    def _cacheFeaturedSpeaker(websafeSpeakerKey, websafeConferenceKey):
        """Create featured speaker announcement & assign to memcache.

        Only adds an announcement if the speaker has more than one session
        by the speaker at the conference.
        """

        # Get speaker
        speaker = ndb.Key(urlsafe = websafeSpeakerKey).get()

        # Get conference
        conference = ndb.Key(urlsafe = websafeConferenceKey).get()

        # Get speaker sessions
        q = Session.query(ancestor = conference.key)
        sessions = q.filter(Session.speakerKey == speaker.key).fetch()

        # Only feature if the speaker has more than on session
        if len(sessions) > 1:
            announcement = "Featured speaker: " + speaker.name
            announcement += "\nSessions:"
            for s in  sessions:
                announcement += "\n- " + s.name
            memcache.set(MEMCACHE_FEATURED_SPEAKER_KEY, announcement)
        else:
            announcement = "Not a featured speaker..."
            memcache.set(MEMCACHE_FEATURED_SPEAKER_KEY, announcement)

        return announcement


    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='speaker/featured/get',
            http_method='GET',
            name='getFeaturedSpeaker')
    def getFeaturedSpeaker(self, request):
        """Return featured speaker announcement from memcache."""
        return StringMessage(data=memcache.get(MEMCACHE_FEATURED_SPEAKER_KEY) or "")
