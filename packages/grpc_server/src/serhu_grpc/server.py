"""gRPC server setup for the BeingService.

Provides ``create_server`` to build a configured gRPC server instance
and ``serve`` as the main entry point for running the service.

Run with:
    python -m serhu_grpc.server --port 50051
"""

from __future__ import annotations

import argparse
import logging
from concurrent import futures

import grpc

from serhu_orchestrator.proto.ser_identity_pb2_grpc import add_BeingServiceServicer_to_server
from serhu_grpc.service import SerhuBeingServicer

logger = logging.getLogger(__name__)

DEFAULT_PORT = 50051
DEFAULT_WORKERS = 4


def create_server(
    *,
    port: int = DEFAULT_PORT,
    max_workers: int = DEFAULT_WORKERS,
    servicer: SerhuBeingServicer | None = None,
) -> grpc.Server:
    """Create and configure a gRPC server.

    Parameters
    ----------
    port : int
        Port to listen on.
    max_workers : int
        Maximum number of thread pool workers.
    servicer : SerhuBeingServicer | None
        Optional pre-configured servicer instance.

    Returns
    -------
    grpc.Server
        A configured but not-yet-started gRPC server.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    add_BeingServiceServicer_to_server(servicer or SerhuBeingServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    return server


def serve(port: int = DEFAULT_PORT, max_workers: int = DEFAULT_WORKERS) -> None:
    """Start the gRPC server and block until termination.

    Parameters
    ----------
    port : int
        Port to listen on.
    max_workers : int
        Maximum number of thread pool workers.
    """
    logging.basicConfig(level=logging.INFO)
    server = create_server(port=port, max_workers=max_workers)
    server.start()
    logger.info("SerHu BeingService gRPC server listening on port %d", port)
    server.wait_for_termination()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="SerHu gRPC BeingService server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen on")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="Thread pool workers")
    args = parser.parse_args()
    serve(port=args.port, max_workers=args.workers)


if __name__ == "__main__":
    main()
