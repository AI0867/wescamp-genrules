#! /usr/bin/env python

import pysvn

BASE_URL = "svn://svn.berlios.de/wescamp-i18n"
BRANCHES = "/branches/"
TRUNK = "/trunk/"

MAINLINED_ROOT_ADDONS = [
    "/Descent-po",
    "/Liberty-po",
    "/Northern_Rebirth-po",
    "/Orcish_Incursion-po",
    "/Sceptre_of_Fire-po",
    "/Son_Of_The_Black_Eye-po",
    "/The_South_Guard-po",
    "/Two_Brothers-po",
    "/Under_the_Burning_Suns-po",
]

DELETED_ROOT_ADDONS = [
    "/The_Heist-po",
    "/Wesnoth_Holdem-po",
]

DELETED_OTHER_ADDONS = [
    ("Legend_of_Wesmere-1.4", "/branches/1.4/Legend_of_Wesmere"),
    ("Rise-1.4", "/branches/1.4/Rise"),
    ("The_Life_Of_A_Mage-1.4", "/branches/1.4/The_Life_Of_A_Mage"),
]

IGNORED_PATHS = [
    # /Liberty and /po paths, which were removed in r3 to be replaced by /Liberty-po
    "/Liberty",
    "/po",
    # Removed testcase for addon-server syncing
    "/trunk/Flight_Freedom_1_3",
    # Test commits
    "/trunk/foo",
    "/trunk/test",
]

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
    root_addons += MAINLINED_ROOT_ADDONS
    # And addons that were removed for other reasons
    root_addons += DELETED_ROOT_ADDONS
    for addon in root_addons:
        name = format_name(addon)
        if name.endswith("-po"):
            name = name[:-3]
            repos.append( ("{0}-root".format(name), addon) )
        elif name == "The_Hammer_of_Thursagan":
            # Special-case THoT, it's missing the -po suffix
            pass
            # We manually add this rule later, as the rename job @ r1703 has some strange history
            #repos.append( ("{0}-root".format(name), addon) )
        else:
            print "Unrecognised path {0}".format(addon)

    # Other deleted addons
    repos += DELETED_OTHER_ADDONS

    for repo in repos:
        rules.write("""
create repository {0}
end repository""".format(repo[0]))

    for repo in repos:
        rules.write("""
match {0}/
    repository {1}
    branch master
end match""".format(strip_base(repo[1]), repo[0]))

    # THoT was moved within the root at some point (capitalisation of 'Of')
    rules.write("""
create repository The_Hammer_of_Thursagan-root
end repository
match /The_Hammer_Of_Thursagan/
    repository The_Hammer_of_Thursagan-root
    branch master
    max revision 1702
end match
match /The_Hammer_Of_Thursagan/
    min revision 1703
end match
match /The_Hammer_of_Thursagan/
    max revision 1703
end match
match /The_Hammer_of_Thursagan/
    repository The_Hammer_of_Thursagan-root
    branch master
    min revision 1704
end match""")

    for ignore in IGNORED_PATHS:
        rules.write("""
match {0}
end match""".format(ignore))

