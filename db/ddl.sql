-- Table: public.exchange_data

-- DROP TABLE IF EXISTS public.exchange_data;

CREATE TABLE IF NOT EXISTS public.exchange_data
(
    currency text COLLATE pg_catalog."default" NOT NULL,
    date timestamp without time zone NOT NULL,
    rate bigint NOT NULL
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.exchange_data
    OWNER to postgres;