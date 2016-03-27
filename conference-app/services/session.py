import endpoints
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import ndb

from models.conference import Conference
from models.session import Session
from models.session import SessionForm
from models.session import SessionForms
from services import BaseService
from services import login_required


class SessionService(BaseService):
    """Session Service v0.1"""

    @login_required
    def create_session(self, websafe_conference_key, request):
        """Create new session. Open only to the organizer of the conference.

        Args:
            websafe_conference_key (string)
            request (SessionForm)

        Returns:
            SessionForm updated with the new object's key

        Raises:
            endpoints.ForbiddenException if the user is not the conference owner
        """
        # Get Conference object
        conference = self.get_conference(websafe_conference_key)

        # Verify that the user is the conference organizer
        user_id = self.get_user_id()
        if user_id != conference.organizerUserId:
            raise endpoints.ForbiddenException(
                'Only the owner can update the conference.')

        # Allocate session ID and generate session key
        p_key = conference.key
        s_id = Conference.allocate_ids(size = 1, parent = p_key)[0]
        s_key = ndb.Key(Session, s_id, parent = p_key)

        # Create and store new session object
        session = Session.to_object(request)
        session.key = s_key # set the key since this is a new object
        session.put()

        # Check for featured speakers - delegate to a task
        if session.speakerKey:
            taskqueue.add(
                params={'websafeSpeakerKey': session.speakerKey.urlsafe(),
                        'websafeConferenceKey': conference.key.urlsafe()},
                url='/tasks/set_feature_speaker'
            )

        # Return form back
        return session.to_form()

    def get_conference_sessions(self, websafe_conference_key):
        """Given a conference, return all sessions.

        Args:
            websafe_conference_key (string)

        Returns:
            SessionForms
        """
        # Get Conference object
        conference = self.get_conference(websafe_conference_key)

        # Query sessions by ancestor conference
        sessions = Session.query(ancestor = conference.key)

        return SessionForms(
            items = [s.to_form() for s in sessions]
        )

    def get_conference_sessions_by_type(self, websafe_conference_key, type_of_session):
        """Given a conference, return all sessions of a specified type
        (e.g. lecture, keynote, workshop).

        Args:
            websafe_conference_key (string)
            type_of_session (string)

        Returns:
            SessionForms
        """
        # Get Conference object
        conference = self.get_conference(websafe_conference_key)

        # Query sessions by ancestor and type property
        query = Session.query(ancestor = conference.key)
        sessions = query.filter(Session.typeOfSession == type_of_session)

        return SessionForms(
            items = [s.to_form() for s in sessions]
        )

    def get_sessions_by_speaker(self, websafe_speaker_key):
        """Given a speaker, return all sessions given by this particular speaker,
        across all conferences.

        Args:
            websafe_speaker_key (string)

        Returns:
            SessionForms
        """
        # Get Speaker object
        speaker = self.get_speaker(websafe_speaker_key)

        # Query sessions by speaker key property
        query = Session.query()
        sessions = query.filter(Session.speakerKey == speaker.key)

        return SessionForms(
            items = [s.to_form() for s in sessions]
        )
