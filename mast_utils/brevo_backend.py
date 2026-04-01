"""
Custom Django email backend that sends via Brevo's HTTP API (port 443),
bypassing the SMTP relay which is blocked by the firewall.
"""
import logging
import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger('mast.email')


class BrevoEmailBackend(BaseEmailBackend):

    API_URL = 'https://api.brevo.com/v3/smtp/email'

    def send_messages(self, email_messages):
        sent = 0
        for msg in email_messages:
            try:
                self._send(msg)
                sent += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
                logger.error('Brevo send failed: %s', e)
        return sent

    def _send(self, msg):
        from_email, from_name = self._parse_address(msg.from_email)
        payload = {
            'sender': {'name': from_name, 'email': from_email},
            'to': [{'email': addr} for addr in msg.to],
            'subject': msg.subject,
        }

        # Prefer HTML alternative if present
        html_body = None
        if hasattr(msg, 'alternatives'):
            for content, mimetype in msg.alternatives:
                if mimetype == 'text/html':
                    html_body = content
                    break

        if html_body:
            payload['htmlContent'] = html_body
        else:
            payload['textContent'] = msg.body

        resp = requests.post(
            self.API_URL,
            headers={'api-key': settings.BREVO_API_KEY, 'Content-Type': 'application/json'},
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        logger.info('Email sent via Brevo to %s (messageId: %s)', msg.to, resp.json().get('messageId'))

    @staticmethod
    def _parse_address(address):
        """Parse 'Name <email>' or plain 'email' into (email, name)."""
        if '<' in address:
            name, rest = address.split('<', 1)
            return rest.rstrip('>').strip(), name.strip()
        return address.strip(), ''
