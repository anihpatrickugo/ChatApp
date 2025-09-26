
import algoliasearch_django as algoliasearch
from algoliasearch_django.decorators import register
from users.models import User

@register(User)
class UserIndex(algoliasearch.AlgoliaIndex):
    fields = ("id", "get_photo", "username", "first_name", "last_name", "email")
    settings = {"searchableAttributes": ["username", "first_name", "last_name", "email"]}
    index_name = "users"
