CREATE TABLE Users (
    user_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    nickname VARCHAR(100),
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Workspace (
    workspace_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_workspace_created_by
        FOREIGN KEY (created_by) REFERENCES Users(user_id)
);

CREATE TABLE WorkspaceMembership (
    workspace_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, user_id),
    CONSTRAINT fk_ws_membership_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ws_membership_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE WorkspaceAdmin (
    workspace_id INT NOT NULL,
    user_id INT NOT NULL,
    granted_by INT NOT NULL,
    granted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (workspace_id, user_id),
    CONSTRAINT fk_ws_admin_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ws_admin_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ws_admin_granted_by
        FOREIGN KEY (granted_by) REFERENCES Users(user_id)
);

CREATE TABLE WorkspaceInvitation (
    workspace_invite_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id INT NOT NULL,
    invited_user_id INT NOT NULL,
    invited_by INT NOT NULL,
    invited_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_ws_inv_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ws_inv_invited_user
        FOREIGN KEY (invited_user_id) REFERENCES Users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ws_inv_invited_by
        FOREIGN KEY (invited_by) REFERENCES Users(user_id),
    CONSTRAINT chk_ws_inv_status
        CHECK (status IN ('pending', 'accepted', 'declined'))
);

CREATE TABLE Channel (
    channel_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    workspace_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    created_by INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_channel_workspace
        FOREIGN KEY (workspace_id) REFERENCES Workspace(workspace_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_channel_created_by
        FOREIGN KEY (created_by) REFERENCES Users(user_id),
    CONSTRAINT chk_channel_type
        CHECK (channel_type IN ('public', 'private', 'direct')),
    CONSTRAINT uq_channel_name_per_workspace
        UNIQUE (workspace_id, name)
);

CREATE TABLE ChannelMembership (
    channel_id INT NOT NULL,
    user_id INT NOT NULL,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (channel_id, user_id),
    CONSTRAINT fk_ch_membership_channel
        FOREIGN KEY (channel_id) REFERENCES Channel(channel_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ch_membership_user
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE ChannelInvitation (
    channel_invite_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id INT NOT NULL,
    invited_user_id INT NOT NULL,
    invited_by INT NOT NULL,
    invited_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    CONSTRAINT fk_ch_inv_channel
        FOREIGN KEY (channel_id) REFERENCES Channel(channel_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ch_inv_invited_user
        FOREIGN KEY (invited_user_id) REFERENCES Users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ch_inv_invited_by
        FOREIGN KEY (invited_by) REFERENCES Users(user_id),
    CONSTRAINT chk_ch_inv_status
        CHECK (status IN ('pending', 'accepted', 'declined'))
);

CREATE TABLE Message (
    message_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_id INT NOT NULL,
    sender_id INT NOT NULL,
    message_body TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_message_channel
        FOREIGN KEY (channel_id) REFERENCES Channel(channel_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_message_sender
        FOREIGN KEY (sender_id) REFERENCES Users(user_id)
        ON DELETE CASCADE
);


ALTER TABLE WorkspaceInvitation
ADD CONSTRAINT uq_ws_invitation UNIQUE (workspace_id, invited_user_id);

ALTER TABLE ChannelInvitation
ADD CONSTRAINT uq_ch_invitation UNIQUE (channel_id, invited_user_id);