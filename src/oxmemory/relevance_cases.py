"""New fixed cases for abstention, independent of the earlier Git fixture queries."""

CASES = [
    # split, id, query, relevant statement or None, distractor statements
    (
        "development",
        "dev-connection",
        "How many database connections can we open?",
        "The database connection pool allows twenty concurrent connections.",
        ["Deployment artifacts are compressed with gzip.", "The interface supports dark mode."],
    ),
    (
        "development",
        "dev-health",
        "Where should a load balancer check service health?",
        "The readiness probe is available at /ready for load balancer health checks.",
        ["Database migrations run before deployment.", "User avatars are square."],
    ),
    (
        "development",
        "dev-dedupe",
        "How are duplicate webhook deliveries prevented?",
        "Webhook deliveries are deduplicated using the event identifier.",
        ["The webhook endpoint accepts JSON requests.", "Logs are kept for a week."],
    ),
    (
        "development",
        "dev-paraphrase",
        "Can clients submit the same purchase twice safely?",
        "Order creation uses an idempotency key to avoid duplicate purchases.",
        ["Product prices exclude tax.", "Orders contain a shipping address."],
    ),
    (
        "development",
        "dev-owner",
        "Who is responsible for production incident escalation?",
        None,
        ["The service writes errors to stderr.", "Health checks run every ten seconds."],
    ),
    (
        "development",
        "dev-sla",
        "What uptime guarantee is promised to customers?",
        None,
        ["Customer records have a UUID primary key.", "The status page uses a blue theme."],
    ),
    (
        "development",
        "dev-same-topic",
        "Who approved the webhook retry policy?",
        None,
        ["Webhook retry delay is exponential.", "Webhook payloads use JSON."],
    ),
    (
        "development",
        "dev-cost",
        "What is the monthly database hosting cost?",
        None,
        ["The database pool has twenty connections.", "The database uses TLS connections."],
    ),
    (
        "held_out",
        "test-pool",
        "When do unused connections close?",
        "Idle database connections are closed after two minutes.",
        ["Database backups are encrypted.", "The API accepts JSON payloads."],
    ),
    (
        "held_out",
        "test-health",
        "Which URL confirms the process is alive?",
        "The process liveness endpoint is /alive.",
        ["The readiness check tests database connectivity.", "The admin interface uses port 9000."],
    ),
    (
        "held_out",
        "test-limit",
        "What happens when a caller exceeds its request quota?",
        "Rate-limited callers receive HTTP 429 and a Retry-After header.",
        ["Requests include a correlation identifier.", "The server returns JSON errors."],
    ),
    (
        "held_out",
        "test-paraphrase",
        "How do we keep two workers from processing the same item?",
        "Workers claim queue items using an exclusive database lock.",
        ["Queue items include a creation timestamp.", "Worker logs contain job identifiers."],
    ),
    (
        "held_out",
        "test-upload",
        "How is the uploaded file's integrity checked?",
        "Uploaded files are verified using a SHA-256 checksum.",
        ["Uploaded files go to object storage.", "Upload progress is shown as a percentage."],
    ),
    (
        "held_out",
        "test-redaction",
        "Are access credentials allowed in application logs?",
        "Passwords and access tokens are redacted before log messages are written.",
        ["Application logs are rotated daily.", "Metrics are collected every minute."],
    ),
    (
        "held_out",
        "test-deletion",
        "Can a user recover an account immediately after deleting it?",
        "Deleted accounts are soft-deleted for seven days before permanent removal.",
        ["Account identifiers use UUIDs.", "Usernames are case-insensitive."],
    ),
    (
        "held_out",
        "test-cors",
        "Which browser origin can call the API?",
        "The API permits cross-origin requests only from https://app.example.invalid.",
        ["API requests use HTTPS.", "The development frontend runs on port 3000."],
    ),
    (
        "held_out",
        "test-owner",
        "Who is the security incident commander?",
        None,
        ["Security events are logged to the audit table.", "Incident identifiers use UUIDs."],
    ),
    (
        "held_out",
        "test-budget",
        "What budget is allocated to cloud storage?",
        None,
        ["Cloud storage objects are encrypted.", "Storage uploads use signed URLs."],
    ),
    (
        "held_out",
        "test-approval",
        "Who approved the rate limit settings?",
        None,
        ["The rate limit is one hundred requests per minute.", "Excess requests return HTTP 429."],
    ),
    (
        "held_out",
        "test-law",
        "Which jurisdiction governs customer contracts?",
        None,
        ["Customer records store a billing country.", "Invoices use ISO currency codes."],
    ),
    (
        "held_out",
        "test-rpo",
        "What recovery point objective did the business agree to?",
        None,
        ["Database backups run at midnight.", "Recovery scripts verify file checksums."],
    ),
    (
        "held_out",
        "test-vendor",
        "When does our cloud vendor contract expire?",
        None,
        ["Cloud access tokens expire after one hour.", "Object storage keeps file versions."],
    ),
    (
        "held_out",
        "test-contact",
        "What is the emergency support phone number?",
        None,
        ["Support tickets receive sequential numbers.", "User profiles can contain phone numbers."],
    ),
    (
        "held_out",
        "test-why",
        "Why did the team choose this message broker?",
        None,
        ["The message broker is RabbitMQ.", "Messages use durable queues."],
    ),
]


def dataset():
    return [
        dict(
            partition=p,
            id=i,
            query=q,
            memories=([answer] if answer else []) + noise,
            relevant=["m0"] if answer else [],
            label_note="Only the explicit answer is relevant; topic overlap alone is insufficient.",
        )
        for p, i, q, answer, noise in CASES
    ]
