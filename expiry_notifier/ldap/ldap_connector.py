from django.conf import settings
from ldap3 import Server, Connection, Tls, ALL, core
import ssl
import logging

logger = logging.getLogger(__name__)

def get_ldap_connection():
    tls_config = Tls(
        validate = ssl.CERT_NONE,
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
            connect_timeout=settings.LDAP_CONNECTION_TIMEOUT if hasattr(settings, 'LDAP_CONNECTION_TIMEOUT') else 10
        )

        conn = Connection(
            server,
            user=settings.AUTH_LDAP_BIND_DN,
            password=settings.AUTH_LDAP_BIND_PASSWORD,
            auto_bind=True,
            raise_exceptions=True,
            receive_timeout=settings.LDAP_RECEIVE_TIMEOUT if hasattr(settings, 'LDAP_RECEIVE_TIMEOUT') else 30
        )

        logger.info(f"Успешное подключение к LDAP-серверу {settings.LDAP_SERVER}")
        return conn

    except core.exceptions.LDAPCertificateError as e:
        logger.error(f"Ошибка сертификата LDAP: {e}")
        raise core.exceptions.LDAPCertificateError(
            "Не удалось верифицировать сертификат LDAP-сервера. "
            "Проверьте LDAP_CA_CERT_FILE в настройках."
        ) from e

    except core.exceptions.LDAPException as e:
        logger.error(f"Ошибка подключения к LDAP: {e}")
        raise core.exceptions.LDAPException(
            f"Не удалось подключиться к LDAP-серверу: {str(e)}"
        ) from e
