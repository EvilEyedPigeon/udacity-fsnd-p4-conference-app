ud858
=====

Course code for Building Scalable Apps with Google App Engine in Python class


Project 4: Conference Organization App
======================================

Starting code cloned from https://github.com/udacity/ud858

Starting app included functionality related to conferences and user profiles:
creating a profile, creating and updating conferences, querying conferences,
and registering for conferences. 


Structure
=========

- Divided into multiple services.
  - May consider combining into a single API latter, even if implementation is broken down into multiple files.


Usage
=====

- Clone
- Set app ID
- Set client IDs
- Deploy
- Test with API explorer

TODO
====

- Change code to use Python coding conventions
- Keep websafe keys in forms??? 


Task 1: Add Sessions to a Conference
====================================

- Partly done. Needs to be completed and refined.
  - Make speakers an entity
  - Handle special cases
  - Organize


Task 2: Add Sessions to User Wishlist
=====================================

Wishlists are stored as entities with a user Profile as the parent.
They store a list of Session keys.

Users can add any session to their wish list, even if they are not registered
for the conference. It is common for users to want to go before registering.

For the moment, it is also possible to add sessions that have already passed.
Allow this? Users may still want to see info about past sessions, especially
if more things are added later, like for example, notes about the session or
video recordings. Then the wishlist would be more like a list of favorites
than an actual "whish" list.

- User can add session to wish list


Task 3: Work on Indexes and Queries
=====================================


Task 4: Add a Task
==================
