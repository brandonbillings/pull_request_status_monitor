
import os
import requests
import json
import datetime
import time


class PrStatusWorker:
    def __init__(self):
        self._gh_pat_env_key = "GITHUB_PAT"
        self._gh_user_env_key = "GITHUB_USER"
        self._gh_repo_key = "GITHUB_REPO"
        self._gh_target_branch_key = "GITHUB_BRANCH"
        self._gh_pr_review_threshold_key = "GITHUB_PR_REVIEW_THRESHOLD"
        self._slack_token_key = "SLACK_BOT_TOKEN"
        self._slack_channel_key = "SLACK_CHANNEL"
        self._slack_user_key = "SLACK_USER"
        self._poll_frequency_key = "PR_STATUS_MONITOR_POLL_FREQUENCY"

        self._github_pat = os.getenv(self._gh_pat_env_key, "NA")
        self._github_user = os.getenv(self._gh_user_env_key, "NA")
        self._github_repo = os.getenv(self._gh_repo_key, "NA")
        self._github_target_branch = os.getenv(self._gh_target_branch_key, "NA")
        self._github_pr_review_threshold_days = os.getenv(self._gh_pr_review_threshold_key, 3)
        self._slack_token = os.getenv(self._slack_token_key, "NA")
        self._slack_channel = os.getenv(self._slack_channel_key, "NA")
        self._slack_user = os.getenv(self._slack_user_key, "NA")
        self._poll_frequency_seconds = os.getenv(self._poll_frequency_key, 60)
        self._gh_api_header = {'Authorization': f'token {self._github_pat}'}
        self._status_worker_polling = True

        #Cast the poll/threshold vars to ints, or in the event of erroneous values set to defaults (60 second poll cycle, 3 day threshold).
        try:
            self._poll_frequency_seconds = int(self._poll_frequency_seconds)
            self._github_pr_review_threshold_days = int(self._github_pr_review_threshold_days)
        except ValueError:
            self._poll_frequency_seconds = 60
            self._github_pr_review_threshold_days = 3

    def get_all_open_prs(self):
        #Grab all PRs in an open state.
        pr_dict = {}
        open_pr_api_url = f"https://api.github.com/repos/{self._github_user}/{self._github_repo}/pulls"

        pr_params = {
            "state": "open"
        }

        response = requests.get(open_pr_api_url, headers=self._gh_api_header, params=pr_params)

        if response.status_code == 200:
            open_pr_payload = response.json()

            if len(open_pr_payload) > 0:
                for pull_request in open_pr_payload:
                    pr_number = pull_request.get("number", -1)

                    if pr_number != -1:
                        pr_dict[pr_number] = pull_request

        return pr_dict

    def check_pr_reviews(self, pr_dict):
        prs_exceeds_threshold = {}
        prs_within_threshold = {}

        #Check all open PR's for reviews.  If the reviews are empty, then check the creation date against the threshold value.
        for pr_number in pr_dict:
            pull_request = pr_dict[pr_number]
            pr_url = f"https://api.github.com/repos/{self._github_user}/{self._github_repo}/pulls/{pr_number}/reviews"
            response = requests.get(pr_url, headers=self._gh_api_header)
            reviews_payload = response.json()

            if len(reviews_payload) == 0:
                created_date = pull_request.get("created_at")

                if self.pr_exceeds_threshold(created_date):
                    prs_exceeds_threshold[pr_number] = pull_request
                else:
                    prs_within_threshold[pr_number] = pull_request

        if prs_exceeds_threshold or prs_within_threshold:
            self.send_slack_message(prs_exceeds_threshold, prs_within_threshold)

    def pr_exceeds_threshold(self, created_date_str):
        created_date = datetime.datetime.strptime(created_date_str, "%Y-%m-%dT%H:%M:%SZ")
        current_date = datetime.datetime.utcnow()
        time_delta = current_date - created_date
        exceeds_threshold = time_delta.days > self._github_pr_review_threshold_days
        return exceeds_threshold

    def do_pr_status_check(self):
        pr_dict = self.get_all_open_prs()
        self.check_pr_reviews(pr_dict)

    def send_slack_message(self, exceed_threshold_dict, within_threshold_dict):
        slack_api_url = "https://slack.com/api/chat.postMessage"
        bearer_token = f"Bearer {self._slack_token}"

        post_header = {
            "Authorization": bearer_token
        }

        attachment_blocks = []
        str_threshold = str(self._github_pr_review_threshold_days)

        if exceed_threshold_dict:
            msg = f"The following pull requests are awaiting review, and require *immediate attention*, as they are exceeding the acceptable review threshold of {str_threshold} days:\n\n"

            for pr_number in exceed_threshold_dict:
                pr_url = exceed_threshold_dict.get(pr_number).get("html_url")
                msg += pr_url + "\n"

            attach = {
                "color": "#FF0000",
                "text": msg
            }

            attachment_blocks.append(attach)

        if within_threshold_dict:
            msg = f"The following pull requests are awaiting review, but are still within the acceptable review threshold of {str_threshold} days:\n\n"

            for pr_number in within_threshold_dict:
                pr_url = within_threshold_dict.get(pr_number).get("html_url")
                msg += pr_url + "\n"

            attach = {
                "color": "#008000",
                "text": msg
            }

            attachment_blocks.append(attach)

        msg_data = {
            'token': self._slack_token,
            'channel': self._slack_channel,
            'text': '',
            "attachments": json.dumps(attachment_blocks)
        }

        response = requests.post(slack_api_url, headers=post_header, data=msg_data)
        test = 1

    def stop_pr_status_polling(self):
        self._status_worker_polling = False

    def start_pr_status_polling(self):
        while self._status_worker_polling:
            self.do_pr_status_check()
            time.sleep(self._poll_frequency_seconds)
