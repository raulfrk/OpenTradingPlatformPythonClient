import json

import structlog

# Configure structlog to use the JSON renderer
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(serializer=json.dumps),
    ],
    context_class=dict,
)

log = structlog.get_logger()
