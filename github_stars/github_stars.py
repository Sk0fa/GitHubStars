from github_stars.repo import Repo
from github_stars import links
import requests
import sys
import json
import re
import asyncio
import argparse


class GitHubStars:
    LastPageRe = re.compile(r'next.*?<https://.*?page=(\d+)>;.*last')
    ReposOnPage = 30

    def __init__(self, login):
        self.login = login
        self.loop = asyncio.get_event_loop()

    def start(self):
        result = self.loop.run_until_complete(self.get_github_stars())
        self.loop.close()
        self.print_result(result)

    async def get_github_stars(self):
        repos = await self.get_starred_repos()
        self.check_on_empty_starred(repos)

        futures = [self.get_stars_count(repo) for repo in repos]
        done, pending = await asyncio.wait(
            futures, loop=self.loop, return_when=asyncio.ALL_COMPLETED)

        return {task.result()[0]: task.result()[1] for task in done}

    async def get_starred_repos(self):
        starred_page = requests.get(links.get_starred_repos % self.login)
        repos_info = json.loads(starred_page.text)
        self.check_on_error(repos_info)
        repos = [Repo(repo_info) for repo_info in repos_info]

        if 'Link' in starred_page.headers:
            pages_count = self.get_pages_count(starred_page)
            starred_pages = await self.wait_futures([self.loop.run_in_executor(
                None, requests.get,
                links.get_starred_repos_by_page % (self.login, num))
                for num in range(2, pages_count + 1)])

            for page in starred_pages:
                repos += self.get_repos_from_page(page)

        return repos

    async def get_stars_count(self, repo):
        stargazers_page = await self.loop.run_in_executor(
            None, requests.get,
            links.get_list_stargazers % (repo.owner, repo.name))

        if 'Link' in stargazers_page.headers:
            pages_count = self.get_pages_count(stargazers_page)

            last_page = await self.loop.run_in_executor(
                None, requests.get,
                links.get_list_stargazers_by_page
                % (repo.owner, repo.name, pages_count))

            stars_count = (pages_count - 1) * self.ReposOnPage +\
                len(json.loads(last_page.text))
        else:
            stars_count = len(json.loads(stargazers_page.text))

        return repo.svn_url, stars_count

    async def wait_futures(self, futures):
        done, pending = await asyncio.wait(
            futures, loop=self.loop,
            return_when=asyncio.ALL_COMPLETED)

        return [task.result() for task in done]

    def get_repos_from_page(self, page):
        repos_info = json.loads(page.text)
        self.check_on_error(repos_info)
        return [Repo(repo_info) for repo_info in repos_info]

    def get_pages_count(self, response):
        return int(self.LastPageRe.search(response.headers['Link'])
                   .group(1))

    @staticmethod
    def print_result(result):
        for url in result:
            print('%s - %d' % (url, result[url]))

    @staticmethod
    def check_on_error(repo):
        if 'message' in repo:
            sys.stderr.write(repo['message'])
            sys.exit(1)

    @staticmethod
    def check_on_empty_starred(repos):
        if len(repos) == 0:
            print('Does not have starred repos')
            sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--login", help="Enter github user login", required=True)
    args = parser.parse_args()
    GitHubStars(args.login).start()
