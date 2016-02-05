============
Introduction
============

An alternative concordancer front end to the `Manatee
<https://nlp.fi.muni.cz/trac/noske>`_ corpus engine.

============
Installation
============

This is all highly experimental at the moment, so there's just a dev setup. Just
clone the repository, create a virtualenv (or not), then ``pip install -r
requirements.txt`` and ``python marlin.py``. You'll probably need to update some
config values for your own use case (the location of your ``MANATEE_REGISTRY``,
the path to the Python API module), but just follow the tracebacks.

Then visit `<http://localhost:1993>`_.

Tested on Python 2.7+.

========
Dev tips
========

Download the latest ``turbolinks.js`` from Rails' upstream Turbolinks GitHub
repository to get all the latest goodies (``autofocus`` working out of the box,
a loading bar for free, maybe more?).

====
Name
====

It's just a lousy pun on manatee -- manatees are sea mammals, marlins are one of
the fastest fish in the world. But you can make it stand for a backronym of
Manatee Access Reimplemented by a LINguist if you'd like :)
