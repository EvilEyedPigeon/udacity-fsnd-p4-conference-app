"""Session App Engine data & ProtoRPC models."""

from protorpc import messages

from google.appengine.ext import ndb


class SessionType(messages.Enum):
    """SessionType -- Session type enumeration value"""
    NOT_SPECIFIED = 1
    PRESENTATION = 2
    OTHER = 3

class Session(ndb.Model):
    """Session -- Session object"""
    name = ndb.StringProperty()
    typeOfSession = ndb.StringProperty(default = "NOT_SPECIFIED")
    speaker = ndb.StringProperty()
    highlights = ndb.StringProperty(repeated = True)
    date = ndb.DateProperty()
    startTime = ndb.TimeProperty()
    duration = ndb.IntegerProperty() # in minutes

class SessionForm(messages.Message):
    """SessionForm -- Session outbound form message"""
    name = messages.StringField(1)
    typeOfSession = messages.EnumField("SessionType", 2)
    speaker = messages.StringField(3)
    highlights = messages.StringField(4, repeated = True)
    date = messages.StringField(5)
    startTime = messages.StringField(6)
    duration = messages.IntegerField(7, variant = messages.Variant.INT32) # in minutes

class SessionForms(messages.Message):
    """SessionForms -- multiple Session outbound form message"""
    items = messages.MessageField(SessionForm, 1, repeated = True)
