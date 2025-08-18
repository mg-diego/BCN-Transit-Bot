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
It provides real-time information about metro and bus stops, interactive maps, and lets you save your favorite stations for quick access.



## 👾 Features

- 🗺️ <b>Interactive Map:</b> Select bus or metro stops directly from a map.

- 🚏 <b>Stop Information:</b> Get detailed info about stops and lines in real time.

- ⭐ <b>Favorites:</b> Add and manage your favorite stations for faster access.

- 📊 <b>Usage Tracking:</b> Keeps track of user sessions to improve experience.



## 🚀 Getting Started

You don’t need to install anything to try <code>BCN Transit Bot</code>.
The bot is already deployed and available on Telegram:

👉 [BCN Transit Bot](https://t.me/BCN_Transit_Bot)

Just open the link, start the bot, and explore Barcelona’s metro and bus network in real time.

## 🛠️ Project Architecture

```mermaid
graph TD

    10["💻 Telegram Bot"]
    7["👤 User"]
    8["🌐 External Transport API"]
    9["⭐ Favorites Data"]

    subgraph 1["User Interface CLI"]
        31["🚇 Metro Handler"]
        32["🚌 Bus Handler"]
        33["❤️ Favorites Handler"]
        34["❓ Help Handler"]
        35["⌨️ Keyboard Factory"]
        36["📋 Menu Handler"]
    end

    subgraph 2["Providers"]
        26["❤️ Favorites Manager"]
        27["📝 Logger"]
        28["🗺️ Mapper"]
        29["🔒 Secrets Manager"]
        30["🌐 Transport API Service"]
    end

    subgraph 3["Domain Models Data Classes"]
        subgraph 4["Metro Domain Models"]
            20["🚇 Metro Access"]
            21["🔗 Metro Connection"]
            22["🛤️ Metro Line"]
            23["🚉 Metro Station"]
            24["⏱️ Next Metro"]
            25["📅 Next Scheduled Metro"]
        end
        subgraph 5["Bus Domain Models"]
            17["🚌 Bus Line"]
            18["🛑 Bus Stop"]
            19["⏱️ Next Bus"]
        end
    end

    subgraph 6["Application Services"]
        11["🚇 Metro Service"]
        12["🚌 Bus Service"]
        13["💾 Cache Service"]
        14["💬 Message Service"]
        15["🔄 Update Manager"]
    end

    %% Edges
    10 -->|Drives| 1
    6 -->|Uses| 2
    6 -->|Uses| 3
    1 -->|Invokes| 6
    2 -->|Connects to| 8
    2 -->|Manages| 9
    7 -->|Interacts with| 10

    %% Classes & Colors
    classDef ui fill:#2196f3,color:#fff,stroke:#1a237e,stroke-width:2px;
    classDef providers fill:#4caf50,color:#fff,stroke:#1b5e20,stroke-width:2px;
    classDef domain fill:#ff9800,color:#000,stroke:#e65100,stroke-width:2px;
    classDef services fill:#9c27b0,color:#fff,stroke:#4a148c,stroke-width:2px;
    classDef external fill:#90a4ae,color:#000,stroke:#37474f,stroke-width:2px;
    classDef cli fill:#607d8b,color:#fff,stroke:#263238,stroke-width:2px;
    classDef actor fill:#f44336,color:#fff,stroke:#b71c1c,stroke-width:2px;

    %% Assign classes ONLY to internal boxes
    class 31,32,33,34,35,36 ui;
    class 26,27,28,29,30 providers;
    class 20,21,22,23,24,25,17,18,19 domain;
    class 11,12,13,14,15 services;
    class 8,9 external;
    class 10 cli;
    class 7 actor;

```



## 🔰 Contributing

- **🐛 [Report Issues](https://github.com/mg-diego/BCN-Transit-Bot/issues)**: Submit bugs found or log feature requests for the `BCN-Transit-Bot` project.
- **💡 [Submit Pull Requests](https://github.com/mg-diego/BCN-Transit-Bot/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your github account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/mg-diego/BCN-Transit-Bot
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to github**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://github.com{/mg-diego/BCN-Transit-Bot/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=mg-diego/BCN-Transit-Bot">
   </a>
</p>
</details>



## 🎗 License

This project is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

You are free to use, modify, and distribute this software in compliance with the license terms.  
See the [LICENSE](./LICENSE) file for full details.

---