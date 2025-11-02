FROM public.ecr.aws/lambda/python:3.10
COPY inference.py requirements.txt ./
RUN pip install -r requirements.txt
CMD ["inference.handler"]

