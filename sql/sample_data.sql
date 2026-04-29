INSERT INTO Users (email, username, nickname, password) VALUES
('kavish@gmail.com', 'kavish', 'Kavish', 'kavish578'),
('dev@yahoo.com', 'dev', 'Dev', 'dev1907'),
('pooja@gmail.com', 'pooja', 'Pooja', 'pooja1902'),
('david@hotmail.com', 'david', 'Dave', 'david123'),
('yash@gmail.com', 'yash', 'Yashu', 'yash9988'),
('vansh@gmail.com', 'vansh', 'Vansh', 'vansh2606');

INSERT INTO Workspace (name, description, created_by, created_at) VALUES
('Math Club', 'Workspace for math discussions and planning', 1, '2026-04-01 09:00:00'),
('Startup Team', 'Workspace for startup collaboration', 4, '2026-04-02 10:00:00');

INSERT INTO WorkspaceMembership (workspace_id, user_id, joined_at) VALUES
(1, 1, '2026-04-01 09:05:00'),
(1, 2, '2026-04-01 09:10:00'),
(1, 3, '2026-04-02 11:00:00'),
(1, 5, '2026-04-03 12:00:00'),
(2, 4, '2026-04-02 10:05:00'),
(2, 5, '2026-04-02 10:10:00'),
(2, 6, '2026-04-03 14:00:00');

INSERT INTO WorkspaceAdmin (workspace_id, user_id, granted_by, granted_at) VALUES
(1, 1, 1, '2026-04-01 09:06:00'),
(1, 2, 1, '2026-04-02 09:00:00'),
(2, 4, 4, '2026-04-02 10:06:00');

INSERT INTO WorkspaceInvitation (workspace_id, invited_user_id, invited_by, invited_at, status) VALUES
(1, 6, 1, '2026-04-05 10:00:00', 'pending'),
(2, 2, 4, '2026-04-06 11:00:00', 'pending'),
(2, 3, 4, '2026-04-07 12:00:00', 'declined');

INSERT INTO Channel (workspace_id, name, channel_type, created_by, created_at) VALUES
(1, 'general', 'public', 1, '2026-04-01 10:00:00'),
(1, 'geometry', 'public', 2, '2026-04-02 10:30:00'),
(1, 'committee', 'private', 1, '2026-04-03 15:00:00'),
(1, 'kavish-dev', 'direct', 1, '2026-04-03 16:00:00'),
(2, 'announcements', 'public', 4, '2026-04-02 11:00:00'),
(2, 'founders', 'private', 4, '2026-04-03 11:30:00');

INSERT INTO ChannelMembership (channel_id, user_id, joined_at) VALUES
-- Math Club: general
(1, 1, '2026-04-01 10:05:00'),
(1, 2, '2026-04-01 10:06:00'),
(1, 3, '2026-04-02 11:05:00'),

-- Math Club: geometry
(2, 1, '2026-04-02 10:35:00'),
(2, 2, '2026-04-02 10:36:00'),
(2, 5, '2026-04-04 13:00:00'),

-- Math Club: committee
(3, 1, '2026-04-03 15:05:00'),
(3, 2, '2026-04-03 15:06:00'),

-- Math Club: direct kavish-dev
(4, 1, '2026-04-03 16:01:00'),
(4, 2, '2026-04-03 16:01:30'),

-- Startup Team: announcements
(5, 4, '2026-04-02 11:05:00'),
(5, 5, '2026-04-02 11:06:00'),

-- Startup Team: founders
(6, 4, '2026-04-03 11:35:00'),
(6, 6, '2026-04-03 11:36:00');

INSERT INTO ChannelInvitation (channel_id, invited_user_id, invited_by, invited_at, status) VALUES
-- For query 4: invited more than 5 days ago and not joined
(1, 5, 1, '2026-04-10 09:00:00', 'pending'),
(1, 6, 1, '2026-04-10 09:30:00', 'pending'),

-- invited and joined later
(1, 3, 1, '2026-04-01 12:00:00', 'accepted'),

-- geometry channel invites
(2, 3, 2, '2026-04-08 14:00:00', 'pending'),
(2, 5, 2, '2026-04-03 12:00:00', 'accepted'),

-- private channel invites
(3, 2, 1, '2026-04-03 14:30:00', 'accepted'),
(3, 3, 1, '2026-04-03 14:45:00', 'pending'),

-- startup public channel
(5, 6, 4, '2026-04-09 10:00:00', 'pending'),

-- startup private channel
(6, 6, 4, '2026-04-03 11:00:00', 'accepted');

INSERT INTO Message (channel_id, sender_id, message_body, sent_at) VALUES
(1, 1, 'Welcome everyone to the Math Club general channel.', '2026-04-01 10:10:00'),
(1, 2, 'Glad to be here.', '2026-04-01 10:12:00'),
(1, 3, 'Can someone explain perpendicular bisectors?', '2026-04-02 11:10:00'),

(2, 1, 'Today we will discuss perpendicular lines in geometry.', '2026-04-02 10:40:00'),
(2, 2, 'Two lines are perpendicular if they meet at 90 degrees.', '2026-04-02 10:45:00'),
(2, 5, 'I will share more examples tomorrow.', '2026-04-04 13:10:00'),

(3, 1, 'Committee meeting starts at 5 PM.', '2026-04-03 15:10:00'),
(3, 2, 'Noted, I will join on time.', '2026-04-03 15:12:00'),

(4, 1, 'Hi Dev, are you free for a quick chat?', '2026-04-03 16:05:00'),
(4, 2, 'Yes, give me 10 minutes.', '2026-04-03 16:06:00'),

(5, 4, 'Welcome to the Startup Team announcements channel.', '2026-04-02 11:10:00'),
(5, 5, 'Looking forward to the launch updates.', '2026-04-02 11:12:00'),

(6, 4, 'Founders meeting tomorrow morning.', '2026-04-03 11:40:00'),
(6, 6, 'Understood. I will prepare the deck.', '2026-04-03 11:45:00');