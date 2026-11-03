# Copyright (c) 2026 Jay Kerkar, Chaitanya Kelkar, Chirag Poornamath, Yash Kolekar and Shanta Sondur
# SPDX-License-Identifier: Apache-2.0
"""Runnable demo: TA provisioning CLI + device/server TCP processes.
Thin adapters over the transport-agnostic protocol/
core -- see demo/_transport.py for the length-prefixed JSON framing
(Section 4.3) and the envelope this layer wraps around M1/M2 so a server
can signal a rejection instead of a raw response."""
