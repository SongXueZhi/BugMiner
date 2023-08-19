# -*- coding: utf-8 -*-
# get <issue,commit>
import random
from time import sleep
import pandas as pd
from github import Github

result_log = 'all.csv'
done_list_file = "done.list"

# Enter your Github token, you may enter several tokens here!
#
user_token = [
    'ghp_xxxxxxxxxxxxxxx'
]

g = Github(user_token[random.randint(0, len(user_token) - 1)])


def read_done_list():
    my_file = open(done_list_file, "r")
    content_list = my_file.readlines()
    a = list()
    for content in content_list:
        content = content.replace("\n", "")
        a.append(content)
    return a


def write_log(con, filename):
    with open(filename, 'a') as file_object:
        file_object.write(con + '\n')


# Note that, I handle each github api access with loop
# Break Unless sucess
def get_issues_for_repo(repo):
    global g
    while True:
        try:
            repo_issues = repo.get_issues(state='closed')
            return repo_issues
        except Exception as e:
            print(e)
            try:
                if 'rate' in str(e):
                    sleep(1800)
                    g = Github(user_token[random.randint(0, len(user_token) - 1)])
                else:
                    return None
            except Exception as e:
                print(e)
                return None


def get_comments_for_issue(issue):
    global g
    while True:
        try:
            comments = issue.get_comments()
            return comments
        except Exception as e:
            print(e)
            try:
                if 'rate' in str(e):
                    sleep(1800)
                    g = Github(user_token[random.randint(0, len(user_token) - 1)])
                else:
                    return None
            except Exception as e:
                print(e)
                return None


def get_event_for_issue(issue):
    global g
    while True:
        try:
            issue_events = issue.get_events()
            return issue_events
        except Exception as e:
            print(e)
            try:
                if 'rate' in str(e):
                    sleep(1800)
                    g = Github(user_token[random.randint(0, len(user_token) - 1)])
                else:
                    return None
            except Exception as e:
                print(e)
                return None


def get_commit_from_id(cid, repo):
    global g
    while True:
        try:
            commit_info = repo.get_commit(cid)
            return commit_info
        except Exception as e:
            print(e)
            try:
                if 'rate' in str(e):
                    sleep(1800)
                    g = Github(user_token[random.randint(0, len(user_token) - 1)])
                else:
                    return None
            except Exception as e:
                print(e)
                return None
            # calling the search repo API


def get_repositories(keywords):
    global g
    while True:
        try:
            repo = g.get_repo(keywords)
            return repo
        except Exception as e:
            print(e)
            try:
                if 'rate' in str(e):
                    sleep(1800)
                    g = Github(user_token[random.randint(0, len(user_token) - 1)])
                else:
                    return None
            except Exception as e:
                print(e)
                return None


# traverse issues，obtain the information of issue and commit
def get_relations(repo_issues, repo_name, repo):
    relations = []
    if repo_issues is not None:
        total = repo_issues.totalCount
    else:
        return
    i = 0.0
    for issue in repo_issues:
        i += 1
        issue_number = issue.number
        print(str(issue_number) + " " + str(i / float(total)))
        issue_title = issue.title
        if issue_title is None:
            issue_title = ""
        issue_title.encode('utf-8', 'ignore')
        issue_body = issue.body
        if issue_body is None:
            issue_body = ""
        issue_body.encode('utf-8', 'ignore')
        issue_html_url = issue.html_url
        if issue_html_url is None:
            issue_html_url = ""
        issue_html_url.encode('utf-8', 'ignore')
        # remove Pull Request，we only need issue
        if 'pull' not in issue_html_url:
            label_for_issue = 1
            if label_for_issue is not None:
                issue_events = get_event_for_issue(issue)
                if issue_events is None:
                    continue
                commit_ids = []
                for issue_event in issue_events:
                    if issue_event.commit_id is not None:
                        commit_id = issue_event.commit_id
                        commit_ids.append(commit_id)
                print(commit_ids)
                if len(commit_ids) == 1:
                    commit_info = get_commit_from_id(commit_id, repo)
                    if commit_info is None:
                        continue
                    commit_message = commit_info.commit.message
                    if '#' or 'issue' in commit_message and str(issue_number) in commit_message:
                        commit_url = commit_info.html_url
                        relation_tup = (repo_name, issue_html_url, commit_url, label_for_issue)
                        write_log(repo_name + "," + issue_html_url + "," + commit_url + "," + str(label_for_issue),
                                  result_log)
                        relations.append(relation_tup)
                else:
                    relation_tup = None
                    for cid in commit_ids:
                        commit_info = get_commit_from_id(cid, repo)
                        if commit_info is None:
                            continue
                        commit_message = commit_info.commit.message
                        if '#' or 'issue' in commit_message and str(issue_number) in commit_message:
                            # commit_number = re.findall(r"(?<=\#)\d+", commit_message)
                            commit_url = commit_info.html_url
                            relation_tup = (repo_name, issue_html_url, commit_url, label_for_issue)
                    if relation_tup is not None:
                        write_log(repo_name + "," + issue_html_url + "," + commit_url + "," + str(label_for_issue),
                                  result_log)
                        relations.append(relation_tup)
    print(relations)
    return relations


def handleTask(full_name):
    repo = get_repositories(full_name)
    # handle unknown exception casue repositories is None
    if repo is None:
        return
    flag = 0
    repo_name = repo.name
    repo_name.encode('utf-8', 'ignore')
    done_list = read_done_list()
    if repo_name in done_list:
        print(repo_name + " skip")
        return
    print(repo_name)
    write_log(repo_name, done_list_file)
    repo_language = repo.language
    # Some projects have none language
    if repo_language is None:
        return
    repo_language.encode('utf-8', 'ignore')
    if "Java" != repo_language:
        return
    # Skip forked project
    if repo.fork:
        return
    repo_issues = get_issues_for_repo(repo)
    if repo_issues is None:
        return
    relations_info = []
    # Parse commit and issue relation to get Regression BFC
    try:
        relations_info = get_relations(repo_issues, repo_name, repo)
    except Exception as e:
        print(e)
        try:
            if 'rate' in str(e):
                sleep(1800)
                g = Github(user_token[random.randint(0, len(user_token) - 1)])
            else:
                return None
        except Exception as e:
            print(e)
            return None
    if len(relations_info) == 0:
        print("exit here in len(relations_info)")
        return
    if '/' in repo_name:
        repo_name = repo_name.replace('/', '_')
    file_name = 'relations_of_' + repo_name + '.csv'
    data = pd.DataFrame(relations_info)
    try:
        if flag == 0:
            csv_headers = ['repo_name', 'issue_url', 'commit_url', 'label']
            data.to_csv(file_name, header=csv_headers, index=False,
                        mode='a+', encoding='utf-8-sig')

        else:
            data.to_csv(file_name, header=False, index=False,
                        mode='a+', encoding='utf-8-sig')
            flag += 1
    except Exception as e:
        print(e)


if __name__ == '__main__':
    # a project full name should be provided here!
    handleTask('uniVocity/univocity-parsers')
