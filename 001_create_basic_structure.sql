/***
 *    Hunspell FTS Test — basic structure
 *    Schemas + extensions + version management
 */

create schema if not exists helpers;
create schema if not exists ext;

create extension if not exists unaccent schema ext;
create extension if not exists pg_trgm schema ext;

-- ---------------------------------------------------------------------------
-- Version management (from 002_create_version_management.sql)
-- ---------------------------------------------------------------------------

set search_path = public, ext, helpers;

create table __version
(
	version_id         int generated always as identity not null primary key,
	component          text                             not null default 'main',
	version            text                             not null,
	title              text                             not null,
	description        text,
	execution_started  timestamptz                      not null default now(),
	execution_finished timestamptz
);

create unique index uq_version on __version (component, version);

create function start_version_update(_version text, _title text, _description text default null,
																		 _component text default 'main')
	returns setof __version
	language sql
as
$$

insert into __version(component, version, title, description)
VALUES (_component, _version, _title, _description)
returning *;

$$;

create function stop_version_update(_version text, _component text default 'main')
	returns setof __version
	language sql
as
$$

update __version
set execution_finished = now()
where component = _component
	and version = _version
returning *;

$$;

create function check_version(_version text, _component text default 'main')
	returns bool
	language sql
	cost 1
as
$$
select exists(select
						from __version
						where component = _component
							and version = _version);

$$;
