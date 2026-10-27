"""accounts views — SKELETON. Implement per §4.1, §4.3, §14.2, §15.

Routes (see accounts/urls.py, already wired):
  signup/         -> SignupView          (FR-1.*)
  login/          -> FamilyLoginView     (FR-3.1)
  profile/        -> ProfileView         (FR-3.5)
  profile/edit/   -> ProfileUpdateView   (FR-3.5)
The password change/reset routes use Django's built-in views (already wired).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.views.generic import FormView, TemplateView, UpdateView
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import EmailAuthenticationForm, ProfileForm, SignupForm  # noqa: F401


class SignupView(FormView):
    """Create a family (FR-1.*). Template: accounts/signup.html."""

    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("dashboard:overview")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:overview")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome to FamilyLedger, {user.get_short_name()}!")
        return super().form_valid(form)

    


    
    # TODO: success_url, dispatch() redirect if already authed, form_valid()
    #       (call form.save(), log the user in, redirect to the dashboard).


class FamilyLoginView(LoginView):
    """Email + password login (FR-3.1). Template: accounts/login.html."""

    template_name = "accounts/login.html"
    def get_success_url(self):
        return reverse_lazy("dashboard:overview")
    
    def get_form_class(self):
        return EmailAuthenticationForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "FamilyLedger Login"
        context['submit_label'] = "Log In"
        return context
    
    def form_valid(self, form):
        """Log the user in and redirect to the dashboard."""
        login(self.request, form.get_user())
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Add an error message and re-render the form."""
        messages.error(self.request, "Invalid email or password. Please try again.")
        return super().form_invalid(form)
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().post(request, *args, **kwargs)  
     
    def get_initial(self):
        initial = super().get_initial()
        initial['username'] = ''
        return initial
    
    def get_template_names(self):
        return [self.template_name]
    
    def get_form_kwargs(self):  
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request  # Pass the request to the form if needed
        return kwargs   
    
    def get_redirect_url(self):
        """Return the URL to redirect to after login."""
        return self.get_success_url()
    



class ProfileView(LoginRequiredMixin, TemplateView):
    """Show account + membership details (FR-3.5). Template: accounts/profile.html."""

    template_name = "accounts/profile.html"
    # TODO: add "member" (the request user's FamilyMember) to the context.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["member"] = self.request.user.family_member_or_none
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Edit first/last name + phone (FR-3.5). Template: core/object_form.html."""

    form_class = ProfileForm
    template_name = "core/object_form.html"
    success_url = reverse_lazy("accounts:profile")
    # TODO: get_object() -> self.request.user; success_url; object_form context
    #       keys (form_title, submit_label, cancel_url); form_valid() message.

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_title"] = "Edit profile"
        context["submit_label"] = "Save profile"
        context["cancel_url"] = self.success_url
        return context

    def form_valid(self, form):
        messages.success(self.request, "Profile updated.")
        return super().form_valid(form)
