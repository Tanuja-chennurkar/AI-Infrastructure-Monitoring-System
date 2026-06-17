from opentelemetry import trace

from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk.trace import TracerProvider

from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor
)

from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter
)

resource = Resource.create(
    {
        "service.name": "sentinel-ai"
    }
)

provider = TracerProvider(
    resource=resource
)

trace.set_tracer_provider(provider)

provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint="tempo:4317",
            insecure=True
        )
    )
)

tracer = trace.get_tracer(__name__)
print("Telemetry initialized")