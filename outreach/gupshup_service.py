import logging
from typing import Tuple
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class GupshupSMSService:
    """
    Simple wrapper for Gupshup Enterprise SMS API
    Supports OTP and TRANSACTIONAL message types.
    """

    def __init__(self):
        # Base URL
        self.base_url = getattr(
            settings,
            'GUPSHUP_BASE_URL',
            'https://enterprise.smsgupshup.com/GatewayAPI/rest'
        )

        # Sender ID (if needed by your account; sample sets but doesn't pass it)
        self.sender_id = getattr(settings, 'GUPSHUP_SENDER_ID', 'JOSHSK')

        # Credentials: use environment if provided, else fall back to sample values
        self.userid_otp = getattr(settings, 'GUPSHUP_USERID_OTP', '2000196837')
        self.password_otp = getattr(settings, 'GUPSHUP_PASSWORD_OTP', 'p#mebmD8')
        self.userid_txn = getattr(settings, 'GUPSHUP_USERID_TXN', '2000196838')
        self.password_txn = getattr(settings, 'GUPSHUP_PASSWORD_TXN', 'CrzD*2Wg')

    def send_sms(self, mobile: str, message: str, msg_type: str = 'TRANSACTIONAL') -> Tuple[bool, str]:
        """
        Send an SMS via Gupshup.

        msg_type: 'OTP' or 'TRANSACTIONAL'
        Returns (success, info_message)
        """
        msg_type = (msg_type or 'TRANSACTIONAL').upper()

        if msg_type == 'OTP':
            userid = self.userid_otp
            password = self.password_otp
        else:
            userid = self.userid_txn
            password = self.password_txn

        if not userid or not password:
            return False, 'Gupshup credentials missing for type {}'.format(msg_type)

        # Build URL using the same pattern as the provided sample code
        url = (
            f"{self.base_url}?method=SendMessage"
            f"&send_to={mobile}"
            f"&msg={message}"
            f"&msg_type=TEXT&userid={userid}&auth_scheme=plain&password={password}&v=1.1&format=text"
        )

        # Encode special characters exactly as in the sample
        url = url.replace('#', '%23').replace('+', '%2b')

        try:
            logger.info(f"Sending Gupshup SMS to {mobile} (type={msg_type})")
            resp = requests.get(url, timeout=15)
            text = resp.text.strip()
            logger.info(f"Gupshup response ({resp.status_code}): {text}")

            if resp.ok and 'success' in text.lower():
                return True, text
            return False, text
        except requests.RequestException as e:
            logger.error(f"Network error sending SMS to {mobile}: {str(e)}")
            return False, f"Network error: {str(e)}"


