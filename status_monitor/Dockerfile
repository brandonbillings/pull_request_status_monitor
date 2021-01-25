#Use the lightweight core slim python dockerhub python base image.
FROM python:3.9.1-slim

#Set the image env vars from compose args.
ARG GITHUB_PAT
ARG GITHUB_USER
ARG GITHUB_REPO
ARG GITHUB_BRANCH
ARG GITHUB_PR_REVIEW_THRESHOLD
ARG SLACK_BOT_TOKEN
ARG SLACK_CHANNEL
ARG SLACK_USER
ARG PR_STATUS_MONITOR_POLL_FREQUENCY

ENV GITHUB_PAT=$GITHUB_PAT
ENV GITHUB_USER=$GITHUB_USER
ENV GITHUB_REPO=$GITHUB_REPO
ENV GITHUB_BRANCH=$GITHUB_BRANCH
ENV GITHUB_PR_REVIEW_THRESHOLD=$GITHUB_PR_REVIEW_THRESHOLD
ENV SLACK_BOT_TOKEN=$SLACK_BOT_TOKEN
ENV SLACK_CHANNEL=$SLACK_CHANNEL
ENV SLACK_USER=$SLACK_USER
ENV PR_STATUS_MONITOR_POLL_FREQUENCY=$PR_STATUS_MONITOR_POLL_FREQUENCY

#Update/install any base image package patches/updates.
RUN apt-get update && apt-get dist-upgrade && apt-get install
RUN python -m pip install --upgrade pip

#Create a new non-root execution scope user and home directory.
RUN useradd -ms /bin/bash pyworker
USER pyworker
WORKDIR /home/pyworker

#This is the only external python library/dependency of the container, so no need to pip install from a requirements file.
RUN pip install requests

#Copy the worker class & init script files to the worker home directory.
COPY . /home/pyworker

#Start the status worker thread.
CMD ["python", "RunStatusWorker.py"]