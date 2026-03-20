# Game Distribution Service - donwme

Trying to build a Steam-like game distribution service/platform, will use CLI for front-end interaction allowing for user and game publishers to upload and download games 

Initial design idea -
<img width="1525" height="705" alt="image" src="https://github.com/user-attachments/assets/e7c504e7-18ee-4150-93c2-7263fc92d9cd" />

Let's separate - User and Publisher to get a better picture
### User Flows
- Game purchase flow is easy, user buys we write the successful purchase to db (not going to implement this)
- Game download flow is a task, we assume user has already purchased some games and its already updated in db
```mermaid
sequenceDiagram

    participant U as User CLI
    participant A as API Service
    participant D as DB
    participant B as Blob Storage

    U->>A: JWT Authentication


    A->>D: check purchase
    D-->>A: OK
    A->>D: fetch manifest
    D-->>A: manifest
    A->>A: generate SAS token

    A-->>U: manifest + SAS token

    par Parallel chunk downloads
        U->>B: request chunk (SAS)
        B-->>U: download chunk
        U->>B: ...
    
    end

    U->>U: verify download and install
```

### Publisher Flows
- The publisher uploads game on the platform
```mermaid
sequenceDiagram

    participant P as Publisher CLI
    participant A as API Service
    participant D as DB
    participant B as Blob Storage
    

    P->>A: JWT Authentication


    A->>A: create upload session
    A->>A: generate SAS token

    A-->>P: SAS token

    par Parallel chunk uploads
        P->>B: upload chunk (SAS)
        P->>B: upload chunk (SAS)
        P->>B: upload chunk (SAS)
    end

    P->>A: commit

    A->>B: verify upload
    B-->>A: OK

    A->>A: build manifest

    A->>D: store manifest
    D-->>A: OK

    A-->>P: success
```
