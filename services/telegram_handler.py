def telegram_handler(request):
    return {
        "data": request,
        "meta": {
            "code": "ok",
            "message": "OK"
        }
    }