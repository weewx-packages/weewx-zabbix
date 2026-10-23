# WeeWX observations for Zabbix

Send non-null LOOP observations to Zabbix trapper items with `zabbix_sender`.
The repository also provides a Zabbix 7 template for METRICWX weather data.

This is the weewx-packages continuation, release **0.2.0**.
[Origin](ORIGIN.md) records the upstream revision; [repair notes](REPAIR_NOTES.md)
describe the maintenance changes.

The catalog archive targets WeeWX `>=5.5.2,<5.7` and Python `>=3.10,<3.15`.

## Install

Use `weectl` from the Python environment running WeeWX. With stock WeeWX 5,
install the published archive:

```sh
weectl extension install https://github.com/weewx-packages/weewx-zabbix/releases/download/v0.2.0/weewx-zabbix-0.2.0.tar.gz --config /path/to/weewx.conf
```

Replace `/path/to/weewx.conf` with your station configuration. You can also
download that URL and pass the local archive to the same command. Use elevated
permissions only when your station files require them.

## Configure the sender

Install `zabbix_sender` on the WeeWX host and create a host on your Zabbix
server. The configured host name must match Zabbix's technical host name.
The runtime uses WeeWX and the Python standard library; PyYAML is only needed
for checks that read the YAML template.

```ini
[ZABBIX]
    enable = true
    zabbix_sender = /usr/bin/zabbix_sender
    server = 127.0.0.1
    host = weewx-host
    prefix = weewx_
    unit_system = METRICWX
```

The installer registers `user.zabbix.Zabbix` as a process service. Import
[weewx_template.yaml](weewx_template.yaml) into Zabbix 7 and attach it to that
host. It expects Celsius, millimetres, m/s and hPa. Disable items for sensors
that your station does not provide. The template credits Dustin Demuth's
upstream contribution.

Alternatively, create individual items of type `Zabbix trapper`, such as
`weewx_outTemp`, combining `prefix` with the WeeWX observation name.

Restart WeeWX yourself, then check the log and Zabbix Latest data after a LOOP
packet. Nonzero sender exit status is logged as an error.

## Observations and limits

Every non-null packet value is sent, including metadata such as `dateTime` and
`usUnits`. Available keys depend on your station and other services. Without
`unit_system`, values retain their incoming units. Zero values are included.

The service invokes `zabbix_sender` synchronously for every LOOP packet. The
installer's `send_interval` setting is not read by the runtime, so it does not
throttle sending. There is no configurable sender timeout or TLS setup here.
Use the sender and server's own access controls. This service has no device
driver or archive replay.

The original [WH2600 setup diagram](doc/images/wh2600.png) shows a station feeding
WeeWX through an interceptor, then this service forwarding the readings.
The extension consumes WeeWX packets and is not tied to that hardware.

Copyright 2018 Marc Pignat. [Apache License 2.0](LICENSE).
