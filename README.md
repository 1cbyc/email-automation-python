# email-automation-python

Email automation tool supporting Gmail, Outlook, Yahoo, and custom SMTP with OAuth2, templating, scheduling, profiles, and CI/CD.

## Features
- CLI for sending emails with dynamic sender, recipients, subject, body, HTML, and attachments
- Jinja2 templating for dynamic, branded emails
- Configuration profiles for multiple environments/accounts
- Advanced logging (console and file)
- Scheduling helper for cron/Task Scheduler
- Multi-provider support (Gmail, Outlook, Yahoo, custom SMTP)
- OAuth2 authentication for Gmail and Outlook
- Test suite and GitHub Actions CI/CD

## Setup
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your credentials
4. (Optional) Add profiles in `profiles/` and templates in `templates/`

## Usage
- Send a basic email:
  ```
  python main.py --to recipient@example.com --subject "Test" --body "Hello"
  ```
- Use a template:
  ```
  python main.py --template sample.html --context title="Hi" --context message="Body" --context sender="Me" --to recipient@example.com --subject "Test"
  ```
- Use OAuth2:
  ```
  python main.py --provider gmail --oauth2 --to recipient@example.com --subject "Test" --body "Hello"
  ```
- Schedule with helper:
  ```
  python schedule_helper.py
  ```

## Documentation
- See `docs/explanation.md` for technical details
- See `docs/whats-next.md` for usage, extension, and deployment

## Testing
- Run `pytest` to execute the test suite

## CI/CD
- GitHub Actions workflow in `.github/workflows/python-app.yml`

## License
MIT 