# # custom_admin/mixins.py
# import logging
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from rest_framework.exceptions import AuthenticationFailed
# from django.shortcuts import redirect
# from django.urls import reverse
# from django.contrib import messages

# logger = logging.getLogger(__name__)

# class JWTLoginRequiredMixin:
#     def dispatch(self, request, *args, **kwargs):
#         logger.info("Проверка JWT для %s", request.path)
#         try:
#             # Проверяем заголовок Authorization
#             authenticator = JWTAuthentication()
#             user_auth_tuple = authenticator.authenticate(request)
#             if user_auth_tuple is None:
#                 # Проверяем query-параметр token (для теста)
#                 token = request.GET.get('token')
#                 if token:
#                     # Временное решение: создаём фейковый заголовок
#                     request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
#                     user_auth_tuple = authenticator.authenticate(request)
#             if user_auth_tuple is not None:
#                 request.user, request.auth = user_auth_tuple
#                 logger.info("Успешная аутентификация: %s", request.user)
#             else:
#                 raise AuthenticationFailed("Требуется авторизация.")
#         except AuthenticationFailed as e:
#             logger.error("Ошибка аутентификации: %s", str(e))
#             messages.error(request, "Пожалуйста, войдите в систему.")
#             return redirect(reverse('admin-login'))
#         return super().dispatch(request, *args, **kwargs)



# class AdminRequiredMixin(JWTLoginRequiredMixin):
#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_admin:
#             messages.error(request, "Только администраторы могут выполнять это действие.")
#             return redirect(reverse('admin-login'))
#         return super().dispatch(request, *args, **kwargs)