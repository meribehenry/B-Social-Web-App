from core.pagination import DynamicCursorPagination

class PostCursorPagination(DynamicCursorPagination):
    ordering = "-date_created"
    ordering_fields = ["date_created", "analytics__like_count"]