FROM python:3

WORKDIR /usr/src/monkalot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD [ "python", "./monkalot.py" ]