# Job Board Application Architecture

## System Overview

```mermaid
graph TB
    subgraph "Frontend"
        UI[Web Interface]
    end
    
    subgraph "Backend"
        API[FastAPI App]
        AUTH[Authentication]
        PAY[Payment Handler]
    end
    
    subgraph "Data"
        DB[(SQLite DB)]
    end
    
    subgraph "External"
        STRIPE[Stripe API]
    end
    
    UI --> API
    API --> AUTH
    API --> PAY
    API --> DB
    PAY --> STRIPE
```

## User Flow

```mermaid
flowchart LR
    A[User] --> B{User Type}
    B -->|Public| C[View Jobs]
    B -->|Employer| D[Manage Jobs]
    B -->|Admin| E[Admin Panel]
    
    D --> F[Create Job]
    F --> G[Pay with Stripe]
    G --> H[Job Published]
    
    C --> I[Search Jobs]
    I --> J[Apply to Job]
```

## Database Schema

```mermaid
erDiagram
    EmployerAccount {
        int id PK
        string email
        string company_name
    }
    
    Job {
        int id PK
        string title
        string description
        int employer_id FK
        string status
    }
    
    EmployerAccount ||--o{ Job : "creates"
```

## Payment Flow

```mermaid
sequenceDiagram
    participant E as Employer
    participant A as App
    participant S as Stripe
    
    E->>A: Create Job
    A->>A: Save Draft
    A->>S: Create Payment
    S-->>A: Payment URL
    A-->>E: Redirect to Stripe
    S->>A: Payment Success
    A->>A: Publish Job
```

## Security Layers

```mermaid
graph TB
    subgraph "Security"
        AUTH[Session Auth]
        CSRF[CSRF Protection]
        VALID[Input Validation]
    end
    
    AUTH --> CSRF
    CSRF --> VALID
```

This simplified architecture shows:

1. **Clean Separation**: Frontend, Backend, Data, and External services
2. **Simple User Flows**: Three main user types with clear paths
3. **Core Database**: Essential entities only
4. **Payment Process**: Straightforward Stripe integration
5. **Security**: Basic but effective security layers 