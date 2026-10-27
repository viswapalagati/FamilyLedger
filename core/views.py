"""core views — SKELETON.

``HomeView`` (route ``/``, name ``home``): send authenticated users to the
dashboard overview and anonymous users to the login page (§13, §9.3).
"""

from django.views.generic import RedirectView
from django.contrib.auth.views import redirect_to_login


class HomeView(RedirectView):
    """Redirect ``/`` to the dashboard (or login when signed out)."""
    permanent = False
    print("home")
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            print("authenticated-------------------------------", self.request.user)
            return "/dashboard/"
        return None 


    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            print("not authenticated")
            return redirect_to_login(request.get_full_path(), login_url="/accounts/login/")
        return super().get(request, *args, **kwargs)
        

    # TODO: implement get(); redirect to "dashboard:overview" or the login page.
