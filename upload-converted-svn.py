#!/usr/bin/python

import sys, os.path, subprocess, urllib2, json

sys.path.append("/home/ai/src/wesnoth-git/data/tools/")

import wesnoth.libgithub as libgithub

upload_dirs = []

def prepare_repo(repo):
    name, version = os.path.basename(repo).split("-")
    versiondir = os.path.join("/tmp", "wescamp-upload", version)
    if versiondir not in upload_dirs:
        upload_dirs.append(versiondir)
        if not os.path.exists(versiondir):
            os.makedirs(versiondir)
    execute(["git", "clone", repo, os.path.join(versiondir, name)], versiondir)

def upload_versiondir(versiondir):
    github = libgithub.GitHub(versiondir, os.path.basename(versiondir))
    for addon in os.listdir(versiondir):
        addon = github.addon(addon)
        reponame = "{0}-{1}".format(addon.name, addon.github.version)
        print "Upload add-on {0} version {1} from dir {2}".format(addon.name, addon.github.version, addon._get_dir())
        execute(["git", "remote", "set-url", "origin", "git@github.com:wescamp/{0}".format(reponame)], addon._get_dir())
        create_remote(reponame)
        addon.commit("Initial upload")

_GITHUB_API_BASE = "https://api.github.com/"
_GITHUB_API_REPOS = "orgs/wescamp/repos"
_GITHUB_API_TEAMS = "orgs/wescamp/teams"
# PUT /teams/:id/repos/:org/:repo
_GITHUB_API_TEAM_REPO = "teams/{0}/repos/wescamp/{1}"

def create_remote(reponame):
    url = _GITHUB_API_BASE + _GITHUB_API_REPOS
    request = urllib2.Request(url)
    requestdata = { "name" : reponame }
    repodata = github_api_request(request, requestdata, authenticate=True)

    url = _GITHUB_API_BASE + _GITHUB_API_TEAMS
    request = urllib2.Request(url)
    teams = github_api_request(request, authenticate=True)

    # This can probably be cleaner
    team_number = [team["id"] for team in teams if team["name"] == "Developers"][0]

    # PUT /teams/:id/repos/:org/:repo
    url = _GITHUB_API_BASE + _GITHUB_API_TEAM_REPO
    request = urllib2.Request(url.format(team_number, reponame))
    request.get_method = lambda: "PUT"
    # Github requires data for every modifying request, even if there is none
    github_api_request(request, data="", authenticate=True)


def github_api_request(request, data=None, authenticate=False):
    if data == "":
        # Workaround for PUTs requiring data, even if you have nothing to pass
        request.add_data(data)
    elif data:
        request.add_data(json.dumps(data))

    # Manually adding authentication data
    # Basic works in curl, but urllib2 doesn't
    # probably because github's API doesn't send a www-authenticate header
    if authenticate:
        from base64 import encodestring
        base64string = encodestring(github_userpass()).replace('\n','')
        request.add_header("Authorization", "Basic {0}".format(base64string))

    try:
        response = urllib2.urlopen(request)
    except IOError as e:
        raise libgithub.Error("GitHub API failure: " + str(e))
    if response.code == 204:
        # 204 = No content
        return None
    else:
        return json.load(response)

def github_userpass():
    raise libgithub.Error("Replace this line with something returning a user:pass string")

def execute(cmd, cwd=None):
    p = subprocess.Popen(cmd, close_fds=True, cwd=cwd)
    while(p.poll() == None):
        pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: {0} <things to upload> ...".format(sys.argv[0])
        sys.exit(1)

    for repo in sys.argv[1:]:
        if not os.path.isabs(repo):
            print "Rejecting {0}: not an absolute path".format(repo)
            sys.exit(1)

    for repo in sys.argv[1:]:
        prepare_repo(os.path.realpath(repo))

    for versiondir in upload_dirs:
        print "Uploading from dir {0}".format(versiondir)
        upload_versiondir(versiondir)

