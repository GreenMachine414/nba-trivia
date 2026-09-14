DROP TABLE IF EXISTS season_stats;
DROP TABLE IF EXISTS draft_history;
DROP TABLE IF EXISTS rosters;
DROP TABLE IF EXISTS coaches;
DROP TABLE IF EXISTS awards;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS players;

CREATE TABLE IF NOT EXISTS teams (
    team_id       BIGINT PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    abbreviation  VARCHAR(10) NOT NULL,
    city          VARCHAR(50),
    state         VARCHAR(50),
    year_founded  INT
);

CREATE TABLE IF NOT EXISTS players (
    player_id     BIGINT PRIMARY KEY,
    player_name   VARCHAR(100) NOT NULL,
    from_year     INT,
    to_year       INT,
    is_active     BOOLEAN
);

CREATE TABLE IF NOT EXISTS season_stats (
    player_id          BIGINT REFERENCES players(player_id),
    team_id            BIGINT REFERENCES teams(team_id),
    season             VARCHAR(10),
    season_start_year  INTEGER,
    age                FLOAT,
    games_played       INT,
    minutes            FLOAT,
    fgm                FLOAT,
    fga                FLOAT,
    fg_pct             FLOAT,
    fg3m               FLOAT,
    fg3a               FLOAT,
    fg3_pct            FLOAT,
    ftm                FLOAT,
    fta                FLOAT,
    ft_pct             FLOAT,
    pts                FLOAT,
    oreb               FLOAT,
    dreb               FLOAT,
    reb                FLOAT,
    ast                FLOAT,
    tov                FLOAT,
    stl                FLOAT,
    blk                FLOAT
);

CREATE INDEX IF NOT EXISTS idx_season_stats_start_year ON season_stats (season_start_year);
CREATE INDEX IF NOT EXISTS idx_season_stats_player_id ON season_stats (player_id);

CREATE TABLE IF NOT EXISTS draft_history (
    player_id         BIGINT REFERENCES players(player_id),
    season            VARCHAR(10),
    round_number      INT,
    round_pick        INT,
    overall_pick      INT,
    team_id           BIGINT REFERENCES teams(team_id),
    organization      VARCHAR(100),
    organization_type VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS rosters (
    team_id            BIGINT REFERENCES teams(team_id),
    season             VARCHAR(10),
    season_start_year  INTEGER,
    player_id          BIGINT REFERENCES players(player_id),
    jersey_number      VARCHAR(10),
    position           VARCHAR(10),
    height             VARCHAR(10),
    weight             VARCHAR(10),
    age                FLOAT
);

CREATE INDEX IF NOT EXISTS idx_rosters_start_year ON rosters (season_start_year);
CREATE INDEX IF NOT EXISTS idx_rosters_player_id ON rosters (player_id);

CREATE TABLE IF NOT EXISTS coaches (
    team_id           BIGINT REFERENCES teams(team_id),
    season            VARCHAR(10),
    coach_id          BIGINT,
    coach_name        VARCHAR(100),
    coach_type        VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS awards (
    player_id         BIGINT REFERENCES players(player_id),
    season            VARCHAR(10),
    description       VARCHAR(255)
);