class Repo:
    def __init__(self, repo_info):
        self.svn_url = repo_info['svn_url']
        self.name = repo_info['name']
        self.owner = repo_info['owner']['login']
