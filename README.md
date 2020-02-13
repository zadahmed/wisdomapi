## Wisdom Deployment

### Setting up Ubuntu DigitalOcean droplet

Follow this tutorial to set up Ubuntu 18.04 server: https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04

### Import code

Deploy Wisdom code from `deployment` branch into /wisdom folder:

    $ git clone --branch deployment https://github.com/zadahmed/wisdomapi.git

### Set up virtualenv

Change directory into /wisdom folder where you have imported the code, create a Python Venv and activate it:

    $ pip3 install virtualenv
    $ virtualenv wisdomenv
    $ source wisdomenv/bin/activate

### Install dependencies

Use the requirements.txt file to install dependencies:

    $ pip3 install -r requirements.txt

### Set up MongoDB

Follow these steps to install MongoDB or use this tutorial: https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-18-04:

    $ sudo apt update
    $ sudo apt install -y mongodb
    $ sudo systemctl status mongodb
    $ mongo --eval 'db.runCommand({ connectionStatus: 1 })'
    $ sudo systemctl status mongodb
    $ sudo systemctl restart mongodb
    $ sudo systemctl enable mongodb

Now create the database user `admin` and database `wisdomdb`:

    $ mongo
    $ use admin
    $ db.createUser({user:"admin", pwd:"admin123", roles:[{role:"root", db:"admin"}]})

Edit the mongodb.service file to include authorisation optin:

    $ sudo nano /lib/systemd/system/mongodb.service
    $ ExecStart=/usr/bin/mongod --auth --config /etc/mongod.conf

Reload the service and log in:

    $ sudo systemctl daemon-reload
    $ sudo service mongodb restart
    $ mongo -u admin -p admin123 --authenticationDatabase admin

Some basic commands for MongoDB:

    $ show dbs
    $ show collections
    $ use <DB NAME>
    $ db.createCollection("<COLLECTION NAME>")
    $ db.<COLLECTION NAME>.insert()
    $ db.<COLLECTION NAME>.remove({})
    $ db.dropDatabase()
    $ db.<COLLECTION NAME>.find(query)

### Committing changes to GitHub

Use the `deployment` branch to run code on the server. When changes are made, push the changes using the following command:

    $ git push wisdomapi deployment
