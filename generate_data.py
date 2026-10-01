import os

DOCUMENTS = {
    "it_postgres_failover.txt": "The failover mechanism for our primary PostgreSQL cluster triggers automatically after 3 missed heartbeats. It routes traffic to the secondary cluster in the us-east-1 region.",
    "it_vpn_access.txt": "Employees must use Cisco AnyConnect for VPN access. Multi-factor authentication via Duo is strictly required for all connections outside the corporate network.",
    "hr_pet_policy.txt": "The company pet policy allows only registered service animals in the office. Emotional support animals and personal pets (including dogs and cats) are strictly prohibited on premises.",
    "hr_remote_work.txt": "Employee remote work policy mandates 3 days in office for engineering teams starting Q3. Approved work-from-home days are Tuesday and Thursday.",
    "eng_titan_architecture.txt": "Project TITAN-9000 architecture uses a decentralized distributed ledger with a 500ms block time. It is written in C++ and utilizes a custom KD-Tree for state management.",
    "eng_api_ratelimits.txt": "The public-facing REST API enforces a strict rate limit of 100 requests per minute per IP address. Exceeding this triggers a 429 Too Many Requests response.",
    "sec_password_rotation.txt": "Corporate passwords must be rotated every 90 days. Passwords must be at least 16 characters long and cannot reuse any of the previous 5 passwords.",
    "sec_incident_response.txt": "In the event of a P1 security breach, the incident response team must isolate the affected subnet within 15 minutes and notify the CISO immediately.",
    "ops_oncall_schedule.txt": "The DevOps on-call rotation shifts every Friday at 12:00 PM UTC. Primary on-call must acknowledge PagerDuty alerts within 5 minutes.",
    "ops_kubernetes_scaling.txt": "Our Kubernetes clusters use the Horizontal Pod Autoscaler (HPA). It triggers when CPU utilization exceeds 75% for more than 3 consecutive minutes."
}

os.makedirs("docs", exist_ok=True)

for filename, content in DOCUMENTS.items():
    with open(f"docs/{filename}", "w") as f:
        f.write(content)

print(f"Successfully generated {len(DOCUMENTS)} mock documents in the 'docs/' folder.")