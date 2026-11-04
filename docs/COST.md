
# LLM Cost Report

## 1. Model and Pricing

- Provider: FakeProvider
- Model label: llama3.1:8b
- Input price per million tokens: $0
- Output price per million tokens: $0

The fake provider is used for testing without a real LLM API.
Therefore, these results do not represent production model pricing.

For production usage, update this section with the actual model name,
provider pricing page, and input/output prices.

## 2. Average Token Usage Per Call

Based on 15 successful calls recorded in `logs/cost.jsonl`.

- Total successful calls: 15
- Average input tokens per call: 175.00
- Average output tokens per call: 20.53

The averages include the RAG test call, which used 2,504 input tokens.
Token counts are estimated by the Fake Provider.

## 3. Estimated Cost Per Question

Formula:

Cost per question =
(input tokens × input price per million
+ output tokens × output price per million) / 1,000,000

- Estimated cost per question: $0.00 (Fake Provider; simulated cost)

Use the actual model's published input and output token prices.

## 4. Estimated Cost For 1,000 Questions

Cost for 1,000 questions = average cost per question × 1,000

- Estimated cost for 1,000 questions:  $0.00 (Fake Provider; simulated cost)

This is an estimate. Actual costs depend on prompt length, answer length,
model pricing, retries, and fallback usage.

## 5. One Way to Reduce Cost

Reduce unnecessary prompt tokens by sending only relevant conversation
history and keeping system instructions concise. This can reduce input
token usage and overall API cost.
