from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('',
    url(
        r'^$',
        'django.views.generic.simple.direct_to_template',
        {
            'template':'base.html', 
        },
        name='home'
    ),
    url(
        r'^server-busy/$',
        'django.views.generic.simple.direct_to_template',
        {
            'template':'scaler/server_busy.html', 
        },
        name='server-busy'
    ),
)
