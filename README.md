
# Github Pull Request Status Monitor Application

Per the instructions, this application polls a specified github repo and searches for *open* pull requests that have no reviews, and reports them via a slack bot app to a designated slack channel.  
The following parameters (set as environmental variables) are defined in the docker compose config, which dictate the behavior of the application.

```
GITHUB_PAT: This is the personal access token defined in this github repo that allows API access.
GITHUB_USER: The github username/owner of this repo.
GITHUB_REPO: The name of the repo the status monitor is checking.
GITHUB_BRANCH: The *target*/*destination* branch of the repo where PR's are being merged/monitored.
GITHUB_PR_REVIEW_THRESHOLD: Value (in days) which is the allowable limit for PR's waiting for review.
SLACK_BOT_TOKEN: The API auth token generated for the target slack bot/app to send messages through the API.
SLACK_CHANNEL: The slack channel name to send messages to.
SLACK_USER: The slack user account name.
PR_STATUS_MONITOR_POLL_FREQUENCY: The frequency (in seconds) the app should poll github to check for unreviewed PR's.
```

There is a dummy_pr_folder in this repo where a simple text file lives.  In order to test this app, i created a development
branch off master, and would make changes to the text file, and open PR's against master to validate the functionality was working as expected.
Beyond that, this folder can be ignored.  All of the rest of the core code lives in status_monitor.

# Application Design

The application itself is fairly straightforward.  It consists of a worker base class (PyStatusWorker) which defines all the core functionality
and interactions with both the github and slack API's, and a simple invocation script (RunStatusWorker.py) which simply instantiates the worker class
in a thread.  

There is only one external dependency for this application, which is the python requests HTTP library (https://requests.readthedocs.io/en/master/). 
This is a ubiquitous library for making standard http requests (GET/POST, etc), and is the basis for all API calls in this app.  I deliberately chose this
approach instead of using third party API libraries to minimize dependencies/complexity, however these could have been the alternatives used:

```
https://github.com/PyGithub/PyGithub
https://github.com/slackapi/python-slack-sdk
```

# Containerization

The application runs in a standard docker container using the 3.9.1-slim official python base image from dockerhub.  There is a basic
docker-compose yaml file that defines the container service and build context, and really the only configuration needed is setting
the environmental variables in the build context.

To build/deploy the image:

Step 1 (Build the image):

![](https://lh3.googleusercontent.com/pw/ACtC-3dxSHpmPCP50fJiRoEIprRASjX_F6Xus4NNeg13Ft3iG0cc3zlH8mxFbNWZjFp47Yj_WieqjuGXWknnclnC7ENZATJnOXtfTRkMDx8kF13ovXbNlymXs6pd43UMPBtw9X8MPAiSViLHthCUNjdCNjn1=w982-h268-no?authuser=0)

Step 2 (Tag & Push):

Tag the local image in preparation to push it to our image repo (in this case AWS ECR).  Now you may be wondering why ECR?  And the reason is it has built in image vulnerability scanning.  Once your image is pushed you get
a nice clean report of potential vulnerabilities (and in the case of this image there actually is a new glibc debian issue that was just discovered a few weeks ago, currently pending a hotfix).

![](https://lh3.googleusercontent.com/pw/ACtC-3cIvTgprdCxsNmGNM8yA4uZMvMZU6fpFG0kVGCpLZgFlgywJQxw9zl39etfcbRUoHHFNgUizRHNmAirYmPUfMovwx5Zd2YylmNcqrLhpStETiuZw6_yk_0P5pqaRmLiLXQph5x7AkTqz71-j40vUelK=w1204-h288-no?authuser=0)

Now we push the image.  You can see, for ECR we need to interact with the AWS cli.  More specifically we have to generate a login token and then tell docker to login with our ECR repo as our target server.

![](https://lh3.googleusercontent.com/pw/ACtC-3cZ76rI7htKWEWS0BGGO15aNFZLcBQ9WHoLaS8pV8ZT5CGnBpaHbPwcKL9oH3-nASE0No6mlGsveE2U8pNCF5HKnTDZOUDJ6LftaR3ojTptVa0ZddIp_huZRB8X1ocTUhJABvWkvMfRLBThXRpIL5Q1=w1560-h616-no?authuser=0)

And when that completes we can then go see our image in ECR and check the vulnerability report:

![](https://lh3.googleusercontent.com/pw/ACtC-3f1RJikjyh8e2EIDmeaOmy84dtf5X3Utmis4GNZRR-WjPordKwJHeGKjouFc3QheXMMP8G7jktYbPnLT4vo0vxYm2nt2oBZ3L00EHMSFuXtmF4zG3KGv7jbXvmug6vSuAX5CYCZTEyuirxfIo61CRCi=w2543-h1101-no?authuser=0)

# Kubernetes Deployment

For the sake of this exercise, all deployment tasks will be within the scope of a local minikube cluster.  In a true production environment there would be other tools to manage the kubernetes cluster/node infrastructure, like EKS for cloud, 
or something like Rancher for an on-prem configuration. So now that we have our image built and pushed to our repo, we can deploy it.

Step 1:

Becuase we are pulling the image from ECR we need to configure the minikube security addon for our AWS creds (otherwise our deployment will fail to pull the image).  Then we enable the addon, and we are good to go.

![](https://lh3.googleusercontent.com/pw/ACtC-3dqXxIi9UfRIZrg4eNp1YR6P7I59VJaTkMSAw2NxRc721mvM5KcaRt9sTZh5WfW0hQDQJJX144asN76kQ2seL043p6r9CCvo-hc9Rq97AMN0yjEWFsCuOo-aag3EjlbE6x5YWrnzzn06L3Y0nofLGtk=w809-h408-no?authuser=0)

Step 2:

Just check the local cluster to verify nothing else is currently deployed.

![](https://lh3.googleusercontent.com/pw/ACtC-3fkWpKh-iBcY4HjSi0xzGzddVjMAwFO0sLS7N0QLFykuVe7tWs8qkM7m7_HLVXIqaUmYwK2eWcXEM7P7MfGUbJ2sZp_lmZz6djp6v7TFpIFy6ORfnNos8l-d8WmU9BlFsRbQuFZINCllipZbnSpXAdk=w628-h258-no?authuser=0)

Step 3:

There is a deployment.yaml setup to deploy the container app.  It points to our ECR image and is configured to generate a replicaset of 3 pods (i know this is probably not a "real world" configuration, but this will be explained below).

Then we simply apply the deployment.  And check to see that our 3 pods are initialized.

![](https://lh3.googleusercontent.com/pw/ACtC-3dhbFiXTXKani1MnjJi0vnCQBeMeDB71aYs76oLBx8AYriBllUX0zUSsqyAM3JYCNMYSHYqE3WfChtsyAoGTAE0ag_9hEelf4674d04F3qH085APYqsZBG_snSn1f_4O263-g4xrwxRvl18PcnwyDWj=w751-h255-no?authuser=0)

Step 4:

Now we open our slack channel and verify everything is working. You can see below, that becuase we have three pods running the container, and our poll cycle is set to 60 seconds, each minute we are getting blocks of three
messages sent to us from the monitor app (in this example i have *one* open/unreviewed PR in my target repo).  Again, while this is not a real world or practical behavior, it just demonstrates the deployment is functioning as expected. 

![](https://lh3.googleusercontent.com/pw/ACtC-3eS3KWUK9CRKZv0Ce_-ac2Xeeierw2WZHEDaTkGIhWfaf9rZ22vbhFC1H_IXkj0dczChWcpB86yVEbfbVZPpFl31ferYhqFhxa0bdhh42TtxFK-mbPcVqy3iOsqE-f4rCFiycqgGmX5dIgfHLAUR_JR=w1398-h1297-no?authuser=0)

Step 5:

Once we are done tear down the local deployment.

![](https://lh3.googleusercontent.com/pw/ACtC-3dlmEN8uLEjH43-DU_EVtTAg2OzCAUWndngD85C0NxxCS8C6nQlFCXjWMlJgRi9OLTvor73XW9RFZBY3521xabMSUAietEA65tMWS4gaGD9Ndpc0wcv9xpKAS63RKyqOe71GkTC9xSqJZMgMh4ZmaXM=w851-h402-no?authuser=0)
