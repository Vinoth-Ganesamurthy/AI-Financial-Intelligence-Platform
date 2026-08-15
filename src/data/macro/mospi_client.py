"""
Secure MoSPI eSankhyiki client configuration.

The third-party package enables legacy SSL support but
also disables certificate verification. This wrapper
preserves the required legacy connection option while
restoring CA certificate and hostname verification.
"""

import ssl

import certifi
import esankhyiki
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


MOSPI_RETRY_STATUS_CODES = [
    429,
    500,
    502,
    503,
    504,
]


class VerifiedLegacySSLAdapter(HTTPAdapter):
    """
    HTTPS adapter with normal certificate verification
    and legacy server-connect support.
    """

    def init_poolmanager(
        self,
        *args,
        **kwargs,
    ):
        ssl_context = ssl.create_default_context(
            cafile=certifi.where()
        )

        legacy_option = getattr(
            ssl,
            "OP_LEGACY_SERVER_CONNECT",
            0x4,
        )

        ssl_context.options |= legacy_option

        kwargs["ssl_context"] = ssl_context

        return super().init_poolmanager(
            *args,
            **kwargs,
        )


def configure_mospi_tls():
    """
    Replace the package's insecure HTTPS adapter with
    a certificate-verifying adapter.
    """

    client = getattr(
        esankhyiki,
        "_client",
        None,
    )

    if client is None:
        raise RuntimeError(
            "The eSankhyiki client is unavailable."
        )

    retry_strategy = Retry(
        total=3,
        connect=2,
        read=2,
        status=3,
        backoff_factor=0.6,
        status_forcelist=(
            MOSPI_RETRY_STATUS_CODES
        ),
        allowed_methods=frozenset(
            {"GET", "POST"}
        ),
        respect_retry_after_header=True,
    )

    adapter = VerifiedLegacySSLAdapter(
        max_retries=retry_strategy
    )

    client.session.verify = certifi.where()

    client.session.mount(
        "https://",
        adapter,
    )

    return client


def get_mospi_data(
    dataset,
    filters,
):
    """
    Fetch MoSPI data using verified HTTPS.
    """

    configure_mospi_tls()

    return esankhyiki.get_data(
        dataset,
        filters,
    )