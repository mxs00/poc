# Project Overview

## Architecture
- **Database**: PostgreSQL without ORM only native sql

## Database Schema Notes
- table names need to be prefixed with tbl_
- key column names need to be prefixed with table acronym 
- add audit columns
- maintain referential integrity
- foreign keys are prefixed with the table acronym
- use varchar for keys, do not use UUID datatype

====
prompts:
create a postgres database schema to manage llm pipelines to handle the pipeline steps can be sequential,parallel,start,end. 
each step needs to have reference to next and previous step in pipeline, maintain steps relationship in seperate table
create pipeline definition tables
create pipeline runtime execution tables

 chats, sessions, messages, conversations. 

the schema needs to have referencial integrity, 
table names need to be prefixed with tbl_
all keys need to be prefixed with table acronym 


create readme.md file
--------------------------------------------------
-- Pipeline Definition Tables

-- Table to store pipeline definitions
CREATE TABLE tbl_pipeline_definition (
    pipeline_id VARCHAR(255) PRIMARY KEY,
    pipeline_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table to store individual pipeline steps
CREATE TABLE tbl_pipeline_step (
    step_id VARCHAR(255) PRIMARY KEY,
    pipeline_id VARCHAR(255) NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(50) NOT NULL, -- 'sequential', 'parallel', 'start', 'end'
    step_config JSONB,
    execution_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pipeline_id) REFERENCES tbl_pipeline_definition(pipeline_id) ON DELETE CASCADE,
    -- Ensure step types are valid
    CONSTRAINT chk_step_type CHECK (step_type IN ('sequential', 'parallel', 'start', 'end'))
);

-- Table to maintain relationships between pipeline steps
CREATE TABLE tbl_pipeline_step_relationship (
    relationship_id VARCHAR(255) PRIMARY KEY,
    pipeline_id VARCHAR(255) NOT NULL,
    from_step_id VARCHAR(255),
    to_step_id VARCHAR(255),
    relationship_type VARCHAR(50) NOT NULL, -- 'next', 'previous'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pipeline_id) REFERENCES tbl_pipeline_definition(pipeline_id) ON DELETE CASCADE,
    FOREIGN KEY (from_step_id) REFERENCES tbl_pipeline_step(step_id) ON DELETE CASCADE,
    FOREIGN KEY (to_step_id) REFERENCES tbl_pipeline_step(step_id) ON DELETE CASCADE,
    -- Ensure relationship types are valid
    CONSTRAINT chk_relationship_type CHECK (relationship_type IN ('next', 'previous'))
);

-- Pipeline Execution Tables

-- Table to store pipeline execution instances
CREATE TABLE tbl_pipeline_execution (
    execution_id VARCHAR(255) PRIMARY KEY,
    pipeline_id VARCHAR(255) NOT NULL,
    execution_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pipeline_id) REFERENCES tbl_pipeline_definition(pipeline_id) ON DELETE CASCADE,
    -- Ensure execution status values are valid
    CONSTRAINT chk_execution_status CHECK (execution_status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Table to store individual step execution instances
CREATE TABLE tbl_step_execution (
    step_execution_id VARCHAR(255) PRIMARY KEY,
    execution_id VARCHAR(255) NOT NULL,
    step_id VARCHAR(255) NOT NULL,
    step_execution_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (execution_id) REFERENCES tbl_pipeline_execution(execution_id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES tbl_pipeline_step(step_id) ON DELETE CASCADE,
    -- Ensure step execution status values are valid
    CONSTRAINT chk_step_execution_status CHECK (step_execution_status IN ('pending', 'running', 'completed', 'failed', 'cancelled'))
);

-- Indexes for better performance
CREATE INDEX idx_pipeline_definition_active ON tbl_pipeline_definition(is_active);
CREATE INDEX idx_pipeline_step_pipeline_id ON tbl_pipeline_step(pipeline_id);
CREATE INDEX idx_pipeline_step_order ON tbl_pipeline_step(pipeline_id, execution_order);
CREATE INDEX idx_pipeline_step_relationship_pipeline ON tbl_pipeline_step_relationship(pipeline_id);
CREATE INDEX idx_pipeline_step_relationship_from ON tbl_pipeline_step_relationship(from_step_id);
CREATE INDEX idx_pipeline_step_relationship_to ON tbl_pipeline_step_relationship(to_step_id);
CREATE INDEX idx_pipeline_execution_pipeline_id ON tbl_pipeline_execution(pipeline_id);
CREATE INDEX idx_pipeline_execution_status ON tbl_pipeline_execution(execution_status);
CREATE INDEX idx_step_execution_execution_id ON tbl_step_execution(execution_id);
CREATE INDEX idx_step_execution_step_id ON tbl_step_execution(step_id);
CREATE INDEX idx_step_execution_status ON tbl_step_execution(step_execution_status);
