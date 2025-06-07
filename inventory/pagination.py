from rest_framework.pagination import PageNumberPagination

class ContractPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 100
    page_query_param = 'page'


class CustomPagination(PageNumberPagination):
    page_size = 10  # По умолчанию 10 элементов на страницу
    page_size_query_param = 'limit'  # Параметр для изменения размера страницы
    max_page_size = 100  # Максимум 100 элементов