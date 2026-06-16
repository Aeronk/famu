# Murimi OS — Entity Relationship Diagram

Single-database multi-tenancy: every business table carries `tenant_id`
(FK → `tenants.id`). `users.tenant_id` is nullable (Super Admin = platform-level);
`market_prices` / `knowledge_*` have a nullable `tenant_id` (NULL = global/shared).

```mermaid
erDiagram
    tenants ||--o{ users : has
    tenants ||--o{ farms : owns
    tenants ||--o{ crop_cycles : scopes
    tenants ||--o{ livestock : scopes
    tenants ||--o{ expenses : scopes
    tenants ||--o{ incomes : scopes

    users ||--o{ refresh_tokens : issues
    users ||--o{ whatsapp_contacts : maps
    users ||--o{ ai_conversations : chats

    farms ||--o{ crop_cycles : grows
    farms ||--o{ tobacco_cycles : grows
    farms ||--o{ livestock : holds
    farms ||--o{ weather_records : observed_at
    farms ||--o{ activities : logs

    crop_cycles ||--o{ crop_inputs : receives
    crop_cycles ||--o{ harvests : yields
    crop_cycles ||--o{ activities : timeline

    tobacco_cycles ||--o{ tobacco_reaping : reaps
    tobacco_cycles ||--o{ tobacco_curing : cures
    tobacco_cycles ||--o{ tobacco_grading : grades
    tobacco_cycles ||--o{ tobacco_deliveries : delivers

    livestock ||--o{ vaccinations : vaccinated
    livestock ||--o{ disease_events : diagnosed
    livestock ||--o{ weight_records : weighed
    livestock ||--o{ breeding_records : bred
    livestock ||--o{ feed_records : fed

    ai_conversations ||--o{ ai_messages : contains
    knowledge_documents ||--o{ knowledge_chunks : embedded

    tenants {
        uuid id PK
        string name
        string slug UK
        enum   type
        enum   status
        jsonb  settings
    }
    users {
        uuid id PK
        uuid tenant_id FK "nullable (super admin)"
        string email UK "nullable"
        string phone_number UK "nullable"
        enum   role
        enum   language
    }
    farms {
        uuid id PK
        uuid tenant_id FK
        string name
        float  gps_lat
        float  gps_lng
        string province
        string soil_type
        float  size_ha
    }
    crop_cycles {
        uuid id PK
        uuid tenant_id FK
        uuid farm_id FK
        enum   crop_type
        date   planting_date
        float  area_ha
        enum   status
    }
    livestock {
        uuid id PK
        uuid tenant_id FK
        uuid farm_id FK
        enum   species
        string tag_number
        float  weight_kg
    }
    knowledge_chunks {
        uuid id PK
        uuid document_id FK
        text   content
        vector embedding "vector(1536) on pgvector"
    }
```

## Table groups

| Domain         | Tables |
|----------------|--------|
| Tenancy / Identity | `tenants`, `users`, `refresh_tokens`, `whatsapp_contacts` |
| Farm           | `farms`, `activities` |
| Crop           | `crop_cycles`, `crop_inputs`, `harvests` |
| Tobacco        | `tobacco_cycles`, `tobacco_reaping`, `tobacco_curing`, `tobacco_grading`, `tobacco_deliveries` |
| Livestock      | `livestock`, `vaccinations`, `disease_events`, `weight_records`, `breeding_records`, `feed_records` |
| Finance        | `expenses`, `incomes`, `loans`, `input_credits` |
| Weather/Market | `weather_records`, `weather_alerts`, `market_prices` |
| AI / RAG       | `knowledge_documents`, `knowledge_chunks`, `ai_conversations`, `ai_messages`, `image_analyses` |
| ML / Sim       | `predictions`, `simulations` |
| Notifications  | `notifications`, `notification_preferences` |
