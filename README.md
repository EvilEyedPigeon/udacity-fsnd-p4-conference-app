Project 4: Conference Organization App
======================================

This project is a simple API for a conference organization app, created using
[Google App Engine](https://cloud.google.com/appengine/docs) and Python
as part of Udacity's Full-Stack Web Developer Nanodegree.

Starting app included functionality related to conferences and user profiles:
creating and updating conferences, querying conferences creating a profile,
and registering for conferences. 

For this project, additional functionality has been added for handling
conference sessions and speakers, and user wish lists.

Starting code cloned from https://github.com/udacity/ud858


Overall structure
-----------------

Most of the original code is left untouched, except mainly for breaking it into
a couple of files to organize things better.

Model objects and forms are now in the ```models``` package, and api classes
are in the ```api``` package, with modules for different things such as sessions,
speakers, and wish lists.

Also, the actual implementations of the services are in the ```services```
package, so the enpoint methods just delegate to those internal services.
Some more work can be done here to make the separation better. Especially
when considering the parameters that the services should receive.

Another thing to consider is having a unified API. For the project submission
there are actually multiple APIs for handling conferences, sessions, speakers,
and wish lists. This is in part because the naming convention required by the
project for the API methods makes it hard to find related methods when all the
methods are listed together.


Task 1: Add Sessions to a Conference
------------------------------------

The original API allowed creating conferences, but there was no concept
of session. So the first task was to add sessions and speakers.

Sessions have several properties such as name, highlights, speaker, etc.
They are part of a conference, so each session is a child of the conference
it belongs to. The details of the properties may be refined (for example,
parsing of dates at times which only allow ```%Y-%m-%d``` and ```%H:%M:%S```
formats), but I got to play with different types, such as enums, strings,
dates, keys, and repeated properties.

Just like sessions, speakers are also entities. However, the same speaker
can present at different conferences, so they have no parent. For now the
speakers are kept simple, with only a name and email, but being an entity
it could easily be expanded to have more fields and related functionality.

To associate a speaker with a session, each session entity can have
a speaker key. This key is optional and only one speaker is allowed
per session. Changing these things would be easy if necessary, but I
preffered to keep things simple for now.

One possibility I considered was having a speaker be a child of a user
profile entity. In that case, a speaker would have to be registered and
may have to have a Google account. A problem with this is that some
speakers may not want to register, and also the conference organizers
may want to define everything even if speakers do not have a profile.
In the future, I would think that associating a speaker with a profile
as a better option.

Required API methods (in ```session``` module):

- getConferenceSessions(websafeConferenceKey)
- getConferenceSessionsByType(websafeConferenceKey, typeOfSession)
- getSessionsBySpeaker(websafeSpeakerKey)
- createSession(SessionForm, websafeConferenceKey)

Other API methods (in ```speaker``` module):

- createSpeaker(SpeakerForm): Create a new speaker.
- getSpeakers(): Get list of all speakers.


Task 2: Add Sessions to User Wishlist
-------------------------------------

Wishlists are stored as entities with a user Profile as the parent.
They store a list of Session keys.

It is common for users to want to go to a conference before registering,
users can add any session to their wish list, even if they are not registered
for the conference. 

For the moment, it is also possible to add sessions that have already passed.
Should this be allowed? It is possible that users will want to see info about
past sessions, especially if more things are added later, like for example,
notes about the session or video recordings. Then the wishlist would be more
like a list of favorites than an actual "wish" list.

Required API methods (in ```wishlist``` module):

- addSessionToWishlist(websafeSessionKey)
- deleteSessionInWishlist(websafeSessionKey)
- getSessionsInWishlist()


Task 3: Work on Indexes and Queries
-----------------------------------

### Two additional queries

Given a conference, there were already queries for getting all sessions and sessions by type,
but there are no queries for getting speakers. The only query related to speakers so far is
for getting all sessions by a speaker, accross all conferences.

A user may be interested in all sessions accross all conferences for a given speaker,
but when looking at (or attending) a specific conference, users may be interested on
things for that conference only.

Additional queries (in ```speaker``` module):

- getConferenceSpeakers(websafeConferenceKey): Given a conference, get the list of all speakers.
- getSessionsByConferenceSpeaker(websafeSpeakerKey, websafeConferenceKey): Given a speaker and a conference, return all sessions given by the speaker at the conference.

### Query related problem

*Let’s say that you don't like workshops and you don't like sessions after 7 pm.
How would you handle a query for all non-workshop sessions before 7 pm? 
What is the problem for implementing this query? What ways to solve it did you think of?*

The problem with this query is that it requires two inequality filters,
which is not supported by the NDB Datastore.

One possibility is to query using one inequality filter for the time,
and use the IN operator to search for a session type in a list including
all types except for workshops.

Another possibility is to filter by time or type after doing the query.
This would be easy, but may be memory intensive and slower. 

For fun, there is an (experimental) query method that received a list of filters.
It uses all equality filters and inequality filters for at most one field
when querying the NDB Datastore. Then, it applies other inequality filters
in memory. For now, it can only receive filters for the session type
and the start time, since querying any number of fields requires too
many indices.

API method (in ```session``` module):

- querySessions(QueryForms)


To query for all non-workshop sessions before 7 pm, pass the following filters:
```
{
  "filters": 
  [
    {
      "field": "TYPE",
      "operator": "NE",
      "value": "WORKSHOP"
    },
    {
      "field": "TIME",
      "operator": "LT",
      "value": "19:00:00"
    }
  ]
}
```


Task 4: Add a Task
------------------

*When a new session is added to a conference, check the speaker. If there is more than one session
by this speaker at this conference, also add a new Memcache entry that features the speaker and
session names. You can choose the Memcache key. The logic above should be handled using
App Engine's Task Queue.*

Required API methods (in ```speaker``` module):

- getFeaturedSpeaker()


Usage
-----

1) Clone the project (if you don't have git, you may download the project from github).
```
$ git clone git@github.com:pt314/udacity-fsnd-p4-conference-app.git
```

2) Download and install the [Google App Engine SDK for Python](https://cloud.google.com/appengine/downloads).

3) Run the App Engine Launcher and add application.

4) Create [App Engine project](https://console.cloud.google.com/) with your own ID.

5) Update the value of `application` in `app.yaml` to the app ID you have registered
   in the App Engine admin console.

6) Update the values at the top of `settings.py` to reflect the respective
   client IDs you have registered in the [Developer Console](https://console.developers.google.com/).

7) Update the value of CLIENT_ID in `static/js/app.js` to the Web client ID.

8) (Optional) Mark the configuration files as unchanged as follows:
```
$ git update-index --assume-unchanged app.yaml settings.py static/js/app.js
```

9) Deploy to App Engine and test API with the API explorer.


TODO
----

- Change code to use Python coding conventions everywhere.
- Consider combining into a single API.
- Do better input validation.
- Cleanup original conference API code (original code is mostly untouched).
- Finish generic query method that receives any list of filters, and applies
  inequality filters in memory if necessary (mostly done, will add later).
- Play with the UI.
