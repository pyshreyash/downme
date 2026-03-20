# Game Distribution Service - donwme

Trying to build a Steam-like game distribution service/platform, will use CLI for front-end interaction allowing for user and game publishers to upload and download games 

Initial design idea -
<img width="1525" height="705" alt="image" src="https://github.com/user-attachments/assets/e7c504e7-18ee-4150-93c2-7263fc92d9cd" />

A little detailed but still messy - 
```mermaid
flowchart TD

    %% Actors
    user[User]
    publisher[Publisher]

    %% CLIs
    cli_user[User CLI]
    cli_pub[Publisher CLI]

    %% Core Services
    api[API Service\n- Auth (JWT)\n- Entitlement\n- Manifest\n- SAS Generator]
    db[(Database\nUsers / Purchases / Games / Versions / Manifests)]
    blob[(Azure Blob Storage\nGame Chunks)]

    %% User Flow
    user --> cli_user
    cli_user -->|Request manifest + SAS| api
    api -->|Check entitlement| db
    api -->|Return manifest + SAS| cli_user
    cli_user -->|Download chunks via SAS| blob

    %% Publisher Flow
    publisher --> cli_pub
    cli_pub -->|Auth + upload request| api
    api -->|Return SAS| cli_pub
    cli_pub -->|Upload chunks via SAS| blob
    cli_pub -->|Commit upload| api

    %% Backend Processing
    api -->|Validate chunks| blob
    api -->|Store manifest + metadata| db
```
