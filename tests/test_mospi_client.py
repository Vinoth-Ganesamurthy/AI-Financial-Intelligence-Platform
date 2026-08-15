"""
Tests for secure MoSPI HTTPS configuration.
"""

import ssl
from unittest.mock import MagicMock, patch

import certifi

from src.data.macro import mospi_client


def test_verified_adapter_requires_certificates():
    adapter = (
        mospi_client.VerifiedLegacySSLAdapter()
    )

    ssl_context = (
        adapter
        .poolmanager
        .connection_pool_kw["ssl_context"]
    )

    assert ssl_context.verify_mode == (
        ssl.CERT_REQUIRED
    )

    assert ssl_context.check_hostname is True


@patch.object(
    mospi_client.esankhyiki,
    "_client",
)
def test_configure_mospi_tls(
    mock_client,
):
    mock_client.session = MagicMock()

    result = (
        mospi_client.configure_mospi_tls()
    )

    assert result is mock_client

    assert mock_client.session.verify == (
        certifi.where()
    )

    mock_client.session.mount.assert_called_once()

    mount_arguments = (
        mock_client.session.mount.call_args.args
    )

    assert mount_arguments[0] == "https://"

    assert isinstance(
        mount_arguments[1],
        mospi_client.VerifiedLegacySSLAdapter,
    )


@patch.object(
    mospi_client.esankhyiki,
    "get_data",
)
@patch.object(
    mospi_client,
    "configure_mospi_tls",
)
def test_get_mospi_data_uses_secure_configuration(
    mock_configure,
    mock_get_data,
):
    mock_get_data.return_value = [
        {"value": 5.5}
    ]

    result = mospi_client.get_mospi_data(
        "PLFS",
        {"indicator_code": 3},
    )

    mock_configure.assert_called_once()

    mock_get_data.assert_called_once_with(
        "PLFS",
        {"indicator_code": 3},
    )

    assert result == [
        {"value": 5.5}
    ]