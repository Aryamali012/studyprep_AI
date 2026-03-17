-- ============================================================
--  StudyPrep AI  –  Database Schema
--  Run once before starting the server:
--    mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS studyprep
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE studyprep;

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id       VARCHAR(36)   NOT NULL,
    full_name     VARCHAR(255)  NOT NULL,
    email         VARCHAR(255)  NOT NULL,
    password_hash TEXT          NOT NULL,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Refresh tokens ────────────────────────────────────────────────────────────
-- Stores a SHA-256 hash of the token, never the raw value.
-- One row per issued token; rotated on every /refresh call.
CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id    VARCHAR(36)  NOT NULL,
    user_id     VARCHAR(36)  NOT NULL,
    token_hash  VARCHAR(64)  NOT NULL,
    expires_at  DATETIME     NOT NULL,
    revoked     TINYINT(1)   NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (token_id),
    UNIQUE KEY uq_rt_hash (token_hash),
    CONSTRAINT fk_rt_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_rt_user ON refresh_tokens (user_id);

-- ── User Notes ────────────────────────────────────────────────────────────────
-- Stores AI-generated study notes per user.
CREATE TABLE IF NOT EXISTS user_notes (
    id          INT           NOT NULL AUTO_INCREMENT,
    user_id     VARCHAR(36)   NOT NULL,
    topic       VARCHAR(500)  NOT NULL,
    content     LONGTEXT      NOT NULL,
    pdf_path    VARCHAR(500)  DEFAULT NULL,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    CONSTRAINT fk_notes_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_notes_user ON user_notes (user_id);
