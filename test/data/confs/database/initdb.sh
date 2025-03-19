psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" < "${DB_SCHEMA}"
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<EOF
INSERT INTO users (id, name, status, usertype) VALUES (1, 'kojiadmin', 0, 0);
INSERT INTO user_perms (user_id, perm_id, creator_id) VALUES (1, 1, 1);

INSERT INTO users (id, name, status, usertype) VALUES (2, 'kojibuilder', 0, 1);
INSERT INTO user_perms (user_id, perm_id, creator_id) VALUES (2, 9, 1);
INSERT INTO host (id, user_id, name) VALUES (1, 2, 'kojibuilder');
INSERT INTO host_config (host_id, arches, capacity, enabled, active, creator_id) VALUES (1, '$(uname -m)', 2.0, TRUE, TRUE, 1);
INSERT INTO host_channels (host_id, channel_id, creator_id) VALUES (1, 1, 1);
INSERT INTO host_channels (host_id, channel_id, creator_id) VALUES (1, 2, 1);

INSERT INTO users (id, name, status, usertype) VALUES (3, 'kojira', 0, 1);
INSERT INTO user_perms (user_id, perm_id, creator_id) VALUES (3, 10, 1);
EOF
