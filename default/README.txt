Source Repository Settings

REPOSITORY CLONE URL

https://source.developers.google.com/p/manglebracket/

Your repository is currently empty. Use one of the following to push content to it.

Initialize your Cloud Repository on your local machine

To initialize this repository on your local machine:
Install Google Cloud SDK
Run gcloud init manglebracket
Commit content to the newly created git repository
Push them using git push -u origin master
Push from an existing repository to your Cloud Repository

To push existing Git commits to your Cloud Repository:
Install Google Cloud SDK
Authenticate using the following commands: 
gcloud auth login 
git config credential.helper gcloud.sh (replace the script by gcloud.cmd if you are running Windows)
Then, to push your existing commits, use the following commands: 
git remote add google https://source.developers.google.com/p/manglebracket/ 
git push google master
Alternatively, instead of using the Google Cloud SDK to manage your authentication, you can manually generate your Git credentials by following this link.

Connect an external repository

If you connect a repository, your Cloud Repository will mirror the connected repository's content. Pushing to the Cloud Repository will no longer be possible.