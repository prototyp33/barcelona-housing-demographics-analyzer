# Spike Dependencies Diagram

**Fecha:** Diciembre 2025  
**Propósito:** Visualización de dependencias y critical path del spike

---

## Critical Path (Must complete in order)

```mermaid
graph TD
    A[#198 Spike Epic] --> B[#199 Portal Dades]
    A --> C[#200 INE API]
    A --> D[#201 Catastro]
    A --> E[#206 Validation Framework]
    
    B --> F[#205 barrio_id Linking]
    C --> F
    D --> F
    
    F --> G[#204 PostgreSQL Schema]
    B --> G
    C --> G
    D --> G
    
    B --> H[#208 Hedonic Model]
    C --> H
    E --> H
    
    H --> I[#198 GO Decision]
    G --> I
    F --> I
    
    H --> J[#209 DiD Viability]
    B --> J
    C --> J
    
    J --> I
    
    I --> K[#187 Fase 1: Database]
    K --> L[#194 Fase 2: Critical Extractors]
    L --> M[#195 Fase 3: Complementary]
    L --> N[#196 Fase 4: Integration]
    M --> N
    
    style A fill:#5319E7,stroke:#333,stroke-width:3px,color:#fff
    style I fill:#B60205,stroke:#333,stroke-width:3px,color:#fff
    style H fill:#0E8A16,stroke:#333,stroke-width:2px,color:#fff
    style F fill:#FBCA04,stroke:#333,stroke-width:2px
```

---

## Parallel Work Streams

```mermaid
gantt
    title Spike Timeline - Parallel Work Streams
    dateFormat YYYY-MM-DD
    section Equipo A - Data Sources
    Portal Dades (#199)           :a1, 2025-12-16, 2d
    INE API (#200)                :a2, 2025-12-16, 2d
    Catastro (#201)               :a3, 2025-12-16, 2d
    Validation Framework (#206)   :a4, 2025-12-16, 1d
    barrio_id Linking (#205)       :crit, a5, 2025-12-18, 1d
    PostgreSQL Schema (#204)      :crit, a6, 2025-12-18, 2d
    Data Quality (#207)           :a7, 2025-12-19, 1d
    
    section Equipo B - Analytics
    Hedonic Model (#208)          :crit, b1, 2025-12-16, 4d
    DiD Viability (#209)          :b2, 2025-12-16, 4d
    
    section Decision
    GO/NO-GO Decision             :milestone, crit, m1, 2025-12-20, 0d
```

---

## Team Workflow

```mermaid
graph LR
    subgraph "Equipo A - Data Infrastructure"
        A1[#199 Portal Dades]
        A2[#200 INE API]
        A3[#201 Catastro]
        A4[#206 Framework]
        A5[#205 Linking]
        A6[#204 Schema]
        A7[#207 Quality]
        
        A1 --> A5
        A2 --> A5
        A3 --> A5
        A5 --> A6
        A1 --> A7
        A2 --> A7
        A3 --> A7
    end
    
    subgraph "Equipo B - Analytics"
        B1[#208 Hedonic]
        B2[#209 DiD]
        
        B1 --> B2
    end
    
    subgraph "Sync Points"
        S1[Tuesday EOD<br/>Data Delivery]
        S2[Thursday PM<br/>Findings Review]
        S3[Friday PM<br/>GO Decision]
    end
    
    A1 --> S1
    A2 --> S1
    A3 --> S1
    S1 --> B1
    S1 --> B2
    
    A6 --> S2
    A7 --> S2
    B1 --> S2
    B2 --> S2
    
    S2 --> S3
    S3 --> Fase1[#187 Fase 1]
    
    style S1 fill:#0E8A16,stroke:#333,stroke-width:2px,color:#fff
    style S2 fill:#FBCA04,stroke:#333,stroke-width:2px
    style S3 fill:#B60205,stroke:#333,stroke-width:3px,color:#fff
```

---

## Blocking Relationships Matrix

| Issue | Can Start | Blocks | Blocked By |
|-------|-----------|--------|------------|
| #198 | ✅ Monday 9 AM | ALL | None |
| #199 | ✅ Monday 9 AM | #205, #207, #204, #208 | None |
| #200 | ✅ Monday 9 AM | #205, #207, #204, #208 | None |
| #201 | ✅ Monday 9 AM | #205, #207, #204 | None |
| #206 | ✅ Monday 9 AM | #208, #209 (soft) | None |
| #208 | ⚠️ Monday (mock) or Tuesday (real) | #198 (GO) | #199, #200 (soft) |
| #209 | ⚠️ Monday (mock) or Tuesday (real) | #198 (GO) | #208 (soft), #199 |
| #205 | ⚠️ Wednesday AM | #204, #207 | #199, #200, #201 |
| #204 | ⚠️ Wednesday PM | #188, #189, #187 | #199, #200, #201, #205, #208 |
| #207 | ⚠️ Tuesday PM | #198 (GO) | #199, #200, #201 |

---

## Post-Spike Dependencies

```mermaid
graph TD
    Spike[#198 Spike<br/>GO Decision] --> Fase1[#187 Fase 1<br/>Database Infrastructure]
    
    Fase1 --> Fase2[#194 Fase 2<br/>Critical Extractors]
    Fase1 --> Fase4[#196 Fase 4<br/>Integration]
    
    Fase2 --> Fase3[#195 Fase 3<br/>Complementary Extractors]
    Fase2 --> Fase4
    
    Fase3 --> Fase4
    
    Fase4 --> Production[Production Launch]
    
    style Spike fill:#B60205,stroke:#333,stroke-width:3px,color:#fff
    style Fase1 fill:#5319E7,stroke:#333,stroke-width:2px,color:#fff
    style Fase2 fill:#0E8A16,stroke:#333,stroke-width:2px,color:#fff
    style Fase3 fill:#FBCA04,stroke:#333,stroke-width:2px
    style Fase4 fill:#D93F0B,stroke:#333,stroke-width:2px,color:#fff
    style Production fill:#1D76DB,stroke:#333,stroke-width:3px,color:#fff
```

---

**Última actualización:** Diciembre 2025

