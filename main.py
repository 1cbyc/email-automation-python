import os
import smtplib
from email.message import EmailMessage
import click
from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from jinja2 import Environment, FileSystemLoader, select_autoescape
import logging
from base64 import urlsafe_b64encode
from google.oauth2.credentials import Credentials as GoogleCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from requests_oauthlib import OAuth2Session
from google.auth.transport.requests import Request

PROVIDERS = {
    "gmail": {"server": "smtp.gmail.com", "port": 587},
    "outlook": {"server": "smtp.office365.com", "port": 587},
    "yahoo": {"server": "smtp.mail.yahoo.com", "port": 587},
    "custom": {"server": None, "port": None}
}

load_dotenv()
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        RichHandler(console=console),
        logging.FileHandler("email_automation.log")
    ]
)
logger = logging.getLogger("email_automation")

SCOPES = [
    "https://mail.google.com/",
    "https://outlook.office.com/SMTP.Send"
]

def render_template(template_name, context):
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "xml"])
    )
    template = env.get_template(template_name)
    return template.render(**context)

def get_provider_settings(provider, custom_server, custom_port):
    if provider in PROVIDERS and provider != "custom":
        return PROVIDERS[provider]["server"], PROVIDERS[provider]["port"]
    if provider == "custom" and custom_server and custom_port:
        return custom_server, int(custom_port)
    return None, None

def get_profile(profile):
    profile_path = f"profiles/{profile}.env"
    if os.path.exists(profile_path):
        load_dotenv(profile_path, override=True)

def get_gmail_oauth2_token():
    creds = None
    if os.path.exists("token.json"):
        creds = GoogleCredentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.getenv("GOOGLE_OAUTH_CLIENT_SECRET_JSON"), SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def get_outlook_oauth2_token():
    client_id = os.getenv("OUTLOOK_CLIENT_ID")
    client_secret = os.getenv("OUTLOOK_CLIENT_SECRET")
    redirect_uri = os.getenv("OUTLOOK_REDIRECT_URI", "http://localhost:8000")
    token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    scope = ["https://outlook.office.com/SMTP.Send"]
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=scope)
    authorization_url, state = oauth.authorization_url(
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize")
    print(f"Go to the following URL and authorize: {authorization_url}")
    authorization_response = input("Enter the full callback URL: ")
    token = oauth.fetch_token(
        token_url=token_url,
        authorization_response=authorization_response,
        client_secret=client_secret
    )
    return token

def get_oauth2_string(username, access_token):
    auth_string = f"user={username}\1auth=Bearer {access_token}\1\1"
    return urlsafe_b64encode(auth_string.encode()).decode()

def send_email(smtp_server, smtp_port, username, password, sender, recipients, subject, body, html, attachments, provider, oauth2):
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    if html:
        msg.add_alternative(body, subtype="html")
    else:
        msg.set_content(body)
    for path in attachments:
        with open(path, "rb") as f:
            data = f.read()
            name = os.path.basename(path)
        msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=name)
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        if oauth2:
            if provider == "gmail":
                creds = get_gmail_oauth2_token()
                auth_string = get_oauth2_string(username, creds.token)
                server.docmd("AUTH", "XOAUTH2 " + auth_string)
            elif provider == "outlook":
                token = get_outlook_oauth2_token()
                access_token = token["access_token"]
                auth_string = get_oauth2_string(username, access_token)
                server.docmd("AUTH", "XOAUTH2 " + auth_string)
            else:
                raise Exception("OAuth2 is only supported for Gmail and Outlook.")
        else:
            server.login(username, password)
        server.send_message(msg)

@click.command()
@click.option("--subject", prompt=True)
@click.option("--body", prompt=False)
@click.option("--html", is_flag=True, default=False)
@click.option("--to", multiple=True, help="Recipient email address. Can be used multiple times.")
@click.option("--attachment", multiple=True, type=click.Path(exists=True), help="File to attach. Can be used multiple times.")
@click.option("--template", type=str, help="Jinja2 template filename in templates/ directory.")
@click.option("--profile", type=str, help="Configuration profile name (loads profiles/{profile}.env).")
@click.option("--context", type=str, multiple=True, help="Template context as key=value. Can be used multiple times.")
@click.option("--provider", type=click.Choice(["gmail", "outlook", "yahoo", "custom"]), default=None, help="Email provider to use.")
@click.option("--custom-server", type=str, default=None, help="Custom SMTP server (for provider=custom).")
@click.option("--custom-port", type=int, default=None, help="Custom SMTP port (for provider=custom).")
@click.option("--oauth2", is_flag=True, default=False, help="Use OAuth2 authentication (Gmail/Outlook only).")
def cli(subject, body, html, to, attachment, template, profile, context, provider, custom_server, custom_port, oauth2):
    if profile:
        get_profile(profile)
    env_provider = os.getenv("EMAIL_PROVIDER")
    use_provider = provider or env_provider or "gmail"
    smtp_server, smtp_port = get_provider_settings(use_provider, custom_server, custom_port)
    if not smtp_server or not smtp_port:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
    username = os.getenv("EMAIL_USERNAME")
    password = os.getenv("EMAIL_PASSWORD")
    sender = os.getenv("EMAIL_FROM")
    recipients = list(to) if to else [os.getenv("EMAIL_TO")]
    ctx = dict(pair.split("=", 1) for pair in context)
    if template:
        try:
            body = render_template(template, ctx)
            html = True
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            console.print(f"[red]Template rendering failed: {e}[/red]")
            return
    elif not body:
        console.print("[red]Body is required if no template is provided[/red]")
        return
    try:
        send_email(smtp_server, smtp_port, username, password, sender, recipients, subject, body, html, list(attachment), use_provider, oauth2)
        logger.info("Email sent successfully")
        console.print("[green]Email sent successfully[/green]")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        console.print(f"[red]Failed to send email: {e}[/red]")

if __name__ == "__main__":
    cli()