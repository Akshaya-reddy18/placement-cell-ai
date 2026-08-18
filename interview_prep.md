# Placement Cell AI — Complete AI Engineer Interview Preparation

This document is your master defense script for a ₹9–10 LPA AI Engineer interview. It is strictly based on the **ACTUAL** codebase of your Placement Cell AI project. Do not deviate from these facts during your interview.

---

## PART 1 — PROJECT MASTER EXPLANATION

### 30-Second Version (Elevator Pitch)
"I built an agentic AI platform to automate career placement. It uses a FastAPI and LangGraph backend to parse student resumes, extract a structured skill graph using Gemini, and then semantically matches those skills against live job listings stored in a Supabase vector database. The system then provides personalized ATS scoring, skill gap analysis, and adaptive mock interviews, all orchestrated by autonomous AI agents."

### 1-Minute Version
"My project is an AI-driven placement platform that acts as a personalized career advisor. It solves the problem of generic job boards by building a deep understanding of a student's actual capabilities. 
When a user uploads a resume, a background LangGraph pipeline triggers. First, it extracts a normalized skill graph using Gemini. Then, it scrapes live jobs from SerpAPI, embeds them into pgvector, and performs semantic search (Job RAG) to find highly relevant roles. Finally, specialized AI agents generate a tailored ATS score, pinpoint exact skill gaps, and conduct a dynamic mock interview. The entire system is secured via Supabase JWT authentication and Row Level Security."

### 2-Minute Version (Standard "Tell me about your project")
"I developed the Placement Cell AI to bridge the gap between student resumes and industry requirements using Agentic workflows. 
**The Problem:** Standard job portals rely on keyword matching, leading to poor recommendations and zero actionable feedback for freshers.
**The Architecture:** I built the backend in Python using FastAPI, backed by PostgreSQL and Supabase for strict data isolation. 
**The AI Pipeline:** I orchestrated a multi-agent system using LangGraph. Instead of a brittle sequential script, I have distinct nodes: a Profile Agent, Job Match Agent, ATS Agent, Skill Gap Agent, and Career Strategy Agent.
**The RAG Implementation:** A key feature is semantic job matching. Instead of naive resume RAG, I extract a structured JSON 'Skill Graph' from the resume using Gemini. I embed this graph and perform a vector similarity search against a pgvector database of live jobs scraped via SerpAPI. This ensures we match on conceptual capability, not just keywords.
**The Result:** The student gets a dashboard with personalized job rankings, an objective ATS score, a roadmap for skill gaps, and an adaptive mock interview that challenges them on their specific weak points."

---

## PART 2 — COMPLETE ARCHITECTURE

### Actual Runtime Flow
1. **Authentication:** User logs in via Supabase Auth (JWT).
2. **Onboarding:** Frontend sends career goals and preferences. Backend links `auth.users.id` to `students.user_id`.
3. **Resume Upload:** User uploads PDF. FastAPI extracts text via `PyMuPDF` in-memory.
4. **Agent Orchestration (LangGraph):** FastAPI triggers `run_placement_analysis` as a `BackgroundTask`.
5. **Profile Agent:** Sends raw resume text to Gemini. Outputs a structured JSON `skill_graph`.
6. **Job Match Agent:** Scrapes live jobs via SerpAPI. Creates embeddings. Performs pgvector semantic search (Job RAG) using the `skill_graph`. Ranks jobs using Gemini.
7. **ATS / Skill Gap / Career Agents:** Run sequentially using the parsed profile to generate persistent feedback.
8. **Dashboard:** React frontend fetches the personalized, DB-persisted JSON results.

### Interviewer-Friendly Diagram (Whiteboard this!)
```text
[ React UI ] --(JWT)--> [ FastAPI Backend ]
                              |
                     [ Supabase Postgres ] (RLS Secured)
                              |
                      [ BackgroundTask ]
                              |
                      [ LangGraph State ]
                      /       |         \
         [Profile Agent] [Job Agent]  [ATS/Gap Agents]
               |              |              |
           (Gemini)     (pgvector RAG)   (Gemini)
               |              |              |
         Skill Graph     Scrape & Match   Feedback JSON
```

---

## PART 3 — TECHNOLOGY STACK DEEP DIVE

* **Python & FastAPI:** Chosen for native AI/Data ecosystem support and async performance. Better than Flask/Django for high-throughput, async LLM API calls.
* **Supabase & PostgreSQL (pgvector):** Chosen because it provides a unified relational + vector database with built-in JWT authentication and Row Level Security. Avoids the complexity of managing a separate Pinecone/Milvus cluster.
* **LangGraph:** Chosen over vanilla LangChain or sequential scripts because it allows stateful, resilient multi-agent orchestration. If the ATS agent fails, the graph state is preserved.
* **Gemini (Google GenAI):** Chosen for its massive context window and cost-effective structured JSON output capabilities.
* **PyMuPDF (fitz):** Chosen over PyPDF2 for superior text extraction accuracy from complex resume layouts.

---

## PART 4 — AUTHENTICATION & SECURITY

**Q: How does the backend identify the student securely?**
"The React frontend sends a Supabase JWT in the `Authorization: Bearer` header. The FastAPI backend validates this token natively via `client.auth.get_user()`. We NEVER trust a `student_id` passed in the request body. We extract the `auth.users.id`, map it to our `students` table, and explicitly scope all database queries to that verified ID."

**Q: How does User A get prevented from accessing User B's data?**
"Two layers. First, the backend API explicitly enforces the token ID. Second, the Database layer uses Supabase Row Level Security (RLS). Policies like `USING (student_id IN (SELECT id FROM students WHERE user_id = auth.uid()))` strictly drop any unauthorized SQL execution at the Postgres engine level."

**Q: Why does the backend use a `service_role` key?**
"Background tasks (like LangGraph agents) run asynchronously after the HTTP request finishes. The `service_role` key bypasses RLS, allowing the agents to write analysis results to the database without needing the user's active JWT session. This key is stored securely in backend environment variables and NEVER exposed to the frontend."

---

## PART 5 — THE RESUME PIPELINE

**Actual Implementation:** PDF → `PyMuPDF` text → Gemini `profile_agent` → JSON `skill_graph` → DB.

**Q: Why didn't you directly use the resume text for job matching?**
"Because raw resumes are incredibly noisy. They contain addresses, irrelevant hobbies, and inconsistent formatting. By using an LLM to extract a structured `skill_graph` first (Entity Extraction), I normalize the data into a pure capability matrix. This vastly improves the signal-to-noise ratio for downstream semantic search."

**Q: What if the resume is badly formatted?**
"I used `PyMuPDF`, which is highly resilient at block-text extraction. If text extraction fails completely (e.g., an image-only PDF), the FastAPI route explicitly catches this and throws a 422 error before invoking the AI, preventing expensive garbage-in-garbage-out API calls."

---

## PART 6 — RAG (RETRIEVAL-AUGMENTED GENERATION)

**⚠️ CRITICAL DISTINCTION:** You built **Job RAG**, NOT Resume RAG.

**Q: Explain your RAG implementation.**
"My system uses Retrieval-Augmented Generation to find matching jobs. 
1. **Embedding:** I take the student's extracted `skill_graph` and embed it using Gemini's embedding model.
2. **Storage:** Live jobs scraped from SerpAPI are embedded and stored in PostgreSQL using the `pgvector` extension.
3. **Retrieval:** I use cosine similarity (`<=>`) in a Postgres RPC function to retrieve the top 15 most semantically similar jobs.
4. **Generation:** Those 15 retrieved jobs are passed as context to the `job_match_agent` (Gemini), which reasons over them and outputs a final personalized ranking and match justification."

**Q: Why not send all scraped jobs directly to Gemini?**
"Context window limits and cost. Sending 100+ job descriptions to an LLM is slow and expensive. RAG acts as a highly efficient semantic filter, allowing me to pass only the top 15 most relevant candidates to the LLM for heavy reasoning."

---

## PART 7 — LANGGRAPH & AGENTIC AI

**Q: What makes this project 'Agentic'?**
"It's agentic because the workflow is decentralized and state-driven. Instead of a monolithic function, I have discrete nodes (Profile Agent, ATS Agent, Career Agent). They all subscribe to a shared `AgentState`. If a task requires external data (like the Job Match Agent needing SerpAPI), it autonomously triggers that tool, mutates the global state, and passes control to the next node in the graph."

**Q: Why LangGraph instead of normal Python functions?**
"State persistence and fault tolerance. LangGraph maintains an immutable state log. If the ATS Agent fails due to an API timeout, the graph knows exactly where it stopped. The `skill_graph` generated by the Profile Agent isn't lost; the graph can resume seamlessly."

---

## PART 8 — JOB FETCHING SYSTEM

**Actual Implementation:** `job_match_agent` → `scrape_jobs_serpapi` → JSON → Embedding → Semantic Search.

**Q: How do you prevent duplicate jobs?**
"Before saving to the database or embedding, the scraper aggregates results and deduplicates them using a composite hash of the `title` and `company`. The Supabase DB also enforces a UNIQUE constraint on the `url`."

**Q: How do you know the job URL is legitimate?**
"During my initial audits, I found the API occasionally returned Google search fallback URLs. I implemented explicit backend filtering to discard any URL containing `google.com/search`, ensuring the UI only renders direct application links."

---

## PART 9 — PERSONALIZATION ENGINE

**Q: How does personalization actually work?**
"It's a multi-stage funnel. 
First, Hard Filters: The backend filters the SQL query based on the user's explicitly selected work mode and experience level. 
Second, Semantic Filter (RAG): `pgvector` retrieves jobs conceptually similar to the student's skill graph. 
Third, LLM Scoring: The `job_match_agent` receives the filtered jobs and mathematically scores them (Max 100) by calculating the intersection of the student's skill set, the job requirements, and applying heavy penalties if a fresher applies to a senior role."

---

## PART 10 — DEBUGGING & ERROR HANDLING (Real Scenarios!)

**Q: Tell me about a difficult bug you solved in this project.**
"I had a critical pipeline failure where the LangGraph background task wouldn't start. The logs showed a Supabase exception: `column resume_text of relation student_profiles does not exist`. 
**Diagnosis:** I traced the API route and found the code was attempting to upsert the raw resume text into the `student_profiles` table, but the database schema actually stored `resume_text` in the `students` table. 
**Fix:** I audited the schema, removed the invalid dictionary key from the `student_profiles` upsert, and ensured it was only updated via `.update().eq('id', student_id)` on the `students` table. This instantly unblocked the entire AI pipeline."

---

## PART 11 — PERFORMANCE & SCALABILITY

**Q: How would you scale this to 100,000 users?**
1. **Asynchronous Queues:** I would move the `BackgroundTasks` to **Celery + Redis** to distribute the heavy LangGraph execution across multiple worker nodes.
2. **Vector Indexing:** I would optimize `pgvector` by adjusting the `ivfflat` index `lists` parameter based on row count to keep cosine similarity lookups under 50ms.
3. **Job Caching:** Instead of scraping SerpAPI per user, I would run a cron job to scrape and embed jobs globally into the `jobs` table every 6 hours. The user's RAG query would then only search our local, pre-embedded database, drastically reducing API latency and costs.

---

## PART 12 — PROJECT CHALLENGE QUESTIONS (DEFENSE)

**"Why use an LLM for skill extraction instead of regex or NLP libraries like spaCy?"**
"Resumes have infinite formatting variations. A candidate might write 'Proficient in creating RESTful APIs using Python and Django'. Regex will miss that if it's strictly looking for 'Backend'. An LLM understands semantic context and can accurately deduce that the candidate possesses 'Python', 'Django', and 'API Design' skills, normalizing them into a predictable JSON structure."

**"Is your ATS score an actual industry-standard ATS?"**
"No, and I'm transparent about that. Proprietary ATS systems like Taleo use closed-source parsing algorithms. My system is an *ATS Simulator*. It uses an LLM to evaluate the resume against standard industry heuristics (keyword density, action verbs, formatting logic) to give the student directional feedback on how a real ATS *might* score them."

**"How do you prevent the LLM from hallucinating an evaluation in the Mock Interview?"**
"I use strict Prompt Engineering. I provide the LLM with the exact question asked and the user's exact answer. The system prompt forces it to output structured JSON with strict keys (`readiness_score`, `feedback`), and I use a temperature of `0.7` to balance conversational flexibility with analytical determinism."

---

## PART 13 — FOLLOW-UP QUESTION CHAINS (RAG)

**Interviewer:** "What is RAG?"
**You:** "Retrieval-Augmented Generation. It's a technique where you retrieve relevant data from a database and inject it into an LLM's prompt to give it context it wasn't trained on."

**Interviewer:** "Why did you use it?"
**You:** "To match students with live jobs. I can't send 10,000 jobs to Gemini due to context limits. RAG filters those down to the top 15 most relevant."

**Interviewer:** "Why not just fine-tune a model instead?"
**You:** "Fine-tuning is for teaching a model a new *behavior* or *format*, not new *facts*. Live jobs expire and change daily. RAG allows the model to access real-time, dynamic data without expensive retraining."

**Interviewer:** "How do you know the retrieval is relevant?"
**You:** "Because we use vector embeddings. By embedding the student's skill graph and the job descriptions into 768-dimensional space, cosine similarity ensures we retrieve jobs that are conceptually similar, even if the exact keywords differ."

---

## PART 14 — RAPID REVISION CHEAT SHEET

* **DB:** PostgreSQL (Supabase)
* **Vector Ops:** `pgvector`, `ivfflat` index, cosine similarity (`<=>`)
* **Agent Flow:** `profile` -> `job_match` -> `ats` -> `skill_gap` -> `career`
* **Auth Flow:** Supabase JWT -> `auth.get_user()` -> `students.user_id`
* **RAG Flow:** Generate Skill JSON -> Embed -> `pgvector` Search -> Pass top 15 to LLM.
* **Never Say:** "Resume RAG" (Say "Job RAG using extracted skills").
* **Never Say:** "The frontend passes the student ID securely" (Say "The backend extracts the ID from the JWT").

---
*End of Script. Read, internalize the architectural flows, and practice answering the 'Why' questions aloud.*
