FROM python:3.11-slim
WORKDIR /grader
RUN pip install --no-cache-dir numpy scipy pillow shapely
COPY score_metric.py /grader/score_metric.py
COPY grader.py /grader/grader.py
COPY render_result.py /grader/render_result.py
COPY render_errors.py /grader/render_errors.py
COPY render_review.py /grader/render_review.py
COPY ground_truth.json /grader/ground_truth.json
COPY drawing.png /grader/drawing.png
COPY test.sh /tests/test.sh
RUN chmod +x /tests/test.sh
