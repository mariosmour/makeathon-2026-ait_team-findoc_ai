-- 1. Enable the pgvector extension to work with embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create a table to store the main document analysis (metadata)
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    fields JSONB,
    line_items JSONB,
    raw_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Create a table to store the document chunks and their embeddings
CREATE TABLE document_chunks (
    id BIGSERIAL PRIMARY KEY,
    doc_id TEXT REFERENCES documents(doc_id) ON DELETE CASCADE,
    filename TEXT,
    page INTEGER,
    source_text TEXT NOT NULL,
    polygon JSONB, -- Stores the bounding box coordinates for frontend visual evidence
    -- Define the embedding vector dimension. 
    -- 1536 is standard for OpenAI (text-embedding-ada-002 or text-embedding-3-small)
    -- If using an open-source model like all-MiniLM-L6-v2, change this to 384.
    embedding vector(1536) 
);

-- 4. Create an HNSW index on the embedding column for fast similarity search
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- 5. Create a Postgres function (RPC) to search for similar chunks
-- This function can be called directly from your Python backend via the Supabase client
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_threshold float,
    match_count int,
    p_doc_id text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    doc_id text,
    filename text,
    page integer,
    source_text text,
    polygon jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.doc_id,
        dc.filename,
        dc.page,
        dc.source_text,
        dc.polygon,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    -- Only search within a specific document if p_doc_id is provided
    WHERE (p_doc_id IS NULL OR dc.doc_id = p_doc_id)
      -- Only return matches above the similarity threshold
      AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
