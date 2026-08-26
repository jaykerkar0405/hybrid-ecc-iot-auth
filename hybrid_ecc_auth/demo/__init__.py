"""Runnable demo: TA provisioning CLI + device/server TCP processes
(PRD Section 4.2). Thin adapters over the transport-agnostic protocol/
core -- see demo/_transport.py for the length-prefixed JSON framing
(Section 4.3) and the envelope this layer wraps around M1/M2 so a server
can signal a rejection instead of a raw response."""
