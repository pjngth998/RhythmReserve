FROM python

WORKDIR /app

COPY requirement.txt .

RUN pip install -r requirement.txt

COPY FINAL_CODE .

CMD ["python3", "mcp_code.py"]