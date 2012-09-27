#!/usr/bin/python
Import sys
import os
import ConfigParser
import requests
import json
#import pymongo
import time
#import datetime
#import threading

hosts = ['fort-pub5.etn']
mbean_bases = ['Catalina:type=GlobalRequestProcessor,name=jk-*','Catalina:type=DataSource,name=*,class=javax.sql.DataSource,host=localhost,path=/']
attributes = ['requestCount', 'numActive', 'maxActive', 'numIdle', 'maxIdle']

class dotdictify(dict):
        marker = object()
        def __init__(self, value=None):
                if value is None:
                        pass
                elif isinstance(value, dict):
                        for key in value:
                                self.__setitem__(key, value[key])
                else:
                        raise TypeError, 'expected dict'

        def __setitem__(self, key, value):
                if isinstance(value, dict) and not isinstance(value, dotdictify):
                        value = dotdictify(value)
                dict.__setitem__(self, key, value)

        def __getitem__(self, key):
                found = self.get(key, dotdictify.marker)
                if found is dotdictify.marker:
                        found = dotdictify()
                        dict.__setitem__(self, key, found)
                return found

        __setattr__ = __setitem__
        __getattr__ = __getitem__

def postRequest(host, query, mbean, attribute):
        url = 'http://jk.'+ host + '/jolokia/'
        payload = {'type':query,'mbean':mbean,'attribute':attribute}
        headers = {'content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        return dotdictify(r.json)

def feedMongo(host):
        from pymongo import Connection
        connection = Connection('localhost', 27017)
        db = connection['monitoring']
        collection = db['monitoring']
        for mbean_base in mbean_bases:
                for attribute in attributes:
                        mbean_base_response = postRequest(host, 'search', mbean_base,'')
                        for mbean in mbean_base_response.value:
                                mbean_response = postRequest(host, 'read', mbean, attribute)
                                if mbean_response.status == 404:
                                        break
                                collection.insert(mbean_response)

for host in hosts:
        while True:
                try:
                        print 'Running...'
                        feedMongo(host)
                        time.sleep(2)
                except:
                        print 'Error!'
                        raise

