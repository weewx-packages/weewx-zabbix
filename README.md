# WeeWX observations for Zabbix

Send non-null LOOP observations to Zabbix trapper items with `zabbix_sender`.
The repository also provides a Zabbix 7 template for METRICWX weather data.

This is the weewx-packages continuation of
[RandomReaper/weewx-zabbix](https://github.com/RandomReaper/weewx-zabbix).
[Origin](ORIGIN.md) records the upstream revision; [repair notes](REPAIR_NOTES.md)
describe the maintenance changes.

## Requirements

* `zabbix_sender` on the WeeWX host.
* A Zabbix server with a host for the station. The configured `host` must match
  the technical host name in Zabbix.

The runtime uses only WeeWX and the Python standard library.

## Installation

Install `zabbix` from the [WeeWX packages catalog](https://github.com/weewx-packages/catalog/blob/main/packages/zabbix.md).
The catalog page lists the current release, its WeeWX and Python
requirements, and the install, update and removal commands.

The installer registers `user.zabbix.Zabbix` as a process service and adds a
`[ZABBIX]` section. Adjust it as shown below, restart WeeWX, then check the
WeeWX log and the Zabbix latest data after the first LOOP packet.

## Configuration

```ini
[ZABBIX]
    enable = true
    zabbix_sender = /usr/bin/zabbix_sender
    server = 127.0.0.1
    host = weewx-host
    prefix = weewx_
    unit_system = METRICWX
```

| Option | Default | Meaning |
|---|---|---|
| `enable` | `false` | Send data. The installer sets it to `true`. |
| `zabbix_sender` | `/usr/bin/zabbix_sender` | Path of the `zabbix_sender` program. |
| `server` | `127.0.0.1` | Zabbix server, passed to `zabbix_sender -z`. |
| `host` | `weewx-host` | Zabbix host that receives the values. |
| `prefix` | `weewx_` | Prepended to each WeeWX observation name to form the item key. |
| `unit_system` | none | `US`, `METRIC` or `METRICWX`. Without it, values keep their incoming units. |
| `send_interval` | `0` | Minimum seconds between two runs of `zabbix_sender`. LOOP packets in between are dropped. `0` sends every packet. |

Without the `[ZABBIX]` section, or with an unknown `unit_system` or a
non-numeric `send_interval`, the service logs an error and stays off. WeeWX
keeps running.

### Using the template

Import [weewx_template.yaml](weewx_template.yaml) into Zabbix 7 and link it to
the station's host. It expects `prefix = weewx_` and `unit_system = METRICWX`,
that is Celsius, millimetres, m/s and hPa. Disable the items for sensors your
station does not have.

### Creating items by hand

Create an item of type `Zabbix trapper` for each observation you want. The key
is `prefix` followed by the WeeWX observation name, for example
`weewx_outTemp`.

## Limitations

* Every non-null value of a LOOP packet is sent, including zero values and
  metadata such as `dateTime` and `usUnits`. The keys depend on your station
  and other services.
* `zabbix_sender` runs synchronously for every packet it sends. There is no
  timeout.
* A nonzero exit status of `zabbix_sender` is logged as an error. If the
  program cannot be started, for example because the path is wrong, the error
  is logged and the packet is dropped. This repeats with every LOOP packet.
* There is no TLS or authentication setting. Use the access controls of
  `zabbix_sender` and the Zabbix server.
* The service sends LOOP packets only. It does not replay archive records.

The original [WH2600 setup diagram](doc/images/wh2600.png) shows a station
feeding WeeWX through an interceptor, then this service forwarding the
readings. The service works with any WeeWX station.

## Development

```sh
python -m pytest -q tests
```

Run it in a Python environment with WeeWX, pytest and PyYAML installed. The
template test reads the YAML file.

## License

Copyright 2018 Marc Pignat. [Apache License 2.0](LICENSE).

The Zabbix 7 template is adapted from a contribution by Dustin Demuth.
