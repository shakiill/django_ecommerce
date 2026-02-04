from django.http import JsonResponse


class HandlePreflightMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the request method is OPTIONS (preflight request)
        if request.method == "OPTIONS":
            response = JsonResponse({"message": "Preflight OK"})
            response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = (
                "content-type, authorization, tenant, x-csrftoken"
            )
            response["Access-Control-Allow-Credentials"] = "true"
            return response

        # For non-OPTIONS requests, process normally
        return self.get_response(request)
