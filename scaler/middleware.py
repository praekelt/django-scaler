import time

from django.http import HttpResponseRedirect
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.conf import settings

# In-memory caches are used since different processes do not necessarily
# exhibit the same response times, even though they may share a caching backend
# like memcached. We also don't have to be concerned with thread safety so no
# need to use LocMemCache.
_cache = {}
_request_response_times = {}

SERVER_BUSY_URL = reverse(
    settings.DJANGO_SCALER.get('server_busy_url_name', 'server-busy')
)


def redirect_n_slowest_dummy():
    return 0


def redirect_n_slowest_from_cache():
    """Simple retrieval from whatever cache is in use"""
    return cache.get('django_scaler_n_slowest')


def redirect_percentage_slowest_dummy():
    return 0


def redirect_percentage_slowest_from_cache():
    """Simple retrieval from whatever cache is in use"""
    return cache.get('django_scaler_percentage_slowest')


class ScalerMiddleware:
    """Add as the first middleware in your settings file"""

    def process_request(self, request):

        # Ajax requests are not subject to scaling. Busy page is exempt from
        # scaling.
        if request.is_ajax() or request.META['PATH_INFO'] == SERVER_BUSY_URL:
            return

        # If a n_slowest or percentage_slowest is provided then forcefully
        # redirect the n slowest or percentage_slowest requests. This allows
        # external processes to easily instruct us to scale back.
        n_slowest = settings.DJANGO_SCALER.get(
            'redirect_n_slowest_function', redirect_n_slowest_dummy
        )()
        percentage_slowest = settings.DJANGO_SCALER.get(
            'redirect_percentage_slowest_function',
            redirect_percentage_slowest_dummy
        )()
        if not request.is_ajax() and (n_slowest or percentage_slowest):
            # Sort by slowest reversed
            paths = sorted(
                _request_response_times,
                key=_request_response_times.__getitem__,
                reverse=True
            )
            if n_slowest:
                li = paths[:n_slowest]
                if request.META['PATH_INFO'] in li:
                    return HttpResponseRedirect(SERVER_BUSY_URL)
            if percentage_slowest:
                n = int(round(percentage_slowest / 100.0 * len(paths)))
                li = paths[:n]
                if request.META['PATH_INFO'] in li:
                    return HttpResponseRedirect(SERVER_BUSY_URL)

        # On to automatic redirection
        now = time.time()

        # Marker for process_response
        setattr(request, '_django_scaler_stamp', now)

        # Cache key uses path info
        prefix = request.META['PATH_INFO'] + '-scaler-'

        # Fetch values
        key_stamp = prefix + 'stamp'
        key_hits = prefix + 'hits'
        key_trend = prefix + 'trend'
        key_redir = prefix + 'redir'
        stamp = _cache.get(key_stamp, 0)
        hits = _cache.get(key_hits, 0)
        trend = _cache.get(key_trend, [])
        redir = _cache.get(key_redir, now)

        # Nothing to do if not enough hits yet
        if hits > settings.DJANGO_SCALER.get('trend_size', 100):
            avg = stamp * 1.0 / hits

            # Update request response times dictionary
            _request_response_times[request.META['PATH_INFO']] = avg

            # If trend is X slower than average then redirect, unless
            # enough time has passed to attempt processing.
            slow_threshold = settings.DJANGO_SCALER.get(
                'slow_threshold', 4.0
            )
            if sum(trend) * 1.0 / len(trend) > avg * slow_threshold:

                # Has enough time passed to allow the request?
                redirect_for = settings.DJANGO_SCALER.get(
                    'redirect_for', 60
                )
                if now - redir > redirect_for:
                    # Yes, enough time has passed

                    # Clear time of last redirect
                    try:
                        del _cache[key_redir]
                    except KeyError:
                        pass

                    # Clear trend since it currently stores slow response
                    # times. We want a fresh start.
                    _cache[key_trend] = []

                else:
                    # No, not enough time has passed. Keep redirecting.

                    # Remove marker so process_response does not store data
                    delattr(request, '_django_scaler_stamp')

                    # Set time of last redirect if it has not been set
                    _cache.setdefault(key_redir, now)

                    return HttpResponseRedirect(SERVER_BUSY_URL)

    def process_response(self, request, response):
        t = getattr(request, '_django_scaler_stamp', None)
        # Anything to do?
        if t is not None:
            # Diff in milliseconds
            diff = int((time.time() - t) * 1000)

            # Fetch values
            prefix = request.META['PATH_INFO'] + '-scaler-'
            key_stamp = prefix + 'stamp'
            key_hits = prefix + 'hits'
            key_trend = prefix + 'trend'
            stamp = _cache.get(key_stamp, 0)
            hits = _cache.get(key_hits, 0)
            trend = _cache.get(key_trend, [])

            # Set values
            _cache[key_stamp] = stamp + diff
            _cache[key_hits] = hits + 1
            trend_size = settings.DJANGO_SCALER.get('trend_size', 100)
            _cache[key_trend] = (trend + [diff])[-trend_size:]

        return response
