--
-- PostgreSQL database dump
--

\restrict qHVoRQOaw5CGKv35By6mOykdO6UT9zwnGfEXsRmi6F73HsaOhLuClQecPDPXEPE

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg12+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg12+1)

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
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: sandboxtype; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE public.sandboxtype AS ENUM (
    'E2B',
    'LOCAL'
);


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_environment_variables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_environment_variables (
    id character varying NOT NULL,
    key character varying NOT NULL,
    value character varying NOT NULL,
    description character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    agent_id character varying NOT NULL
);


--
-- Name: agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agents (
    id character varying NOT NULL,
    agent_type character varying,
    name character varying,
    description character varying,
    system character varying,
    topic character varying,
    message_ids json,
    metadata_ json,
    llm_config json,
    embedding_config json,
    tool_rules json,
    mcp_tools json,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);


--
-- Name: agents_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agents_tags (
    agent_id character varying NOT NULL,
    tag character varying NOT NULL
);


--
-- Name: block; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.block (
    template_name character varying,
    description character varying,
    label character varying NOT NULL,
    is_template boolean NOT NULL,
    value character varying NOT NULL,
    "limit" integer NOT NULL,
    metadata_ json,
    organization_id character varying,
    user_id character varying NOT NULL,
    id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying
);


--
-- Name: blocks_agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.blocks_agents (
    agent_id character varying NOT NULL,
    block_id character varying NOT NULL,
    block_label character varying NOT NULL
);


--
-- Name: cloud_file_mapping; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.cloud_file_mapping (
    id character varying NOT NULL,
    cloud_file_id character varying NOT NULL,
    local_file_id character varying NOT NULL,
    status character varying NOT NULL,
    "timestamp" character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);


--
-- Name: episodic_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.episodic_memory (
    id character varying NOT NULL,
    occurred_at timestamp without time zone NOT NULL,
    last_modify json NOT NULL,
    actor character varying NOT NULL,
    event_type character varying NOT NULL,
    summary character varying NOT NULL,
    details character varying NOT NULL,
    tree_path json NOT NULL,
    metadata_ json,
    embedding_config json,
    details_embedding public.vector(4096),
    summary_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);


--
-- Name: files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.files (
    source_id character varying,
    file_name character varying,
    file_path character varying,
    source_url character varying,
    google_cloud_url character varying,
    file_type character varying,
    file_size integer,
    file_creation_date character varying,
    file_last_modified_date character varying,
    id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);


--
-- Name: knowledge_vault; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.knowledge_vault (
    id character varying NOT NULL,
    entry_type character varying NOT NULL,
    source character varying NOT NULL,
    sensitivity character varying NOT NULL,
    secret_value character varying NOT NULL,
    caption character varying NOT NULL,
    last_modify json NOT NULL,
    metadata_ json,
    embedding_config json,
    caption_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);


--
-- Name: messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.messages (
    id character varying NOT NULL,
    role character varying NOT NULL,
    text character varying,
    content json,
    model character varying,
    name character varying,
    tool_calls json NOT NULL,
    tool_call_id character varying,
    step_id character varying,
    otid character varying,
    tool_returns json,
    group_id character varying,
    sender_id character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL,
    agent_id character varying NOT NULL
);


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    name character varying NOT NULL,
    id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying
);


--
-- Name: procedural_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.procedural_memory (
    id character varying NOT NULL,
    entry_type character varying NOT NULL,
    summary character varying NOT NULL,
    steps json NOT NULL,
    tree_path json NOT NULL,
    last_modify json NOT NULL,
    metadata_ json,
    embedding_config json,
    summary_embedding public.vector(4096),
    steps_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);


--
-- Name: providers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.providers (
    name character varying NOT NULL,
    api_key character varying,
    id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);


--
-- Name: resource_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.resource_memory (
    id character varying NOT NULL,
    title character varying NOT NULL,
    summary character varying NOT NULL,
    resource_type character varying NOT NULL,
    content character varying NOT NULL,
    tree_path json NOT NULL,
    last_modify json NOT NULL,
    metadata_ json,
    embedding_config json,
    summary_embedding public.vector(4096),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);


--
-- Name: sandbox_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sandbox_configs (
    id character varying NOT NULL,
    type public.sandboxtype NOT NULL,
    config json NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);


--
-- Name: sandbox_environment_variables; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sandbox_environment_variables (
    id character varying NOT NULL,
    key character varying NOT NULL,
    value character varying NOT NULL,
    description character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    sandbox_config_id character varying NOT NULL
);


--
-- Name: semantic_memory; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.semantic_memory (
    id character varying NOT NULL,
    name character varying NOT NULL,
    summary character varying NOT NULL,
    details character varying NOT NULL,
    source character varying NOT NULL,
    tree_path json NOT NULL,
    metadata_ json,
    last_modify json NOT NULL,
    created_at timestamp without time zone NOT NULL,
    embedding_config json,
    details_embedding public.vector(4096),
    name_embedding public.vector(4096),
    summary_embedding public.vector(4096),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying,
    user_id character varying NOT NULL
);


--
-- Name: steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.steps (
    id character varying NOT NULL,
    origin character varying,
    organization_id character varying,
    provider_id character varying,
    provider_name character varying,
    model character varying,
    context_window_limit integer,
    completion_tokens integer NOT NULL,
    prompt_tokens integer NOT NULL,
    total_tokens integer NOT NULL,
    completion_tokens_details json,
    tags json,
    tid character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying
);


--
-- Name: tools; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tools (
    name character varying NOT NULL,
    tool_type character varying NOT NULL,
    return_char_limit integer,
    description character varying,
    tags json NOT NULL,
    source_type character varying NOT NULL,
    source_code character varying,
    json_schema json,
    id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);


--
-- Name: tools_agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tools_agents (
    agent_id character varying NOT NULL,
    tool_id character varying NOT NULL
);


--
-- Name: user_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_settings (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    chat_model character varying(100),
    memory_model character varying(100),
    timezone character varying(100),
    persona character varying(100),
    persona_text text,
    ui_preferences jsonb,
    custom_settings jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted boolean DEFAULT false,
    _created_by_id character varying,
    _last_updated_by_id character varying
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    name character varying NOT NULL,
    status character varying NOT NULL,
    timezone character varying NOT NULL,
    id character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    is_deleted boolean DEFAULT false NOT NULL,
    _created_by_id character varying,
    _last_updated_by_id character varying,
    organization_id character varying
);


--
-- Name: agent_environment_variables agent_environment_variables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_environment_variables
    ADD CONSTRAINT agent_environment_variables_pkey PRIMARY KEY (id);


--
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- Name: block block_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block
    ADD CONSTRAINT block_pkey PRIMARY KEY (id);


--
-- Name: blocks_agents blocks_agents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocks_agents
    ADD CONSTRAINT blocks_agents_pkey PRIMARY KEY (agent_id, block_id, block_label);


--
-- Name: cloud_file_mapping cloud_file_mapping_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cloud_file_mapping
    ADD CONSTRAINT cloud_file_mapping_pkey PRIMARY KEY (id);


--
-- Name: episodic_memory episodic_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.episodic_memory
    ADD CONSTRAINT episodic_memory_pkey PRIMARY KEY (id);


--
-- Name: files files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_pkey PRIMARY KEY (id);


--
-- Name: knowledge_vault knowledge_vault_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_vault
    ADD CONSTRAINT knowledge_vault_pkey PRIMARY KEY (id);


--
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: procedural_memory procedural_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedural_memory
    ADD CONSTRAINT procedural_memory_pkey PRIMARY KEY (id);


--
-- Name: providers providers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.providers
    ADD CONSTRAINT providers_pkey PRIMARY KEY (id);


--
-- Name: resource_memory resource_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_memory
    ADD CONSTRAINT resource_memory_pkey PRIMARY KEY (id);


--
-- Name: sandbox_configs sandbox_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sandbox_configs
    ADD CONSTRAINT sandbox_configs_pkey PRIMARY KEY (id);


--
-- Name: sandbox_environment_variables sandbox_environment_variables_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sandbox_environment_variables
    ADD CONSTRAINT sandbox_environment_variables_pkey PRIMARY KEY (id);


--
-- Name: semantic_memory semantic_memory_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_memory
    ADD CONSTRAINT semantic_memory_pkey PRIMARY KEY (id);


--
-- Name: steps steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.steps
    ADD CONSTRAINT steps_pkey PRIMARY KEY (id);


--
-- Name: tools tools_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_pkey PRIMARY KEY (id);


--
-- Name: agent_environment_variables uix_key_agent; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_environment_variables
    ADD CONSTRAINT uix_key_agent UNIQUE (key, agent_id);


--
-- Name: sandbox_environment_variables uix_key_sandbox_config; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sandbox_environment_variables
    ADD CONSTRAINT uix_key_sandbox_config UNIQUE (key, sandbox_config_id);


--
-- Name: tools uix_name_organization; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT uix_name_organization UNIQUE (name, organization_id);


--
-- Name: sandbox_configs uix_type_organization; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sandbox_configs
    ADD CONSTRAINT uix_type_organization UNIQUE (type, organization_id);


--
-- Name: blocks_agents unique_agent_block; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocks_agents
    ADD CONSTRAINT unique_agent_block UNIQUE (agent_id, block_id);


--
-- Name: agents_tags unique_agent_tag; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents_tags
    ADD CONSTRAINT unique_agent_tag PRIMARY KEY (agent_id, tag);


--
-- Name: tools_agents unique_agent_tool; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools_agents
    ADD CONSTRAINT unique_agent_tool PRIMARY KEY (agent_id, tool_id);


--
-- Name: block unique_block_id_label; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block
    ADD CONSTRAINT unique_block_id_label UNIQUE (id, label);


--
-- Name: blocks_agents unique_label_per_agent; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocks_agents
    ADD CONSTRAINT unique_label_per_agent UNIQUE (agent_id, block_label);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_user_settings_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_settings_user_id ON public.user_settings USING btree (user_id);


--
-- Name: ix_episodic_memory_combined_fts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_episodic_memory_combined_fts ON public.episodic_memory USING gin (to_tsvector('english'::regconfig, (((COALESCE(summary, ''::character varying))::text || ' '::text) || (COALESCE(details, ''::character varying))::text)));


--
-- Name: ix_episodic_memory_details_fts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_episodic_memory_details_fts ON public.episodic_memory USING gin (to_tsvector('english'::regconfig, (details)::text)) WHERE (details IS NOT NULL);


--
-- Name: ix_episodic_memory_summary_fts; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_episodic_memory_summary_fts ON public.episodic_memory USING gin (to_tsvector('english'::regconfig, (summary)::text)) WHERE (summary IS NOT NULL);


--
-- Name: ix_messages_agent_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_agent_created_at ON public.messages USING btree (agent_id, created_at);


--
-- Name: ix_messages_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_messages_created_at ON public.messages USING btree (created_at, id);


--
-- Name: agent_environment_variables agent_environment_variables_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_environment_variables
    ADD CONSTRAINT agent_environment_variables_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE CASCADE;


--
-- Name: agent_environment_variables agent_environment_variables_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_environment_variables
    ADD CONSTRAINT agent_environment_variables_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: agents agents_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: agents_tags agents_tags_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agents_tags
    ADD CONSTRAINT agents_tags_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id);


--
-- Name: block block_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block
    ADD CONSTRAINT block_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: block block_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.block
    ADD CONSTRAINT block_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: blocks_agents blocks_agents_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocks_agents
    ADD CONSTRAINT blocks_agents_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id);


--
-- Name: cloud_file_mapping cloud_file_mapping_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.cloud_file_mapping
    ADD CONSTRAINT cloud_file_mapping_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: episodic_memory episodic_memory_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.episodic_memory
    ADD CONSTRAINT episodic_memory_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: episodic_memory episodic_memory_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.episodic_memory
    ADD CONSTRAINT episodic_memory_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: files files_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.files
    ADD CONSTRAINT files_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: blocks_agents fk_block_id_label; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.blocks_agents
    ADD CONSTRAINT fk_block_id_label FOREIGN KEY (block_id, block_label) REFERENCES public.block(id, label) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: knowledge_vault knowledge_vault_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_vault
    ADD CONSTRAINT knowledge_vault_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: knowledge_vault knowledge_vault_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.knowledge_vault
    ADD CONSTRAINT knowledge_vault_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: messages messages_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE CASCADE;


--
-- Name: messages messages_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: messages messages_step_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_step_id_fkey FOREIGN KEY (step_id) REFERENCES public.steps(id) ON DELETE SET NULL;


--
-- Name: messages messages_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: procedural_memory procedural_memory_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedural_memory
    ADD CONSTRAINT procedural_memory_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: procedural_memory procedural_memory_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.procedural_memory
    ADD CONSTRAINT procedural_memory_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: providers providers_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.providers
    ADD CONSTRAINT providers_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: resource_memory resource_memory_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_memory
    ADD CONSTRAINT resource_memory_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: resource_memory resource_memory_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.resource_memory
    ADD CONSTRAINT resource_memory_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: sandbox_configs sandbox_configs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sandbox_configs
    ADD CONSTRAINT sandbox_configs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: sandbox_environment_variables sandbox_environment_variables_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sandbox_environment_variables
    ADD CONSTRAINT sandbox_environment_variables_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: sandbox_environment_variables sandbox_environment_variables_sandbox_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sandbox_environment_variables
    ADD CONSTRAINT sandbox_environment_variables_sandbox_config_id_fkey FOREIGN KEY (sandbox_config_id) REFERENCES public.sandbox_configs(id);


--
-- Name: semantic_memory semantic_memory_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_memory
    ADD CONSTRAINT semantic_memory_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: semantic_memory semantic_memory_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.semantic_memory
    ADD CONSTRAINT semantic_memory_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: steps steps_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.steps
    ADD CONSTRAINT steps_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id) ON DELETE RESTRICT;


--
-- Name: steps steps_provider_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.steps
    ADD CONSTRAINT steps_provider_id_fkey FOREIGN KEY (provider_id) REFERENCES public.providers(id) ON DELETE RESTRICT;


--
-- Name: tools_agents tools_agents_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools_agents
    ADD CONSTRAINT tools_agents_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE CASCADE;


--
-- Name: tools_agents tools_agents_tool_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools_agents
    ADD CONSTRAINT tools_agents_tool_id_fkey FOREIGN KEY (tool_id) REFERENCES public.tools(id) ON DELETE CASCADE;


--
-- Name: tools tools_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: users users_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- PostgreSQL database dump complete
--

\unrestrict qHVoRQOaw5CGKv35By6mOykdO6UT9zwnGfEXsRmi6F73HsaOhLuClQecPDPXEPE

