"""Speaker App Engine data & ProtoRPC models."""

from protorpc import messages

from google.appengine.ext import ndb


#------ Model objects ---------------------------------------------------------

class Speaker(ndb.Model):
    """Speaker -- Speaker object"""
    name = ndb.StringProperty(required = True)
    email = ndb.StringProperty(required = True)

    def to_form(self):
        """Convert Speaker to SpeakerForm."""
        return _copy_speaker_to_form(self)

    @staticmethod
    def to_object(request):
        """Convert SpeakerForm/request to Speaker."""
        return _copy_form_to_speaker(request)

class SpeakerForm(messages.Message):
    """Speaker -- Speaker form message"""
    name = messages.StringField(1)
    email = messages.StringField(2)
    websafeKey = messages.StringField(3)

class SpeakerForms(messages.Message):
    """SpeakerForms -- multiple Speaker outbound form message"""
    items = messages.MessageField(SpeakerForm, 1, repeated = True)


#------ Mapping functions -----------------------------------------------------

def _copy_speaker_to_form(speaker):
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

def _copy_form_to_speaker(request):
    """Copy relevant fields from SpeakerForm/request to Speaker."""
    speaker = Speaker()
    form = SpeakerForm()
    for field in form.all_fields():
        if field.name == "websafeKey":
            # Set key
            if getattr(request, field.name):
                setattr(speaker, "key", ndb.Key(urlsafe = getattr(request, field.name)))
        elif hasattr(speaker, field.name):
            # Copy other fields
            setattr(speaker, field.name, getattr(request, field.name))
    return speaker

#------------------------------------------------------------------------------
