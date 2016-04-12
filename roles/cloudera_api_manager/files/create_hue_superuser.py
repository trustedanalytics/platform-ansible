#!/usr/bin/env python
# Copyright (c) 2015 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import httplib2
import urllib
import sys
from re import match, search, DOTALL

ACCEPTED_CODES = '[23]..'
if len(sys.argv) > 2:
  URL = 'http://{0}:8888/accounts/login/'.format(sys.argv[1])
  CF_PASS = sys.argv[2]
else:
  print "Hue adress and cf password required"
  sys.exit(0)

# request to extract csrfmiddlewaretoken
h = httplib2.Http()
h.add_credentials('cf', CF_PASS)
resp, content = h.request(URL)

result = search("<input[^>]*name=['\"]csrfmiddlewaretoken['\"][^>]*value=['\"]([^>'\"]*)['\"][^>]*>", content, DOTALL)
if result is None:
  print 'Invalid response. Wrong backend is activated'
  sys.exit(1)

token = result.group(1)

body = {'csrfmiddlewaretoken': token, 'username': 'cf', 'password': CF_PASS, 'next': '/'}

headers = {'Cookie': 'csrftoken={0};'.format(token), 'Content-Type': 'application/x-www-form-urlencoded'}
resp, content = h.request(URL, 'POST', body=urllib.urlencode(body), headers=headers)

if match(ACCEPTED_CODES, resp['status']) is None:
  sys.exit(1)

print 'Account created'
sys.exit(0)
