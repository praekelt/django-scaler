import time

from django.http import HttpResponseRedirect
from django.core.cache import cache
from django.conf import settings

# In-memory caches are used since different processes do not necessarily
# exhibit the same response times, even though they may share a caching backend
# like memcached. We also don't have to be concerned with thread safety so no 
# need to use LocMemCache.
_cache = {}
_request_response_times = {}


class ScalerMiddleware:
    """Add as the first middleware in your settings file"""

    def process_request(self, request):
       
        # If a scaler level key is present on the cache then forcefully
        # redirect the 'level' most expensive requests. This allows external
        # processes to easily instruct us to scale back.  xxx: abstract so we
        # can add more mechanisms
        level = cache.get('django_scaler_level')
        if not request.is_ajax() and level:
            # Sort by most expensive reversed
            li = sorted(
                _request_response_times, 
                key=_request_response_times.__getitem__, 
                reverse=True
            )[:level]
            if request.META['PATH_INFO'] in li:
                return HttpResponseRedirect('/coming-soon/')

        # Ajax requests are not subject to scaling. Busy page is exempt from 
        # scaling.
        if not request.is_ajax() and not request.META['PATH_INFO'].startswith('/coming-soon/'):
            print ""
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

            # Nothing to do if no hits yet
            if hits:
                avg = stamp * 1.0 / hits       

                # Update request response times dictionary
                _request_response_times[request.META['PATH_INFO']] = avg

                print "AVG: %s" % avg
                print "TREND: %s" % trend
                #avg = 10

                # If trend is 50% slower than average then redirect, unless 
                # enough time has passed to attempt processing.
                if sum(trend) * 1.0 / len(trend) > avg * 1.5:
                    print "REDIR: %s" % redir
                    
                    # Has enough time passed to allow the request?
                    if now - redir > 60:
                        # Yes, enough time has passed
                        print "ENOUGH"

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
                        print "REDIRECT"

                        # Remove marker so process_response does not store data
                        delattr(request, '_django_scaler_stamp')

                        # Set time of last redirect if it has not been set
                        _cache.setdefault(key_redir, now)

                        return HttpResponseRedirect('/coming-soon/')

    def process_response(self, request, response):
        print "RESPONSE"
        t = getattr(request, '_django_scaler_stamp', None)
        # Anything to do?
        if t is not None:
            # Diff in milliseconds
            diff = int((time.time() - t) * 1000)
            print "DIFF: %s" % diff

            # Fetch values
            prefix = request.META['PATH_INFO'] + '-scaler-'
            key_stamp = prefix + 'stamp'
            key_hits = prefix + 'hits'
            key_trend = prefix + 'trend'
            print _cache
            stamp = _cache.get(key_stamp, 0)
            hits = _cache.get(key_hits, 0)
            trend = _cache.get(key_trend, [])

            # Set values
            _cache[key_stamp] = stamp + diff
            _cache[key_hits] = hits + 1
            _cache[key_trend] = (trend + [diff])[-10:]

        return response
