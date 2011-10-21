#! /usr/bin/env python

import pysvn

BASE_URL = "svn://svn.berlios.de/wescamp-i18n"
BRANCHES = "/branches/"
TRUNK = "/trunk/"

DELETED_ROOT_ADDONS = [
    ("/A_New_Order-po", 2261),
    ("/An_Orcish_Incursion-po", 2083),
    ("/Attack_of_the_Undead-po", 2164),
    ("/Children_of_Dragons-po", 2117),
    ("/Delfadors_Memoirs-po", 2554),
    ("/Descent-po", 1541),
    ("/Eliador-po", 2136),
    ("/Extended_Era-po", 1894),
    ("/Extended_Era_xtra_1.2-po",1891),
    ("/Flight_Freedom-po", 2291),
    ("/Invasion_from_the_Unknown-po", 1992),
    ("/Legend_of_Wesmere-po", 2018),
    ("/Liberty-po", 1595),
    ("/Northern_Rebirth-po", 1509),
    ("/Orcish_Incursion-po", 1417),
    ("/Pack_Sapient-po", 2012),
    ("/Saving_Elensefar-po", 2262),
    ("/Sceptre_of_Fire-po", 1632),
    ("/Son_Of_The_Black_Eye-po", 1632),
    ("/The_Dark_Hordes-po", 2376),
    ("/The_Heist-po", 1460),
    ("/The_South_Guard-po", 1417),
    ("/Two_Brothers-po", 811),
    ("/Under_the_Burning_Suns-po", 1417),
    ("/Wesnoth_Holdem-po", 1460),
]

DELETED_ADDONS = [
    ("Legend_of_Wesmere-1.4", "/branches/1.4/Legend_of_Wesmere", 2339),
    ("Legend_of_Wesmere-trunk", "/trunk/Legend_of_Wesmere", 2329),
    ("Rise-1.4", "/branches/1.4/Rise", 1957),
    ("The_Life_Of_A_Mage-1.4", "/branches/1.4/The_Life_Of_A_Mage", 2465),
    ("The_Silver_Lands-1.8", "/branches/1.8/The_Silver_Lands", 3166),
]

IGNORED_PATHS = [
    # /Liberty and /po paths, which were removed in r3 to be replaced by /Liberty-po
    "/Liberty",
    "/po",
    # Removed testcase for addon-server syncing
    "/trunk/Flight_Freedom_1_3",
    # Renamed to Eastern_Europe_at_War, with identical contents
    "/branches/1.8/EEaW",
    "/branches/1.10/EEaW",
    # Test commits
    "/trunk/foo",
    "/trunk/bar",
    "/trunk/test",
    "/foo",
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
    root_addons = [(item["name"],) for item in client.ls(BASE_URL) if
        not item["name"].endswith("/branches") and
        not item["name"].endswith("/trunk")]
    # And addons that were removed from there
    root_addons += DELETED_ROOT_ADDONS
    for addon in root_addons:
        name = format_name(addon[0])
        if name.endswith("-po"):
            name = name[:-3]
            if len(addon) == 2:
                repo = ("{0}-root".format(name), addon[0], addon[1])
            else:
                repo = ("{0}-root".format(name), addon[0])
            repos.append(repo)
        elif name == "The_Hammer_of_Thursagan":
            # Special-case THoT, it's missing the -po suffix
            pass
            # We manually add this rule later, as the rename job @ r1703 has some strange history
            #repos.append( ("{0}-root".format(name), addon) )
        else:
            print "Unrecognised path {0}".format(addon[0])

    # Other deleted addons
    repos += DELETED_ADDONS

    for repo in repos:
        rules.write("""
create repository {0}
end repository""".format(repo[0]))

    for repo in repos:
        rules.write("""
match {0}/
    repository {1}""".format(strip_base(repo[1]), repo[0]))
        if len(repo) == 3:
            rules.write("""
    max revision {0}""".format(repo[2]))
        rules.write("""
    branch master
end match""")

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
    max revision 1862
end match""")

    for ignore in IGNORED_PATHS:
        rules.write("""
match {0}
end match""".format(ignore))

