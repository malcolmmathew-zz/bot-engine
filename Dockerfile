# base python
FROM python:default

# add requirements and install in root
ADD requirements.txt /requirements.txt

RUN pip install -r requirements.txt

# expose port for other containers
EXPOSE 8080
