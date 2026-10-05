"""Agent core: a question becomes a plan of tool calls, the tools fetch from the local
database, and the answer is grounded in what they returned.

See ``runner.run_question`` for the end-to-end flow.
"""
