-- Database initialization for DeepAgents MCP RAG system

-- Create Phoenix database for observability
CREATE DATABASE phoenix;

-- Create evaluation results table
CREATE TABLE IF NOT EXISTS evaluation_results (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dataset_size INTEGER NOT NULL,
    answer_relevancy DECIMAL(5,4),
    context_precision DECIMAL(5,4),
    context_recall DECIMAL(5,4),
    faithfulness DECIMAL(5,4),
    overall_score DECIMAL(5,4),
    metadata JSONB,
    results_json JSONB
);

-- Create performance metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(50) NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latency_ms INTEGER NOT NULL,
    num_results INTEGER NOT NULL,
    cache_hit BOOLEAN DEFAULT FALSE,
    token_count INTEGER,
    metadata JSONB
);

-- Create retrieval logs table
CREATE TABLE IF NOT EXISTS retrieval_logs (
    id SERIAL PRIMARY KEY,
    strategy VARCHAR(50) NOT NULL,
    query TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT TRUE,
    latency_ms INTEGER,
    num_results INTEGER,
    error_message TEXT,
    metadata JSONB
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_evaluation_strategy_timestamp ON evaluation_results(strategy, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_strategy_timestamp ON performance_metrics(strategy, timestamp);
CREATE INDEX IF NOT EXISTS idx_retrieval_strategy_timestamp ON retrieval_logs(strategy, timestamp);
CREATE INDEX IF NOT EXISTS idx_performance_query_hash ON performance_metrics(query_hash);

-- Create views for common queries
CREATE OR REPLACE VIEW strategy_performance AS
SELECT
    strategy,
    COUNT(*) as total_queries,
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    AVG(num_results::DECIMAL) as avg_results_count,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::DECIMAL / COUNT(*) as cache_hit_rate
FROM performance_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY strategy;

CREATE OR REPLACE VIEW latest_evaluations AS
SELECT DISTINCT ON (strategy)
    strategy,
    timestamp,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
    overall_score,
    dataset_size
FROM evaluation_results
ORDER BY strategy, timestamp DESC;

-- Insert initial test data
INSERT INTO evaluation_results (
    strategy, dataset_size, answer_relevancy, context_precision,
    context_recall, faithfulness, overall_score, metadata
) VALUES
    ('ensemble', 20, 0.87, 0.82, 0.89, 0.93, 0.88, '{"test_run": true}'),
    ('vector', 20, 0.85, 0.79, 0.86, 0.91, 0.85, '{"test_run": true}'),
    ('bm25', 20, 0.78, 0.88, 0.75, 0.95, 0.84, '{"test_run": true}')
ON CONFLICT DO NOTHING;