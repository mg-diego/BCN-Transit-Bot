<p align="center">
    <img src="docs/banner.jpg" align="center" width="80%">
</p>
<p align="center">
	<img src="https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram" alt="telegram-bot">
	<img src="https://img.shields.io/badge/python-3.13.3%2B-blue" alt="repo-language">
    <img src="https://img.shields.io/github/license/saltstack/salt" alt="license">
	<img src="https://img.shields.io/github/last-commit/mg-diego/BCN-Transit-Bot" alt="last-commit">
</p>
<p align="center"><!-- default option, no dependency badges. -->
</p>
<p align="center">
	<!-- default option, no dependency badges. -->
</p>

## 🔗 Table of Contents

- [📍 Overview](#-overview)
- [👾 Features](#-features)
- [🚀 Getting Started](#-getting-started)
- [🛠️ Project Architecture](#-project-architecture)
- [📌 Project Roadmap](#-project-roadmap)
- [🔰 Contributing](#-contributing)
- [🎗 License](#-license)
- [🙌 Acknowledgments](#-acknowledgments)

---

## 📍 Overview

<code>BCN Transit Bot</code> is a Telegram bot that helps you explore and navigate Barcelona’s public transportation system.
It provides real-time information about metro, bus and tram stops, interactive maps, and lets you save your favorite stations for quick access.



## 👾 Features

- 🗺️ <b>Interactive Map:</b> Select bus, metro or tram stops directly from a map.

- 🚏 <b>Stop Information:</b> Get detailed info about stops and lines in real time.

- ⭐ <b>Favorites:</b> Add and manage your favorite stations for faster access.

- 🌐 <b>Language Support:</b> Switch between English, Spanish, and Catalan for a personalized experience.

- 📊 <b>Usage Tracking:</b> Keeps track of user sessions to improve experience.



## 🚀 Getting Started

You don’t need to install anything to try <code>BCN Transit Bot</code>.
The bot is already deployed and available on Telegram:

👉 [BCN Transit Bot](https://t.me/BCN_Transit_Bot)

Just open the link, start the bot, and explore Barcelona’s metro and bus network in real time.


https://github.com/user-attachments/assets/824458b8-456d-4c1b-a00f-a180094d11cd





## 🛠️ Project Architecture

```mermaid
graph TD
    %% Actors
    U["👤 User"]
    B["💻 Telegram Bot"]

    %% User Interface CLI Handlers
    subgraph CLI["User Interface CLI"]
        MH["🚇 Metro Handler"]
        BH["🚌 Bus Handler"]
        TH["🚋 Tram Handler"]
        FH["⭐ Favorites Handler"]
        LH["🌐 Language Handler"]
        HH["❓ Help Handler"]
        KF["⌨️ Keyboard Factory"]
        MHN["📋 Menu Handler"]
    end

    %% Application Services
    subgraph Services["Application Services"]
        MS["🚇 Metro Service"]
        BS["🚌 Bus Service"]
        TS["🚋 Tram Service"]
        CS["💾 Cache Service"]
        MSGS["💬 Message Service"]
        UM["🔄 Update Manager"]
    end

    %% Domain Models
    subgraph Domain["Domain Models Data Classes"]
        subgraph Metro["Metro Domain"]
            MA["🚇 Metro Access"]
            MC["🔗 Metro Connection"]
            ML["🛤️ Metro Line"]
            MSN["🚉 Metro Station"]
            NM["⏱️ Next Metro"]
            NSM["📅 Next Scheduled Metro"]
        end
        subgraph Bus["Bus Domain"]
            BL["🚌 Bus Line"]
            BSN["🛑 Bus Stop"]
            NB["⏱️ Next Bus"]
        end
        subgraph Tram["Tram Domain"]
            TL["🚋 TramLine"]
            TSN["🛑 TramStop"]
            NT["⏱️ NextTram"]
        end
    end

    %% Providers
    subgraph Internal["Internal Providers"]
        L["📝 Logger"]
        M["🗺️ Mapper"]
        SM["🔒 Secrets Manager"]
        LM["🌐 Language Manager"]
    end

    subgraph External["External Providers"]
        UDM["💾 User Data Manager"]
        TAS["🌐 Transport API Service"]
    end

    %% External API and data
    EXT["🌐 External Transport API"]
    FD["⭐ Favorites Data"]
    UPD["👤 User Profile Data"]

    %% Flow edges
    U -->|Interacts with| B
    B -->|Drives| CLI

    %% Handlers -> Services
    MH -->|Invokes| MS
    BH -->|Invokes| BS
    TH -->|Invokes| TS
    FH -->|Uses| UDM

    %% Services -> Domain
    MS -->|Uses| Metro
    BS -->|Uses| Bus
    TS -->|Uses| Tram

    %% External connections
    UDM -->|Manages| FD
    UDM -->|Manages| UPD
    TAS -->|Connects to| EXT

    Services -->|Uses| Internal
    Services -->|Uses| External
    Services -->|Uses| Domain

    %% Classes & Colors
    classDef ui fill:#2196f3,color:#fff,stroke:#1a237e,stroke-width:2px;
    classDef providers fill:#4caf50,color:#fff,stroke:#1b5e20,stroke-width:2px;
    classDef domain fill:#ff9800,color:#000,stroke:#e65100,stroke-width:2px;
    classDef services fill:#9c27b0,color:#fff,stroke:#4a148c,stroke-width:2px;
    classDef external fill:#90a4ae,color:#000,stroke:#37474f,stroke-width:2px;
    classDef cli fill:#607d8b,color:#fff,stroke:#263238,stroke-width:2px;
    classDef actor fill:#f44336,color:#fff,stroke:#b71c1c,stroke-width:2px;

    %% Assign classes
    class MH,BH,TH,FH,LH,HH,KF,MHN ui;
    class L,M,SM,LM providers;
    class MA,MC,ML,MSN,NM,NSM,BL,BSN,NB,TL,TSN,NT domain;
    class MS,BS,TS,CS,MSGS,UM services;
    class UDM,TAS external;
    class B cli;
    class U actor;

```



## 🔰 Contributing

Contributions are welcome! Please read the [Contributing Guide](./CONTRIBUTING.md) to get started.

- **🐛 [Report Issues](https://github.com/mg-diego/BCN-Transit-Bot/issues)**: Submit bugs found or log feature requests for the `BCN-Transit-Bot` project.
- **💡 [Submit Pull Requests](https://github.com/mg-diego/BCN-Transit-Bot/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<br>

<p align="left">
   <a href="https://github.com{/mg-diego/BCN-Transit-Bot/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=mg-diego/BCN-Transit-Bot">
   </a>
</p>



## 🎗 License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

You are free to use, modify, and distribute this software in compliance with the license terms.  
See the [LICENSE](./LICENSE) file for full details.

---
