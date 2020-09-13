#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
from os import listdir
from os.path import isfile, join
import time
import argparse
import requests
import json

parser = argparse.ArgumentParser()
parser.add_argument("operate", help="get,set,ota")
parser.add_argument("domain", help="domain of the server, e.g. https://us.wio.seeed.io")
parser.add_argument("access_token", help="the access token of this board")
args = parser.parse_args()

if args.operate not in ['get', 'set', 'ota', 'get-config', 'clear', 'set-config']:
    print('invalid operation - {}!'.format(args.operate))
    sys.exit(1)

if args.operate == 'get':
    r = requests.get('{}/v1/cotf/project?access_token={}'.format(args.domain.rstrip('/'), args.access_token), verify=False)
    if r.status_code == 200:
        print('=> The Response\n')
        print(r.json())
        print('\n')

        for file_name, file_contents in r.json().items():
            with open(file_name, 'w') as f:
                f.write(file_contents)
        print('=> Saved into files')
    else:
        print('HTTP get failed, status code: {}'.format(r.status_code))
        print('Error message: {}'.format(r.text))
        sys.exit(1)

if args.operate == 'set':
    files = [f for f in listdir('./') if isfile(join('./', f))]
    payload = {}
    for file_name in files:
        if '.h' in file_name or '.cpp' in file_name:
            with open(file_name, 'r') as f:
                payload[file_name] = f.read()

    print(payload)
    print('\n')
    print('=> Posting contents...')
    r = requests.post('{}/v1/cotf/project?access_token={}'.format(args.domain.rstrip('/'), args.access_token), json=payload, verify=False)
    if r.status_code == 200:
        print('=> Success!')
    else:
        print('HTTP post failed, status code: {}'.format(r.status_code))
        print('Error message: {}'.format(r.text))
        sys.exit(1)

if args.operate == 'ota':
    r = requests.post('{}/v1/ota/trigger?access_token={}&build_phase=2'.format(args.domain.rstrip('/'), args.access_token), verify=False)
    if r.status_code == 200:
        print('=> Success! The OTA has been triggered.')
    else:
        print('HTTP post failed, status code: {}'.format(r.status_code))
        print('Error message: {}'.format(r.text))
        sys.exit(1)

    while(True):
        r = requests.get('{}/v1/ota/status?access_token={}'.format(args.domain.rstrip('/'), args.access_token), verify=False)
        msg = r.json()
        print(msg)
        print('\n')
        if 'ota_status' not in msg:
            break
        if msg.get('ota_status') != 'going':
            break
        time.sleep(1)

if args.operate == 'get-config':
    r = requests.get('{}/v1/node/config?access_token={}'.format(args.domain.rstrip('/'), args.access_token), verify=False)
    if r.status_code == 200:
        print('=> The Response\n')
        print(r.json())
        print('\n')

        with open("{}-config.json".format(args.access_token), 'w') as f:
            json.dump(r.json(),f)
        print('=> Saved into files')
    else:
        print('HTTP get failed, status code: {}'.format(r.status_code))
        print('Error message: {}'.format(r.text))
        sys.exit(1)

if args.operate == 'set-config':
    file_path = "{}-config.json".format(args.access_token)

    if not isfile(file_path):
        sys.exit(1)

    with open(file_path, 'r') as f:
        payload = json.load(f)
        payload = payload['config']

    print(payload)
    print('\n')
    print('=> Posting contents...')
    r = requests.post('{}/v1/ota/trigger?access_token={}&build_phase=1'.format(args.domain.rstrip('/'), args.access_token), json=payload, verify=False)
    if r.status_code == 200:
        print('=> Success!')
    else:
        print('HTTP post failed, status code: {}'.format(r.status_code))
        print('Error message: {}'.format(r.text))
        sys.exit(1)
    while(True):
        r = requests.get('{}/v1/ota/status?access_token={}'.format(args.domain.rstrip('/'), args.access_token), verify=False)
        msg = r.json()
        print(msg)
        print('\n')
        if 'ota_status' not in msg:
            break
        if msg.get('ota_status') != 'going':
            break
        time.sleep(1)

if args.operate == 'clear':
    print('=> Posting contents...')
    r = requests.post('{}/v1/ota/trigger?access_token={}&build_phase=0'.format(args.domain.rstrip('/'), args.access_token), verify=False)
    if r.status_code == 200:
        print('=> Success!')
    else:
        print('HTTP post failed, status code: {}'.format(r.status_code))
        print('Error message: {}'.format(r.text))
        sys.exit(1)