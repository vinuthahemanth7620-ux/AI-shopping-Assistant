from urllib.parse import urljoin
from flask import url_for, request


class AuthPresenter:
    """
    Auth Presenter Layer - Parses client metadata (User-Agent, IP address)
    and formats data for email templates and login audit logging.
    Follows MVP Architecture.
    """

    @staticmethod
    def parse_user_agent(user_agent_str: str) -> dict:
        """
        Parse User-Agent string to extract Browser, Operating System, and Device Name.
        """
        ua = str(user_agent_str or '').strip()
        ua_lower = ua.lower()

        # 1. Operating System Detection
        if 'windows' in ua_lower:
            os_name = 'Windows OS'
        elif 'macintosh' in ua_lower or 'mac os' in ua_lower:
            os_name = 'macOS'
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            os_name = 'iOS'
        elif 'android' in ua_lower:
            os_name = 'Android OS'
        elif 'linux' in ua_lower:
            os_name = 'Linux OS'
        else:
            os_name = 'Unknown Operating System'

        # 2. Browser Detection
        if 'edg' in ua_lower or 'edge' in ua_lower:
            browser_name = 'Microsoft Edge'
        elif 'chrome' in ua_lower and 'chromium' not in ua_lower:
            browser_name = 'Google Chrome'
        elif 'firefox' in ua_lower:
            browser_name = 'Mozilla Firefox'
        elif 'safari' in ua_lower and 'chrome' not in ua_lower:
            browser_name = 'Apple Safari'
        elif 'opera' in ua_lower or 'opr' in ua_lower:
            browser_name = 'Opera'
        else:
            browser_name = 'Standard Web Browser'

        # 3. Device Type Detection
        if 'mobile' in ua_lower or 'iphone' in ua_lower or 'android' in ua_lower:
            device_type = 'Mobile Device'
        elif 'ipad' in ua_lower or 'tablet' in ua_lower:
            device_type = 'Tablet Device'
        else:
            device_type = 'Desktop Computer'

        return {
            'browser': browser_name,
            'operating_system': os_name,
            'device_name': device_type,
            'full_string': ua[:200]
        }
