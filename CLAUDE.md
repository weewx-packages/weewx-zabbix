# weewx-zabbix

WeeWX extension. The runtime module is in `bin/user/`; `install.py` is the extension installer.

Keep upstream Python style and use docstrings instead of runtime type annotations. Preserve copyright and license notices. Date changes to GPL/Apache files.

## Tests

Run `python -m pytest -q` in an environment with WeeWX and pytest installed. The tests use local receivers and temporary station directories. WeeWX 4 tests pass bin_root explicitly to keep installation isolated.
