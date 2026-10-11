--
-- PostgreSQL database dump
--

\restrict WhmfzShecoqsR7eT073YMVscPoV8QWa23qQEVPu4UGDZTEWTBnGdoJQcgk8RIbr

-- Dumped from database version 18.4
-- Dumped by pg_dump version 18.4

-- Started on 2026-09-25 00:19:19

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 3 (class 3079 OID 17818)
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- TOC entry 5307 (class 0 OID 0)
-- Dependencies: 3
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- TOC entry 2 (class 3079 OID 17124)
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- TOC entry 5308 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 231 (class 1259 OID 17656)
-- Name: app_users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.app_users (
    id bigint NOT NULL,
    username character varying(50) NOT NULL,
    password_hash text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.app_users OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 17655)
-- Name: app_users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.app_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.app_users_id_seq OWNER TO postgres;

--
-- TOC entry 5309 (class 0 OID 0)
-- Dependencies: 230
-- Name: app_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.app_users_id_seq OWNED BY public.app_users.id;


--
-- TOC entry 229 (class 1259 OID 17540)
-- Name: chat_documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_documents (
    chat_id bigint NOT NULL,
    document_id bigint NOT NULL
);


ALTER TABLE public.chat_documents OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 17508)
-- Name: chats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chats (
    id bigint NOT NULL,
    title character varying(255) DEFAULT 'New Chat'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id bigint NOT NULL
);


ALTER TABLE public.chats OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 17507)
-- Name: chats_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chats_id_seq OWNER TO postgres;

--
-- TOC entry 5310 (class 0 OID 0)
-- Dependencies: 225
-- Name: chats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chats_id_seq OWNED BY public.chats.id;


--
-- TOC entry 222 (class 1259 OID 17453)
-- Name: document_chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.document_chunks (
    id bigint NOT NULL,
    source character varying(255) NOT NULL,
    page_number integer,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    embedding public.vector(384) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    document_id bigint NOT NULL
);


ALTER TABLE public.document_chunks OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 17452)
-- Name: document_chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.document_chunks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.document_chunks_id_seq OWNER TO postgres;

--
-- TOC entry 5311 (class 0 OID 0)
-- Dependencies: 221
-- Name: document_chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.document_chunks_id_seq OWNED BY public.document_chunks.id;


--
-- TOC entry 224 (class 1259 OID 17479)
-- Name: documents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.documents (
    id bigint NOT NULL,
    filename character varying(255) NOT NULL,
    stored_filename character varying(255) NOT NULL,
    file_type character varying(20) NOT NULL,
    file_size_bytes bigint DEFAULT 0,
    status character varying(20) DEFAULT 'processing'::character varying NOT NULL,
    chunk_count integer DEFAULT 0 NOT NULL,
    error_message text,
    uploaded_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    user_id bigint NOT NULL,
    CONSTRAINT valid_document_status CHECK (((status)::text = ANY ((ARRAY['processing'::character varying, 'ready'::character varying, 'failed'::character varying])::text[])))
);


ALTER TABLE public.documents OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 17478)
-- Name: documents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.documents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.documents_id_seq OWNER TO postgres;

--
-- TOC entry 5312 (class 0 OID 0)
-- Dependencies: 223
-- Name: documents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.documents_id_seq OWNED BY public.documents.id;


--
-- TOC entry 228 (class 1259 OID 17520)
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    id bigint NOT NULL,
    chat_id bigint NOT NULL,
    role character varying(20) NOT NULL,
    content text NOT NULL,
    sources jsonb DEFAULT '[]'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_message_role CHECK (((role)::text = ANY ((ARRAY['user'::character varying, 'assistant'::character varying])::text[])))
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 17519)
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.messages_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_id_seq OWNER TO postgres;

--
-- TOC entry 5313 (class 0 OID 0)
-- Dependencies: 227
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


--
-- TOC entry 235 (class 1259 OID 17779)
-- Name: retrieval_run_chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.retrieval_run_chunks (
    id bigint NOT NULL,
    retrieval_run_id bigint NOT NULL,
    chunk_id bigint NOT NULL,
    context_position integer NOT NULL,
    retrieval_type character varying(20) NOT NULL,
    similarity_score double precision,
    keyword_score double precision,
    hybrid_score double precision,
    reranker_score double precision,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT retrieval_context_position_check CHECK ((context_position > 0)),
    CONSTRAINT retrieval_type_check CHECK (((retrieval_type)::text = ANY ((ARRAY['vector'::character varying, 'keyword'::character varying, 'hybrid'::character varying, 'neighbour'::character varying])::text[])))
);


ALTER TABLE public.retrieval_run_chunks OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 17732)
-- Name: retrieval_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.retrieval_runs (
    id bigint NOT NULL,
    chat_id bigint NOT NULL,
    user_message_id bigint NOT NULL,
    assistant_message_id bigint NOT NULL,
    request_type character varying(20) DEFAULT 'answer'::character varying NOT NULL,
    retrieval_query text NOT NULL,
    vector_candidate_count integer DEFAULT 0 NOT NULL,
    keyword_candidate_count integer DEFAULT 0 NOT NULL,
    combined_candidate_count integer DEFAULT 0 NOT NULL,
    seed_count integer DEFAULT 0 NOT NULL,
    context_count integer DEFAULT 0 NOT NULL,
    highest_similarity double precision,
    minimum_similarity double precision,
    claude_called boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT retrieval_runs_counts_check CHECK (((vector_candidate_count >= 0) AND (keyword_candidate_count >= 0) AND (combined_candidate_count >= 0) AND (seed_count >= 0) AND (context_count >= 0))),
    CONSTRAINT retrieval_runs_request_type_check CHECK (((request_type)::text = ANY ((ARRAY['answer'::character varying, 'regenerate'::character varying])::text[])))
);


ALTER TABLE public.retrieval_runs OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 17812)
-- Name: retrieval_details; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.retrieval_details AS
 SELECT users.id AS user_id,
    users.username,
    chats.id AS chat_id,
    chats.title AS chat_title,
    runs.id AS retrieval_run_id,
    runs.request_type,
    runs.created_at AS retrieved_at,
    runs.user_message_id,
    question_message.content AS question,
    runs.assistant_message_id,
    answer_message.content AS answer,
    runs.retrieval_query,
    runs.vector_candidate_count,
    runs.keyword_candidate_count,
    runs.combined_candidate_count,
    runs.seed_count,
    runs.context_count,
    count(run_chunks.id) OVER (PARTITION BY runs.id) AS stored_chunk_count,
    runs.highest_similarity,
    runs.minimum_similarity,
    runs.claude_called,
    run_chunks.context_position,
    run_chunks.retrieval_type,
    run_chunks.similarity_score,
    run_chunks.keyword_score,
    run_chunks.hybrid_score,
    run_chunks.reranker_score,
    documents.id AS document_id,
    documents.filename,
    chunks.id AS chunk_id,
    chunks.page_number,
    chunks.chunk_index,
    chunks.content AS chunk_content
   FROM (((((((public.retrieval_runs runs
     JOIN public.chats ON ((chats.id = runs.chat_id)))
     JOIN public.app_users users ON ((users.id = chats.user_id)))
     JOIN public.messages question_message ON ((question_message.id = runs.user_message_id)))
     JOIN public.messages answer_message ON ((answer_message.id = runs.assistant_message_id)))
     LEFT JOIN public.retrieval_run_chunks run_chunks ON ((run_chunks.retrieval_run_id = runs.id)))
     LEFT JOIN public.document_chunks chunks ON ((chunks.id = run_chunks.chunk_id)))
     LEFT JOIN public.documents ON ((documents.id = chunks.document_id)));


ALTER VIEW public.retrieval_details OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 17778)
-- Name: retrieval_run_chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.retrieval_run_chunks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.retrieval_run_chunks_id_seq OWNER TO postgres;

--
-- TOC entry 5314 (class 0 OID 0)
-- Dependencies: 234
-- Name: retrieval_run_chunks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.retrieval_run_chunks_id_seq OWNED BY public.retrieval_run_chunks.id;


--
-- TOC entry 232 (class 1259 OID 17731)
-- Name: retrieval_runs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.retrieval_runs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.retrieval_runs_id_seq OWNER TO postgres;

--
-- TOC entry 5315 (class 0 OID 0)
-- Dependencies: 232
-- Name: retrieval_runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.retrieval_runs_id_seq OWNED BY public.retrieval_runs.id;


--
-- TOC entry 5093 (class 2604 OID 17659)
-- Name: app_users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_users ALTER COLUMN id SET DEFAULT nextval('public.app_users_id_seq'::regclass);


--
-- TOC entry 5086 (class 2604 OID 17511)
-- Name: chats id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats ALTER COLUMN id SET DEFAULT nextval('public.chats_id_seq'::regclass);


--
-- TOC entry 5079 (class 2604 OID 17456)
-- Name: document_chunks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_chunks ALTER COLUMN id SET DEFAULT nextval('public.document_chunks_id_seq'::regclass);


--
-- TOC entry 5081 (class 2604 OID 17482)
-- Name: documents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents ALTER COLUMN id SET DEFAULT nextval('public.documents_id_seq'::regclass);


--
-- TOC entry 5090 (class 2604 OID 17523)
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


--
-- TOC entry 5104 (class 2604 OID 17782)
-- Name: retrieval_run_chunks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_run_chunks ALTER COLUMN id SET DEFAULT nextval('public.retrieval_run_chunks_id_seq'::regclass);


--
-- TOC entry 5095 (class 2604 OID 17735)
-- Name: retrieval_runs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_runs ALTER COLUMN id SET DEFAULT nextval('public.retrieval_runs_id_seq'::regclass);


--
-- TOC entry 5128 (class 2606 OID 17668)
-- Name: app_users app_users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_pkey PRIMARY KEY (id);


--
-- TOC entry 5130 (class 2606 OID 17670)
-- Name: app_users app_users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.app_users
    ADD CONSTRAINT app_users_username_key UNIQUE (username);


--
-- TOC entry 5126 (class 2606 OID 17546)
-- Name: chat_documents chat_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_documents
    ADD CONSTRAINT chat_documents_pkey PRIMARY KEY (chat_id, document_id);


--
-- TOC entry 5120 (class 2606 OID 17518)
-- Name: chats chats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats
    ADD CONSTRAINT chats_pkey PRIMARY KEY (id);


--
-- TOC entry 5113 (class 2606 OID 17466)
-- Name: document_chunks document_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_pkey PRIMARY KEY (id);


--
-- TOC entry 5116 (class 2606 OID 17497)
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (id);


--
-- TOC entry 5124 (class 2606 OID 17534)
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- TOC entry 5137 (class 2606 OID 17793)
-- Name: retrieval_run_chunks retrieval_run_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_run_chunks
    ADD CONSTRAINT retrieval_run_chunks_pkey PRIMARY KEY (id);


--
-- TOC entry 5134 (class 2606 OID 17762)
-- Name: retrieval_runs retrieval_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_runs
    ADD CONSTRAINT retrieval_runs_pkey PRIMARY KEY (id);


--
-- TOC entry 5140 (class 2606 OID 17795)
-- Name: retrieval_run_chunks unique_chunk_per_run; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_run_chunks
    ADD CONSTRAINT unique_chunk_per_run UNIQUE (retrieval_run_id, chunk_id);


--
-- TOC entry 5142 (class 2606 OID 17797)
-- Name: retrieval_run_chunks unique_position_per_run; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_run_chunks
    ADD CONSTRAINT unique_position_per_run UNIQUE (retrieval_run_id, context_position);


--
-- TOC entry 5117 (class 1259 OID 17681)
-- Name: documents_user_filename_unique; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX documents_user_filename_unique ON public.documents USING btree (user_id, lower((filename)::text));


--
-- TOC entry 5121 (class 1259 OID 17699)
-- Name: idx_chats_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chats_user_id ON public.chats USING btree (user_id);


--
-- TOC entry 5114 (class 1259 OID 17557)
-- Name: idx_document_chunks_document_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_document_chunks_document_id ON public.document_chunks USING btree (document_id);


--
-- TOC entry 5118 (class 1259 OID 17698)
-- Name: idx_documents_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_documents_user_id ON public.documents USING btree (user_id);


--
-- TOC entry 5122 (class 1259 OID 17558)
-- Name: idx_messages_chat_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_messages_chat_id ON public.messages USING btree (chat_id);


--
-- TOC entry 5135 (class 1259 OID 17811)
-- Name: retrieval_run_chunks_chunk_id_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX retrieval_run_chunks_chunk_id_index ON public.retrieval_run_chunks USING btree (chunk_id);


--
-- TOC entry 5138 (class 1259 OID 17810)
-- Name: retrieval_run_chunks_run_id_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX retrieval_run_chunks_run_id_index ON public.retrieval_run_chunks USING btree (retrieval_run_id);


--
-- TOC entry 5131 (class 1259 OID 17808)
-- Name: retrieval_runs_chat_id_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX retrieval_runs_chat_id_index ON public.retrieval_runs USING btree (chat_id);


--
-- TOC entry 5132 (class 1259 OID 17809)
-- Name: retrieval_runs_created_at_index; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX retrieval_runs_created_at_index ON public.retrieval_runs USING btree (created_at DESC);


--
-- TOC entry 5147 (class 2606 OID 17547)
-- Name: chat_documents chat_documents_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_documents
    ADD CONSTRAINT chat_documents_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(id) ON DELETE CASCADE;


--
-- TOC entry 5148 (class 2606 OID 17552)
-- Name: chat_documents chat_documents_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_documents
    ADD CONSTRAINT chat_documents_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- TOC entry 5145 (class 2606 OID 17676)
-- Name: chats chats_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chats
    ADD CONSTRAINT chats_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_users(id) ON DELETE CASCADE;


--
-- TOC entry 5143 (class 2606 OID 17501)
-- Name: document_chunks document_chunks_document_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.document_chunks
    ADD CONSTRAINT document_chunks_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(id) ON DELETE CASCADE;


--
-- TOC entry 5144 (class 2606 OID 17671)
-- Name: documents documents_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_users(id) ON DELETE CASCADE;


--
-- TOC entry 5146 (class 2606 OID 17535)
-- Name: messages messages_chat_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_chat_id_fkey FOREIGN KEY (chat_id) REFERENCES public.chats(id) ON DELETE CASCADE;


--
-- TOC entry 5152 (class 2606 OID 17803)
-- Name: retrieval_run_chunks retrieval_run_chunks_chunk_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_run_chunks
    ADD CONSTRAINT retrieval_run_chunks_chunk_fk FOREIGN KEY (chunk_id) REFERENCES public.document_chunks(id) ON DELETE CASCADE;


--
-- TOC entry 5153 (class 2606 OID 17798)
-- Name: retrieval_run_chunks retrieval_run_chunks_run_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_run_chunks
    ADD CONSTRAINT retrieval_run_chunks_run_fk FOREIGN KEY (retrieval_run_id) REFERENCES public.retrieval_runs(id) ON DELETE CASCADE;


--
-- TOC entry 5149 (class 2606 OID 17773)
-- Name: retrieval_runs retrieval_runs_assistant_message_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_runs
    ADD CONSTRAINT retrieval_runs_assistant_message_fk FOREIGN KEY (assistant_message_id) REFERENCES public.messages(id) ON DELETE CASCADE;


--
-- TOC entry 5150 (class 2606 OID 17763)
-- Name: retrieval_runs retrieval_runs_chat_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_runs
    ADD CONSTRAINT retrieval_runs_chat_fk FOREIGN KEY (chat_id) REFERENCES public.chats(id) ON DELETE CASCADE;


--
-- TOC entry 5151 (class 2606 OID 17768)
-- Name: retrieval_runs retrieval_runs_user_message_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.retrieval_runs
    ADD CONSTRAINT retrieval_runs_user_message_fk FOREIGN KEY (user_message_id) REFERENCES public.messages(id) ON DELETE CASCADE;


-- Completed on 2026-09-25 00:19:20

--
-- PostgreSQL database dump complete
--

\unrestrict WhmfzShecoqsR7eT073YMVscPoV8QWa23qQEVPu4UGDZTEWTBnGdoJQcgk8RIbr

