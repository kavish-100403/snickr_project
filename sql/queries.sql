-- =========================================
-- (1) Create a new user account
-- with email, username, nickname, and password
-- =========================================
INSERT INTO Users (email, username, nickname, password)
VALUES ('riya@gmail.com', 'riya', 'Riya', 'riya123');

-- =========================================
-- (2) Create a new public channel inside a workspace
-- by a particular user, after checking authorization
--
-- Authorization rule from the project:
-- any user in a workspace can create channels,
-- so we check workspace membership.
-- =========================================
INSERT INTO Channel (workspace_id, name, channel_type, created_by)
SELECT 1, 'algebra', 'public', 3
WHERE EXISTS (
    SELECT 1
    FROM WorkspaceMembership wm
    WHERE wm.workspace_id = 1
      AND wm.user_id = 3
);


-- =========================================
-- (3) For each workspace, list all current administrators
-- =========================================
SELECT
    w.workspace_id,
    w.name AS workspace_name,
    u.user_id,
    u.username,
    u.email,
    wa.granted_at
FROM Workspace w
JOIN WorkspaceAdmin wa
    ON w.workspace_id = wa.workspace_id
JOIN Users u
    ON wa.user_id = u.user_id
ORDER BY w.workspace_id, u.username;


-- =========================================
-- (4) For each public channel in a given workspace,
-- list the number of users that were invited to join
-- the channel more than 5 days ago and have not yet joined
--
-- Example uses workspace_id = 1
-- =========================================
SELECT
    c.channel_id,
    c.name AS channel_name,
    COUNT(
        CASE
            WHEN ci.invited_at < CURRENT_TIMESTAMP - INTERVAL '5 days'
             AND cm.user_id IS NULL
            THEN 1
        END
    ) AS invited_not_joined_count
FROM Channel c
LEFT JOIN ChannelInvitation ci
    ON c.channel_id = ci.channel_id
LEFT JOIN ChannelMembership cm
    ON ci.channel_id = cm.channel_id
   AND ci.invited_user_id = cm.user_id
WHERE c.workspace_id = 1
  AND c.channel_type = 'public'
GROUP BY c.channel_id, c.name
ORDER BY c.channel_id;

-- =========================================
-- (5) For a particular channel, list all messages
-- in chronological order
--
-- Example uses channel_id = 2
-- =========================================
SELECT
    m.message_id,
    u.username AS sender_username,
    m.message_body,
    m.sent_at
FROM Message m
JOIN Users u
    ON m.sender_id = u.user_id
WHERE m.channel_id = 2
ORDER BY m.sent_at ASC, m.message_id ASC;


-- =========================================
-- (6) For a particular user, list all messages
-- they have posted in any channel
--
-- Example uses user_id = 1
-- =========================================
SELECT
    m.message_id,
    c.name AS channel_name,
    w.name AS workspace_name,
    m.message_body,
    m.sent_at
FROM Message m
JOIN Channel c
    ON m.channel_id = c.channel_id
JOIN Workspace w
    ON c.workspace_id = w.workspace_id
WHERE m.sender_id = 1
ORDER BY m.sent_at ASC, m.message_id ASC;


-- =========================================
-- (7) For a particular user, list all messages
-- accessible to this user that contain the keyword
-- 'perpendicular' in the message body.
--
-- Accessible means:
-- user must be a member of the workspace
-- and a member of the channel.
--
-- Example uses user_id = 1
-- =========================================
SELECT
    m.message_id,
    w.name AS workspace_name,
    c.name AS channel_name,
    u.username AS sender_username,
    m.message_body,
    m.sent_at
FROM Message m
JOIN Channel c
    ON m.channel_id = c.channel_id
JOIN Workspace w
    ON c.workspace_id = w.workspace_id
JOIN Users u
    ON m.sender_id = u.user_id
WHERE LOWER(m.message_body) LIKE '%perpendicular%'
  AND EXISTS (
      SELECT 1
      FROM WorkspaceMembership wm
      WHERE wm.workspace_id = w.workspace_id
        AND wm.user_id = 1
  )
  AND EXISTS (
      SELECT 1
      FROM ChannelMembership cm
      WHERE cm.channel_id = c.channel_id
        AND cm.user_id = 1
  )
ORDER BY m.sent_at ASC, m.message_id ASC;