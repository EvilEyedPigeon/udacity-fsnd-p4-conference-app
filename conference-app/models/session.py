"""Conference session App Engine data & ProtoRPC models."""

from datetime import datetime

from protorpc import messages
from google.appengine.ext import ndb

from models.speaker import Speaker


#------ Model objects ---------------------------------------------------------

class SessionType(messages.Enum):
    """SessionType -- Session type enumeration value"""
    NOT_SPECIFIED = 1
    LECTURE = 2
    KEYNOTE = 3
    WORKSHOP = 4
    OTHER = 5

class Session(ndb.Model):
    """Session -- Session object"""
    name = ndb.StringProperty(required = True)
    typeOfSession = ndb.StringProperty(default = "NOT_SPECIFIED")
    speakerKey = ndb.KeyProperty(kind = Speaker)
    highlights = ndb.StringProperty(repeated = True)
    date = ndb.DateProperty()
    location = ndb.StringProperty()
    startTime = ndb.TimeProperty()
    duration = ndb.IntegerProperty() # in minutes

class SessionForm(messages.Message):
    """SessionForm -- Session outbound form message"""
    name = messages.StringField(1)
    typeOfSession = messages.EnumField("SessionType", 2)
    websafeSpeakerKey = messages.StringField(3)
    highlights = messages.StringField(4, repeated = True)
    date = messages.StringField(5)
    location = messages.StringField(6)
    startTime = messages.StringField(7)
    duration = messages.IntegerField(8, variant = messages.Variant.INT32) # in minutes
    websafeKey = messages.StringField(9)

class SessionForms(messages.Message):
    """SessionForms -- multiple Session outbound form message"""
    items = messages.MessageField(SessionForm, 1, repeated = True)


#------ Mapping functions -----------------------------------------------------

def _copySessionToForm(session):
    """Copy relevant fields from Session to SessionForm."""
    form = SessionForm()
    for field in form.all_fields():
        if field.name == "typeOfSession":
            # Convert session type string to Enum
            if getattr(session, field.name):
                setattr(form, field.name, getattr(SessionType, getattr(session, field.name)))
        elif field.name == "websafeSpeakerKey":
            # Set URL-safe key
            if getattr(session, "speakerKey"):
                setattr(form, field.name, getattr(session, "speakerKey").urlsafe())
        elif field.name == "date":
            # Convert Date to string
            if getattr(session, field.name):
                setattr(form, field.name, str(getattr(session, field.name)))
        elif field.name == "startTime":
            # Convert Time to string
            if getattr(session, field.name):
                setattr(form, field.name, str(getattr(session, field.name)))
        elif field.name == "websafeKey":
            # Set URL-safe key
            if getattr(session, "key"):
                setattr(form, field.name, getattr(session, "key").urlsafe())
        elif hasattr(session, field.name):
            # Copy other fields
            if getattr(session, field.name):
                setattr(form, field.name, getattr(session, field.name))
    form.check_initialized()
    return form

def _copyFormToSession(request):
    """Copy relevant fields from SessionForm to Session."""
    session = Session()
    form = SessionForm()
    for field in form.all_fields():
        if field.name == "typeOfSession":
            # Convert Enum to string
            if getattr(request, field.name):
                setattr(session, field.name, str(getattr(request, field.name)))
        elif field.name == "websafeSpeakerKey":
            # Set key
            if getattr(request, field.name):
                setattr(session, "speakerKey", ndb.Key(urlsafe = getattr(request, field.name)))
        elif field.name == "date":
            # Convert string to Date
            if getattr(request, field.name):
                date_string = getattr(request, field.name)
                date = datetime.strptime(date_string, "%Y-%m-%d").date()
                setattr(session, field.name, date)
        elif field.name == "startTime":
            # Convert string to Time
            if getattr(request, field.name):
                time_string = getattr(request, field.name)
                time = datetime.strptime(time_string, "%H:%M:%S").time()
                setattr(session, field.name, time)
        elif field.name == "websafeKey":
            # Set key
            if getattr(request, field.name):
                setattr(session, "key", ndb.Key(urlsafe = getattr(request, field.name)))
        elif hasattr(session, field.name):
            # Copy other fields
            setattr(session, field.name, getattr(request, field.name))
    return session

#------------------------------------------------------------------------------
