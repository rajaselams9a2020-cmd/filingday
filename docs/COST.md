
# LLM Cost Report

## 1. Model and Pricing

- Provider: FakeProvider (local testing)
- Model: fake-model
- Input price per million tokens: $0 (fake provider)
- Output price per million tokens: $0 (fake provider)

The fake provider is used for testing without a real LLM API.
Therefore, these results do not represent production model pricing.

For production usage, update this section with the actual model name,
provider pricing page, and input/output prices.

## 2. Average Token Usage Per Question

Use the records in `logs/cost.jsonl` and the `/usage` endpoint
to calculate average input and output tokens per question.

- Total successful questions: TODO
- Average input tokens per question: TODO
- Average output tokens per question: TODO

Calculate averages using successful calls only.

## 3. Estimated Cost Per Question

Formula:

Cost per question =
(input tokens × input price per million
+ output tokens × output price per million) / 1,000,000

- Estimated cost per question: TODO

Use the actual model's published input and output token prices.

## 4. Estimated Cost For 1,000 Questions

Cost for 1,000 questions = average cost per question × 1,000

- Estimated cost for 1,000 questions: TODO

This is an estimate. Actual costs depend on prompt length, answer length,
model pricing, retries, and fallback usage.

## 5. One Way to Reduce Cost

Reduce unnecessary prompt tokens by sending only relevant conversation
history and keeping system instructions concise. This can reduce input
token usage and overall API cost.
