#!/usr/bin/env python3
# encoding: utf-8

import yaml
import argparse
from ipaddress import IPv4Network
from glob import glob
from jinja2 import Template, Environment, FileSystemLoader
from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from pprint import pprint as pp

from define import BASEFOLDER, TEMPLATES


def parse_args(args=None):
    """
    Parse the arguments/options passed to the program on the command line.
    """

    parser = argparse.ArgumentParser(description=__doc__,
                        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('devices', type=str, metavar='devices')
    parser.add_argument('-pp', '--pprint-only', dest='pp', action='store_true')

    subparsers = parser.add_subparsers(help='sub-command help')

    evpn = subparsers.add_parser('evpn', help='evpn only')
    evpn.set_defaults(which='evpn')
    evpn.add_argument('-t', '--type-route', type=str, dest='type')
    evpn.add_argument('-nv', '--number-of-vlan', type=int, dest='nv')
    evpn.add_argument('-vid', '--first-vlan-id', type=int, dest='vid')

    (args, rest_args) = parser.parse_known_args()
    if args.vid is None:
        args.vid = 1

    return args

def show_diff(cu):
    """
    show configuration | compare
    """
    return cu.diff()

def commit(cu):
    """
    issues commit check follofs commit if everything is fine,
    prints error otherwise
    """
    if cu.commit_check():
        if cu.commit():
            print("Done")
    else:
        print("Something is wrong with commit")
        return

def push(hostname, config):
    if args.pp:
        print(config)
    else:
        dev = Device(hostname, user='ularc', password='Poclab123')
        dev.open(gather_facts=False)
        dev.timeout = 60
        dev.bind(cu=Config)
        with Config(dev, mode='private') as cu:
            cu.load('delete policy-options policy-statement EVPN-host-routes term default')
            cu.load(config, format='text', merge=True)
            cu.load('set policy-options policy-statement EVPN-host-routes term default then reject')
            diff = show_diff(cu)
            if diff:
                print(diff)
                commit(cu)
            #cu.rollback()
        dev.close()

def do_evpn(device, **kwargs):
    def _do_routing_insatnce():
        template = env.get_template('evpn/routing-instances.j2')
        vlans = list(range(args.vid, args.vid+args.nv))
        vlan_list = str(vlans[0]) + '-' + str(vlans[-1])
        return template.render({'vlans': vlans, 
                                'type': 'Type2' if args.type == 'type2' else 'VRF_L3'
                                })

    def _do_vlans():
        template = env.get_template('evpn/vlans.j2')
        vlans = list(range(args.vid, args.vid+args.nv))
        return template.render({'vlans': vlans })

    def _do_protocol():
        template = env.get_template('evpn/evpn-protocol.j2')
        vlans = list(range(args.vid, args.vid+args.nv))
        return template.render({'vlans': vlans})

    def _do_policy():
        template = env.get_template('evpn/policies.j2')
        vlans = list(range(args.vid, args.vid+args.nv))
        supernet = list(IPv4Network(u'100.0.0.0/12').subnets(prefixlen_diff=12))
        subnets = [supernet[int(vlanid)] for vlanid in vlans]
        return template.render({'vlans': vlans,
                                'type': 'Type2' if args.type == 'type2' else 'VRF_L3',
                                'subnets': subnets
  							   })

    def _do_interfaces():
        template = env.get_template('evpn/interfaces.j2')
        supernet = list(IPv4Network(u'100.0.0.0/12').subnets(prefixlen_diff=12))
        macs = []
        vlans = list(range(args.vid, args.vid+args.nv))
        subnets = [str(supernet[int(vlanid)][1]) for vlanid in vlans]
        for i in vlans:
            s = "{0:011d}0".format(i)
            macs.append(":".join(a+b for a,b in zip(s[::2], s[1::2])))

        return template.render({'vlans': vlans,
								'macs': macs,
                                'base_interface': kwargs['base_interface'],
                                'type': 'Type2' if args.type == 'type2' else 'VRF_L3',
                                'subnets': subnets,
                                })

    device_config = ''
    device_config += _do_routing_insatnce() + '\n'
    device_config += _do_vlans() + '\n'
    device_config += _do_protocol() + '\n'
    device_config += _do_policy() + '\n'
    device_config += _do_interfaces() + '\n'
    push(device, device_config)

if __name__ == '__main__':
    args = parse_args()
    env = Environment(loader=FileSystemLoader(TEMPLATES))
    env.globals.update(zip=zip)
    env.globals.update(enum=enumerate)

    with open(args.devices, 'r') as f:
        device_dict = yaml.safe_load(f)
    devices = device_dict['PEs']
    if args.which == 'evpn':
        for device in devices.items():
            do_evpn(device[0], **device[1])
