============
Introduction
============

An alternative concordancer front end to the `Manatee
<https://nlp.fi.muni.cz/trac/noske>`_ corpus engine.

============
Installation
============

To be frank, this is really an abandoned experiment with very bare
features, kind of wobbly in places. I've come to know Python much better
since then. Still, for the purpose of nostalgic reminiscing, I've put
together a `Dockerfile`, so that I can run it from time to time :) So if
you want to try it out, install Docker for your platform, and then:

```sh
git clone https://github.com/dlukes/marlin.git
cd marlin
# at this point, put a file named `vertikala` inside the directory,
# containing your corpus in the CWB/SketchEngine vertical format, and a
# file named `test`, containing the SketchEngine configuration file
# for the corpus
doker build -t marlin .
docker run -p 1993:1993 marlin
```

Then visit `<http://localhost:1993>`_ in your favorite browser.

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

=======
Credits
=======

Icons are by `Glyphicons <http://glyphicons.com/>`_.

=======
License
=======

Copyright © 2016 `ÚČNK <http://korpus.cz>`_/David Lukeš

Distributed under the `GNU General Public License v3
<http://www.gnu.org/licenses/gpl-3.0.en.html>`_.
