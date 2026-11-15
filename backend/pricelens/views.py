from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        "project": "PriceLens AI",
        "status": "running",
        "backend": "Django REST Framework"
    }, status=200)
