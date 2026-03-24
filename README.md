<p align="center">
  <h1 align="center">✈️ Agentic AI Group Trip Planner</h1>
  <p align="center">
    <strong>Stop arguing. Start exploring. Let AI plan the perfect group trip — democratically.</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
    <img src="https://img.shields.io/badge/Streamlit-1.54+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
    <img src="https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini" />
    <img src="https://img.shields.io/badge/LangChain-1.2+-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain" />
    <img src="https://img.shields.io/badge/Supabase-Postgres-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase" />
  </p>
  <p align="center">
    <a href="#-live-demo"><img src="https://img.shields.io/badge/🚀_Live_Demo-Try_the_App-FF4B4B?style=for-the-badge" alt="Live Demo" /></a>
  </p>
</p>

---

## 🚀 Live Demo

> **[▶️ Try the App Here!](https://YOUR_DEPLOYED_URL_HERE)**
>
> *(Replace with your actual Streamlit Cloud / deployment link)*

---

## 🛑 The Problem

Planning a group trip is traditionally a **logistical nightmare**. It usually involves endless, chaotic WhatsApp group chats, conflicting budgets, and one "designated planner" who has to do hours of research. Even worse, human planners often fail to realize the geographic distance between places, resulting in itineraries that force the group to **zigzag across a city**, wasting time and money on transit.

## 💡 The Solution

This application acts as an **impartial, mathematically precise AI Travel Agent**. It completely eliminates the friction of group planning through a seamless three-step pipeline:

1.  **🔍 AI Scouting:** The "Trip Leader" inputs the destination, dates, and a strict budget. The AI (**Gemini + Tavily**) autonomously researches and curates a list of highly-rated, budget-appropriate activities and hidden gems.

2.  **🗳️ Democratic Consensus:** The app generates a unique **invite code (UUID)**. Friends join anonymously and vote on the AI's curated list, ensuring everyone gets a say in the vacation.

3.  **🧠 Deterministic Orchestration:** The "**Architect Agent**" tallies the votes and passes the winners through a **deterministic math engine (OSRM)** to solve the **Traveling Salesperson Problem**. It generates a mathematically optimized, day-by-day itinerary complete with transit instructions, budget-compliant hotel options (via **Amadeus**), and a master **Google Maps** navigation link.

---

## 📸 Sneak Peeks

<p align="center">
  <img src="assets/screenshots/01_create_trip.png" alt="Create Trip Page" width="80%" />
  <br /><em>🌍 Plan a New Group Trip — Input destination, dates, and budget.</em>
</p>

<p align="center">
  <img src="assets/screenshots/02_join_adventure.png" alt="Join the Adventure" width="80%" />
  <br /><em>🎟️ Join the Adventure — Friends paste the Trip ID to enter the voting booth.</em>
</p>

<p align="center">
  <img src="assets/screenshots/03_destination_hype.png" alt="Destination Hype" width="80%" />
  <br /><em>🌟 AI-Generated Destination Hype — Gemini creates an exciting welcome for every destination.</em>
</p>

<p align="center">
  <img src="assets/screenshots/04_voting_ui.png" alt="Voting UI" width="80%" />
  <br /><em>🗳️ Vote on Activities — Select your must-dos and set your overarching travel vibe.</em>
</p>

<p align="center">
  <img src="assets/screenshots/05_final_itinerary.png" alt="Final Itinerary" width="80%" />
  <br /><em>📅 The Perfect Itinerary — Day-by-day schedule with hotels, transit, and Google Maps link.</em>
</p>

---

## ⚡ Key Features

| Feature | Description |
|---|---|
| 🤖 **AI-Powered Scouting** | Tavily web search + Gemini curation finds the best attractions, restaurants, and hidden gems for any destination |
| 🗳️ **Democratic Voting** | Share a unique Trip ID with your group — everyone votes on their favorite picks |
| 🗺️ **TSP Route Optimization** | OSRM-powered Traveling Salesperson solver eliminates zigzag itineraries |
| 🏨 **Real Hotel Search** | Amadeus API finds budget-compliant accommodation near your destination |
| 🛺 **Smart Transit Planning** | Auto-calculates walk vs. rickshaw vs. cab based on distance and daily budget |
| 📍 **Google Maps Integration** | One-click master navigation URL covering every stop in optimized order |
| 🎉 **Hype Engine** | Gemini generates exciting destination descriptions to get the group hyped |
| 💰 **Budget Enforcement** | Dynamic constraints scale places, restaurants, and costs to your per-person budget |

---

## 🏗️ System Architecture

```
                            ┌───────────────────────────────┐
                            │      👤 GROUP LEADER           │
                            │   Inputs Dest, Dates, Budget   │
                            └───────────────┬───────────────┘
                                            │
              ╔═════════════════════════════════════════════════════════╗
              ║           PHASE 1: PLANNING & SCOUTING                 ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                        ║
              ║  ┌──────────────┐    ┌──────────────┐                  ║
              ║  │ 🚀 Launch    │───▶│ 🧮 Calculate  │                  ║
              ║  │  AI Scout    │    │  Constraints  │                  ║
              ║  │  (Streamlit) │    │  (Math Logic) │                  ║
              ║  └──────────────┘    └──────┬───────┘                  ║
              ║                             │                          ║
              ║                    ┌────────▼────────┐                 ║
              ║                    │ 🔍 Tavily API    │                 ║
              ║                    │ Search Attractions│                ║
              ║                    │ & Hidden Gems    │                 ║
              ║                    └────────┬────────┘                 ║
              ║                             │                          ║
              ║                    ┌────────▼────────┐                 ║
              ║                    │ 🤖 Gemini 2.5    │                 ║
              ║                    │ Curate, Score &  │                 ║
              ║                    │ Format JSON      │                 ║
              ║                    └────────┬────────┘                 ║
              ║                             │                          ║
              ║                    ┌────────▼────────┐                 ║
              ║                    │ 💾 Supabase      │                 ║
              ║                    │ Save trips &     │                 ║
              ║                    │ places           │                 ║
              ║                    └────────┬────────┘                 ║
              ╚═════════════════════════════╪═══════════════════════════╝
                                            │
                                    Shares Trip UUID
                                            │
              ╔═════════════════════════════════════════════════════════╗
              ║           PHASE 2: DEMOCRATIC CONSENSUS                ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                        ║
              ║  ┌──────────────┐    ┌──────────────┐                  ║
              ║  │ 🎟️ Member    │───▶│ 🎉 Hype Engine│                  ║
              ║  │  Enters UUID │    │   (Gemini)    │                  ║
              ║  └──────────────┘    └──────┬───────┘                  ║
              ║                             │                          ║
              ║                    ┌────────▼────────┐                 ║
              ║                    │ 📋 Fetch Curated │                 ║
              ║                    │   Places (DB)    │                 ║
              ║                    └────────┬────────┘                 ║
              ║                             │                          ║
              ║                    ┌────────▼────────┐                 ║
              ║                    │ 🗳️ User Votes    │                 ║
              ║                    │ & Selects Vibe   │                 ║
              ║                    └────────┬────────┘                 ║
              ║                             │                          ║
              ║                    ┌────────▼────────┐                 ║
              ║                    │ 💾 Supabase      │                 ║
              ║                    │ Save members &   │                 ║
              ║                    │ votes            │                 ║
              ║                    └────────┬────────┘                 ║
              ╚═════════════════════════════╪═══════════════════════════╝
                                            │
                                   Click "View Plan"
                                            │
              ╔═════════════════════════════════════════════════════════╗
              ║        PHASE 3: REFLECTION & ORCHESTRATION             ║
              ╠═════════════════════════════════════════════════════════╣
              ║                                                        ║
              ║  ┌──────────────┐    ┌──────────────┐                  ║
              ║  │ 📅 Trigger   │───▶│ 📥 Fetch All  │                  ║
              ║  │  Final Plan  │    │  Trip Data    │                  ║
              ║  └──────────────┘    └──────┬───────┘                  ║
              ║                             │                          ║
              ║                    ┌────────▼────────┐                 ║
              ║                    │ 🧮 Tally Votes   │                 ║
              ║                    │ & Filter Top N   │                 ║
              ║                    └───┬────────┬────┘                 ║
              ║                        │        │                      ║
              ║           ┌────────────▼─┐  ┌───▼────────────┐        ║
              ║           │ 🌍 Geopy /   │  │ 🏨 Amadeus     │        ║
              ║           │ Photon       │  │ Hotel API      │        ║
              ║           │ (Geocoding)  │  │ (Budget Filter)│        ║
              ║           └──────┬───────┘  └───┬────────────┘        ║
              ║                  │              │                      ║
              ║           ┌──────▼───────┐      │                      ║
              ║           │ 🗺️ OSRM      │      │                      ║
              ║           │ Solve TSP    │      │                      ║
              ║           └──────┬───────┘      │                      ║
              ║                  │              │                      ║
              ║           ┌──────▼───────┐      │                      ║
              ║           │ 🛺 Transport  │      │                      ║
              ║           │ Walk vs Uber │      │                      ║
              ║           └──────┬───────┘      │                      ║
              ║                  │              │                      ║
              ║                  └──────┬───────┘                      ║
              ║                         │                              ║
              ║                ┌────────▼────────┐                     ║
              ║                │ 🤖 Gemini 2.5    │                     ║
              ║                │ Build Day-by-Day │                     ║
              ║                │ Schedule (JSON)  │                     ║
              ║                └────────┬────────┘                     ║
              ║                         │                              ║
              ║                ┌────────▼────────┐                     ║
              ║                │ 💾 Supabase      │                     ║
              ║                │ Save itinerary   │                     ║
              ║                └────────┬────────┘                     ║
              ╚═════════════════════════╪═══════════════════════════════╝
                                        │
                     ┌──────────────────┼──────────────────┐
                     │                  │                  │
              ┌──────▼──────┐  ┌────────▼──────┐  ┌───────▼──────┐
              │ 📅 Day-by-  │  │ 📍 Google Maps│  │ 🏨 Hotel     │
              │ Day Timeline│  │ Optimized URL │  │ Options      │
              └──────┬──────┘  └────────┬──────┘  └───────┬──────┘
                     │                  │                  │
                     └──────────────────┼──────────────────┘
                                        │
                            ┌───────────▼───────────┐
                            │  ✨ PERFECT TRIP!  ✨   │
                            └───────────────────────┘
```

> 🔗 **[View the full interactive architecture diagram on Mermaid Live →](https://mermaid.live/edit#pako:eNq1Vw1v2jgY_ivvZdpKd9AWkn5Ft0k0BMrUFgRh0x2cTiYxYNWJIyfpyq777_faDpQyept6u1Rq_BG_H8_7-LH5YoUiopZrzbj4HC6IzCFoTRLA5_VrGOZLzpI5eJxkGc3MeKg6LTqDgsGMce6-bredC-eimuVS3FL31Ww2K9u1zyzKF24jva-Gggup57asRNPSiu177TP_h6zUffW3ZYjzuLTkNM6O284L4yHpKq1zr3F6cfRCM1zMWbjG5_7s6Ojlmc1YQnhpyz-v-yf287bsraDWtazVajAa-gPwb4LB46prpkYZlZVKR4oihStKIir3913XxeLWau8fukla5Bm0aJZXoUVymlXhoojmNH-AYSiKPJBsPqdyw9G7H37WS_qXzaEPdReCSx-GXm8UQLODcb7YZlZM55KkC-gvSEaV5T4nSaK4_MbEjU3zqXo2MxlfkSIJF9DsmuE_12CY_jXJF48rt2yoyfHE8ggPC45oQWuZkBiJ4IkEy0RYkme_TeXh-4BIxFBFFdIM3kH9CH4FG95CpUWWGdSgvj-xlGvDI-U9IHeML3e5NjPo1zSg2e9qJ0NKpMokR89hzjAEzP6SRRFNoEPjzHhQhFf2cYQlTKexy8nGNHoyPWgcHEMbabrQ_rxCYs5VBYXEl3-v_cKAKLSV77aQMcnhw7B3U2aHe1b5bl3Ud_nE4XFlYg2LlExVHZGAumGyI3cU9nLJ0mwPbe-lGsu9ibWvLEdTY4Ym0c_gZsOFln_d8wbNoOvBx17Qvem82CqmBbUD3F1DFFws_2jUbT3ANY2nVPpJLssi76QyBqK4RJOsyB6B2lg7Nm3ADpXG9gaFL5cp9ZM5S-guvB9nscSqA6YHFVPvfQ18hyZUFRo-UR6KmMJHNqVP69mmebgw5N7lZ2N6rNtgqBOVG8IUUFv6KBR5Rt1dZlZzY6VhMKSchqhV5Z56o8PaSL110djNscb3OBZrRA3L7kT-v5HMNgLYHHiX3cD3_qsIYmaGZh5n4S3CQT9rGXyAJsoCyxGttXo_yzeMaUBnClnUDwSgh0upkjLVf0Rx2-K4fENbn13K7UYpdM2bnG8xAkdKOuDqtFpWsqrq_IQTAeHPCSEvdRDfZplSHcZxK0AgUrjRVb1BwdUy-xbsbZXtUKFuRLsVUE9p9RPpEg4RIpEjKiu9NbHTeyV6VyQ_vMI5TwgZIQYYylO57Q0H19_Y1jPNGE_hYufGUYvQv3rBwJxi5RY1dBUc-RpIZK2-tw0Jp1mK1MVA-lJMOY2fBoGfJlkq5E7FX08qRFftTXfqmINPhN_CHQqNEh21cSJAb-aOcNhiWU6SkG6j7Ik4ZXwnymX26LNswSXWkT-CzJKoNF9TZjgjSW6-2UL4X5yUU6qUeGJj4EgYvOQgTZTMZTmGqXRAOzSm8XgeYvqYncKdYldDwrDSYv4tiZSZ9Z54_jhdf_LckYpVi9MV6FRiUd3VKdpwFih6uBujgtPt49TeLXX296SOIaVQ3OXyLwwr_vlC1-7eNK8AL3j90cuFbQs7nfKoW94g9N4wI6Xer3hkBu1NscNVY1SC2nRZwxcELFYbh-K4ylrfu1cfNsbXJFM60hFizilckxRJP7j65kN7bAjbS82VC_cAXk2WG9-tE8eTPFHKilu1V-Tp6uKFUaFsoUv939aB-0lUqfSpnKmElTzC6hiOftEXdm3bqlpzySLLzWVBq1aMfCaqa31RlicWcj1GrrjYjIi8nViT5CuuSUnyhxDxahn-FpgvLHdGeIa9Io3QS4sRPBYeP0EmUOmJIskt1zk61jYs94t1b7n10_MD5-zsFIdPHefYaVStpeXW6if2gXPu1O3GuY2_h04c-2vV-lu7rR849vFZ4-jkFB_bOak3vv4DCQhdaA)**

### 🧩 Tech Stack Breakdown

| Layer | Technology | Role |
|---|---|---|
| **Frontend** | Streamlit | Interactive 3-page web UI |
| **LLM** | Google Gemini 2.5 Flash | Place curation, hype generation, itinerary scheduling |
| **LLM Framework** | LangChain + LangGraph | Structured LLM invocation |
| **Web Search** | Tavily API | Real-time destination research (advanced depth) |
| **Database** | Supabase (PostgreSQL) | Persistent storage for trips, places, votes, members, itineraries |
| **Hotels** | Amadeus API | Real hotel search by geocoordinates and budget filtering |
| **Routing** | OSRM (Open Source) | Driving distance matrix + Greedy Nearest-Neighbor TSP solver |
| **Geocoding** | Geopy (Nominatim + Photon) | Dual-engine coordinate resolution with fuzzy fallback |
| **Maps** | Google Maps Directions URL | One-click optimized multi-stop navigation |

---

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:

- **Python 3.13+** — [Download](https://www.python.org/downloads/)
- **uv** (recommended) or **pip** — [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Git** — [Download](https://git-scm.com/)
- A **Supabase** project — [Create one free](https://supabase.com/)
- API keys for **Google AI**, **Tavily**, and **Amadeus** (see Configuration below)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/githarshking/trip-planner-ai.git
cd trip-planner-ai

# 2. Create a virtual environment & install dependencies
uv sync
# --- OR using pip ---
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
```

### ⚙️ Configuration

Create a `.env` file in the project root with the following keys:

```env
# Supabase (https://supabase.com → Project Settings → API)
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-supabase-service-role-key"

# Google Gemini (https://aistudio.google.com/apikey)
GOOGLE_API_KEY="your-google-api-key"

# Tavily Search (https://tavily.com)
TAVILY_API_KEY="tvly-your-tavily-key"

# Amadeus Hotel Search (https://developers.amadeus.com)
AMADEUS_API_KEY="your-amadeus-api-key"
AMADEUS_API_SECRET="your-amadeus-api-secret"
```

### 🗄️ Database Setup

Create the following tables in your Supabase project (SQL Editor):

```sql
-- Trips table
CREATE TABLE trips (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  destination TEXT NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  budget_limit INTEGER NOT NULL,
  status TEXT DEFAULT 'VOTING',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Places table (AI-scouted locations)
CREATE TABLE places (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  category TEXT DEFAULT 'Activity',
  estimated_cost INTEGER DEFAULT 1,
  rating FLOAT DEFAULT 4.5,
  metadata JSONB DEFAULT '{}'
);

-- Members table
CREATE TABLE members (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Votes table
CREATE TABLE votes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  place_id UUID REFERENCES places(id) ON DELETE CASCADE,
  member_id UUID REFERENCES members(id) ON DELETE CASCADE,
  vote_value INTEGER DEFAULT 1,
  comment TEXT,
  UNIQUE(place_id, member_id)
);

-- Itinerary Items table
CREATE TABLE itinerary_items (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  trip_id UUID REFERENCES trips(id) ON DELETE CASCADE,
  day_number INTEGER NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME DEFAULT '00:00:00',
  notes TEXT
);
```

### ▶️ Running Locally

```bash
# From the project root directory
streamlit run app/main.py
```

The app will open at **`http://localhost:8501`** 🎉

---

## 📖 Usage

### Step 1: Create a Trip (Leader)
1. Navigate to **🌍 Create New Trip**
2. Enter the destination, travel dates, and per-person budget (₹ INR)
3. Click **🚀 Launch AI Scout** — the AI researches and curates places
4. **Copy the generated Trip ID** and share it with your group

### Step 2: Vote (All Members)
1. Navigate to **🗳️ Vote on Trip**
2. Paste the Trip ID and enter your name
3. Browse AI-curated places with ratings, costs, and Google search links
4. Check the places you want, select your travel vibe, and submit

### Step 3: Generate the Itinerary (Anyone)
1. Navigate to **📅 View Final Plan**
2. Enter the Trip ID and click **Generate / View Plan**
3. The Architect Agent will:
   - Tally votes and pick the top-voted places
   - Solve the TSP for an optimized route
   - Find budget-compliant hotels via Amadeus
   - Generate a full day-by-day schedule
4. Click the **📍 Google Maps** button for turn-by-turn navigation!

---

## 🎯 Target Audience

- **👫 Friend Groups & Millennials/Gen Z** — Organize weekend getaways or backpacking trips without arguing over where to eat or what to do
- **🎓 College Students** — Strict budget-enforcement features ensure the trip doesn't exceed financial limits
- **👨‍👩‍👧‍👦 Families** — Balance activities catering to different vibes (mixing "Extremely Chill" relaxation with "Attractions")
- **😮‍💨 The "Designated Planner"** — Outsource the research and logistics math to an AI and stop carrying the mental load

---

## 📁 Project Structure

```
trip-planner-ai/
├── app/
│   ├── main.py                 # Streamlit UI (entry point)
│   ├── agents/
│   │   ├── scout.py            # Scout Agent (Tavily + Gemini curation)
│   │   └── architect.py        # Architect Agent (votes → itinerary)
│   ├── database/
│   │   └── connection.py       # Supabase client singleton
│   └── utils/
│       ├── routing.py          # Geocoding + OSRM matrix + TSP solver
│       ├── accommodations.py   # Amadeus hotel search
│       ├── transport.py        # Transit mode & cost calculator
│       └── maps.py             # Google Maps URL generator
├── test_scout.py               # Scout Agent integration test
├── test_routing.py             # Route optimization test
├── pyproject.toml              # Project metadata & dependencies
├── .env                        # API keys (not committed)
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome and appreciated! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### 💡 Ideas for Contribution
- 🌐 Multi-language support
- 📊 Analytics dashboard for voting patterns
- 🔔 Real-time notifications when someone votes
- 🗓️ Calendar export (`.ics`) for the final itinerary
- 🧪 Expanded test coverage

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 githarshking

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

<p align="center">
  Built with ❤️ and a lot of ☕ by <a href="https://github.com/githarshking">githarshking</a>
</p>
