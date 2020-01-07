#!/usr/bin/python

import argparse
import rubrik_cdm
import threading
import Queue
import urllib3
urllib3.disable_warnings()

parser = argparse.ArgumentParser(description='List files at location in snapshot via API', add_help=False)
parser.add_argument('snapshot', type=str, metavar='SNAP', help='Snapshot to list from')
parser.add_argument('directory', type=str, metavar='DIR', help='Directory to list the contents of')
parser.add_argument('-r', '--recursive', help='List files and directories recursively', action='store_true', default=False)
parser.add_argument('-h', '--hostname', help='Hostname of Rubrik Cluster', action='store', default='localhost')
parser.add_argument('-t', '--token', type=str, help='Login token. Use either login token or username/password', action='store', default='')
parser.add_argument('-u', '--username', type=str, help='Username. Use either login token or username/password', action='store', default='')
parser.add_argument('-p', '--password', type=str, help='Password. Use either login token or username/password', action='store', default='')
parser.add_argument('--threads', type=int, help='Number of threads to use for recursive listing; default 64. Do not exceed 300', action='store', default=64)
parser.add_argument('--help', action='help', help='show this help message and exit')

args = parser.parse_args()

host = args.hostname
if args.token:
    token = args.token
    r = rubrik_cdm.Connect(host,api_token=token)
else:
    user = args.username
    passwd = args.password
    r = rubrik_cdm.Connect(host,user,passwd)
lsdir = args.directory
snap = args.snapshot
threads = args.threads

l = list()
q = Queue.Queue()

def worker():
    while True:
        i = q.get()
        ls(i[0], i[1])
        q.task_done()

def ls(snap, path):
    params = {"snapshot_id":snap, "path":path}
    response = r.get("internal", "/browse", authentication=True, params=params)
    data = response[u'data']
    if len(data) == 0:
        l.append(path + '/')
    else:
        for i in data:
            filemode = i[u'fileMode']
            newpath = path + ('' if path == '/' else '/') + i[u'filename']
            if args.recursive and filemode == u'directory':
                q.put([snap, newpath])
            else:
                l.append(newpath + ('/' if filemode == u'directory' else ''))

ls(snap, lsdir)

for i in range(threads):
    t = threading.Thread(target=worker)
    t.daemon = True
    t.start()

q.join()

for i in sorted(l):
    print(i)