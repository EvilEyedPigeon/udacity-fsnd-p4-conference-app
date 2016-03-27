import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from google.appengine.ext import ndb
from google.appengine.api import memcache

import settings
from models import ConflictException
from models import StringMessage
from models.conference import Conference
from models.speaker import Speaker
from models.speaker import SpeakerForm
from models.speaker import SpeakerForms
from models.session import Session
from models.session import SessionForms
from models.session import _copySessionToForm
from services.speaker import SpeakerService


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

@endpoints.api(name = "speaker", version = "v1",
    allowed_client_ids = settings.ALLOWED_CLIENT_IDS, 
    audiences = settings.AUDIENCES,
    scopes = settings.SCOPES)
class SpeakerApi(remote.Service):
    """Speaker API v0.1"""

    def __init__(self):
        self.speaker_service = SpeakerService()

    @endpoints.method(SpeakerForm, SpeakerForm,
            path = "speaker",
            http_method = "POST",
            name = "createSpeaker")
    def create_speaker(self, request):
        """Create new speaker."""
        return self.speaker_service.create_speaker(request)

    @endpoints.method(message_types.VoidMessage, SpeakerForms,
            path = "speaker",
            http_method = "GET",
            name = "getSpeakers")
    def get_speakers(self, request):
        """Get list of all speakers."""
        return self.speaker_service.get_speakers()

    @endpoints.method(SPEAKERS_BY_CONF_GET_REQUEST, SpeakerForms,
            path = "speaker/conference/{websafeConferenceKey}",
            http_method = "GET",
            name = "getConferenceSpeakers")
    def get_conference_speakers(self, request):
        """Given a conference, get the list of all speakers."""
        return self.speaker_service.get_conference_speakers(
            request.websafeConferenceKey)

    @endpoints.method(SESSIONS_BY_CONF_AND_SPEAKER_GET_REQUEST, SessionForms,
            path = "speaker/{websafeSpeakerKey}/conference/{websafeConferenceKey}",
            http_method = "GET",
            name = "getSessionsByConferenceSpeaker")
    def get_sessions_by_conference_speaker(self, request):
        """Given a speaker and a conference, return all sessions given by
        the speaker at the conference.
        """
        return self.speaker_service.get_sessions_by_conference_speaker(
            request.websafeSpeakerKey,
            request.websafeConferenceKey)

    @endpoints.method(message_types.VoidMessage, StringMessage,
            path='speaker/featured/get',
            http_method='GET',
            name='getFeaturedSpeaker')
    def get_featured_speaker(self, request):
        """Return featured speaker announcement from memcache."""
        return self.speaker_service.get_featured_speaker()

    @staticmethod
    def _cache_featured_speaker(websafe_speaker_key, websafe_conference_key):
        """Create featured speaker announcement & assign to memcache.

        Only adds an announcement if the speaker has more than one session
        by the speaker at the conference.
        """
        return SpeakerService._cache_featured_speaker(
            websafe_speaker_key,
            websafe_conference_key)
