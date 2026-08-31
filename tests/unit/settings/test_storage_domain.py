import importlib
import os
from contextlib import contextmanager
from unittest import mock

from django.test import SimpleTestCase


class TestStorageDomainConfiguration(SimpleTestCase):
    """
    django-storages builds every media and static URL from
    AWS_S3_CUSTOM_DOMAIN, so putting a CDN in front of the bucket is a
    configuration change rather than a code change -- and rolling it back is
    unsetting one variable rather than reverting a deploy.
    """

    @contextmanager
    def _environment(self, **overrides):
        # settings.prod refuses to import without a real SECRET_KEY, so the
        # baseline supplies one along with the bucket name the URLs derive
        # from.
        environment = {
            "SECRET_KEY": "a-unique-secret-key-used-only-by-tests",
            "AWS_STORAGE_BUCKET_NAME": "evalai",
        }
        environment.update(overrides)
        with mock.patch.dict(os.environ, environment, clear=False):
            yield

    def _rebuild(self, *module_names):
        """Re-execute the settings chain under the patched environment.

        `from .common import *` does not re-execute common when it is already
        imported, so prod would keep the SECRET_KEY bound at first import and
        refuse to load. common therefore has to be rebuilt before prod is
        imported at all, not merely before it is reloaded.
        """
        import settings.common

        importlib.reload(settings.common)
        module = None
        for name in module_names:
            module = importlib.reload(importlib.import_module(name))
        return module

    def _reload_prod(self, **overrides):
        with self._environment(**overrides):
            return self._rebuild("settings.prod")

    def _reload_staging(self, **overrides):
        with self._environment(**overrides):
            # staging is `from .prod import *`, so the whole chain has to be
            # rebuilt in order before staging re-reads it.
            return self._rebuild("settings.prod", "settings.staging")

    def tearDown(self):
        # These reloads mutate module state that outlives the test, so put
        # both back to their unset-environment form.
        self._reload_prod()
        self._reload_staging()

    def test_defaults_to_the_bucket_s3_domain(self):
        # With the variable absent, behaviour must be exactly what it was
        # before, so merging this changes nothing in production.
        prod = self._reload_prod()

        self.assertEqual(prod.AWS_S3_CUSTOM_DOMAIN, "evalai.s3.amazonaws.com")

    def test_environment_variable_repoints_storage_at_a_cdn(self):
        prod = self._reload_prod(AWS_S3_CUSTOM_DOMAIN="d123.cloudfront.net")

        self.assertEqual(prod.AWS_S3_CUSTOM_DOMAIN, "d123.cloudfront.net")

    def test_static_and_media_urls_both_follow_the_configured_domain(self):
        # They have to move together. A split would serve static assets from
        # the CDN while media kept billing as direct S3 egress, which is the
        # cost this change exists to remove.
        prod = self._reload_prod(AWS_S3_CUSTOM_DOMAIN="d123.cloudfront.net")

        self.assertEqual(
            prod.STATIC_URL, "https://d123.cloudfront.net/static/"
        )
        self.assertEqual(prod.MEDIA_URL, "https://d123.cloudfront.net/media/")

    def test_staging_inherits_the_override(self):
        # staging.py is `from .prod import *`; if that ever stops holding,
        # staging could not be used to rehearse the production cutover.
        staging = self._reload_staging(
            AWS_S3_CUSTOM_DOMAIN="staging.cloudfront.net"
        )

        self.assertEqual(
            staging.AWS_S3_CUSTOM_DOMAIN, "staging.cloudfront.net"
        )
