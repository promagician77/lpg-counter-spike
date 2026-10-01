-- LPG cylinder counting system: transactions and audit trail.
-- Both the AI result and the cashier's final count are stored, so disputes
-- can be reviewed against the camera footage.

create table lanes (
  id          integer primary key,
  name        text not null,           -- e.g. 'Lane 1'
  camera_url  text,                    -- RTSP or USB path
  active      boolean not null default true
);

create table cylinder_sizes (
  id          integer primary key autoincrement,
  label       text not null unique,    -- '20lb', '30lb', '100lb'
  height_cm   real,                    -- reference height for size classification
  color_hint  text                     -- typical color, helps annotation
);

-- One row per transaction (a truck arrives, cylinders are counted, cashier confirms).
create table transactions (
  id              integer primary key autoincrement,
  lane_id         integer not null references lanes(id),
  started_at      text not null default (datetime('now')),
  completed_at    text,

  -- What the AI saw
  ai_total        integer not null default 0,
  ai_breakdown    text,                -- JSON: {"20lb": 12, "30lb": 4, "100lb": 2}

  -- What the cashier confirmed (may differ)
  final_total     integer,
  final_breakdown text,                -- JSON, same shape
  cashier_name    text,

  -- Metadata
  confidence_avg  real,                -- average detection confidence
  video_clip      text,                -- path to the saved clip for this transaction
  status          text not null default 'pending' check (status in ('pending','confirmed','disputed')),
  notes           text                 -- cashier can add a note on correction
);
create index idx_tx_status on transactions(status);
create index idx_tx_date on transactions(started_at);

-- Every correction the cashier makes is logged separately, so the full
-- edit history is available for audit.
create table corrections (
  id              integer primary key autoincrement,
  transaction_id  integer not null references transactions(id),
  size_label      text not null,
  ai_count        integer not null,
  corrected_count integer not null,
  reason          text,
  corrected_at    text not null default (datetime('now')),
  cashier_name    text
);

-- Seed the standard Bahamas LPG sizes.
insert into cylinder_sizes (label, height_cm, color_hint) values
  ('20lb',  46, 'blue'),
  ('30lb',  61, 'silver'),
  ('100lb', 122, 'white');

insert into lanes (id, name) values (1, 'Lane 1');
