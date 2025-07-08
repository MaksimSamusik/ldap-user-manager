from django.conf import settings
from ldap3 import Server, Connection, Tls, ALL, core
import ssl
import logging

logger = logging.getLogger(__name__)


def get_ldap_connection():
    tls_config = Tls(
        validate=ssl.CERT_NONE,
        version=ssl.PROTOCOL_TLSv1_2,
        ca_certs_file=getattr(settings, 'LDAP_CA_CERT_FILE', None),
        valid_names=[settings.LDAP_SERVER_HOSTNAME] if hasattr(settings, 'LDAP_SERVER_HOSTNAME') else None
    )

    try:
        server = Server(
            settings.LDAP_SERVER,
            use_ssl=True,
            tls=tls_config,
            get_info=ALL,
            connect_timeout=getattr(settings, 'LDAP_CONNECTION_TIMEOUT', 10)
        )

        conn = Connection(
            server,
            user=settings.AUTH_LDAP_BIND_DN,
            password=settings.AUTH_LDAP_BIND_PASSWORD,
            auto_bind=True,
            raise_exceptions=True,
            receive_timeout=getattr(settings, 'LDAP_RECEIVE_TIMEOUT', 30)
        )

        logger.info(f"Successfully connected to LDAP server: {settings.LDAP_SERVER}")
        return conn

    except core.exceptions.LDAPSocketOpenError as e:
        logger.error(f"Connection to LDAP server failed (network error): {e}")
        raise core.exceptions.LDAPException(
            f"Could not establish connection to LDAP server: {str(e)}. "
            "Check server availability and network connectivity."
        ) from e
