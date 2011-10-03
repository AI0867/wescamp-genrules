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

    for branch in branches:
        addons = grab_urls(client.ls(branch[1]))
        for addon in addons:
            name = "{0}-{1}".format(format_name(addon), branch[0])
            repos.append( (name, addon) )

    # TODO: What to do with trunk?

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

