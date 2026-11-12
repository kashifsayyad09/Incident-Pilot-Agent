# Benchmark: Decider 2B vs Bedrock-only routing

`benchmark/results/` is empty on purpose. Results are written there only by a real run of
`backend/scripts/benchmark.py` against a running Decider 2B server and/or a Bedrock model you
have access to. The repository ships no benchmark numbers because none have been measured yet.

```bash
cd backend
python scripts/benchmark.py --decider-url http://localhost:9000 \
  --bedrock-model-id <model-or-inference-profile> --region us-east-1 --repeat 10 \
  --decider-hardware "<GPU/CPU you served it on>" [--price-in <USD/1M> --price-out <USD/1M>]
```

Read the "Read this first" section of each generated report before quoting a number: five
hand-written scenarios make agreement a smoke check, and latency depends on your hardware,
region and network.
