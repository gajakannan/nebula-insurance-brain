-- Extensions required by the brain database (BLUEPRINT 2.1; ADR-0054).
-- age's CREATE EXTENSION requires LOAD 'age' first and the ag_catalog schema
-- on search_path for graph functions used later in the feature set.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS age;
LOAD 'age';
ALTER DATABASE brain SET search_path = "$user", public, ag_catalog;
