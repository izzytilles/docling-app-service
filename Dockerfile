# start with python base
FROM python:3.12

# set working directory
WORKDIR /app

# copy requirements and install python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# copy the rest of the application code
COPY . /app

# clean up pip cache
RUN rm -rf /root/.cache

# expose port for app
EXPOSE 8000

# run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "basic_docling:app"]