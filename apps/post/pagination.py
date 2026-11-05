from core.pagination import DynamicCursorPagination
from rest_framework.exceptions import ValidationError



class PostCursorPagination(DynamicCursorPagination):
    ordering = "-date_created"
    ordering_fields = ["date_created", "like_count"]

    ORDERING_MAP = {
    'likes_count': 'analytics__likes_count',
    'comments_count': 'analytics__comments_count',
    'date_created': 'date_created'
    }

    ordering_fields = ['date_created', 'likes_count', 'comments_count']

    def get_ordering(self, request, queryset, view):
        param = request.query_params.get('ordering', self.ordering)
        field_name = param.lstrip('-')
       
        if field_name not in self.ordering_fields:
            raise ValidationError({
                "ordering": f"Invalid ordering. Allowed fields: {self.ordering_fields}. Use '-' for DESC, e.g. '-date_created'"
            })

        # Map likes_count -> analytics__likes_count for DB
        is_desc = param.startswith('-')
        db_field = self.ORDERING_MAP[field_name]
        final_ordering = f"-{db_field}" if is_desc else db_field
       
        return (final_ordering,)