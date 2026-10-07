# PostgreSQL migration boundary

The working academic application intentionally remains SQLite-backed because the GUI, four-level demo databases, and existing service layer are built around local SQLite transactions.

The production migration should be performed as a separate controlled milestone:

1. Introduce a repository interface for voters, votes, checkpoints, events, and the replication outbox.
2. Implement a PostgreSQL repository using parameterized queries and explicit transactions.
3. Run schema migrations for voters, ballot tokens, private ballots, audit events, checkpoints, and the outbox.
4. Run the existing API, tamper, duplicate-vote, and replication tests against both backends.
5. Keep the Tkinter demo on SQLite until parity is proven.

This boundary is deliberate: adding a PostgreSQL container without migrating the service layer would create a misleading deployment claim. The current Docker image is a secure SQLite/API demonstration, while this document defines the safe migration path.
