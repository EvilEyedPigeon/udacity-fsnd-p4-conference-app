import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from models import ConflictException
from models.speaker import Speaker
from models.speaker import SpeakerForm
from models.speaker import SpeakerForms

from settings import WEB_CLIENT_ID
from settings import ANDROID_CLIENT_ID
from settings import IOS_CLIENT_ID
from settings import ANDROID_AUDIENCE

EMAIL_SCOPE = endpoints.EMAIL_SCOPE
API_EXPLORER_CLIENT_ID = endpoints.API_EXPLORER_CLIENT_ID


@endpoints.api(name='speaker', version='v1', audiences=[ANDROID_AUDIENCE],
    allowed_client_ids=[WEB_CLIENT_ID, API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID],
    scopes=[EMAIL_SCOPE])
class SpeakerApi(remote.Service):
    """Speaker API v0.1"""

    # create speaker
    @endpoints.method(SpeakerForm, SpeakerForm,
            path = "speaker",
            http_method = "POST",
            name = "create")
    def createSpeaker(self, request):
        """Create new speaker."""
        return self._createSpeakerObject(request)

    # get list of speakers (with websafe key)
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


    def _createSpeakerObject(self, request):
        """Create Speaker object, returning SpeakerForm/request."""
        
        # Note: When creating a new speaker, the websafeKey in the form is ignored

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
