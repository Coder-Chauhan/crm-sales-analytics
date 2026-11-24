-- Schema for the CRM sales analytics project (SQLite, portable to PostgreSQL)
-- Tables mirror standard Salesforce objects: User, Account, Lead, Opportunity,
-- OpportunityFieldHistory (stage changes) and Task/Event (activities).

DROP TABLE IF EXISTS activities;
DROP TABLE IF EXISTS opportunity_history;
DROP TABLE IF EXISTS opportunities;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id          TEXT PRIMARY KEY,
    rep_name         TEXT NOT NULL,
    region           TEXT NOT NULL,          -- APAC, EMEA, AMER
    team             TEXT NOT NULL,          -- Enterprise, Mid-Market
    hire_date        DATE,
    quarterly_quota  INTEGER NOT NULL
);

CREATE TABLE accounts (
    account_id     TEXT PRIMARY KEY,
    account_name   TEXT NOT NULL,
    industry       TEXT,
    employee_band  TEXT,
    region         TEXT,
    owner_id       TEXT REFERENCES users(user_id),
    created_date   DATE
);

CREATE TABLE leads (
    lead_id                   TEXT PRIMARY KEY,
    lead_source               TEXT,           -- Web, Referral, Event, Outbound, Partner
    created_date              DATE,
    status                    TEXT,           -- Open, Nurturing, Unqualified, Converted
    owner_id                  TEXT REFERENCES users(user_id),
    account_id                TEXT REFERENCES accounts(account_id),
    converted_date            DATE,
    converted_opportunity_id  TEXT
);

CREATE TABLE opportunities (
    opportunity_id     TEXT PRIMARY KEY,
    opportunity_name   TEXT,
    account_id         TEXT REFERENCES accounts(account_id),
    owner_id           TEXT REFERENCES users(user_id),
    lead_source        TEXT,
    type               TEXT,                  -- New Business, Upsell, Renewal
    amount             REAL,
    stage              TEXT,
    probability        INTEGER,
    forecast_category  TEXT,                  -- Pipeline, Best Case, Commit, Closed, Omitted
    created_date       DATE,
    close_date         DATE,
    is_closed          INTEGER,
    is_won             INTEGER,
    loss_reason        TEXT
);

CREATE TABLE opportunity_history (
    opportunity_id  TEXT REFERENCES opportunities(opportunity_id),
    stage           TEXT,
    entered_date    DATE
);

CREATE TABLE activities (
    activity_id     TEXT PRIMARY KEY,
    opportunity_id  TEXT REFERENCES opportunities(opportunity_id),
    owner_id        TEXT REFERENCES users(user_id),
    activity_type   TEXT,                     -- Call, Email, Meeting, Demo
    activity_date   DATE
);

CREATE INDEX idx_opp_owner   ON opportunities(owner_id);
CREATE INDEX idx_opp_close   ON opportunities(close_date);
CREATE INDEX idx_hist_opp    ON opportunity_history(opportunity_id);
CREATE INDEX idx_act_opp     ON activities(opportunity_id);
CREATE INDEX idx_leads_src   ON leads(lead_source);
