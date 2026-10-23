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


def test_missing_sender_drops_packet_without_oserror(tmp_path, caplog):
    service = zabbix.Zabbix(Engine(), {'ZABBIX':{'enable':True,'zabbix_sender':str(tmp_path/'missing')}})
    service.loop(SimpleNamespace(packet={'dateTime':1700000000,'usUnits':weewx.US,'outTemp':32}))
    assert 'Cannot run' in caplog.text


@pytest.mark.parametrize('config', [{}, {'ZABBIX':{'enable':True,'unit_system':'SI'}}])
def test_bad_configuration_leaves_service_unbound(config, caplog):
    bound = []
    engine = SimpleNamespace(bind=lambda *args: bound.append(args))
    zabbix.Zabbix(engine, config)
    assert bound == []
    assert 'Service not active' in caplog.text


def test_send_interval_drops_packets_in_between(tmp_path, monkeypatch):
    sender = tmp_path / 'sender'
    calls = tmp_path / 'calls'
    sender.write_text('#!/bin/sh\necho x >> '+str(calls)+'\ncat > /dev/null\n')
    sender.chmod(0o755)
    clock = [1000.0]
    monkeypatch.setattr(zabbix.time, 'time', lambda: clock[0])
    service = zabbix.Zabbix(Engine(), {'ZABBIX':{'enable':True,'zabbix_sender':str(sender),'send_interval':'60'}})
    for now in [1000.0, 1030.0, 1061.0]:
        clock[0] = now
        service.loop(SimpleNamespace(packet={'dateTime':int(now),'usUnits':weewx.US,'outTemp':32}))
    assert len(calls.read_text().splitlines()) == 2
