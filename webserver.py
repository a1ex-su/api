import git
import json
import logging
import os
import sys
import tarfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from os import walk
from pathlib import Path


logging.basicConfig(format=u'[%(asctime)s] %(message)s', level=logging.INFO)

# TEMPLATES_REPO = "https://github.com/Lord-Griffin/faas-template.git"

if not os.environ.get('TEMPLATES_REPO'):
    logging.error('Variable TEMPLATES_REPO is not set')
    sys.exit(1)

if os.path.isdir('faas-template/.git'):
    logging.info("The repository already exists")
    repo = git.Repo("faas-template")

    logging.info("Pull changes")
    repo.remotes.origin.pull()
else:
    logging.info("the repository does not exist")

    logging.info("Clone")
    repo = git.Repo.clone_from(os.environ['TEMPLATES_REPO'], 'faas-template')

templates = []

for (_, dirnames, _) in walk("faas-template/template"):
    templates.extend(dirnames)
    break

logging.info('Templates: {}'.format(str.join(',', templates)))

if not Path("distribs").exists():
    os.mkdir('distribs')

# Create archives
for template in templates:
    if not Path("distribs/{}.tar.gz".format(template)).exists():
        print("Archive not exists")
        tar = tarfile.open("distribs/" + template + ".tar.gz", "w:gz")
        tar.add("faas-template/template/{}/function".format(template), arcname="function")


class Serv(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            templates_response = []
            for tmpl in templates:
                templates_response.append({"name": 'template-' + tmpl, "runtime": tmpl,
                                           "link": "http://" + self.headers.get('host') + "/" + tmpl + ".tar.gz"})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(templates_response).encode())
        else:
            try:
                with open('distribs/' + self.path[1:], 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/x-gzip')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(404)
                self.send_header('Content-Type', 'Application/json')
                self.end_headers()
                self.wfile.write('{"error": "template not found"}'.encode())


httpd = HTTPServer(('', 8000), Serv)
httpd.serve_forever()
