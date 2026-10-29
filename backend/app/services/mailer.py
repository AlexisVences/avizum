"""Outgoing e-mail: a small interface with a Resend implementation, a console one for development, and an
in-memory one for tests. Callers go through `deliver`, which never raises: a mail failure must not fail a request."""
import logging
from dataclasses import dataclass, field
from html import escape
from typing import Protocol

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class MailDeliveryError(Exception):
    """The provider did not accept the message (or could not be reached)."""


class Mailer(Protocol):
    def send(self, to: str, subject: str, html: str, text: str, idempotency_key: str) -> None: ...


class ResendMailer:
    def __init__(self, api_key: str, sender: str) -> None:
        self._api_key = api_key
        self._sender = sender

    def send(self, to: str, subject: str, html: str, text: str, idempotency_key: str) -> None:
        import resend
        from resend.exceptions import ResendError

        resend.api_key = self._api_key
        try:
            resend.Emails.send(
                {"from": self._sender, "to": [to], "subject": subject, "html": html, "text": text},
                options={"idempotency_key": idempotency_key},
            )
        except (ResendError, ValueError) as exc:
            # ResendError subclasses carry code / error_type / message; none of them include our payload.
            code = getattr(exc, "code", None)
            raise MailDeliveryError(f"{type(exc).__name__} (code={code})") from exc
        except Exception as exc:  # network failures and anything else the SDK lets through
            raise MailDeliveryError(type(exc).__name__) from exc


class ConsoleMailer:
    """Development fallback when no RESEND_API_KEY is set. Logs the message, links included, because that is its
    purpose (clicking the link locally); it must never be selected in production."""

    def send(self, to: str, subject: str, html: str, text: str, idempotency_key: str) -> None:
        logger.info("MAIL (console) to=%s subject=%s\n%s", to, subject, text)


@dataclass
class SentMessage:
    to: str
    subject: str
    html: str
    text: str
    idempotency_key: str


@dataclass
class OutboxMailer:
    """Records messages; used by the tests so nothing touches the network."""

    messages: list[SentMessage] = field(default_factory=list)

    def send(self, to: str, subject: str, html: str, text: str, idempotency_key: str) -> None:
        self.messages.append(SentMessage(to, subject, html, text, idempotency_key))


def build_mailer(settings: Settings) -> Mailer:
    key = settings.resend_api_key.get_secret_value() if settings.resend_api_key else ""
    if key:
        return ResendMailer(key, settings.mail_from)
    return ConsoleMailer()


def get_mailer() -> Mailer:
    """FastAPI dependency (tests override it with an OutboxMailer)."""
    return build_mailer(get_settings())


def deliver(mailer: Mailer, to: str, subject: str, html: str, text: str, idempotency_key: str) -> None:
    """Send and swallow failures. Logs neither the token nor the address."""
    try:
        mailer.send(to, subject, html, text, idempotency_key)
    except MailDeliveryError as exc:
        logger.error("Mail delivery failed (%s)", exc)
    except Exception:
        logger.exception("Mail delivery failed unexpectedly")


# ---- messages (Spanish, short) -------------------------------------------------------------------------------

def _wrap(paragraphs: list[str], link: str | None, button: str | None) -> tuple[str, str]:
    text_parts = list(paragraphs)
    html_parts = [f"<p>{escape(p)}</p>" for p in paragraphs]
    if link and button:
        text_parts.append(f"{button}: {link}")
        html_parts.append(f'<p><a href="{escape(link, quote=True)}">{escape(button)}</a></p>')
        html_parts.append(f"<p>Si el botón no funciona, copia este enlace en tu navegador:<br>{escape(link)}</p>")
    text_parts.append("Avizum")
    html_parts.append("<p>Avizum</p>")
    return "\n\n".join(text_parts), "".join(html_parts)


def verification_message(base_url: str, token: str, first_name: str) -> tuple[str, str, str]:
    link = f"{base_url.rstrip('/')}/verificar-correo?token={token}"
    text, html = _wrap(
        [f"Hola {first_name},", "Confirma tu correo para terminar de configurar tu cuenta. El enlace vence en 24 horas.",
         "Si no creaste una cuenta en Avizum, ignora este mensaje."],
        link, "Confirmar mi correo",
    )
    return "Confirma tu correo en Avizum", html, text


def reset_message(base_url: str, token: str, first_name: str) -> tuple[str, str, str]:
    link = f"{base_url.rstrip('/')}/restablecer-contrasena?token={token}"
    text, html = _wrap(
        [f"Hola {first_name},", "Recibimos una solicitud para restablecer tu contraseña. El enlace vence en 1 hora y solo sirve una vez.",
         "Si no la hiciste tú, ignora este mensaje: tu contraseña no cambiará."],
        link, "Restablecer mi contraseña",
    )
    return "Restablece tu contraseña de Avizum", html, text


def google_account_message(first_name: str) -> tuple[str, str, str]:
    text, html = _wrap(
        [f"Hola {first_name},", "Solicitaste restablecer tu contraseña, pero tu cuenta de Avizum se creó con Google y no tiene contraseña.",
         "Para entrar, usa el botón «Continuar con Google» con la misma cuenta de Google.",
         "Si no fuiste tú, ignora este mensaje."],
        None, None,
    )
    return "Tu cuenta de Avizum usa Google", html, text
