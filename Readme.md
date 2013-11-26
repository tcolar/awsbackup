# Simple AWS backup and snapshot copy script


This scripts allows to backup AWS instances, specify how many copies to keep(It removes older ones), when to copy them to another region
and how many copies to keep there(remove old ones too).

### Installation
First you need to install Boto

WARNING: The boto version in the Ubuntu repo might be very obsolete, so It's best to install from sources

    git clone https://github.com/boto/boto.git
    cd boto
    sudo python setup.py install

Install this :

    cd ..
    git clone https://github.com/tcolar

#### Setup
Copy [aws_example.json](aws_example.json) under aws.json

    cp aws_example.json aws.json

And modify it to your liking to describe which instances to backup,
how many copies to keep(It removes older ones), when to copy them to another region
and how many copies to keep there(remove old ones too).

### Usage:
    cd awsbackup
    python backup.py

#### Cron script
If you want to run it once a day and email you the output:

You can create a script like this (task.sh):

    #!/bin/bash
    cd /home/me/awsbackup/
    python backup.py | mail -s "AWS Backup report" me@mycompany.com

Then have that script run from the cron:

    0 3 * * * /home/me/aws/task.sh &


