#Use the lightweight core slim python dockerhub python base image.
FROM python:3.9.1-slim

#Update/install any base image package patches/updates.
RUN apt-get update && apt-get install
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