# brew install python
# brew upgrade python

import os
import shutil
import subprocess

GIT_DIFF_NO_CHANGES = ''

COLOR_DEFAULT = "\033[0m"
COLOR_BLACK = "\033[0;30m"
COLOR_RED = "\033[0;31m"
COLOR_GREEN = "\033[0;32m"
COLOR_YELLOW = "\033[0;33m"
COLOR_BLUE = "\033[0;34m"
COLOR_PINK = "\033[0;35m"
COLOR_CYAN = "\033[0;36m"
COLOR_WHITE = "\033[0;37m"

SCRIPT_EXECUTION_FOLDER = os.getcwd()


class TravixRepo:
    """Info for Travix repos"""

    repo_name = ""

    def __init__(self, repo_name) -> None:
        super().__init__()
        self.repo_name = repo_name

    def get_name(self):
        return self.repo_name

    def get_repo_url(self):
        return "git@bitbucket.org:xivart/" + self.repo_name + ".git"


class ReposGroup:
    base_folder = ""
    repos = list()

    def __init__(self, base_folder, repos_list=list()):
        self.base_folder = base_folder
        self.repos = list()
        for repo_name in repos_list:
            self.repos.append(TravixRepo(repo_name))


class Repos:
    """Manages the repo collections"""

    groups = list()
    cloned = list()
    failed = list()
    with_uncommitted_changes = list()
    updated = list()


class ConsoleOutput:
    """Formats and present messages"""

    @staticmethod
    def error(message):
        print("{}{}{}".format(COLOR_RED, message, COLOR_DEFAULT))

    @staticmethod
    def info(message):
        print("{}{}{}".format(COLOR_WHITE, message, COLOR_DEFAULT))

    @staticmethod
    def warn(message):
        print("{}{}{}".format(COLOR_PINK, message, COLOR_DEFAULT))

    @staticmethod
    def action(message):
        print("{}{}{}".format(COLOR_BLUE, message, COLOR_DEFAULT))

    @staticmethod
    def debug(message):
        print("{}{}{}".format(COLOR_BLACK, message, COLOR_DEFAULT))


class FileManager:
    """Group file logic"""

    @staticmethod
    def folder_exists(folder_path):
        return os.path.exists(folder_path)

    @staticmethod
    def create_folder(folder_path):
        if not FileManager.folder_exists(folder_path):
            os.makedirs(folder_path)

    @staticmethod
    def delete_folder(folder_name):
        shutil.rmtree(folder_name)

    @staticmethod
    def go_to_folder(folder_path):
        os.chdir(folder_path)


class GitManager:
    """Manages git actions"""

    @staticmethod
    def clone(base_folder, repo_name, repo_url):
        ConsoleOutput.action("Clonning {} ...".format(repo_url))
        try:
            subprocess.run(["git", "clone", repo_url, "{}/{}".format(base_folder, repo_name)],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,
                           check=True)

            ConsoleOutput.action("Clone success {}".format(repo_name))
            Repos.cloned.append(repo_name)

        except subprocess.CalledProcessError as e:
            ConsoleOutput.error("Error cloning {}: {}".format(repo_name, e))
            Repos.failed.append(repo_name)

    @staticmethod
    def contains_uncommitted_changes(base_folder, repo_name):
        FileManager.go_to_folder("{}/{}".format(base_folder, repo_name))
        try:
            result = subprocess.run(["git", "diff-index", "HEAD"],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    check=True)

            if GIT_DIFF_NO_CHANGES != result.stdout.decode("utf-8"):
                ConsoleOutput.warn("Contains uncommitted changes {}".format(repo_name))
                Repos.with_uncommitted_changes.append(repo_name)
                result = True
            else:
                result = False

        except subprocess.CalledProcessError as e:
            ConsoleOutput.error("Error processing {}: {}".format(repo_name, e))
            Repos.failed.append(repo_name)
            result = True

        FileManager.go_to_folder(SCRIPT_EXECUTION_FOLDER)
        return result

    @staticmethod
    def checkout_master(base_folder, repo_name):
        FileManager.go_to_folder("{}/{}".format(base_folder, repo_name))
        try:
            ConsoleOutput.action("Checking out master for {}".format(repo_name))
            subprocess.run(["git", "checkout", "master"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            ConsoleOutput.action("Pulling changes for {}".format(repo_name))
            subprocess.run(["git", "pull"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            ConsoleOutput.action("Up to date {}".format(repo_name))
            Repos.updated.append(repo_name)

        except subprocess.CalledProcessError as e:
            ConsoleOutput.error("Error processing {}: {}".format(repo_name, e))
            Repos.failed.append("{} : {}".format(repo_name, e))

        FileManager.go_to_folder(SCRIPT_EXECUTION_FOLDER)


# Travix repos
Repos.groups.append(ReposGroup("_FOLDER_HERE_",
								[
                                   "_REPO_HERE_"
                                ]))
Repos.groups.append(ReposGroup("_FOLDER2_HERE_",
                               [
                                   "_REPO2_HERE_",
                                   "_REPO3_HERE_"
                               ]))


def report_script_result_group(group_name, repos, logger):
    if repos.__len__() > 0:
        logger("{} repos:".format(group_name))
        for repo in repos:
            logger("\t{}".format(repo))


def report_script_result():
    report_script_result_group("Updated", Repos.updated, ConsoleOutput.info)
    report_script_result_group("Dirty", Repos.with_uncommitted_changes, ConsoleOutput.warn)
    report_script_result_group("Failed", Repos.failed, ConsoleOutput.error)


def main():
    ConsoleOutput.info("Repos script 4.0")

    ConsoleOutput.info("Total of {} groups to process".format(Repos.groups.__len__()))

    repos_groups_visited = 0
    number_of_repos_groups = Repos.groups.__len__()
    for repoGroup in Repos.groups:
        repos_groups_visited = repos_groups_visited + 1
        ConsoleOutput.info("Processing {} ({}/{})".format(repoGroup.base_folder,
                                                          repos_groups_visited,
                                                          number_of_repos_groups))
        repos_within_group_visited = 0
        number_of_repos_within_group = repoGroup.repos.__len__()
        for repo in repoGroup.repos:
            repos_within_group_visited = repos_within_group_visited + 1
            ConsoleOutput.info("Processing {} [{}/{}]:({}/{})".format(repo.get_name(),
                                                                      repos_groups_visited,
                                                                      number_of_repos_groups,
                                                                      repos_within_group_visited,
                                                                      number_of_repos_within_group))
            manage_repo(repoGroup.base_folder, repo.get_name(), repo.get_repo_url())

    report_script_result()


def manage_repo(group_folder, repo_name, repo_url):
    FileManager.create_folder(group_folder)

    if not FileManager.folder_exists("{}/{}".format(group_folder, repo_name)):
        GitManager.clone(group_folder, repo_name, repo_url)

    elif not FileManager.folder_exists("{}/{}/.git".format(group_folder, repo_name)):
        FileManager.delete_folder("{}/{}".format(group_folder, repo_name))
        GitManager.clone(group_folder, repo_name, repo_url)

    elif not GitManager.contains_uncommitted_changes(group_folder, repo_name):
        GitManager.checkout_master(group_folder, repo_name)


if __name__ == "__main__":
    main()
