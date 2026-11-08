-- Run once against an existing PostgreSQL/Supabase database before deploying this revision.
-- First verify there are no duplicate storage_path values.
SELECT storage_path, COUNT(*) FROM documents GROUP BY storage_path HAVING COUNT(*) > 1;

-- If the query above returns no rows, apply the unique index.
CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_storage_path ON documents (storage_path);
