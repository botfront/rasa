"""
Script used to publish GitHub release notes extracted from CHANGELOG.rst.
This script is executed by Travis after a new release was successfully built.

Uses the following environment variables:
* TRAVIS_TAG: the name of the tag of the current commit.
* GH_RELEASE_NOTES_TOKEN: a personal access token with 'repo' permissions.

The script also requires ``pandoc`` to be previously installed in the system.
Requires Python3.6+.

Based on code from pytest.
https://github.com/pytest-dev/pytest/blob/master/scripts/publish_gh_release_notes.py
Copyright Holger Krekel and others, 2004-2019.

Distributed under the terms of the MIT license, pytest is free and open source software.
"""
import os
import re
import sys
from pathlib import Path
from typing import Text

# if this needs any more dependencies, they need to be installed on travis deploy stage
import github3
import pypandoc


def create_github_release(slug: Text, token: Text, tag_name: Text, body: Text):
    """Create a github release."""

    github = github3.login(token=token)
    owner, repo = slug.split("/")
    repo = github.repository(owner, repo)
    return repo.create_release(tag_name=tag_name, body=body)


def parse_changelog(tag_name: Text) -> Text:
    """Read the changelog and extract the most recently release entry."""

    p = Path(__file__).parent.parent / "CHANGELOG.rst"
    changelog_lines = p.read_text(encoding="UTF-8").splitlines()

    title_regex = re.compile(r"\[\d+\.\d+\.\d+(\S*)\]\s*-\s*\d{4}-\d{2}-\d{2}")
    consuming_version = False
    version_lines = []
    for line in changelog_lines:
        m = title_regex.match(line)
        if m:
            # found the version we want: start to consume lines
            # until we find the next version title
            if m.group(1) == tag_name:
                consuming_version = True
            # found a new version title while parsing the version we want: break out
            elif consuming_version:
                break
        if consuming_version:
            version_lines.append(line)

    return "\n".join(version_lines)


def convert_rst_to_md(text):
    return pypandoc.convert_text(text, "md", format="rst")


def main():
    tag_name = os.environ.get("TRAVIS_TAG")
    if not tag_name:
        print("environment variable TRAVIS_TAG not set", file=sys.stderr)
        return 1

    token = os.environ.get("GH_RELEASE_NOTES_TOKEN")
    if not token:
        print("GH_RELEASE_NOTES_TOKEN not set", file=sys.stderr)
        return 1

    slug = os.environ.get("TRAVIS_REPO_SLUG")
    if not slug:
        print("TRAVIS_REPO_SLUG not set", file=sys.stderr)
        return 1

    rst_body = parse_changelog(tag_name)
    md_body = convert_rst_to_md(rst_body)
    if not create_github_release(slug, token, tag_name, md_body):
        print("Could not publish release notes:", file=sys.stderr)
        print(md_body, file=sys.stderr)
        return 5

    print()
    print(f"Release notes for {tag_name} published successfully:")
    print(f"https://github.com/{slug}/releases/tag/{tag_name}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
