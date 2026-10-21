# Repair validation

Version 0.2.0. Original repository and revision are in ORIGIN.md.

* https://github.com/RandomReaper/weewx-zabbix/pull/10: Dustin Demuth template adapted to consistent METRICWX inputs; unique items checked, real Zabbix 7.0.32 API import succeeded.
* https://github.com/RandomReaper/weewx-zabbix/issues/9: Zabbix 7 template imported through real API; requires unit_system=METRICWX as documented.
* https://github.com/RandomReaper/weewx-zabbix/issues/8: Source already uses Python logging. Tests capture logging through configured logger; did not copy erroneous proposed import/try ordering.
* https://github.com/RandomReaper/weewx-zabbix/issues/7: Sender output is normalized to one log line, absent measurements skipped, subprocess errors logged. Local executable fixture verifies actual stdin and stdout handling.

Tests run under WeeWX 4.10.2/5.1.0 on Python 3.10 and WeeWX 5.5.2 on Python 3.14. Local receivers and isolated install directories avoid live station changes. The tests do not establish individual external account permissions.
