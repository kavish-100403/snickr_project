-- ================================================================
-- snickr – Database Schema  (Project 2 revised version)
-- ================================================================
-- Changes from Part 1:
--   1. Passwords stored as Werkzeug pbkdf2:sha256 hashes (the column
--      was already VARCHAR(255), no structural change needed).
--   2. Added six performance indexes for common web-app queries.
--   3. Documented existing unique constraints used for upsert logic
--      (ON CONFLICT) when re-sending invitations.
-- ================================================================

-- ── Core tables ──────────────────────────────────────────────

CREATE TABLE Users (
    user_id    INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email      VARCHAR(255) NOT NULL UNIQUE,
    username   VARCHAR(100) NOT NULL UNIQUE,
    nickname   VARCHAR(100),
    -- Stored as a Werkzeug hash (pbkdf2:sha256:…).  Never plain text.
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Workspace (
    workspace_id INT  GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    description  TEXT,
    created_by   INT  NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_workspace_created_by
        FOREIGN KEY (created_by) REFERENCES Users(user_id)
);

CREATE TABLE WorkspaceMembership (
    workspace_id INT NOT NULL,
    user_id      INT NOT NULL,
    joined_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, user_id),
    CONSTRAINT fk_ws_membership_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id) ON DELETE CASCADE,
    CONSTRAINT fk_ws_membership_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE WorkspaceAdmin (
    workspace_id INT NOT NULL,
    user_id      INT NOT NULL,
    granted_by   INT NOT NULL,
    granted_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, user_id),
    CONSTRAINT fk_ws_admin_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id) ON DELETE CASCADE,
    CONSTRAINT fk_ws_admin_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_ws_admin_granted_by
        FOREIGN KEY (granted_by) REFERENCES Users(user_id)
);

CREATE TABLE WorkspaceInvitation (
    workspace_invite_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id        INT NOT NULL,
    invited_user_id     INT NOT NULL,
    invited_by          INT NOT NULL,
    invited_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_ws_inv_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id) ON DELETE CASCADE,
    CONSTRAINT fk_ws_inv_invited_user
        FOREIGN KEY (invited_user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_ws_inv_invited_by
        FOREIGN KEY (invited_by) REFERENCES Users(user_id),
    CONSTRAINT chk_ws_inv_status
        CHECK (status IN ('pending', 'accepted', 'declined')),
    -- Used by ON CONFLICT DO UPDATE when re-sending a declined invitation
    CONSTRAINT uq_ws_invitation
        UNIQUE (workspace_id, invited_user_id)
);

CREATE TABLE Channel (
    channel_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id INT NOT NULL,
    name         VARCHAR(150) NOT NULL,
    channel_type VARCHAR(20)  NOT NULL,
    created_by   INT NOT NULL,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_channel_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id) ON DELETE CASCADE,
    CONSTRAINT fk_channel_created_by
        FOREIGN KEY (created_by) REFERENCES Users(user_id),
    CONSTRAINT chk_channel_type
        CHECK (channel_type IN ('public', 'private', 'direct')),
    CONSTRAINT uq_channel_name_per_workspace
        UNIQUE (workspace_id, name)
);

CREATE TABLE ChannelMembership (
    channel_id INT NOT NULL,
    user_id    INT NOT NULL,
    joined_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel_id, user_id),
    CONSTRAINT fk_ch_membership_channel
        FOREIGN KEY (channel_id) REFERENCES Channel(channel_id) ON DELETE CASCADE,
    CONSTRAINT fk_ch_membership_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE ChannelInvitation (
    channel_invite_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id        INT NOT NULL,
    invited_user_id   INT NOT NULL,
    invited_by        INT NOT NULL,
    invited_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status            VARCHAR(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_ch_inv_channel
        FOREIGN KEY (channel_id) REFERENCES Channel(channel_id) ON DELETE CASCADE,
    CONSTRAINT fk_ch_inv_invited_user
        FOREIGN KEY (invited_user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_ch_inv_invited_by
        FOREIGN KEY (invited_by) REFERENCES Users(user_id),
    CONSTRAINT chk_ch_inv_status
        CHECK (status IN ('pending', 'accepted', 'declined')),
    -- Used by ON CONFLICT DO UPDATE when re-sending a declined invitation
    CONSTRAINT uq_ch_invitation
        UNIQUE (channel_id, invited_user_id)
);

CREATE TABLE Message (
    message_id   INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id   INT  NOT NULL,
    sender_id    INT  NOT NULL,
    message_body TEXT NOT NULL,
    sent_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_message_channel
        FOREIGN KEY (channel_id) REFERENCES Channel(channel_id) ON DELETE CASCADE,
    CONSTRAINT fk_message_sender
        FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE
);


-- ================================================================
-- Performance indexes  (added for Part 2 web application)
-- ================================================================

-- Fast lookup of all workspaces a user belongs to (dashboard query)
CREATE INDEX idx_wm_user_id  ON WorkspaceMembership(user_id);

-- Fast lookup of all channels a user belongs to (channel visibility)
CREATE INDEX idx_cm_user_id  ON ChannelMembership(user_id);

-- Fast message retrieval by channel in chronological order
CREATE INDEX idx_msg_channel_sent ON Message(channel_id, sent_at);

-- Fast pending-invitation queries (navbar badge + invitations page)
CREATE INDEX idx_wi_invited_user ON WorkspaceInvitation(invited_user_id, status);
CREATE INDEX idx_ci_invited_user ON ChannelInvitation(invited_user_id, status);

-- Fast channel listing per workspace
CREATE INDEX idx_channel_workspace ON Channel(workspace_id);
