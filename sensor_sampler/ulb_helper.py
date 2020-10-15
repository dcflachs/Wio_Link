#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
from os import listdir
from os.path import isfile, join
import time
import argparse
import requests
import json
import re

parser = argparse.ArgumentParser()
parser.add_argument("operate", help="get,set,ota")
parser.add_argument("domain", help="domain of the server, e.g. https://us.wio.seeed.io")
parser.add_argument("access_token", help="the access token of this board")
args = parser.parse_args()

if args.operate not in ['get', 'set', 'ota', 'get-config', 'clear', 'set-config', 'pause_sampling', 'patch']:
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
        if ('.h' in file_name or '.cpp' in file_name) and not ('grove' in file_name):
            print(file_name)
            with open(file_name, 'r') as f:
                payload[file_name] = f.read()

    reg_inc = re.compile('(?#include )grove.*.h')
    with open("./Main.cpp", 'r') as f:
        for line in f:
            match = re.search(reg_inc, line)
            if match and isfile(join('./', match.group(0))):
                file_name = match.group(0)
                print(file_name)
                with open(file_name, 'r') as f:
                    payload[file_name] = f.read()

                file_name = re.sub('.h', '.cpp', file_name)
                with open(file_name, 'r') as f:
                    payload[file_name] = f.read()
                print(file_name)

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

if args.operate == 'pause_sampling':
    print('=> Setting allow sleep...')
    r = requests.post('{}/v2/node/variable/allow_sleep/0?access_token={}'.format(args.domain.rstrip('/'), args.access_token), verify=False)
    if r.status_code == 200:
        print('=> Success!')
    else:
        print('HTTP post failed, status code: {}'.format(r.status_code))
        print('Error message: {}'.format(r.text))
        sys.exit(1)

if args.operate == 'patch':
    print('=> Patching Files...')
    if not isfile("Main.cpp") or not isfile("Main.h"):
        sys.exit(1)
    
    with open("Main.cpp", 'r') as f:
        data = f.readlines()

    for line in data:
        if "sensor_sampler.h" in line:
            print("Error: Already Patched File!")
            sys.exit(1)
    
    regex_inc = re.compile("(.*(grove_.*))_gen.*")
    regex_var = re.compile("extern (.*) \*((Grove.*)_ins)")
    includes = []
    vars = []
    with open("Main.h", 'r') as f:
        for line in f:
            m = regex_inc.search(line)
            if m:
                includes.append(m)
            else:
               m = regex_var.search(line)
               if m:
                   vars.append(m)

    out_data = []
    state = 0
    for line in data:
        out_data.append(line)
        if (state == 0) and "Main.h" in line:
            out_data.append("#include \"sensor_sampler.h\"\n")
            for item in includes:
                out_data.append("{}_sampler.h\"\n".format(item.group(1)))
            out_data.append("\n")
            out_data.append("SensorSampler *SensorSampler_ins;\n")
            out_data.append("\n")
            state = 1
            continue
        if (state == 1) and "void setup()" in line:
            state = 2
            continue
        if (state == 2) and "{" in line:
            out_data.append("\tSensorSampler_ins = new SensorSampler();\n")
            out_data.append("\n")
            for item in vars:
                func = None
                name = item.group(1).lower()
                for m in includes:
                    if name in m.group(2).replace('_',''):
                        func = "__{}_sampler_register".format(m.group(2))
                        break
                if func:
                    out_data.append("\t{}(SensorSampler_ins, {}, \"{}\");\n".format(func, item.group(2), item.group(3)))
            out_data.append("\n")
            out_data.append("\tSensorSampler_ins->start_sampling();\n")
            state = 3 
            continue

    with open("Main.cpp", 'w') as f:
        f.writelines(out_data)
    print('=> Complete')