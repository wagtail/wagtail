Snapsite
========

Snapsite a demo project to make documentation screenshots.

In your env install Wagtail and selenium:

    pip install -e '.[testing,docs]' -U
    pip isntall selenium

Run a container with a selenium server:

    docker run -d -p 4444:4444 --shm-size=2g selenium/standalone-chrome
 
The screenshots are taken in a test:
    
    cd wagtail/tests/snapsite 
    python manage.py test
