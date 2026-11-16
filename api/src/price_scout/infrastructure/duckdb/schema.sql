create table if not exists judged_offers (
    search_id varchar not null,
    offer_id varchar not null,
    product_key varchar,
    product_name varchar,
    category varchar,
    width_cm double,
    depth_cm double,
    height_cm double,
    discarded boolean not null,
    discard_reason varchar,
    judged_at timestamptz not null default current_timestamp,
    primary key (search_id, offer_id)
);

create table if not exists shopping_requests (
    id varchar primary key,
    description varchar not null,
    market json not null,
    budget double,
    preferences json not null,
    status varchar not null,
    steps json not null,
    plan json,
    error varchar,
    created_at timestamp not null,
    updated_at timestamp not null
);

create table if not exists llm_calls (
    id varchar primary key,
    request_id varchar,
    task varchar not null,
    model varchar not null,
    prompt_version varchar not null,
    input_tokens integer not null,
    output_tokens integer not null,
    cost_usd double,
    latency_ms integer not null,
    ok boolean not null,
    error varchar,
    created_at timestamp not null
);

alter table shopping_requests alter column budget drop not null;

alter table judged_offers add column if not exists judge_version varchar;
