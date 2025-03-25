CREATE EXTENSION "uuid-ossp";
CREATE EXTENSION "pg_trgm";



-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema
CREATE SCHEMA IF NOT EXISTS rag;

-- Tabla para los cursos
CREATE TABLE rag.courses (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,

    metadata JSONB DEFAULT '{}'::jsonb, -- maybe store tags, or topics, etc
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para las lecciones
CREATE TABLE rag.lessons (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    title VARCHAR(255) NOT NULL,
    video_url VARCHAR(255),

    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    course_id INTEGER REFERENCES rag.courses(id),
    UNIQUE(course_id, title)
);

-- Tabla para las transcripciones raw (como respaldo y referencia)
CREATE TABLE rag.raw_transcriptions (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content TEXT NOT NULL,

    metadata JSONB DEFAULT '{}'::jsonb,  -- puede incluir info del modelo ASR usado, configuración, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    lesson_id INTEGER REFERENCES rag.lessons(id)
);

-- Tabla para los chunks procesados
CREATE TABLE rag.chunks (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content TEXT NOT NULL,
    start_time INTEGER NOT NULL, -- tiempo de inicio en segundos
    end_time INTEGER NOT NULL,   -- tiempo final en segundos
    embedding vector(384),       -- ajusta según tu modelo
    
    metadata JSONB DEFAULT '{}'::jsonb,     -- puede incluir speaker, topic, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    lesson_id INTEGER REFERENCES rag.lessons(id),
    transcription_id INTEGER REFERENCES rag.raw_transcriptions(id),

    CHECK (start_time < end_time)
);


-- Índices
CREATE INDEX idx_courses_code ON rag.courses(code);
CREATE INDEX idx_lessons_course ON rag.lessons(course_id);
CREATE INDEX idx_chunks_lesson ON rag.chunks(lesson_id);

CREATE INDEX idx_chunks_embedding ON rag.chunks 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX idx_chunks_metadata ON rag.chunks USING gin (metadata);
CREATE INDEX idx_lessons_metadata ON rag.lessons USING gin (metadata);