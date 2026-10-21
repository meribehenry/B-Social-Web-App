from .base import *  # Import base settings (or local/dev if inheriting from there)

# -----------------------------------------------------------------------------
# 1. Debug Mode
# -----------------------------------------------------------------------------
# Keep DEBUG False to catch bugs that only happen in production (like missing templates or static files).
DEBUG = False


# -----------------------------------------------------------------------------
# 2. Database Configuration
# -----------------------------------------------------------------------------
# Using SQLite in-memory speeds up pytest execution dramatically.
# If you rely heavily on PostgreSQL-specific features (JSONFields, Trigram, etc.),
# keep PostgreSQL but override the DB name to avoid touching dev data.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# -----------------------------------------------------------------------------
# 3. Password Hashing (Massive Speedup!)
# -----------------------------------------------------------------------------
# Argon2/PBKDF2 are deliberately slow to prevent brute-force attacks.
# MD5 is weak for security, but making hundreds of password hashes in tests 100x faster!
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


# -----------------------------------------------------------------------------
# 4. Email Backend
# -----------------------------------------------------------------------------
# Intercept emails in memory so tests don't send real emails or crash.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


# -----------------------------------------------------------------------------
# 5. Caching
# -----------------------------------------------------------------------------
# Use dummy cache or local memory so tests don't depend on an external Redis/Memcached instance.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}


# -----------------------------------------------------------------------------
# 6. Celery / Background Tasks (If applicable)
# -----------------------------------------------------------------------------
# Run Celery tasks synchronously (in the same thread) during tests.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EPROPAGATE_EXCEPTIONS = True


# -----------------------------------------------------------------------------
# 7. Media & Files Handling
# -----------------------------------------------------------------------------
# Store uploaded files in a temporary directory so test uploads don't clutter your actual media folder.
import tempfile

MEDIA_ROOT = tempfile.mkdtemp()


# -----------------------------------------------------------------------------
# 8. Secret Key & Security
# -----------------------------------------------------------------------------
SECRET_KEY = "test-secret-key-only-for-pytest-do-not-use-in-production"
ALLOWED_HOSTS = ["*"]