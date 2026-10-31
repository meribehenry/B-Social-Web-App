from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Post
import uuid
import django_filters


class PostFilter(django_filters.FilterSet):
    author = django_filters.CharFilter(method='filter_author')
    recent = django_filters.NumberFilter(method='filter_recent')
    # is_liked = django_filters.BooleanFilter(method='filter_is_liked')
    # trending = django_filters.BooleanFilter(method='filter_trending')
    # has_media = django_filters.BooleanFilter(method='filter_has_media')

    class Meta:
        model = Post
        fields = ['author', 'recent',] # 'is_liked', 'trending', 'has_media']

    def filter_author(self, queryset, name, value):
        value = value.strip()
        try:
            uuid.UUID(value)
            # It a valid uuid
            return queryset.filter(author__id=value)
        except ValueError:
            return queryset.filter(author__username=value)

    def filter_recent(self, queryset, name, value):
        threshold = timezone.now() - timedelta(days=int(value))
        return queryset.filter(date_created__gte=threshold)

    # def filter_is_liked(self, queryset, name, value):
    #     request = getattr(self, 'request', None)
    #     if request and request.user.is_authenticated and value:
    #         return queryset.filter(likes__user=request.user)
    #     return queryset

    # def filter_trending(self, queryset, name, value):
    #     if not value:
    #         return queryset
    #     last_week = timezone.now() - timedelta(days=7)
    #     return queryset.filter(created_at__gte=last_week).annotate(
    #         engagement_score=Count('likes', distinct=True) + Count('comments', distinct=True)
    #     ).order_by('-engagement_score')

    # def filter_has_media(self, queryset, name, value):
    #     if value:
    #         return queryset.exclude(media='').exclude(media__isnull=True)
    #     return queryset.filter(Q(media='') | Q(media__isnull=True))