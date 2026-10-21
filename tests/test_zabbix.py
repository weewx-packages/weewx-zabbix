import logging
import pathlib
from types import SimpleNamespace

import pytest
import yaml
import weewx
import zabbix


class Engine:
    def bind(self, *args):
        pass


def test_sender_process_and_one_line_output(tmp_path, caplog):
    sender = tmp_path / 'sender'
    payload = tmp_path / 'payload'
    sender.write_text('#!/usr/bin/env python3\nimport pathlib,sys\npathlib.Path('+repr(str(payload))+').write_bytes(sys.stdin.buffer.read())\nprint("processed: 2;\\n failed: 0")\n')
    sender.chmod(0o755)
    service = zabbix.Zabbix(Engine(), {'ZABBIX':{'enable':True,'zabbix_sender':str(sender),'unit_system':'METRICWX'}})
    with caplog.at_level(logging.DEBUG):
        service.loop(SimpleNamespace(packet={'dateTime':1700000000,'usUnits':weewx.US,'outTemp':32,'windDir':None}))
    lines = payload.read_text().splitlines()
    assert 'weewx-host weewx_outTemp 0.0' in lines
    assert not any('windDir' in line for line in lines)
    assert any(r.message.endswith('processed: 2; failed: 0') for r in caplog.records)
    assert not any('\n' in r.message for r in caplog.records)


def test_template_has_unique_items_and_matching_metric_units():
    document = yaml.safe_load((pathlib.Path(__file__).parents[1]/'weewx_template.yaml').read_text())['zabbix_export']
    assert document['version'] == '7.0'
    items = document['templates'][0]['items']
    assert len({i['uuid'] for i in items}) == len(items)
    assert len({i['key'] for i in items}) == len(items)
    temperature = next(i for i in items if i['key']=='weewx_outTemp')
    assert temperature['units'] == '°C'
    assert 'preprocessing' not in temperature
