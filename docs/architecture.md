\# VoyageMind AI - System Architecture



\## Overview



VoyageMind AI is a full-stack AI travel planning platform that combines a React frontend, FastAPI backend, LangGraph-based AI workflow, machine-learning recommendations, external APIs, vector-based memory retrieval, and PostgreSQL persistence.



The production deployment follows:



```text

React + Vite

&#x20;     |

&#x20;     | HTTPS / REST API

&#x20;     v

Vercel

&#x20;     |

&#x20;     v

FastAPI Backend

&#x20;     |

&#x20;     +-------------------+

&#x20;     |                   |

&#x20;     v                   v

AI Planning Workflow   PostgreSQL

&#x20;     |

&#x20;     +-----------------------------+

&#x20;     |             |               |

&#x20;     v             v               v

&#x20;  Weather        Places         Memory

&#x20;   Data          Data         Retrieval

&#x20;     |             |               |

&#x20;     v             v               v

&#x20;External        Geoapify        ChromaDB

&#x20;  APIs            APIs

Production Architecture

&#x20;                        USER

&#x20;                         |

&#x20;                         v

&#x20;             +----------------------+

&#x20;             |   React + Vite       |

&#x20;             |     Frontend         |

&#x20;             +----------+-----------+

&#x20;                        |

&#x20;                        | HTTPS REST API

&#x20;                        v

&#x20;             +----------------------+

&#x20;             |    FastAPI Backend   |

&#x20;             |                      |

&#x20;             | Authentication       |

&#x20;             | Trip Management      |

&#x20;             | Favorites             |

&#x20;             | Recommendations      |

&#x20;             | Trip Planning         |

&#x20;             +----------+-----------+

&#x20;                        |

&#x20;         +--------------+---------------+

&#x20;         |              |               |

&#x20;         v              v               v

&#x20;  +-------------+ +-------------+ +-------------+

&#x20;  | LangGraph   | | ML Engine   | | PostgreSQL  |

&#x20;  | AI Workflow | | Random      | | Database    |

&#x20;  |             | | Forest      | |             |

&#x20;  +------+------+ +-------------+ +-------------+

&#x20;         |

&#x20;         |

&#x20;   +-----+-----------------------------+

&#x20;   |                 |                 |

&#x20;   v                 v                 v

+---------+      +----------+      +-----------+

| Weather |      | Geoapify |      | ChromaDB  |

| APIs    |      | Places   |      | Memory    |

+---------+      +----------+      +-----------+

Frontend Layer



The frontend is implemented using:



React

Vite

JavaScript

Axios

Tailwind CSS



The frontend is responsible for:



User authentication

Travel input collection

Trip planning requests

Recommendation requests

Displaying generated itineraries

Saving trips

Viewing saved trips

Managing favorites

Handling authentication tokens



The frontend communicates with the backend through REST APIs.



Production frontend hosting:



Vercel

Backend Layer



The backend is implemented using:



Python

FastAPI

SQLAlchemy

Pydantic

Uvicorn



The backend provides APIs for:



Authentication

Trips

Favorites

Recommendations

Trip Planning

User Profile



The backend also coordinates communication between the frontend, AI workflow, machine-learning recommendation system, external APIs, vector retrieval, and PostgreSQL.



Production backend hosting:



Render

Authentication Flow



VoyageMind uses JWT-based authentication.



User

&#x20;|

&#x20;| Login credentials

&#x20;v

POST /auth/login

&#x20;|

&#x20;v

FastAPI

&#x20;|

&#x20;| Verify password

&#x20;v

JWT Token

&#x20;|

&#x20;v

Frontend

&#x20;|

&#x20;| Authorization: Bearer <token>

&#x20;v

Protected API Endpoints



The frontend stores the access token locally and attaches it to authenticated API requests.



Protected endpoints use the authenticated user to scope user-specific data.



AI Planning Workflow



The trip-planning workflow combines multiple data sources before generating the final itinerary.



User Travel Request

&#x20;       |

&#x20;       v

Input Validation

&#x20;       |

&#x20;       +--------------------+

&#x20;       |                    |

&#x20;       v                    v

Weather Retrieval       Place Discovery

&#x20;       |                    |

&#x20;       |              +-----+-----+

&#x20;       |              |     |     |

&#x20;       |              v     v     v

&#x20;       |           Nature Shopping Adventure

&#x20;       |

&#x20;       +--------------------+

&#x20;                |

&#x20;                v

&#x20;         Memory Retrieval

&#x20;                |

&#x20;                v

&#x20;      Recommendation Engine

&#x20;                |

&#x20;                v

&#x20;       AI Itinerary Planning

&#x20;                |

&#x20;                v

&#x20;         Final Trip Plan

External API Integration



VoyageMind integrates external services for travel-related information.



Weather



Weather information is retrieved during trip planning and can be incorporated into the generated itinerary.



Geographic / Places Data



Geoapify is used to discover relevant places and attractions based on user interests.



Examples include:



Nature

Shopping

Adventure

Architecture

History

Museums

Nightlife

Currency



Currency exchange information is used by the recommendation workflow to normalize budget-related calculations across currencies.



Machine Learning Layer



VoyageMind includes a machine-learning recommendation component based on a Random Forest Regressor.



The workflow is:



User Inputs

&#x20;    |

&#x20;    v

Feature Preparation

&#x20;    |

&#x20;    v

Machine Learning Model

&#x20;    |

&#x20;    v

Recommendation Scores

&#x20;    |

&#x20;    v

Recommended Destinations



The recommendation workflow accepts travel-related parameters such as:



Budget

Duration

Interests

Currency

Walking preference



During production testing, budget and interest changes produced observable recommendation differences.



Duration values were correctly transmitted from the frontend, although duration changes did not consistently produce visibly different recommendation results. This is documented as a current model/recommendation limitation.



RAG and Memory Layer



VoyageMind uses vector-based retrieval for user memory.



User Preferences

&#x20;      |

&#x20;      v

Memory Storage

&#x20;      |

&#x20;      v

Vector Representation

&#x20;      |

&#x20;      v

ChromaDB

&#x20;      |

&#x20;      v

Relevant Memory Retrieval

&#x20;      |

&#x20;      v

AI Planning Workflow



Retrieved memories can provide additional context for personalized travel planning.



Database Layer



PostgreSQL is used for persistent application data.



The main entities are:



users

trips

favorites



Relationships:



users

&#x20; |

&#x20; +------< trips

&#x20; |

&#x20; +------< favorites



User-owned trips and favorites are associated with the authenticated user through foreign keys.



Data Flow



A typical trip-generation request follows this flow:



1\. User enters travel requirements

&#x20;                |

&#x20;                v

2\. React frontend validates inputs

&#x20;                |

&#x20;                v

3\. Axios sends REST request

&#x20;                |

&#x20;                v

4\. FastAPI receives request

&#x20;                |

&#x20;                v

5\. Authentication is validated

&#x20;                |

&#x20;                v

6\. AI planning workflow starts

&#x20;                |

&#x20;       +--------+--------+

&#x20;       |        |        |

&#x20;       v        v        v

&#x20;    Weather  Places   Memory

&#x20;       |        |        |

&#x20;       +--------+--------+

&#x20;                |

&#x20;                v

7\. Recommendation processing

&#x20;                |

&#x20;                v

8\. Itinerary generation

&#x20;                |

&#x20;                v

9\. Final response returned

&#x20;                |

&#x20;                v

10\. User can save journey

&#x20;                |

&#x20;                v

11\. PostgreSQL persistence

Production Deployment



The production environment is split into three primary services.



+---------------------------+

| Vercel                    |

| React Frontend            |

+-------------+-------------+

&#x20;             |

&#x20;             | HTTPS

&#x20;             v

+---------------------------+

| Render                    |

| FastAPI Backend           |

+-------------+-------------+

&#x20;             |

&#x20;             |

&#x20;             v

+---------------------------+

| Render PostgreSQL         |

| Application Database      |

+---------------------------+

Security Architecture



Security mechanisms include:



JWT authentication

Password hashing

Protected API endpoints

Environment variables for secrets

.env excluded from Git

Production CORS configuration

User-scoped database queries



Sensitive values such as API keys, JWT secrets, and database credentials are never stored in the repository.



Error Handling and Resilience



The application was tested against several failure scenarios:



Missing destination

Invalid date range

Invalid JWT

Backend/network failure

External API failure

Duplicate favorite interaction



The frontend displays controlled error states instead of exposing raw backend failures to the user.



The places workflow also contains fallback handling for external geographic-data retrieval failures.



Performance Characteristics



Production testing showed:



/recommendations

Approximately 4.15 seconds



/plan-trip

Approximately 53-66 seconds server response



The longer trip-planning latency is expected from the combination of:



AI processing

Multiple workflow components

External API requests

Recommendation processing

Memory retrieval



A Render memory-limit restart was observed during production testing. A subsequent controlled trip-planning request completed successfully.



Current Architecture Limitations



The current implementation has several areas that can be improved:



Trip planning has relatively high latency.

Recommendation duration sensitivity requires further model improvement.

Recommendation inference produces a scikit-learn feature-name warning that can be cleaned up.

Duplicate trip saves are currently possible.

Production frontend contains some verbose debug logging.

Additional caching could reduce repeated external API calls.

Background job processing could improve long-running trip generation.



These are improvement opportunities rather than blockers for the current deployed application.



Future Architecture



Potential future improvements include:



React

&#x20; |

&#x20; v

API Gateway

&#x20; |

&#x20; v

FastAPI

&#x20; |

&#x20; +----------------------+

&#x20; |                      |

&#x20; v                      v

Redis Cache          Task Queue

&#x20;                        |

&#x20;                        v

&#x20;                 AI Planning Workers

&#x20;                        |

&#x20;         +--------------+--------------+

&#x20;         |              |              |

&#x20;         v              v              v

&#x20;      LLMs          External APIs    ML Models

&#x20;         |

&#x20;         v

&#x20;      RAG / Memory

&#x20;         |

&#x20;         v

&#x20;     PostgreSQL



Possible additions:



Redis caching

Background task queues

Streaming responses

Distributed workers

Observability and tracing

Automated evaluation

CI/CD testing

Rate limiting

More advanced recommendation models

