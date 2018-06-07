from unittest.mock import patch
from github_stars.github_stars import GitHubStars
from github_stars.repo import Repo
import unittest
import requests
import asyncio
import re
import json


get_starred_repos_re = re.compile(r'users/(.*?)/starred\?access_token=[a-zA-Z0-9]+$')
get_starred_repos_by_page_re = re.compile(r'users/(.*?)/starred\?access_token=[a-zA-Z0-9]+&page=\d+')
get_list_stargazers_re = re.compile(r'repos/.*?/.*?/stargazers\?access_token=[a-zA-Z0-9]+$')
get_list_stargazers_by_page_re = re.compile(r'repos/.*?/.*?/stargazers\?access_token=[a-zA-Z0-9]+&page=\d+')

mock_starred_repos = [
    {
        "name": "fRepo",
        "svn_url": "fRepoUrl",
        "owner": {"login": "fRepoLogin"}
    },
    {
        "name": "sRepo",
        "svn_url": "sRepoUrl",
        "owner": {"login": "sRepoLogin"}
    }
]

mock_starred_repos_last_page = [
    {
        "name": "lastRepo",
        "svn_url": "lastRepoUrl",
        "owner": {"login": "lastRepoLogin"}
    }
]

mock_stargazers_list = [
    {}, {}, {}
]

mock_stargazers_list_pages = [1] * GitHubStars.ReposOnPage


def mock_get_starred_repos(url):
    return MockResponse(json.dumps(mock_starred_repos), '')


def mock_get_stars_count(url):
    return MockResponse(json.dumps(mock_stargazers_list), '')


def mock_get_starred_repos_with_pages(url):
    if get_starred_repos_re.search(url):
        return MockResponse(json.dumps(mock_starred_repos), {'Link': 'next<https://page=2>;last'})
    elif get_starred_repos_by_page_re.search(url):
        return MockResponse(json.dumps(mock_starred_repos_last_page), '')


def mock_get_stars_count_with_pages(url):
    if get_list_stargazers_re.search(url):
        return MockResponse(json.dumps(mock_stargazers_list_pages),
                            {'Link': 'next<https://page=21>;last'})
    elif get_list_stargazers_by_page_re.search(url):
        return MockResponse(json.dumps([1] * 3), '')


class MockResponse:
    def __init__(self, text, headers):
        self.text = text
        self.headers = headers


class Tests(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def test_get_starred_repos(self):
        with patch.object(requests, 'get', side_effect=mock_get_starred_repos):
            g_stars = GitHubStars('testUser')
            result = self.loop.run_until_complete(g_stars.get_starred_repos())
            self.assertEqual(result[0].name, 'fRepo')
            self.assertEqual(result[0].svn_url, 'fRepoUrl')
            self.assertEqual(result[0].owner, 'fRepoLogin')
            self.assertEqual(result[1].name, 'sRepo')
            self.assertEqual(result[1].svn_url, 'sRepoUrl')
            self.assertEqual(result[1].owner, 'sRepoLogin')

    def test_get_stars_count(self):
        with patch.object(requests, 'get', side_effect=mock_get_stars_count):
            g_stars = GitHubStars('testUser')
            result = self.loop.run_until_complete(
                g_stars.get_stars_count(Repo({
                    'name': 'repoName',
                    'svn_url': 'repoUrl',
                    'owner': {'login': 'repoLogin'}})))
            self.assertEqual(result[0], 'repoUrl')
            self.assertEqual(result[1], 3)

    def test_get_starred_repos_with_pages(self):
        with patch.object(requests, 'get', side_effect=mock_get_starred_repos_with_pages):
            g_stars = GitHubStars('testUser')
            result = self.loop.run_until_complete(g_stars.get_starred_repos())
            self.assertEqual(3, len(result))
            self.assertEqual(result[0].name, 'fRepo')
            self.assertEqual(result[1].name, 'sRepo')
            self.assertEqual(result[2].name, 'lastRepo')

    def test_get_stars_count_with_pages(self):
        with patch.object(requests, 'get', side_effect=mock_get_stars_count_with_pages):
            g_stars = GitHubStars('testUser')
            result = self.loop.run_until_complete(
                g_stars.get_stars_count(Repo({
                    'name': 'repoName',
                    'svn_url': 'repoUrl',
                    'owner': {'login': 'repoLogin'}})))
            self.assertEqual(20 * GitHubStars.ReposOnPage + 3, result[1])
            self.assertEqual('repoUrl', result[0])
