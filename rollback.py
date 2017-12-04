#!/usr/bin/env python3
# encoding: utf-8

import yaml
import argparse
from jnpr.junos import Device
from jnpr.junos.utils.config import Config

from define import BASEFOLDER, TEMPLATES

def parse_args(args=None):
    """
    Parse the arguments/options passed to the program on the command line.
    """

    parser = argparse.ArgumentParser(description=__doc__,
                        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('devices', type=str, metavar='devices')
    (args, rest_args) = parser.parse_known_args()

    return args

def rollback(hostname):
    dev = Device(hostname, user='ularc', password='Poclab123')
    dev.open(gather_facts=False)
    dev.timeout = 60
    dev.bind(cu=Config)
    with Config(dev, mode='private') as cu:
        cu.rollback(1)
        cu.commit()
        print('{} - Done'.format(hostname))
    dev.close()

if __name__ == '__main__':
    args = parse_args()
    with open(args.devices, 'r') as f:
        device_dict = yaml.safe_load(f)
    devices = device_dict['PEs']
    for device in devices.items():
        rollback(device[0])
