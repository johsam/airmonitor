#!/usr/bin/env python

import sys
import time
import argparse
import os
import syslog
import signal
import logging

from daemon import Daemon
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from influxdb import InfluxDBClient
from voc import Voc


class Airmonitor(Daemon):

    def tick(self):
        # syslog.syslog('Tick! The time is: %s' % datetime.now())

        epoch = int(time.time())
        ppm = self.voc.getPpm()

        points = []
        point = {
            "measurement": 'voc',
            "time": epoch,
            "tags": {
                "type": "airsensor"
            },
            "fields": {
                "value": float(ppm)
            }
        }
        points.append(point)
        self.client.write_points(points, database=args.influxdb, time_precision='s')

    def sigusr1handler(self, signum, frame):
        syslog.syslog("Shutting down scheduler")

        self.scheduler.shutdown()
        self.voc.shutdown()

        syslog.syslog("Scheduler stopped, daemon is exiting...")
        sys.exit()

    def run(self):

        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_DAEMON)
        syslog.syslog("Daemon started...")

        signal.signal(signal.SIGUSR1, self.sigusr1handler)

        self.client = InfluxDBClient(args.influxhost, 8086)

        self.voc = Voc()

        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.tick, 'interval', start_date="2017-01-01", seconds=30)
        self.scheduler.start()

        while True:
            time.sleep(1)


if __name__ == "__main__":

    #
    # Parse arguments
    #

    parser = argparse.ArgumentParser(description='Simple daemon for airmonitor')

    parser.add_argument(
        '--pid-file', required=True,
        default='',
        dest='pid_file',
        help='Pid file'
    )

    parser.add_argument(
        '--start', required=False,
        default=False,
        dest='do_start',
        action='store_true'
    )

    parser.add_argument(
        '--stop', required=False,
        default=False,
        dest='do_stop',
        action='store_true'
    )

    parser.add_argument(
        '--status', required=False,
        default=False,
        dest='do_status',
        action='store_true'
    )

    parser.add_argument(
        '--restart', required=False,
        default=False,
        dest='do_restart',
        action='store_true'
    )

    parser.add_argument(
        '--run', required=False,
        default=False,
        dest='do_run',
        action='store_true'
    )

    parser.add_argument(
        '--influx-host', required=True,
        default="localhost",
        dest='influxhost'
    )

    parser.add_argument(
        '--influx-db', required=True,
        default="test",
        dest='influxdb'
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.WARN,
        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        filename="/var/log/airmonitor.log",
        filemode='a'
    )

    daemon = Airmonitor(args.pid_file, verbose=0)

    if args.do_start is True:
        syslog.syslog("Starting...")
        daemon.start()

    elif args.do_stop is True:
        syslog.syslog("Stopping...")
        daemon.stop()

    elif args.do_status is True:
        daemon.is_running()

    elif args.do_run is True:
        daemon.run()

    elif args.do_restart is True:
        syslog.syslog("Restarting...")
        daemon.restart()

    else:
        print("usage: %s start|stop|restart|run" % sys.argv[0])
        sys.exit(2)
