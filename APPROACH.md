# Approach and Architecture

## Data Model & Tree Parsing
- **PDF parsing (PyMuPDF)**: I used PyMuPDF to extract text spans and their corresponding font sizes. The heuristic for defining heading levels relies on font size comparison against standard thresholds (e.g., >16.0 for Level 1, >12.0 for Level 2, and ≤12.0 for Body text).
- **Handling Irregularities**:
  - *Multi-line headings*: Consecutive heading lines of the same level without interleaving body text are merged.
  - *Duplicate headings*: The logical ID system uses the parent path (e.g., `root/1.device-overview/1.1-intended-use`). If two headings have the exact same text and parent, they get indexed (e.g., `-1`, `-2`).
  - *Orphaned text*: Assigned to a virtual "root" node to prevent data loss.
- **Tree Construction**: Stack-based parsing. The parser maintains a `current_path` and pops items when a heading of equal or higher level is encountered.

## Versioning & Match Strategy
- **Strategy**: I used **Path-based matching with Content Hashing**. Each node receives a `logical_id` based on its hierarchical heading path.
- **Why**: Medical devices documents are structured. A specific section (like "Setup > Warnings") retains its identity even if the text changes. By matching logical IDs across v1 and v2, we accurately detect if the underlying *text* of that section changed without losing the identity of the section.
- **Known Failure Mode**: If a heading's text changes significantly (e.g., "Warnings" becomes "Important Safety Warnings"), its `logical_id` changes. The system will see this as a deleted old node and a newly created node, breaking traceability for that specific section.

## LLM Integration & Generation
- I designed the schema to pass the reconstructed context to the LLM. For this local assignment, the LLM endpoint is mocked with structured JSON responses. 
- **Storage**: I used `TinyDB` as the NoSQL local store. Why? Because it requires zero setup for reviewers (no local MongoDB server needed) but fully satisfies the NoSQL constraint of storing unstructured/semi-structured LLM JSON outputs. 
- **Duplicate Selections**: If the same selection is submitted twice, the system creates two separate generation records (as LLM responses are non-deterministic, multiple runs can yield different test ideas).

## Decision Log (Required)

**1. What's the one part of this system most likely to silently give wrong results without erroring? How would you catch it?**
The PDF heuristic parser is the most likely to silently merge body text into a heading or split a heading incorrectly if the source document has an unexpected font size for a specific word (e.g., a large bold warning inside body text). To catch it, I would implement validation checks (e.g., flag nodes where the heading length exceeds 200 characters) and write unit tests against highly irregular mock PDFs.

**2. Where did you choose simplicity over correctness because of time, and what would break first if this went to production as-is?**
I chose to use a simple file-based SQLite database with synchronous SQLAlchemy calls and TinyDB for NoSQL storage. If this went to production as-is, the synchronous database calls and the single-file TinyDB would immediately become a bottleneck under high concurrency or large data volumes, causing blocking and write locks.

**3. Name one input (to your parser, your versioning matcher, or your LLM call) that you did not handle, and what your system does when it sees it.**
I did not explicitly handle tables and lists in the PDF parsing. The `PyMuPDF` `.get_text("dict")` extracts table rows as standard text lines. The system will treat them as body text (since their font size usually matches body text) and append them sequentially, losing the semantic grid structure of the table.
