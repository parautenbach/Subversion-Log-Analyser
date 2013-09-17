# Copyright 2013 Pieter Rautenbach
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pysvn

# Subversion path separator
SVN_SEP = '/'
# Version number separator
VER_SEP = '.'

def setup_svn_client(username, password):
    """Create and configure an instance of a SVN client.
    """
    client = pysvn.Client()
    client.set_store_passwords(False)
    client.set_auth_cache(False)
    client.set_default_username(username)
    client.set_default_password(password)
    client.exception_style = 1
    return client
