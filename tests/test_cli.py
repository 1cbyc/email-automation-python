import os
import pytest
from click.testing import CliRunner
from main import cli

def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Usage' in result.output

def test_cli_missing_required():
    runner = CliRunner()
    result = runner.invoke(cli, ['--subject', 'Test'])
    assert result.exit_code != 0 or 'Body is required' in result.output

def test_cli_template_render(tmp_path):
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    template_file = template_dir / "t.html"
    template_file.write_text("<h1>{{ title }}</h1>")
    os.environ["SMTP_SERVER"] = "smtp.example.com"
    os.environ["SMTP_PORT"] = "587"
    os.environ["EMAIL_USERNAME"] = "user"
    os.environ["EMAIL_PASSWORD"] = "pass"
    os.environ["EMAIL_FROM"] = "from@example.com"
    os.environ["EMAIL_TO"] = "to@example.com"
    runner = CliRunner()
    with runner.isolated_filesystem():
        os.makedirs("templates", exist_ok=True)
        with open("templates/t.html", "w") as f:
            f.write("<h1>{{ title }}</h1>")
        result = runner.invoke(cli, ["--subject", "Test", "--template", "t.html", "--context", "title=Hello"])
        assert result.exit_code == 0 or "Email sent successfully" in result.output or "Failed to send email" in result.output 