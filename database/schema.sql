-- Generated from the Alembic migrations with:
--   docker compose exec -T db pg_dump -U avizum -d avizum --schema-only --no-owner --no-privileges
-- Alembic (backend/migrations) is the source of truth; regenerate this file after each migration.
-- Head at generation time: 20261010_06

--
-- PostgreSQL database dump
--


-- Dumped from database version 16.15 (Debian 16.15-1.pgdg12+2)
-- Dumped by pg_dump version 16.15 (Debian 16.15-1.pgdg12+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: unaccent; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;


--
-- Name: EXTENSION unaccent; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: agent_authorization_type; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.agent_authorization_type AS ENUM (
    'via_publica',
    'sistemas_tecnologicos'
);


--
-- Name: message_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.message_role AS ENUM (
    'user',
    'assistant'
);


--
-- Name: message_status; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.message_status AS ENUM (
    'complete',
    'error',
    'cancelled'
);


--
-- Name: user_role; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.user_role AS ENUM (
    'user',
    'admin'
);


--
-- Name: immutable_unaccent(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.immutable_unaccent(text) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
    AS $_$ SELECT public.unaccent('public.unaccent', $1) $_$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_lookups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_lookups (
    id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    user_id integer,
    agent_id integer
);


--
-- Name: agent_lookups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.agent_lookups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: agent_lookups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.agent_lookups_id_seq OWNED BY public.agent_lookups.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: authorized_agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.authorized_agents (
    id integer NOT NULL,
    plate character varying(50) NOT NULL,
    full_name character varying(255) NOT NULL,
    name_search character varying(255) NOT NULL,
    authorization_type public.agent_authorization_type NOT NULL,
    corporation character varying(100),
    alcaldias character varying(100)[],
    source_id integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: authorized_agents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.authorized_agents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: authorized_agents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.authorized_agents_id_seq OWNED BY public.authorized_agents.id;


--
-- Name: conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversations (
    id integer NOT NULL,
    user_id integer NOT NULL,
    title character varying(80),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conversations_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.conversations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: conversations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.conversations_id_seq OWNED BY public.conversations.id;


--
-- Name: legal_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.legal_chunks (
    id integer NOT NULL,
    source_id integer NOT NULL,
    article character varying(50) NOT NULL,
    fraction character varying(50),
    heading_path text NOT NULL,
    text text NOT NULL,
    page_start integer NOT NULL,
    page_end integer NOT NULL,
    token_count integer NOT NULL,
    embedding public.vector(1536) NOT NULL,
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('spanish'::regconfig, public.immutable_unaccent(((heading_path || ' '::text) || text)))) STORED NOT NULL
);


--
-- Name: legal_chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.legal_chunks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: legal_chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.legal_chunks_id_seq OWNED BY public.legal_chunks.id;


--
-- Name: message_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.message_feedback (
    id integer NOT NULL,
    message_id integer NOT NULL,
    user_id integer NOT NULL,
    value smallint NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_message_feedback_value CHECK ((value = ANY (ARRAY['-1'::integer, 1])))
);


--
-- Name: message_feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.message_feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: message_feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.message_feedback_id_seq OWNED BY public.message_feedback.id;


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    conversation_id integer NOT NULL,
    role public.message_role NOT NULL,
    content text NOT NULL,
    status public.message_status DEFAULT 'complete'::public.message_status NOT NULL,
    citations jsonb,
    tool_calls jsonb,
    model character varying(50),
    input_tokens integer,
    output_tokens integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- Name: official_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.official_sources (
    id integer NOT NULL,
    slug character varying(100) NOT NULL,
    title character varying(300) NOT NULL,
    kind character varying(20) NOT NULL,
    url character varying(1000) NOT NULL,
    sha256 character varying(64) NOT NULL,
    last_reform_date date,
    retrieved_at timestamp with time zone DEFAULT now() NOT NULL,
    is_current boolean DEFAULT true NOT NULL
);


--
-- Name: official_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.official_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: official_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.official_sources_id_seq OWNED BY public.official_sources.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role public.user_role DEFAULT 'user'::public.user_role NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: agent_lookups id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_lookups ALTER COLUMN id SET DEFAULT nextval('public.agent_lookups_id_seq'::regclass);


--
-- Name: authorized_agents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authorized_agents ALTER COLUMN id SET DEFAULT nextval('public.authorized_agents_id_seq'::regclass);


--
-- Name: conversations id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations ALTER COLUMN id SET DEFAULT nextval('public.conversations_id_seq'::regclass);


--
-- Name: legal_chunks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.legal_chunks ALTER COLUMN id SET DEFAULT nextval('public.legal_chunks_id_seq'::regclass);


--
-- Name: message_feedback id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_feedback ALTER COLUMN id SET DEFAULT nextval('public.message_feedback_id_seq'::regclass);


--
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- Name: official_sources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.official_sources ALTER COLUMN id SET DEFAULT nextval('public.official_sources_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: agent_lookups agent_lookups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_lookups
    ADD CONSTRAINT agent_lookups_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: authorized_agents authorized_agents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authorized_agents
    ADD CONSTRAINT authorized_agents_pkey PRIMARY KEY (id);


--
-- Name: conversations conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_pkey PRIMARY KEY (id);


--
-- Name: legal_chunks legal_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.legal_chunks
    ADD CONSTRAINT legal_chunks_pkey PRIMARY KEY (id);


--
-- Name: message_feedback message_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_feedback
    ADD CONSTRAINT message_feedback_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: official_sources official_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.official_sources
    ADD CONSTRAINT official_sources_pkey PRIMARY KEY (id);


--
-- Name: authorized_agents uq_authorized_agents_plate_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authorized_agents
    ADD CONSTRAINT uq_authorized_agents_plate_type UNIQUE (plate, authorization_type);


--
-- Name: message_feedback uq_message_feedback_message_user; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_feedback
    ADD CONSTRAINT uq_message_feedback_message_user UNIQUE (message_id, user_id);


--
-- Name: official_sources uq_official_sources_slug_sha256; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.official_sources
    ADD CONSTRAINT uq_official_sources_slug_sha256 UNIQUE (slug, sha256);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_agent_lookups_agent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agent_lookups_agent_id ON public.agent_lookups USING btree (agent_id);


--
-- Name: ix_agent_lookups_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_agent_lookups_user_id ON public.agent_lookups USING btree (user_id);


--
-- Name: ix_authorized_agents_name_search_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_authorized_agents_name_search_trgm ON public.authorized_agents USING gin (name_search public.gin_trgm_ops);


--
-- Name: ix_authorized_agents_plate; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_authorized_agents_plate ON public.authorized_agents USING btree (plate);


--
-- Name: ix_authorized_agents_source_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_authorized_agents_source_id ON public.authorized_agents USING btree (source_id);


--
-- Name: ix_conversations_user_updated; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversations_user_updated ON public.conversations USING btree (user_id, updated_at);


--
-- Name: ix_legal_chunks_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_legal_chunks_embedding_hnsw ON public.legal_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_legal_chunks_source_article; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_legal_chunks_source_article ON public.legal_chunks USING btree (source_id, article);


--
-- Name: ix_legal_chunks_tsv; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_legal_chunks_tsv ON public.legal_chunks USING gin (tsv);


--
-- Name: ix_messages_conversation_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_conversation_created ON public.messages USING btree (conversation_id, created_at, id);


--
-- Name: ix_official_sources_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_official_sources_slug ON public.official_sources USING btree (slug);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: uq_official_sources_current_slug; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_official_sources_current_slug ON public.official_sources USING btree (slug) WHERE is_current;


--
-- Name: agent_lookups agent_lookups_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_lookups
    ADD CONSTRAINT agent_lookups_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.authorized_agents(id) ON DELETE SET NULL;


--
-- Name: agent_lookups agent_lookups_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_lookups
    ADD CONSTRAINT agent_lookups_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: authorized_agents authorized_agents_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.authorized_agents
    ADD CONSTRAINT authorized_agents_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.official_sources(id);


--
-- Name: conversations conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversations
    ADD CONSTRAINT conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: legal_chunks legal_chunks_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.legal_chunks
    ADD CONSTRAINT legal_chunks_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.official_sources(id) ON DELETE CASCADE;


--
-- Name: message_feedback message_feedback_message_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_feedback
    ADD CONSTRAINT message_feedback_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages(id) ON DELETE CASCADE;


--
-- Name: message_feedback message_feedback_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.message_feedback
    ADD CONSTRAINT message_feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: messages messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.conversations(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--


