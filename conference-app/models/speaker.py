"""Speaker App Engine data & ProtoRPC models."""

from protorpc import messages

from google.appengine.ext import ndb


class Speaker(ndb.Model):
    """Speaker -- Speaker object"""
    name = ndb.StringProperty(required = True)
    email = ndb.StringProperty(required = True)

class SpeakerForm(messages.Message):
    """Speaker -- Speaker form message"""
    name = messages.StringField(1)
    email = messages.StringField(2)
    websafeKey = messages.StringField(3)

class SpeakerForms(messages.Message):
    """SpeakerForms -- multiple Speaker outbound form message"""
    items = messages.MessageField(SpeakerForm, 1, repeated = True)
