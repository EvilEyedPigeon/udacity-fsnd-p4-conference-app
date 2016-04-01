import logging as log
from datetime import datetime

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

from models import QUERY_OPERATORS
from models import OPERATOR_LOOKUP
from models import QueryForms
from models.session import QUERY_FIELDS


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

    # Experimental. Just playing with queries using filters...
    def query_sessions(self, request):
        """Query for sessions.

        This uses some filters to query the NDB Datastore, and applies
        other filters in memory. An arbitrary list of filters can be
        passed in, but the query won't work if the required indices
        for the query sent to NDB have not been created.

        Args:
            request (QueryForms):
                List of filters.

        Each filter has:
            - field: one of
                "TYPE" (type of session),
                "TIME" (in "HH:MM:SS" format)
            - operator: one of
                "EQ" (=),
                "GT" (>),
                "GTEQ" (>=),
                "LT" (<),
                "LTEQ" (<=),
                "NE" (!=)
            - value: the desired value to compare with

        Returns:
            SessionForms: List of sessions matching all the filters.
        """
        # Run query with filters applied in memory if necessary
        plain_query = Session.query()
        sessions = self._generic_query(plain_query, request.filters, QUERY_FIELDS)

        return SessionForms(
            items = [s.to_form() for s in sessions]
        )

    def _generic_query(self, plain_query, filters, QUERY_FIELDS):
        """Return query results with applied filters.

        All equality filters and inequality filters for at most one field are used
        when querying NDB. Then any remaining inequality filters are automatically
        applied in memory.

        Note that this is convenient, but may not always be the best. It depends
        on how many results are expected, and on the amount of resources (such as
        memory) available.

        Does not handle sorting.

        Args:
            plain_query:
                Base query without any filters.
            filters:
                List of filters, each one with field, operator, and value.
            QUERY_FIELDS:
                Mapping from constants passed to QueryForm, to actual field names

        Returns:
            Results of executing the query and applying all the filters.
        """

        # Start without filters
        q = plain_query 

        # Parse filters
        equality_filters, inequality_filters, inequality_fields = self._format_filters(filters, QUERY_FIELDS)

        # Equality filters don't cause conflicts, so add them all
        for filtr in equality_filters:
            formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
            q = q.filter(formatted_query)

        # A single field with inequality filters is not a problem either
        # Include filters for the first field with inequalities filters
        if (len(inequality_fields) > 0):
            # Remove field and corresponding filters so they are not considered later
            field = inequality_fields.pop()
            filters = inequality_filters[field]
            del inequality_filters[field]
            for filtr in filters:
                formatted_query = ndb.query.FilterNode(filtr["field"], filtr["operator"], filtr["value"])
                q = q.filter(formatted_query)
        
        # Fetch results from NDB
        results = q.fetch()

        # Parse filters and convert string values to field types
        # TODO: This is specific to sessions, so it should be done
        #       outside to make the query code trully generic.
        for field in inequality_fields:
            filters = inequality_filters[field]
            for filtr in filters:
                if filtr["field"] == "date":
                    filtr["value"] = datetime.strptime(filtr["value"], "%Y-%m-%d").date()
                elif filtr["field"] == "startTime":
                    filtr["value"] = datetime.strptime(filtr["value"], "%H:%M:%S").time()

        # If there are more fields with inequality filters, apply filters in memory
        if (len(inequality_fields) > 0):
            filtered_results = []

            log.info("In memory filtering: " + str(inequality_fields))

            # TODO: this can be simplified, and done more compactly
            for result in results:
                keep_it = True
                for field in inequality_fields:
                    filters = inequality_filters[field]
                    for filtr in filters:
                        obj_value = getattr(result, filtr["field"])
                        op = OPERATOR_LOOKUP[filtr["operator"]]

                        # Ignore if value is None and operator is not = or !=
                        # (cannot compare None with <, <=, >, or >=)
                        if not obj_value and not filtr["operator"] in ["=", "!="]:
                            keep_it = False
                            break

                        # Ignore if applying operator returns False
                        if not op(obj_value, filtr["value"]):
                            keep_it = False
                            break

                # Result passed all the filters, so keep it
                if keep_it:
                    filtered_results.append(result)

            results = filtered_results

        return results

    def _format_filters(self, filters, QUERY_FIELDS):
        """Parse, check validity and format user supplied filters.

        Returns:
            equality_filters (list):
                All equality filters
            inequality_filters (map):
                Map with key = field, and value = list of filters for that field
            inequality_fields (set):
                Set of fields with at least one inequality filter
        """
        equality_filters = []
        inequality_filters = {}
        inequality_fields = set([])

        for f in filters:
            filtr = {field.name: getattr(f, field.name) for field in f.all_fields()}

            # Get the real fields and operators
            try:
                filtr["field"] = QUERY_FIELDS[filtr["field"]]
                filtr["operator"] = QUERY_OPERATORS[filtr["operator"]]
            except KeyError:
                raise endpoints.BadRequestException("Filter contains invalid field or operator.")

            # Every operation except "=" is an inequality
            if filtr["operator"] != "=":
                f = filtr["field"]
                inequality_fields.add(f)
                if f not in inequality_filters:
                    inequality_filters[f] = []
                inequality_filters[f].append(filtr)
            else:
                equality_filters.append(filtr)

        return (equality_filters, inequality_filters, inequality_fields)
