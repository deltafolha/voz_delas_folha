FROM python:3.10
WORKDIR /app
# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt .
RUN pip install -r requirements.txt
RUN pip install python-decouple flask_httpauth
COPY . .
CMD [ "python", "main.py" ]                                                                                                                                                          