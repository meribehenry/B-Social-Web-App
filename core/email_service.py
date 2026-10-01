from .logger.logger_client import get_logger
from concurrent.futures import ThreadPoolExecutor
from django.template.loader import get_template
import os
import requests



logger = get_logger(__name__)

executor = ThreadPoolExecutor(max_workers=20)


class EmailService():

    def __init__(self):
        self.url = "https://api.brevo.com/v3/smtp/email"
        self.api_key = os.environ.get("BREVO_API_KEY")

    
    def _get_header(self):
        return {
            "accept": "application/json",
            "api-key": self.api_key,
            "content_type": "application/json"
        }
    

    def _build_email(self, subject, recipient, html):
        return {
            "sender": {
                "name": "B-Social",
                "email": "mercuryboy109@gmail.com"
            },
             
            "to": [
                    {
                        "email": recipient
                    }
                ],
            
            "subject": subject,
            "htmlContent": html
        }
    
    def _send_async_email(self, header, data) -> bool:
        try:
            response = requests.post(self.url, headers=header, json=data, timeout=15)
            logger.info(f"Email sent successfully 💯: {response.status_code}")
            return True

        except requests.exceptions.Timeout:
            logger.error("Brevo timed out")

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Brevo")

        except requests.exceptions.HTTPError as e:
            print(e)
            logger.error("Brevo HTTP Error")

        except requests.exceptions.RequestException:
            logger.error("Unexpected Brevo error")

        except Exception:
            logger.error("Unexpected Brevo error") 

        return False       

    
    def send_email(self, email:str, values:dict, subject:str, template_name=None, html_content_to_add=None,):
        html_content = ""
        if template_name:
            template = get_template(template_name)
            html_content = template.render(values)
        else:
            html_content = html_content_to_add

        return self._send_async_email(
                    self._get_header(), 
                    self._build_email(subject, email, html_content)
                )