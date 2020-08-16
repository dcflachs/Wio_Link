#!/usr/bin/python

import os
from datetime import timedelta
from datetime import datetime
import json
import sqlite3 as lite
import re
import jwt
import md5
import hashlib
import base64
import httplib
import uuid
from shutil import copy
from build_firmware import *
import yaml
import threading
import time
import smtplib
import traceback
import config as server_config

from tornado.httpserver import HTTPServer
from tornado.tcpserver import TCPServer
from tornado import ioloop
from tornado import gen
from tornado import iostream
from tornado import web
from tornado import websocket
from tornado import escape
from tornado.options import define, options
from tornado.log import *
from tornado.concurrent import Future
from tornado_cors import CorsMixin
from tornado.ioloop import IOLoop

from coroutine_msgbus import *

from handlers import NodeBaseHandler

class V2HandlersState():
    def __init__(self, cur, conns):
        self.well_known = {}
        self.v2_listener = V2Listener(self, cur, conns)


class V2Listener():
    def __init__(self, state, cur, conns):
        self.db_cur = cur
        self.v2_state = state
        self.conns = conns
        self.db_cur.execute('select * from users')
        rows = cur.fetchall()
        for row in rows:
            self.well_known_subscriber(row["user_id"])

    @gen.coroutine
    def well_known_subscriber(self, user_id):
        event_q = CoEventBus().listener('/event/users/{}'.format(user_id)).create_queue()
        while True:
            event = yield event_q.get()
            if event and event["event_type"] == "stat" and event["event_data"]["online"]:
                node_sn = event["node_sn"]
                self.db_cur.execute("select * from nodes where node_sn='%s'" % (node_sn))
                r = self.db_cur.fetchone()
                if r:
                    yield gen.sleep(1)
                    gen_log.info('INFO: V2 well-known listener handled node: {}'.format(node_sn))
                    response = yield self.attempt_request(".well-known", node_sn, self.conns, r["name"])

    @gen.coroutine
    def attempt_request(self, uri, node_sn, conns, name):
        if node_sn in conns:
            conn = conns[node_sn]
            result_ok = False
            for x in range(3):
                if not conn.killed:
                    try:
                        cmd = "GET /%s\r\n"%(uri)
                        cmd = cmd.encode("ascii")
                        ok, resp = yield conn.submit_and_wait_resp (cmd, "resp_get", 3)
                        if ok:
                            if 'msg' in resp and type(resp['msg']) == dict:
                                resp['msg']['name'] = name
                                resp['msg']['timestamp'] = datetime.now().isoformat()
                        if not ('status' in resp and resp['status'] != 200):
                            self.v2_state.well_known[node_sn] = resp['msg']
                            result_ok = True
                            break
                    except web.HTTPError:
                        pass
                    except Exception, e:
                        gen_log.error(e)
        raise gen.Return(result_ok)

class NodeV2WellKnownHandler(NodeBaseHandler):

    def initialize (self, conns, state_waiters, state_happened, state_cached):
        self.conns = conns
        self.state_waiters = state_waiters
        self.state_happened = state_happened
        self.node_responses = state_cached.well_known

    @gen.coroutine
    def pre_request(self, req_type, uri):
        return True

    @gen.coroutine
    def post_request(self, req_type, uri, resp):
        #append node name to the response of .well-known
        if 'msg' in resp and type(resp['msg']) == dict:
            resp['msg']['name'] = self.node['name']
            resp['msg']['timestamp'] = datetime.now().isoformat()

    @gen.coroutine
    def get(self, uri):

        uri = uri.split("?")[0]
        gen_log.debug("get: "+ str(uri))

        node = self.get_node()
        if not node:
            return
        self.node = node

        if not self.pre_request('get', uri):
            return

        attempt_result = yield self.attempt_request(uri, node['node_sn'])

        if attempt_result or node['node_sn'] in self.node_responses:
            self.resp(200,meta=self.node_responses[node['node_sn']])
        else:
            self.resp(404, "Node is offline and no info is cached")

    @gen.coroutine
    def attempt_request(self, uri, node_sn):
        result_ok = False
        if node_sn in self.conns:
            conn = self.conns[node_sn]
            if not conn.killed:
                try:
                    cmd = "GET /%s\r\n"%(uri)
                    cmd = cmd.encode("ascii")
                    ok, resp = yield conn.submit_and_wait_resp (cmd, "resp_get")
                    if ok:
                        self.post_request('get', uri, resp)
                    if not ('status' in resp and resp['status'] != 200):
                        self.node_responses[node_sn] = resp['msg']
                        result_ok = True
                except web.HTTPError:
                    # raise
                    pass
                except Exception, e:
                    gen_log.error(e)
        raise gen.Return(result_ok)