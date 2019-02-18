FROM python:3
RUN apt-get update -y
# Install any Python dependencies specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt
COPY . /app
WORKDIR /app
ENTRYPOINT ["python"]
CMD ["app.py"]
