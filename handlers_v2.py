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
import collections

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
        self.write_cache = {}
        self.events_cache = {}
        self.v2_listener = V2Listener(self, cur, conns)


class V2Listener():
    EVENT_QUEUE_LENGTH = 50

    def __init__(self, state, cur, conns):
        self.db_cur = cur
        self.v2_state = state
        self.conns = conns
        self.db_cur.execute('select * from users')
        rows = cur.fetchall()
        for row in rows:
            self.well_known_subscriber(row["user_id"])
            self.queued_write_subscriber(row["user_id"])
            self.events_subscriber(row["user_id"])

    @gen.coroutine
    def well_known_subscriber(self, user_id):
        event_q = CoEventBus().listener('/event/users/{}'.format(user_id)).create_queue()
        while True:
            event = yield event_q.get()
            if (event and 
                event["event_type"] == "stat" and 
                event["event_data"]["online"] and 
                event["event_data"]["at"] == "xchange"):
                node_sn = event["node_sn"]
                self.db_cur.execute("select * from nodes where node_sn='%s'" % (node_sn))
                r = self.db_cur.fetchone()
                if r:
                    yield gen.sleep(1)
                    gen_log.info('INFO: V2 well-known listener handled node: {}'.format(node_sn))
                    response = yield self.attempt_request(".well-known", node_sn, self.conns, r["name"])

    @gen.coroutine
    def attempt_request(self, uri, node_sn, conns, name):
        result_ok = False
        if node_sn in conns:
            conn = conns[node_sn]
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

    @gen.coroutine
    def queued_write_subscriber(self, user_id):
        event_q = CoEventBus().listener('/event/users/{}'.format(user_id)).create_queue()
        while True:
            event = yield event_q.get()
            if (event and 
                event["event_type"] == "stat" and 
                event["event_data"]["online"] and 
                event["event_data"]["at"] == "xchange"):
                node_sn = event["node_sn"]
                if node_sn in self.v2_state.write_cache:
                    self.db_cur.execute("select * from nodes where node_sn='%s'" % (node_sn))
                    r = self.db_cur.fetchone()
                    if r:
                        keys = [k for k in self.v2_state.write_cache[node_sn]]
                        yield gen.sleep(0.5)
                        for key in keys:
                            uri = self.v2_state.write_cache[node_sn][key]
                            del self.v2_state.write_cache[node_sn][key]
                            gen_log.info('INFO: V2 {}'.format(uri))
                            response = yield self.post(uri, node_sn, self.conns)

    @gen.coroutine
    def post (self, uri, node_sn, conns):
        result_ok = False
        if node_sn in self.conns:
            conn = conns[node_sn]
            for x in range(10):
                if not conn.killed:
                    try:
                        ok, resp = yield conn.submit_and_wait_resp(uri, "resp_post", 1)
                        if not ('status' in resp and resp['status'] != 200):
                            result_ok = True
                            break
                        if 'status' in resp and resp['status'] == 404:
                            gen_log.info('INFO: V2 post to {} failed 404'.format(uri))
                            break
                    except web.HTTPError:
                        pass
                    except Exception,e:
                        gen_log.error(e)
        raise gen.Return(result_ok)

    @gen.coroutine
    def events_subscriber(self, user_id):
        event_q = CoEventBus().listener('/event/users/{}'.format(user_id)).create_queue()
        while True:
            event = yield event_q.get()
            event['timestamp'] = datetime.now().isoformat()
            if (event and 
                event["event_type"] == "grove"):
                node_sn = event["node_sn"]
                if not node_sn in self.v2_state.events_cache:
                    self.v2_state.events_cache[node_sn] = collections.deque(maxlen=self.EVENT_QUEUE_LENGTH)
                self.v2_state.events_cache[node_sn].append(event)
                
                

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

class NodeV2WriteHandler(NodeBaseHandler):

    def initialize (self, conns, state_waiters, state_happened, state_cached):
        self.conns = conns
        self.state_waiters = state_waiters
        self.state_happened = state_happened
        self.write_cache = state_cached.write_cache

    @gen.coroutine
    def pre_request(self, req_type, uri):
        return True

    @gen.coroutine
    def post_request(self, req_type, uri, resp):
        pass

    @gen.coroutine
    def post (self, uri):

        uri = uri.split("?")[0].rstrip("/")
        gen_log.info("INFO: V2 POST to: "+ str(uri))

        uri_parts = uri.split("/")

        node = self.get_node()
        if not node:
            return
        self.node = node
        node_sn = node['node_sn']

        if uri_parts[0] == ".clear":
            base_uri ="/".join((uri_parts[1:]))
            if ( node_sn in self.write_cache and 
                 base_uri in self.write_cache[node_sn] ):
                del self.write_cache[node_sn][base_uri]
                self.resp(200,meta="Cleared")
            else:
                self.resp(400,meta="No Queued Command Found")

            return

        if self.request.headers.get("content-type") and self.request.headers.get("content-type").find("json") > 0:
            self.resp(400, "Can not accept application/json post request.")
            return

        if not self.pre_request('post', uri):
            return

        cmd = "POST /%s\r\n"%(uri)
        cmd = cmd.encode("ascii")

        #Post the request directly
        if node_sn in self.conns:
            conn = self.conns[node_sn]
            if not conn.killed:
                try:
                    ok, resp = yield conn.submit_and_wait_resp(cmd, "resp_post")
                    if 'status' in resp and resp['status'] == 404:
                        self.resp(404,meta=resp['msg'])
                        return
                    elif 'status' in resp and resp['status'] != 200:
                        pass
                    else:
                        self.resp(200,meta=resp['msg'])
                        gen_log.info('INFO: V2 POST Command Sent Directly')
                        return
                except web.HTTPError:
                    pass
                except Exception,e:
                    gen_log.error(e)
        
        #Queue the post for later.
        if not node_sn in self.write_cache:
            self.write_cache[node_sn] = {}
        
        base_uri ="/".join((uri_parts[0:-1]))

        msg = "Command Queued"
        if base_uri in self.write_cache[node_sn]:
            msg = "Command Overwritten"

        self.write_cache[node_sn][base_uri] = cmd
        gen_log.info('INFO: V2 POST {}'.format(msg))
        self.resp(200, msg)

class NodeV2EventsHandler(NodeBaseHandler):

    def initialize (self, conns, state_waiters, state_happened, state_cached):
        self.conns = conns
        self.state_waiters = state_waiters
        self.state_happened = state_happened
        self.events_cache = state_cached.events_cache

    # Handles GET /v2/node/event/pop
    #         GET /v2/node/event/length
    #         POST /v2/node/event/clear

    @gen.coroutine
    def pre_request(self, req_type, uri):
        if req_type == 'get':
            if 'pop' in uri or 'length' in uri:
                return True
        elif req_type == 'post':
            if 'clear' in uri:
                return True

        return False

    @gen.coroutine
    def post_request(self, req_type, uri, resp):
        pass

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

        node_sn = node['node_sn']
        if node_sn in self.events_cache:
            if 'length' in uri.split("\\")[0]:
                length = len(self.events_cache[node_sn])
                self.resp(200,meta={'length':length})
                return
            elif 'pop' in uri.split("\\")[0]:
                if len(self.events_cache[node_sn]) > 0:
                    event = self.events_cache[node_sn].popleft()
                    self.resp(200,meta=event)
                    return
                else:
                    self.resp(204,"Queue Empty")
                    return 
            else:
                self.resp(404, "Unknown Endpoint")
                return

        self.resp(404, "Node Unknown")

    @gen.coroutine
    def post (self, uri):

        uri = uri.split("?")[0].rstrip("/")
        gen_log.info("post to: "+ str(uri))

        node = self.get_node()
        if not node:
            return
        self.node = node

        if self.request.headers.get("content-type") and self.request.headers.get("content-type").find("json") > 0:
            self.resp(400, "Can not accept application/json post request.")
            return

        if not self.pre_request('post', uri):
            return

        node_sn = node['node_sn']
        if node_sn in self.events_cache:
            self.events_cache[node_sn].clear()
            self.resp(200,"Success")
            return

        self.resp(404, "Node Unknown")
    