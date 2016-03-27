import endpoints
from google.appengine.api import memcache
from google.appengine.ext import ndb

from models import ConflictException
from models import StringMessage
from models.profile import Profile
from models.session import Session
from models.session import SessionForms
from models.session import _copySessionToForm
from models.speaker import Speaker
from models.speaker import SpeakerForm
from models.speaker import SpeakerForms
from services import BaseService
from services import login_required

MEMCACHE_FEATURED_SPEAKER_KEY = "MEMCACHE_FEATURED_SPEAKER_KEY"


class SpeakerService(BaseService):
    """Speaker Service v0.1"""

    @login_required
    def create_speaker(self, request):
        """Create new speaker.

        Args:
            request (SpeakerForm)

        Returns:
            SpeakerForm updated with the new object's key

        Raises:
            endpoints.BadRequestException if the speaker info is invalid
            models.ConflictException if a speaker with same email already exists
        """
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
        form = self._copy_speaker_to_form(speaker)
        return form

    def get_speakers(self):
        """Get list of all speakers.

        Returns:
            SpeakerForms
        """
        speakers = Speaker.query().fetch()
        return SpeakerForms(
            items = [self._copy_speaker_to_form(s) for s in speakers]
        )

    def get_conference_speakers(self, websafe_conference_key):
        """Given a conference, get the list of all speakers.

        Args:
            websafe_conference_key (string)

        Returns:
            SpeakerForms
        """
        # Get Conference object
        conference = self.get_conference(websafe_conference_key)

        # Get all sessions for the conference
        sessions = Session.query(ancestor = conference.key).fetch()

        # Only use valid keys and ignore duplicates
        speaker_keys = set([s.speakerKey for s in sessions if s.speakerKey])

        # Get the speakers
        speakers = ndb.get_multi(speaker_keys)

        return SpeakerForms(
            items = [self._copy_speaker_to_form(s) for s in speakers]
        )

    def get_sessions_by_conference_speaker(self, websafe_speaker_key, websafe_conference_key):
        """Given a speaker and a conference, return all sessions given by
        the speaker at the conference.

        Args:
            websafe_speaker_key (string)
            websafe_conference_key (string)

        Returns:
            SessionForms
        """
        # Get Speaker object
        speaker = self.get_speaker(websafe_speaker_key)

        # Get Conference object
        conference = self.get_conference(websafe_conference_key)

        # Load sessions
        query = Session.query(ancestor = conference.key)
        sessions = query.filter(Session.speakerKey == speaker.key)

        return SessionForms(
            items = [_copySessionToForm(s) for s in sessions]
        )

    def get_featured_speaker(self):
        """Return featured speaker announcement from memcache.

        Returns:
            Announcement message (string)
        """
        return StringMessage(data = memcache.get(MEMCACHE_FEATURED_SPEAKER_KEY) or "")

    @staticmethod
    def _cache_featured_speaker(websafe_speaker_key, websafe_conference_key):
        """Create featured speaker announcement & assign to memcache.

        Only adds an announcement if the speaker has more than one session
        by the speaker at the conference.

        Args:
            websafe_speaker_key (string)
            websafe_conference_key (string)

        Returns:
            Announcement message (string)
        """
        # Get speaker
        speaker = ndb.Key(urlsafe = websafe_speaker_key).get()

        # Get conferenc e
        conference = ndb.Key(urlsafe = websafe_conference_key).get()

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
            # TODO: For a real app, do not replace the previous speaker with this
            announcement = "Not a featured speaker..."
            memcache.set(MEMCACHE_FEATURED_SPEAKER_KEY, announcement)

        return announcement

    def _copy_speaker_to_form(self, speaker):
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
