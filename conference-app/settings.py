#!/usr/bin/env python

"""settings.py

Udacity conference server-side Python App Engine app user settings

$Id$

created/forked from conference.py by wesc on 2014 may 24

"""
import endpoints

# Replace the following lines with client IDs obtained from the APIs
# Console or Cloud Console.
WEB_CLIENT_ID = 'replace with Web client ID'
ANDROID_CLIENT_ID = 'replace with Android client ID'
IOS_CLIENT_ID = 'replace with iOS client ID'
ANDROID_AUDIENCE = WEB_CLIENT_ID

# Default client IDs, audiences, and scopes for the APIs.
# Usually these do not have to be updated. Just set the client IDs above.
ALLOWED_CLIENT_IDS = [WEB_CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID, ANDROID_CLIENT_ID, IOS_CLIENT_ID]
AUDIENCES = [ANDROID_AUDIENCE]
SCOPES = [endpoints.EMAIL_SCOPE]
