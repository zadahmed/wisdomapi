Wikipedia tools (for Humans)
============================

.. image:: https://img.shields.io/pypi/v/wptools.svg
        :target: https://pypi.python.org/pypi/wptools/

.. image:: https://travis-ci.org/siznax/wptools.svg?branch=master
        :target: https://travis-ci.org/siznax/wptools

.. image:: https://coveralls.io/repos/github/siznax/wptools/badge.svg?branch=master
        :target: https://coveralls.io/github/siznax/wptools

Python and command-line MediaWiki access for Humans

- get page extracts, image, Infobox data, Wikidata, and more
- get a random page, category, or site
- get page statistics
- get category members
- get site info and stats
- get data in any language

This package is intended to make it as easy as possible to get data
from MediaWiki instances, expose more Wikidata, and extend Wikimedia
APIs just for kicks. We say "(for Humans)" because that is a goal_.
Questions, feedback, and especially contributions_ are welcome!


Install
-------

.. code-block:: bash

    $ pip install wptools
    ✨🦄✨


Example
-------

.. code-block:: python

    >>> import wptools


Get a page object:

.. code-block:: python

    >>> page = wptools.page('Gandhi')


Get `API:Query`_ data:

.. _`API:Query`: https://www.mediawiki.org/wiki/API:Query

.. code-block:: python

    >>> page.get_query()
    en.wikipedia.org (query) Gandhi
    en.wikipedia.org (imageinfo) File:Portrait Gandhi.jpg
    Mahatma Gandhi (en) data
    {
      aliases: <list(10)> M K Gandhi, Mohandas Gandhi, Bapu, Gandhi, M...
      assessments: <dict(10)> Pakistan, Alternative Views, South Afric...
      description: <str(67)> pre-eminent leader of Indian nationalism ...
      extext: <str(3077)> Mahātmā **Mohandas Karamchand Gandhi** ( ; H...
      extract: <str(3372)> <p>Mahātmā <b>Mohandas Karamchand Gandhi</b...
      image: <list(2)> {u'size': 2951123, 'kind': 'query-pageimage', u...
      label: Mahatma Gandhi
      length: 262,790
      links: <list(500)> 10 Janpath, 14th Dalai Lama, 1915 Singapore M...
      modified: <dict(1)> page
      pageid: 19379
      random: Salt
      redirected: <list(1)> {u'to': u'Mahatma Gandhi', u'from': u'Gandhi'}
      redirects: <list(53)> {u'ns': 0, u'pageid': 55342, u'title': u'M...
      requests: <list(2)> query, imageinfo
      title: Mahatma Gandhi
      url: https://en.wikipedia.org/wiki/Mahatma_Gandhi
      url_raw: https://en.wikipedia.org/wiki/Mahatma_Gandhi?action=raw
      watchers: 1,811
      wikibase: Q1001
      wikidata_url: https://www.wikidata.org/wiki/Q1001
    }


Get `API:Parse`_ data:

.. _`API:Parse`: https://www.mediawiki.org/wiki/API:Parse

.. code-block:: python

    >>> page.get_parse()
    en.wikipedia.org (parse) Gandhi
    en.wikipedia.org (imageinfo) File:MKGandhi.jpg
    Mahatma Gandhi (en) data
    {
      image: <list(1)> {u'size': 2951123, 'kind': 'parse-image', u'des...
      infobox: <dict(25)> known_for, other_names, image, signature, bi...
      iwlinks: <list(10)> https://biblio.wiki/wiki/Mohandas_K._Gandhi,...
      pageid: 19379
      parsetree: <str(331808)> <root><template><title>Redirect</title>...
      requests: <list(2)> parse, imageinfo
      title: Mahatma Gandhi
      wikibase: Q1001
      wikidata_url: https://www.wikidata.org/wiki/Q1001
      wikitext: <str(261349)> {{Redirect|Gandhi}}{{pp-move-indef}}{{pp...
    }


Get Wikidata_:

.. _Wikidata: https://www.wikidata.org/w/api.php

.. code-block:: python

    >>> page = wptools.page(wikibase='Q1001')
    >>> page.get_wikidata()
    www.wikidata.org (wikidata) Q1001
    www.wikidata.org (labels) Q1280678|P535|P434|Q1860|P3762|Q668|P12...
    www.wikidata.org (labels) P119|Q1930187|P691|P18|P19|P1066|P509|P...
    www.wikidata.org (labels) Q6512732|Q1568|P972|Q84|P1430|P31|Q2140...
    www.wikidata.org (labels) P1576|Q4964182|P1368|P140|Q22336956|P12...
    en.wikipedia.org (imageinfo) File:Portrait Gandhi.jpg
    Mahatma Gandhi (en) data
    {
      aliases: <list(10)> M K Gandhi, Mohandas Gandhi, Bapu, Gandhi, M...
      claims: <dict(113)> P646, P535, P906, P434, P648, P3762, P1711, ...
      description: <str(67)> pre-eminent leader of Indian nationalism ...
      image: <list(1)> {u'size': 2951123, 'kind': 'wikidata-image', u'...
      label: Mahatma Gandhi
      labels: <dict(171)> Q1280678, P535, Q131149, P434, Q1860, P3762,...
      modified: <dict(1)> wikidata
      requests: <list(6)> wikidata, labels, labels, labels, labels, im...
      title: Mahatma_Gandhi
      what: human
      wikibase: Q1001
      wikidata: <dict(112)> Geni.com profile ID (P2600), National Libr...
      wikidata_pageid: 1330
      wikidata_url: https://www.wikidata.org/wiki/Q1001
    }


Get RESTBase_ data:

.. _RESTBase: https://www.mediawiki.org/wiki/RESTBase

.. code-block:: python

    >>> page.get_restbase('/page/summary/')
    en.wikipedia.org (restbase) /page/summary/Gandhi
    Mahatma Gandhi (en) data
    {
      description: <str(67)> pre-eminent leader of Indian nationalism ...
      exhtml: <str(1168)> <p>Mahātmā <b>Mohandas Karamchand Gandhi</b>...
      exrest: <str(931)> Mahātmā Mohandas Karamchand Gandhi (; Hindust...
      image: <list(2)> {'kind': 'restbase-original', u'width': 2024, '...
      pageid: 19379
      requests: <list(1)> restbase
      title: Mahatma_Gandhi
      url: https://en.wikipedia.org/wiki/Gandhi
      url_raw: https://en.wikipedia.org/wiki/Gandhi?action=raw
    }


Get all the things (at once):

.. code-block:: python

    >>> page.get()
    en.wikipedia.org (query) Gandhi
    en.wikipedia.org (parse) 19379
    www.wikidata.org (wikidata) Q1001
    www.wikidata.org (labels) Q1280678|P535|P434|Q1860|P3762|Q668|P12...
    www.wikidata.org (labels) P119|Q1930187|P691|P18|P19|P1066|P509|P...
    www.wikidata.org (labels) Q6512732|Q1568|P972|Q84|P1430|P31|Q2140...
    www.wikidata.org (labels) P1576|Q4964182|P1368|P140|Q22336956|P12...
    en.wikipedia.org (restbase) /page/summary/Mahatma_Gandhi
    en.wikipedia.org (imageinfo) File:MKGandhi.jpg|File:Portrait Gandhi.jpg
    Mahatma Gandhi (en) data
    {
      aliases: <list(10)> M K Gandhi, Mohandas Gandhi, Bapu, Gandhi, M...
      assessments: <dict(10)> Pakistan, Alternative Views, South Afric...
      claims: <dict(113)> P646, P535, P906, P434, P648, P3762, P1711, ...
      description: <str(67)> pre-eminent leader of Indian nationalism ...
      exhtml: <str(1168)> <p>Mahātmā <b>Mohandas Karamchand Gandhi</b>...
      exrest: <str(931)> Mahātmā Mohandas Karamchand Gandhi (; Hindust...
      extext: <str(3077)> Mahātmā **Mohandas Karamchand Gandhi** ( ; H...
      extract: <str(3372)> <p>Mahātmā <b>Mohandas Karamchand Gandhi</b...
      image: <list(6)> {u'size': 2951123, 'kind': 'query-pageimage', u...
      infobox: <dict(25)> known_for, other_names, image, signature, bi...
      iwlinks: <list(10)> https://biblio.wiki/wiki/Mohandas_K._Gandhi,...
      label: Mahatma Gandhi
      labels: <dict(171)> Q1280678, P535, Q131149, P434, Q1860, P3762,...
      length: 262,790
      links: <list(500)> 10 Janpath, 14th Dalai Lama, 1915 Singapore M...
      modified: <dict(2)> wikidata, page
      pageid: 19379
      parsetree: <str(331808)> <root><template><title>Redirect</title>...
      random: Salt
      redirected: <list(1)> {u'to': u'Mahatma Gandhi', u'from': u'Gandhi'}
      redirects: <list(53)> {u'ns': 0, u'pageid': 55342, u'title': u'M...
      requests: <list(9)> query, parse, wikidata, labels, labels, labe...
      title: Mahatma_Gandhi
      url: https://en.wikipedia.org/wiki/Mahatma_Gandhi
      url_raw: https://en.wikipedia.org/wiki/Mahatma_Gandhi?action=raw
      watchers: 1,811
      what: human
      wikibase: Q1001
      wikidata: <dict(112)> Geni.com profile ID (P2600), National Libr...
      wikidata_pageid: 1330
      wikidata_url: https://www.wikidata.org/wiki/Q1001
      wikitext: <str(261349)> {{Redirect|Gandhi}}{{pp-move-indef}}{{pp...
    }


Get more (expensive) data:

.. code-block:: python

    >>> page.get_more()
    en.wikipedia.org (querymore) Gandhi
    Mahatma Gandhi (en) data
    {
      categories: <list(68)> Category:1869 births, Category:1948 death...
      contributors: 2,606
      files: <list(53)> File:Aum Om red.svg, File:Commons-logo.svg, Fi...
      languages: <list(168)> {u'lang': u'af', u'title': u'Mahatma Gand...
      pageid: 19379
      redirected: <list(1)> {u'to': u'Mahatma Gandhi', u'from': u'Gandhi'}
      requests: <list(1)> querymore
      title: Mahatma Gandhi
      views: 19,242
    }


Get data in `another language`_:

.. _`another language`: https://github.com/siznax/wptools/wiki/Language-Codes

.. code-block:: python

    >>> page = wptools.page(lang='zh')
    zh.wikipedia.org (random) 🍰
    哈莉特·塔布曼 (zh) data
    {
      pageid: 211070
      title: 哈莉特·塔布曼
    }


Get data from `another wiki`_:

.. _`another wiki`: https://meta.wikimedia.org/wiki/List_of_Wikipedias

.. code-block:: python

    >>> page = wptools.page(wiki='en.wikiquote.org')
    en.wikiquote.org (random) 🍪
    Malala_Yousafzai (en)
    {
      pageid: 146817
      title: Malala_Yousafzai
    }


Documentation
-------------

See our wiki_.


Please enjoy!


@siznax 👹


.. _contributions: https://github.com/siznax/wptools/blob/master/CONTRIBUTING.md
.. _goal: http://docs.python-requests.org/en/master/user/intro/
.. _wiki: https://github.com/siznax/wptools/wiki


.. :changelog:

Release History
---------------

0.4.17 (2018-08-16)
+++++++++++++++++++

* Support proxy authentication (#130)
* Support page links continuations (#129)
* Support alternate API endpoints (#127)
* Merged @mcepl update to package tests (#125)
* Put API warnings in data attribute (#120)
* Support getting backlinks w/continuations (#119, #122)
* Always respect silent flag (#118)
* Improved infobox parsing (#91, #109)
* Added image (license, assessment) metadata (#104, #105)
* Fixed Wikidata pageid, image bugs (#101, #102)
* Added support for category continuations, subcategories (#99)
* Merged @RobbieClarken fix for non-value Wikidata snaktypes (#98)
* Merged @seansay fix for deleted Wikidata item (#97)
* Fixed TypeError on Windows 10 (#95)
* Fixed RESTBase LookupError on slash titles (#94)
* Added boxterm param for more Infobox reach (#91)
* Improved stress tests, wptool CLI script output
* Fixed get_imageinfo() issue (#93)
* Getting ALL Wikidata (#56)
* Surfaced redirects, disambiguation links (#25)
* Increased test coverage to 95%, pylint score 10.0
* Added more page data, split off expensive queries
* Implemented basic category and site functionality
* Changed page._WIKIPROPS to wikidata.LABELS
* Refactored attributes to only cache, data, flags, params
* Unified Wikimedia APIs access pattern via wptools.core


0.3 (2017-08-13)
++++++++++++++++

* Implemented general RESTBase /page/ access (#67)
* Merged @rikima's contrib plus py3 patch (#66)
* Made page.info(), query(), response() methods useable
* Improved wiki documentation (see Actions, Attributes)


0.2.3 (2017-04-17)
++++++++++++++++++

* Merge @aplz improvement: fetch full lists in infobox values (#62)
* Put HTML extract with wikilinks into 'exhtml'
* Fix AttributeError bug (#47)
* Refactoring fixes


0.2 (2016-11-06)
++++++++++++++++++

* Many fixes/improvements with help of @seansay (thank you!)
* Raise LookupError on API missing page/title
* Consolidated images and caches
* Support get_query() by pageid
* Support proxy, timeout on all API entrypoints
* Support for language variants (e.g. variant='zh-cn')
* Support for non-https wikis via wiki='http://example.com'
* Automatically get_imageinfo() via MediaWiki API:Imageinfo
* moved NOTES.md to wiki


0.1.7 (2016-09-20)
++++++++++++++++++

* Minor fixes
* Provide local SSL certs with python-certifi
* Enabled extending Wikidata properties
* Improved cache checking


0.1.4 (2016-09-06)
++++++++++++++++++

* Python 3 support!
* Implemented get_claims()
* Patch get_rest() path, tests/test_advanced
* Implemented get_wikidata() by title, lang
* Geo coordinates Property:P625 from Wikidata
* Added RESTBase support, lead attribute
* Made wptools.page() the atomic object


0.1.0 (2016-08-25)
++++++++++++++++++

* Many fixes, enhancements.
* ONE CLI SCRIPT TO RULE THEM ALL: wptool.
* Much testing of random (title, lang, and wiki).
* Allow chaining get_s or just get().
* Enabled full-hydration from wikibase only.
* Block further requests on fatal error.
* Get 240x thumbnails instead of default 50x.
* Harmonized silent and verbose arguments.
* Mock-up tests/test_advanced.py.
* Made NOTES.md a knowledge base.
* Use _humans_ in README examples. ;-)


0.0.5 (2016-08-23)
++++++++++++++++++

* Major re-write.
* Exposed core.WPTools as entrypoint.
* Added get_parse(), get_query(), and get_wikidata().
* Added get(self) to query all APIs.
* Added show(self) method to display fetched attrs.
* Show instance attributes after each request.
* Ignore requests if attrs will not be updated.
* Enabled language support across APIs.
* Gets random article if no arguments.
* CLI scripts and tests disabled pending update.


0.0.4 (2016-08-16)
++++++++++++++++++

* Added wptools.lead.
* Added safe_exit() to CLI scripts.
* Removed a fair amount of unused code.


0.0.3 (2016-08-12)
++++++++++++++++++

* Implemented wptools.image choices.
* Added wptools.api to simplify python i/f and CLI scripts.
* Merged @0x9900's CLI dist fixes.
* A little more test coverage.
* Starting to look like a legit module.


0.0.1 (2015)
++++++++++++

* Still better than alternatives for working with articles.


0.0.0 (2012)
++++++++++++

* It seems to work!


