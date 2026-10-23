# Modified 2026-10-22 by weewx-packages: compatibility and tracker repairs.
# Modified 2026-10-23 by weewx-packages: restore send_interval, log a missing
#   section, a bad unit_system or a sender that cannot start instead of
#   stopping or restarting WeeWX.
#############################################################################
#
# \brief   Post weewx data to zabbix
#
# \author  marc at pignat.org
#
# \url     https://github.com/RandomReaper/weewx-zabbix
#
#############################################################################
# 
# Copyright 2018 Marc Pignat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# See the License for the specific language governing permissions and
# limitations under the License.
#
#############################################################################

from datetime import datetime
import os
import time

import weeutil.weeutil
import weewx.engine
import weewx.units
import logging

from subprocess import Popen, PIPE, STDOUT

VERSION = "0.2.1"

log = logging.getLogger(__name__)

class Zabbix(weewx.engine.StdService):
    def __init__(self, engine, config_dict):
        super(Zabbix, self).__init__(engine, config_dict)

        log.info("init")
        # A configuration error leaves the service unbound, so WeeWX keeps
        # running without it, as it does for its own uploaders.
        conf = config_dict.get('ZABBIX')
        if conf is None:
            log.error("No [ZABBIX] section in the configuration. Service not active.")
            return
        self.enable = weeutil.weeutil.to_bool(conf.get('enable', False))
        self.zabbix_sender = conf.get('zabbix_sender', '/usr/bin/zabbix_sender')
        self.prefix = conf.get('prefix', 'weewx_')
        units = conf.get('unit_system')
        if units and units not in weewx.units.unit_constants:
            log.error("Unknown unit_system %s. Service not active.", units)
            return
        self.unit_system = weewx.units.unit_constants[units] if units else None
        self.server = conf.get('server', '127.0.0.1')
        self.host = conf.get('host', 'weewx-host')
        # Minimum seconds between two runs of zabbix_sender. LOOP packets
        # that arrive sooner are dropped. 0 sends every packet.
        try:
            self.send_interval = weeutil.weeutil.to_float(conf.get('send_interval', 0))
        except ValueError:
            log.error("send_interval must be a number of seconds. Service not active.")
            return
        self.last_time = None

        log.debug("self.enable=" + str(self.enable))
        log.debug("self.zabbix_sender=" + self.zabbix_sender)
        log.debug("self.prefix=" + self.prefix)
        log.debug("self.server=" + self.server)
        log.debug("self.host=" + self.host)
        log.debug("self.send_interval=" + str(self.send_interval))

        if self.enable:
            self.bind(weewx.NEW_LOOP_PACKET, self.loop)

    def loop(self, event):
        log.debug("loop data:")
        if (self.send_interval > 0 and self.last_time is not None
                and time.time() - self.last_time < self.send_interval):
            log.debug("Ignoring packet. Next update in %.0fs",
                      self.send_interval - (time.time() - self.last_time))
            return
        self.last_time = time.time()
        s = ""
        packet = event.packet
        if self.unit_system is not None:
            packet = weewx.units.to_std_system(packet, self.unit_system)
        for key,value in packet.items():
            if value is None:
                continue
            l=self.host + " " + self.prefix+key + " " + str(value) + "\n"
            s+=l
            log.debug(l.rstrip())

        c = [self.zabbix_sender, "-z", self.server, "-i", "-"]
        log.debug("command line : " + str(c))
        # weewxd catches an OSError that reaches it, logs it and restarts
        # the engine after 10 s. A zabbix_sender that cannot be started,
        # for example because the path is wrong, would do that with every
        # LOOP packet. Drop the packet instead.
        try:
            p = Popen(c, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
            sender_stdout = p.communicate(input=s.encode())[0]
        except OSError as e:
            log.error('Cannot run %s, packet dropped: %s', self.zabbix_sender, e)
            return
        result = ' '.join(sender_stdout.decode(errors='replace').split())
        if p.returncode:
            log.error('%s exited %d: %s', self.zabbix_sender, p.returncode, result)
        else:
            log.debug('%s result: %s', self.zabbix_sender, result)
