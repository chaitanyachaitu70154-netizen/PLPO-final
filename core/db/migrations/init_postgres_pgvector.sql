-- ==============================================================================
-- PLPO Phase 4: Production PostgreSQL + pgvector Database Schema & DDL
-- ==============================================================================
-- Features:
-- 1. pgvector extension for dense semantic embeddings (768 dimensions)
-- 2. Strict relational integrity, foreign keys with ON DELETE CASCADE
-- 3. High-performance composite B-tree indexes for multi-tenant student querying
-- 4. HNSW vector index for low-latency sub-millisecond approximate nearest neighbor (ANN) search
-- ==============================================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Student Biographical & Educational Profiles
CREATE TABLE IF NOT EXISTS student_profiles (
    student_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    education_level VARCHAR(128),
    subject VARCHAR(128) NOT NULL DEFAULT 'Python Programming',
    current_level VARCHAR(128),
    learning_goal TEXT,
    preferred_pace VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Topic Mastery & Metacognitive Calibration States
CREATE TABLE IF NOT EXISTS topic_masteries (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    topic_name VARCHAR(128) NOT NULL,
    mastery_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    incorrect_attempts INTEGER NOT NULL DEFAULT 0,
    recent_performance_json TEXT NOT NULL DEFAULT '[]',
    misconception_status_json TEXT NOT NULL DEFAULT '{}',
    learning_status VARCHAR(64) NOT NULL DEFAULT 'in_progress',
    last_assessed TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_student_topic UNIQUE (student_id, topic_name)
);

-- 4. Diagnostic & Follow-Up Assessment Telemetry
CREATE TABLE IF NOT EXISTS assessment_attempts (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    question_id VARCHAR(64) NOT NULL,
    topic VARCHAR(128) NOT NULL,
    difficulty VARCHAR(32) NOT NULL DEFAULT 'Medium',
    chosen_option TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    confidence INTEGER NOT NULL CHECK (confidence >= 1 AND confidence <= 5),
    response_time_sec DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 5. Cognitive Misconceptions Lifecycle State
CREATE TABLE IF NOT EXISTS misconception_states (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    misconception_id VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(64) NOT NULL DEFAULT 'detected',
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    remediated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_student_misconception UNIQUE (student_id, misconception_id)
);

-- 6. Dynamic Learning Path Milestones & Versioning
CREATE TABLE IF NOT EXISTS learning_paths (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    milestones_json TEXT NOT NULL,
    rationale TEXT
);

-- 7. Immutable Bayesian State Change Audit Trail
CREATE TABLE IF NOT EXISTS state_change_audits (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL REFERENCES student_profiles(student_id) ON DELETE CASCADE,
    topic_name VARCHAR(128) NOT NULL,
    old_mastery DOUBLE PRECISION NOT NULL,
    new_mastery DOUBLE PRECISION NOT NULL,
    old_confidence DOUBLE PRECISION NOT NULL,
    new_confidence DOUBLE PRECISION NOT NULL,
    reason TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 8. Curriculum Chunks & RAG Semantic Embeddings (pgvector)
CREATE TABLE IF NOT EXISTS curriculum_embeddings (
    id SERIAL PRIMARY KEY,
    topic_name VARCHAR(128) NOT NULL,
    subtopic_title VARCHAR(255) NOT NULL,
    content_text TEXT NOT NULL,
    embedding vector(768),
    embedding_json TEXT,
    metadata_json TEXT DEFAULT '{}' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- ==============================================================================
-- INDEXING STRATEGY FOR CONCURRENT USERS & LARGE DATASETS
-- ==============================================================================

-- B-Tree Indexes on Foreign Keys and Query Selectors
CREATE INDEX IF NOT EXISTS idx_topic_masteries_student_id ON topic_masteries(student_id);
CREATE INDEX IF NOT EXISTS idx_topic_masteries_topic ON topic_masteries(topic_name);
CREATE INDEX IF NOT EXISTS idx_student_topic_status ON topic_masteries(student_id, topic_name, learning_status);

CREATE INDEX IF NOT EXISTS idx_assessment_student_topic ON assessment_attempts(student_id, topic, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessment_question ON assessment_attempts(question_id);
CREATE INDEX IF NOT EXISTS idx_assessment_created_at ON assessment_attempts(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_misc_student_status ON misconception_states(student_id, status);
CREATE INDEX IF NOT EXISTS idx_misc_id ON misconception_states(misconception_id);

CREATE INDEX IF NOT EXISTS idx_learning_paths_student_version ON learning_paths(student_id, version DESC);

CREATE INDEX IF NOT EXISTS idx_state_audits_student_time ON state_change_audits(student_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_state_audits_topic ON state_change_audits(topic_name);

CREATE INDEX IF NOT EXISTS idx_curriculum_topic ON curriculum_embeddings(topic_name);

-- HNSW Vector Index for Sub-Millisecond Cosine Similarity Search
-- Distance metric: cosine distance (<=> operator)
CREATE INDEX IF NOT EXISTS idx_curriculum_embedding_hnsw 
ON curriculum_embeddings 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- ==============================================================================
-- INITIAL SEED: BASELINE DEMO DATA
-- ==============================================================================

INSERT INTO student_profiles (student_id, name, education_level, subject, current_level, learning_goal, preferred_pace)
VALUES (
    'STU-2026-PY-089',
    'Demo Student',
    'Undergraduate Computer Science',
    'Python Programming',
    'Intermediate Foundations',
    'Master Modular Function Design & Data Structures',
    'Moderate (3 modules/week)'
) ON CONFLICT (student_id) DO NOTHING;
