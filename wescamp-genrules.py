#! /usr/bin/env python

import pysvn

BASE_URL = "svn://svn.berlios.de/wescamp-i18n"
BRANCHES = "/branches/"
TRUNK = "/trunk/"


def is_special(subject):
    return subject.endswith("build-system")

def grab_urls(dirents):
    return [item["name"] for item in dirents]

def format_name(url):
    return url.split("/")[-1]

def strip_base(url):
    return url.replace(BASE_URL, "")

if __name__ == "__main__":
    # Repos format: [(name, url), ...]
    repos = []
    client = pysvn.Client()
    rules = open("wescamp.rules", "w")

    branches = grab_urls(client.ls(BASE_URL + BRANCHES))
    specials = [(format_name(item), item) for item in branches if is_special(item)]
    branches = [(format_name(item), item) for item in branches if not is_special(item)]

    for special in specials:
        repos.append(special)

    # Treat trunk as just another branch
    branches.append( ('trunk', BASE_URL + TRUNK) )

    for branch in branches:
        addons = grab_urls(client.ls(branch[1]))
        for addon in addons:
            name = "{0}-{1}".format(format_name(addon), branch[0])
            repos.append( (name, addon) )

    # Handle the add-ons that were dumped in the root
    # This is the revision before standardlayout was created
    before_layout = pysvn.Revision( pysvn.opt_revision_kind.number, 1767)
    root_addons = grab_urls(client.ls(BASE_URL, revision=before_layout))
    # Mainlined addons that were removed before r1767
    root_addons += [ "/Sceptre_of_Fire-po" ]
    for addon in root_addons:
        name = format_name(addon)
        if name.endswith("-po"):
            name = name[:-3]
            repos.append( ("{0}-root".format(name), addon) )
        elif name == "The_Hammer_of_Thursagan":
            # Special-case THoT
            repos.append( ("{0}-root".format(name), addon) )
        else:
            print "Unrecognised path {0}".format(addon)

    for repo in repos:
        rules.write("""
create repository {0}
end repository""".format(repo[0]))

    for repo in repos:
        rules.write("""
match {0}
    repository {1}
    branch master
end match""".format(strip_base(repo[1]), repo[0]))

