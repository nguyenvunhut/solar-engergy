# Solar Energy System Architecture

```mermaid
flowchart LR
    classDef solar fill:#fff8e1,stroke:#fbc02d,stroke-width:2px,color:#f57f17;
    classDef inverter fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:#0d47a1;
    classDef battery fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1b5e20;
    classDef grid fill:#f3e5f5,stroke:#8e24aa,stroke-width:2px,color:#4a148c;
    classDef home fill:#efebe9,stroke:#5d4037,stroke-width:2px,color:#3e2723;
    classDef weather fill:#e0f7fa,stroke:#00acc1,stroke-width:2px,color:#006064;

    Sun["☀️ Sun"]:::weather
    PV["Solar Panels<br>(PV Array)"]:::solar
    Inverter["Solar Inverter<br>(DC to AC)"]:::inverter
    Battery["Battery Storage<br>(DC Storage)"]:::battery
    Meter["Smart Meter"]:::grid
    Grid["Utility Grid"]:::grid
    Home["Home Appliances<br>(AC Load)"]:::home

    %% Năng lượng mặt trời
    Sun -.->|Solar Radiation| PV

    %% Dòng điện một chiều (DC)
    PV ===|DC Power| Inverter
    Inverter ===|DC Power| Battery
    Battery ===|DC Power| Inverter

    %% Dòng điện xoay chiều (AC)
    Inverter ===|AC Power| Meter
    Meter ===|AC Power| Home
    Meter ===|Excess AC| Grid
    Grid ===|Grid AC| Meter

    %% Chú thích
    subgraph Legend ["Energy Flow Legend"]
        direction TB
        l1[DC Power (Direct Current)]:::solar
        l2[AC Power (Alternating Current)]:::inverter
    end
```
