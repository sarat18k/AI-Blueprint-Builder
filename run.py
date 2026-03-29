#!/usr/bin/env python3
"""Launch the A2A Startup Builder server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
