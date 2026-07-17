from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SchoolInfo
from .forms import SchoolInfoForm
from accounts.views import prefet_required


@login_required
@prefet_required
def settings_view(request):
    info = SchoolInfo.get_info()
    form = SchoolInfoForm(request.POST or None, request.FILES or None, instance=info)
    if form.is_valid():
        form.save()
        messages.success(request, "Paramètres enregistrés.")
        return redirect('settings_view')
    return render(request, 'school_settings/settings.html', {'form': form, 'info': info})
