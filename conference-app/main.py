#!/usr/bin/env python

"""
main.py -- Udacity conference server-side Python App Engine
    HTTP controller handlers for memcache & task queue access

$Id$

created by wesc on 2014 may 24

"""

__author__ = 'wesc+api@google.com (Wesley Chun)'

import webapp2
from google.appengine.api import app_identity
from google.appengine.api import mail
from api.conference import ConferenceApi
from api.speaker import SpeakerApi


class SendConfirmationEmailHandler(webapp2.RequestHandler):
    def post(self):
        """Send email confirming Conference creation."""
        mail.send_mail(
            'noreply@%s.appspotmail.com' % (
                app_identity.get_application_id()),     # from
            self.request.get('email'),                  # to
            'You created a new Conference!',            # subj
            'Hi, you have created a following '         # body
            'conference:\r\n\r\n%s' % self.request.get(
                'conferenceInfo')
        )


class SetAnnouncementHandler(webapp2.RequestHandler):
    def get(self):
        """Set Announcement in Memcache."""
        ConferenceApi._cacheAnnouncement()
        self.response.set_status(204)


class SetFeatureSpeakerHandler(webapp2.RequestHandler):
    def post(self):
        """Set featured speaker announcement in Memcache."""
        speaker_key = self.request.get("websafeSpeakerKey")
        conference_key = self.request.get("websafeConferenceKey")
        SpeakerApi._cache_featured_speaker(speaker_key, conference_key)
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/tasks/send_confirmation_email', SendConfirmationEmailHandler),
    ('/crons/set_announcement', SetAnnouncementHandler),
    ('/tasks/set_feature_speaker', SetFeatureSpeakerHandler),
], debug=True)
