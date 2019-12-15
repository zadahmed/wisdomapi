FROM python:3.7-alpine3.8

# Update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.8/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.8/community" >> /etc/apk/repositories

#RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN apk --no-cache --update-cache add gcc gfortran python python-dev py-pip build-base wget freetype-dev libpng-dev openblas-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

# Install chromedriver
RUN apk update
RUN apk add chromium chromium-chromedriver

# Install selenium
RUN pip install --upgrade pip
RUN pip install selenium==3.8.0

# Copy files
RUN mkdir /home/wisdom
COPY ["MontyRun.py", "TopicalCleaner.py", "InfluentialCleaner.py", "FactualCleaner.py", "MontgomeryLog.txt", "requirements.txt", "./home/wisdom/"]
RUN mkdir /home/wisdom/MontGomery
COPY ["MontGomery/BaseMonty.py", "./home/wisdom/MontGomery/"]
RUN mkdir /home/wisdom/MontGomery/Factual
COPY ["MontGomery/Factual/FactualMonty.py", "./home/wisdom/MontGomery/Factual/"]
RUN mkdir /home/wisdom/MontGomery/Topical
COPY ["MontGomery/Topical/TopicalMonty.py", "./home/wisdom/MontGomery/Topical/"]
RUN mkdir /home/wisdom/MontGomery/Influential
COPY ["MontGomery/Influential/InfluentialMonty.py", "./home/wisdom/MontGomery/Influential/"]

RUN pip install numpy pandas
RUN pip install spacy==2.0.18
RUN python -m spacy download en
RUN pip install youtube-dl==2019.4.24
RUN apk add --update --no-cache g++ gcc libxslt-dev
#RUN pip install selenium==3.14.1
RUN pip install nltk==3.3
RUN ["python", "-c", "import nltk; nltk.download('stopwords')"]
RUN ["python", "-c", "import nltk; nltk.download('punkt')"]
RUN ["python", "-c", "import nltk; nltk.download('wordnet')"]
RUN ["python", "-c", "import nltk; nltk.download('averaged_perceptron_tagger')"]
RUN ["python", "-c", "import nltk; nltk.download('maxent_ne_chunker')"]
RUN ["python", "-c", "import nltk; nltk.download('words')"]
RUN pip install urllib3==1.24
RUN pip install sumy==0.7.0
RUN pip install gensim==3.7.3
RUN pip install beautifulsoup4==4.6.0
RUN pip install langdetect==1.0.7

CMD python /home/wisdom/MontyRun.py