-- Placar do pato (D1). Aplicar: npx wrangler d1 execute pato-placar --remote --file=schema.sql
CREATE TABLE IF NOT EXISTS corridas (
  id         INTEGER PRIMARY KEY,
  token_id   TEXT    NOT NULL UNIQUE,   -- cada token de corrida só entra uma vez
  nivel      TEXT    NOT NULL,
  nome       TEXT    NOT NULL,
  tempo      REAL    NOT NULL,          -- segundos
  pontos     INTEGER NOT NULL,          -- recalculado no servidor
  abates     INTEGER NOT NULL,
  pts_abates INTEGER NOT NULL,
  dano       INTEGER NOT NULL,
  mortes     INTEGER NOT NULL,
  idas_hub   INTEGER NOT NULL,
  upgrades   TEXT    NOT NULL,          -- JSON com os níveis de upgrade (a build)
  ip         TEXT    NOT NULL,          -- hash do IP (só para limitar envios)
  criado     INTEGER NOT NULL           -- ms desde 1970
);
CREATE INDEX IF NOT EXISTS corridas_tempo  ON corridas (nivel, tempo);
CREATE INDEX IF NOT EXISTS corridas_pontos ON corridas (nivel, pontos);
CREATE INDEX IF NOT EXISTS corridas_ip     ON corridas (ip, criado);
