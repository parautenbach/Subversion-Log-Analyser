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

# Imports
try:
    import re
    import sys
    import traceback
    import pysvn
    import utils
except Exception as ex:
    print('One or more classes or modules could not be imported: {0}'.format(ex))
    exit(1)

# Patterns
__REVISION_START_PATTERN = '^r(\d+) \| (\w+?) \| (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?$'
__REVISION_START_REGEX = re.compile(__REVISION_START_PATTERN)
__MAD_PATTERN = '^\s+(M|A|D)\s+(.*)$'
__MAD_REGEX = re.compile(__MAD_PATTERN)
__DIFF_SPLIT_PATTERN = '\0|\r|\n'
__HUNK_START_PATTERN = '@@ \-(\d+),(\d+) \+(\d+),(\d+) @@'
__HUNK_START_REGEX = re.compile(__HUNK_START_PATTERN)
__DIFF_LINE_ADDED_PATTERN = '^\+(?!\+\+)'
__DIFF_LINE_ADDED_REGEX = re.compile(__DIFF_LINE_ADDED_PATTERN)
__DIFF_LINE_DELETED_PATTERN = '^\-(?!\-\-)'
__DIFF_LINE_DELETED_REGEX = re.compile(__DIFF_LINE_DELETED_PATTERN)

# Exclusions
__IGNORED_USERNAMES = set(['teamcity', 'build'])
__IGNORED_PATH_PATTERNS = set(['/dev/third-party', '/tags'])
#__IGNORED_PATH_PATTERNS = set([])

# Subversion statuses
__ADD = 'A'
__MOD = 'M'
__DEL = 'D'

# Subversion credentials
__SVN_BASE_URL = 'http://example.com/svn'
__SVN_USERNAME = 'username'
__SVN_PASSWORD = 'password'

# Tester methods
def is_revision_start(line):
    return not __REVISION_START_REGEX.search(line) is None

def is_mad_line(line):
    return not __MAD_REGEX.search(line) is None

def is_ignored_path(path):
    for ignored in __IGNORED_PATH_PATTERNS:
        if ignored in path:
            return True

def is_hunk(line):
    return not __HUNK_START_REGEX.search(line) is None

def is_line_added(line):
    return not __DIFF_LINE_ADDED_REGEX.search(line) is None

def is_line_deleted(line):
    return not __DIFF_LINE_DELETED_REGEX.search(line) is None

# Regex parser methods
def get_revision_start_matches(line):
    match = __REVISION_START_REGEX.match(line)
    revision = match.group(1)
    username = match.group(2)
    datetime = match.group(3)
    return (revision, username, datetime)

def get_mad_matches(line):
    match = __MAD_REGEX.match(line)
    status = match.group(1)
    path = match.group(2)
    return (status, path)

# Main
def main():
    """ Script to parse an SVN log for analysing developers' commits.

    Exit codes:
    0 - normal termination
    1 - other errors
    2 - syntax error
    """

    try:
        client = utils.setup_svn_client(__SVN_USERNAME, __SVN_PASSWORD)
        file_mods = {}
        line_mods = {}
        is_first_line = True
        print('revision,username,datetime,files_modified,files_added,files_deleted,lines_modified,lines_added,lines_deleted')
        for line in sys.stdin:
            #print(line.strip())
            if is_revision_start(line):
                if not is_first_line and not username in __IGNORED_USERNAMES:
                    print('{0},{1},{2},{3},{4},{5},{6},{7},{8}'.format(revision, username, datetime,
                                                                       file_mods[__MOD], file_mods[__ADD], file_mods[__DEL],
                                                                       line_mods[__MOD], line_mods[__ADD], line_mods[__DEL]))
                file_mods = {__MOD: 0, __ADD: 0, __DEL: 0}
                line_mods = {__MOD: 0, __ADD: 0, __DEL: 0}
                (revision, username, datetime) = get_revision_start_matches(line)
                is_first_line = False
            elif is_mad_line(line):
                (status, path) = get_mad_matches(line)
                if is_ignored_path(path):
                    continue
                revisionNr = int(revision)
                currRev = pysvn.Revision(pysvn.opt_revision_kind.number, revisionNr)
                prevRev = pysvn.Revision(pysvn.opt_revision_kind.number, revisionNr - 1)
                full_path = __SVN_BASE_URL + path
                try:
                    diff = client.diff(url_or_path=full_path, revision2=currRev, revision1=prevRev, tmp_path='.')
                    diff_lines = re.split(__DIFF_SPLIT_PATTERN, diff)
                    lines_added = 0
                    lines_deleted = 0
                    for i in reversed(range(len(diff_lines))):
                        diff_line = diff_lines[i]
                        if is_hunk(diff_line):
                            if lines_added == lines_deleted:
                                line_mods[__MOD] += lines_added
                            else:
                                line_mods[__ADD] += lines_added
                                line_mods[__DEL] += lines_deleted
                            lines_added = 0
                            lines_deleted = 0
                        elif is_line_added(diff_line):
                            lines_added += 1
                        elif is_line_deleted(diff_line):
                            lines_deleted += 1
                except pysvn.ClientError:
                    pass
                file_mods[status] += 1

    except Exception as ex:
        print('An unexpected error occurred')
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
