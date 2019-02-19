FROM python:3
RUN apt-get update -y
# Install any Python dependencies specified in requirements.txt
COPY . /dancify
WORKDIR /dancify
RUN pip install --trusted-host pypi.python.org -r requirements.txt
WORKDIR /dancify/app
ENTRYPOINT ["python"]
CMD ["app.py"]
