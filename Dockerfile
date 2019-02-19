FROM python:3
RUN apt-get update -y
# Install any Python dependencies specified in requirements.txt
COPY ./app /dancify
copy ./requirements.txt /dancify/requirements.txt
WORKDIR /dancify
RUN pip install --trusted-host pypi.python.org -r requirements.txt
WORKDIR /dancify
ENTRYPOINT ["python"]
CMD ["app.py"]
