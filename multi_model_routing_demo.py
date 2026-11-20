import boto3
import matplotlib.pyplot as plt

client = boto3.client("bedrock-runtime", region_name="us-east-1")

# $3.00 / $15.00 per 1M tokens
ADVANCED_MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
# $0.06 / $0.24 per 1M tokens
FAST_MODEL = "us.amazon.nova-lite-v1:0"

PRICING = {
    ADVANCED_MODEL: (3.00, 15.00),
    FAST_MODEL: (0.06, 0.24),
}

prompts = [
    "what is cloud computing in one sentence",
    "what are attention heads according to the paper by Vaswani et al.",
]


def ask(model_id, prompt):
    response = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
    )
    usage = response["usage"]
    latency_ms = response["metrics"]["latencyMs"]
    in_rate, out_rate = PRICING[model_id]
    cost = (usage["inputTokens"] * in_rate +
            usage["outputTokens"] * out_rate) / 1_000_000
    return cost, latency_ms


def route_prompt(prompt):
    complex_signals = ["vaswani", "attention",
                       "paper", "explain", "analyze", "architecture"]
    if len(prompt.split()) > 10 or any(word in prompt.lower() for word in complex_signals):
        return ADVANCED_MODEL
    return FAST_MODEL


# 1. Run All-Advanced Baseline
base_cost, base_lat = 0, 0
for p in prompts:
    c, l = ask(ADVANCED_MODEL, p)
    base_cost += c
    base_lat += l

# 2. Run Complexity-Routed
route_cost, route_lat = 0, 0
for p in prompts:
    c, l = ask(route_prompt(p), p)
    route_cost += c
    route_lat += l

# 3. Print Comparison Table
savings_pct = ((base_cost - route_cost) / base_cost) * 100
lat_diff = base_lat - route_lat

print("\n" + "=" * 62)
print(f"{'Strategy':<20} | {'Total Cost ($)':<16} | {'Total Latency (ms)':<18}")
print("-" * 62)
print(f"{'All-Advanced':<20} | ${base_cost:<15.6f} | {base_lat:<18}")
print(f"{'Routed':<20} | ${route_cost:<15.6f} | {route_lat:<18}")
print("=" * 62)
print(f"Cost Saved: {savings_pct:.1f}%  |  Latency Reduced: {lat_diff} ms\n")

# 4. Plot Side-by-Side Graph
strategies = ["All-Advanced", "Routed"]
colors = ["#4F46E5", "#10B981"]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))

ax1.bar(strategies, [base_cost, route_cost], color=colors)
ax1.set_title("Total Cost (USD)")
ax1.set_ylabel("USD ($)")

ax2.bar(strategies, [base_lat, route_lat], color=colors)
ax2.set_title("Total Latency (ms)")
ax2.set_ylabel("Milliseconds (ms)")

plt.suptitle("AWS Bedrock: All-Advanced vs. Multi-Model Routing")
plt.tight_layout()
plt.show()
