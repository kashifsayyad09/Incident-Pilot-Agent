# Strands Decider 2B model server (System One API on :9000).
# NOTE: not built or run in this repo's CI. Pulls torch (large) and downloads the model
# weights from Hugging Face on first start; mount a volume on /root/.cache to keep them.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 HF_HOME=/root/.cache/huggingface
RUN pip install --no-cache-dir strands-decider==0.1.0
EXPOSE 9000
CMD ["strands-decider", "serve", "StrandsAgents/strands-decider-2B-hobson-v19", "--host", "0.0.0.0", "--port", "9000", "--device", "cpu"]
