# MontGomery

This is a ***private*** repository for MontGomery.

***

## Files

#### MontyRun.py
- This is a Python module that will run Monty from the command line.

#### MontyRun.ipynb
- This is a Notebook that will run Monty in an interactive Notebook.

#### MontGomery/
This is the directory that stores of all of the classes for Monty to run. It includes:
- BaseMonty.py - Base class to start and end the program
- Factual/FactualMonty.py - class for Monty's factual tour
- Influential/InfluentialMonty.py - class for Monty's influential tour
- Topical/TopicalMonty.py - class for Monty's topical tour

#### MontgomeryLog.txt
- This is a .txt file that contains a log of completed runs by Monty. 
- It includes: datetime, topic, search, summary points and rating.

#### FactualCleaner.py
- This is a file containing functions for cleaning the factual data sources. 

#### TopicalCleaner.py
- This is a file containing functions for cleaning the topical data sources. 

#### InfluentialCleaner.py
- This is a file containing functions for cleaning the influential data sources. 

## Usage

#### Make local repository

The first step is to clone this remote repository into your local filesystem

    $ git clone https://github.com/agodwinp/montGomery.git

#### Install Python

- Before you can run Monty, you need to install Python and create an environment with Monty's dependencies.
- Let's install Python via Anaconda. Visit this link: https://www.anaconda.com/distribution/ and choose the latest Python version (to date it is 3.7).
- Follow the wizard through installation and now you have a distribution of Python installed.

#### Create Python environment

- Now let's create an environment. Open Anaconda on your Mac and click on the environments tab on the left hand side.
- At the bottom, there should be a button to "Create" a new environment.
- Click on "Create". Name your environment something short and easy to remember.
- Check the box next to "Python" and select the version of Python to be 3.6.
- Leave the box next to "R" as unchecked.
- Now click on "Create" and wait for the environment to be created. 

#### Install dependencies

The dependencies for Monty to run as the following packages:
- **selenium** - used for robotic automation
- **nltk** - used for natural language processing
- **pandas** - used for data manipulation
- **numpy** - used for mathematical computation
- **sumy** - used for natural language processing
- **spacy** - used for named entity recognition
- **gensim** - used for natural language processing
- **BeautifulSoup** - used for web scraping and parsing
- **youtube-dl** - used for analysing YouTube videos
- **langdetect** - used for detecting languages

There are some other packages that will be used, but these will be pre-installed within the environment that you created, thanks to the Anaconda distribution. 

To install each of these packages, use the below snippets. But first, open up a terminal window and start your Python environment by running:

    $ conda activate <name of environment>

You should now see the name of your environment appear on the left side of the terminal output. Make sure you can see this before installing any of the below packages.

**Selenium**

    $ pip install selenium

Once installing Selenium, you need to install a driver to interface into the chosen web browser. We will use Chrome for this. Please install Google Chrome if you don't have it already. Once you have Chrome, follow this link: https://sites.google.com/a/chromium.org/chromedriver/downloads to find the Chrome driver. Download the latest release and place the downloaded file into the same directory as "BaseMonty.py".

Now, you must add the Chromedriver executable to your computers PATH. Run these commands on the terminal to do this:

    $ nano /etc/paths
    Enter your password
    Go to the bottom of the file and add the path directory to the Chromedriver executable, something like this: Users/arun/MontGomery
    $ control-X, to quit
    $ Y, to save
    Press enter to confirm


**NLTK**

    $ pip install nltk

**Pandas**

    $ pip install pandas

**NumPy**

    $ pip install numpy

**Sumy**

    $ pip install sumy

**SpaCy**

    $ pip install -U spacy
    $ python -m spacy download en

**Gensim**

    $ pip install -U gensim

**BeautifulSoup**

    $ pip install beautifulsoup4

**youtube-dl**

    $ sudo pip install youtube-dl

**langdetect**

    $ pip install langdetect

If any of these have trouble installing, move onto the next one and let me know so that I can fix the issue for you!

#### Run Monty

Now you should have all the dependencies installed for Monty to run.

- Open up a terminal window.
- Activate the Python environment that we created and installed the dependencies in.
- Navigate to the cloned folder called MontGomery, within this folder you should see a `MontyRun.py` file.

Finall run the following command and follow the instructions that Monty proposes!

    $ python MontyRun.py

## Authors
- Arun Godwin Patel
