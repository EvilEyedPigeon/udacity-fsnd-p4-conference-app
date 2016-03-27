import endpoints
from functools import wraps
from google.appengine.ext import ndb

from utils import getUserId


#------ Base service ----------------------------------------------------------

class BaseService(object):
    """Base service with basic functionality for other services.

    Includes methods to get the current user and user id, as well as basic
    method for getting other objects, such as conferences and speakers.
    
    Note that when using subclasses of this service it is not necessary
    to pass the current user to the service methods.
    """

    def get_user(self):
        """Get current user."""
        return endpoints.get_current_user()

    def get_user_id(self):
        """Get current user's ID."""
        return getUserId(self.get_user())

    def get_conference(self, websafe_conference_key):
        """Get conference, given a key.

        Args:
            websafe_conference_key (string)

        Raises:
            endpoints.NotFoundException
        """
        # Trying to create a Key with an invalid value raises ProtocolBufferDecodeError.
        # Using from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
        # does not work, as a different ProtocolBufferDecodeError is raised.
        # See: https://github.com/googlecloudplatform/datastore-ndb-python/issues/143
        # Catching all exceptions for now...
        try:
            conference = ndb.Key(urlsafe = websafe_conference_key).get()
        except:
            conference = None
        if not conference:
            raise endpoints.NotFoundException(
                'No conference found with key: %s' % websafe_conference_key)
        return conference

    def get_speaker(self, websafe_speaker_key):
        """Get skeaper, given a key.

        Args:
            websafe_speaker_key (string)

        Raises:
            endpoints.NotFoundException
        """
        # See comment about exceptions in get_conference method
        try:
            speaker = ndb.Key(urlsafe = websafe_speaker_key).get()
        except:
            speaker = None
        if not speaker:
            raise endpoints.NotFoundException(
                'No speaker found with key: %s' % websafe_speaker_key)
        return speaker


#------ Utility functions -----------------------------------------------------

def login_required(func):
    """Decorates a method to ensure that only logged in users can access it.

    Raises:
        endpoints.UnauthorizedException
    """
    @wraps(func)
    def login_required_method(*args, **kargs):
        user = endpoints.get_current_user()
        if not user:
            raise endpoints.UnauthorizedException("Authorization required")
        return func(*args, **kargs)

    return login_required_method

#------------------------------------------------------------------------------
