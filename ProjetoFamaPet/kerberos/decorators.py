from django.contrib.auth.decorators import user_passes_test


def administrador_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_administrador,
        login_url="login",
    )(view_func)


def operador_required(view_func):
    return user_passes_test(
        lambda user: user.is_authenticated and user.is_staff,
        login_url="login",
    )(view_func)