Django Scaler
=============
**Degrade gracefully by automatically replacing heavy pages with static pages while a server is taking strain.**

.. contents:: Contents
    :depth: 5

Installation
------------

#. Install or add ``django-scaler`` to your Python path.

#. Add ``scaler`` to your ``INSTALLED_APPS`` setting.

#. Add ``scaler.middleware.ScalerMiddleware`` to the top of your ``MIDDLEWARE_CLASSES`` setting.

#. Add (r'^scaler/', include('scaler.urls')) to urlpatterns.

Overview
--------

Servers may at times get overloaded due to a variety of reasons. When that
happens you don't want expensive requests to bring down your entire site. The
site must redirect expensive requests to a "server busy" page while the server
is under load, and then automatically remove the redirects once the load has
dropped enough. 

`django-scaler` addresses this situation in two ways. Firstly, it knows which
requests to redirect by itself. Secondly, it can be instructed to redirect the
N most expensive requests. It stores response time data in in-memory caches
enabling it to make these decisions.

Usage
-----

Pasted from ``test_settings.py``::

    DJANGO_SCALER = { 
        'server_busy_url_name': 'server-busy',

        # How many response times to consider for an URL. A small value means slow
        # response times are quickly acted upon, but it may be overly aggressive. 
        # A large value means an URL must be slow for a number of requests before 
        # it is acted upon. The default is 100.
        'trend_size': 10,

        # How much slower than average the trend must be before redirection kicks
        # in. The default is 4.0.
        'slow_threshold': 2.0,

        # How many seconds to keep redirecting an URL before serving normally. The
        # default is 60.
        'redirect_for': 10,

        # A function that returns how many of the slowest URLs must be redirected.
        # Depending on the site, data and load on the server this may be a large
        # number. This allows external processes to instruct the middleware to
        # redirect. The default is 0.
        'redirect_n_slowest_function': lambda: 0
    }

