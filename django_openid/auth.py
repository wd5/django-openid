from django.http import HttpResponseRedirect as Redirect
import consumer

class AuthConsumer(consumer.SessionConsumer):
    """
    An OpenID consumer endpoint that integrates with Django's auth system.
    Uses SessionConsumer rather than CookieConsumer because the auth system
    relies on sessions already.
    """
    after_login_redirect_url = '/'
    
    need_authenticated_user_message = 'You need to sign in with an ' \
        'existing user account to access this page.'
    
    def lookup_openid(self, request, identity_url):
        # Imports live inside this method so they won't get imported if you 
        # over-ride this in your own sub-class 
        from django.contrib.auth.models import User
        return list(
            User.objects.filter(openids__openid = identity_url).distinct()
        )
    
    def log_in_user(self, request, user, openid):
        from django.contrib.auth import login
        # Nasty but necessary - annotate user and pretend it was the regular 
        # auth backend. This is needed so django.contrib.auth.get_user works:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return self.on_login_complete(request, user, openid)
    
    def on_login_complete(self, request, user, openid):
        return Redirect(self.after_login_redirect_url)
    
    def already_logged_in(self, request, openid):
        return Redirect(self.after_login_redirect_url)
    
    def on_logged_in(self, request, openid, openid_response):
        # Do we recognise their OpenID?
        matches = self.lookup_openid(request, openid)
        # Are they logged in already?
        if request.user.is_authenticated():
            # Did we find their account already? If so, ignore login
            if request.user.id in [u.id for u in matches]:
                return self.already_logged_in(request, openid)
            else:
                # Offer to associate this OpenID with their account
                return self.show_associate(request, openid)
        if matches:
            # If there's only one match, log you in as that user
            if len(matches) == 1:
                self.log_in_user(request, matches[0], openid)
            # Otherwise, let them to pick which account they want to log in as
            else:
                return self.show_pick_account(request, openid)
        else:
            # Brand new OpenID; show them the registration screen
            return self.show_registration(request, openid)
    
    def show_associate(self, request, openid=None):
        "Screen that offers to associate an OpenID with a user's account"
        if not request.user.is_authenticated():
            return self.need_authenticated_user(request)
        
        if request.method == 'POST':
            assert False, 'Not yet implemented'
        else:
            return self.render(request, 'django_openid/associate.html', {
                'user': request.user,
                'specific_openid': openid,
                'openids': request.openids,
            })
    
    def need_authenticated_user(self, request):
        return self.show_error(self.need_authenticated_user_message)

            