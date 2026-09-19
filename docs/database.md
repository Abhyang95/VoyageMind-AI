\# VoyageMind AI - Database Architecture



\## Overview



VoyageMind AI uses PostgreSQL as the primary relational database for persistent application data.



The database stores:



\- Registered users

\- Saved trips

\- Favorite destinations



The application uses SQLAlchemy as the ORM layer between FastAPI and PostgreSQL.



\---



\# Database Architecture



```text

&#x20;                   PostgreSQL

&#x20;                       |

&#x20;       +---------------+---------------+

&#x20;       |                               |

&#x20;       v                               v

&#x20;     users                         favorites

&#x20;       |

&#x20;       |

&#x20;       v

&#x20;     trips



Entity Relationship Diagram

+---------------------------+

|          users            |

+---------------------------+

| PK id                     |

| username                  |

| email                     |

| password\_hash             |

| created\_at                |

+-------------+-------------+

&#x20;             |

&#x20;             | 1

&#x20;             |

&#x20;       +-----+-----+

&#x20;       |           |

&#x20;       |           |

&#x20;       | N         | N

&#x20;       v           v

+---------------+  +----------------+

|     trips     |  |   favorites    |

+---------------+  +----------------+

| PK id         |  | PK id          |

| FK user\_id    |  | FK user\_id     |

| destination   |  | destination    |

| departure\_date|  | created\_at     |

| return\_date   |  +----------------+

| days          |

| budget        |

| currency      |

| interests     |

| itinerary     |

| created\_at    |

+---------------+   







Users Table



Table name:



users



Purpose:



Stores registered user accounts and authentication-related information.



Column	Type	Nullable	Description

id	INTEGER	No	Primary key

username	VARCHAR(100)	No	Unique username

email	VARCHAR(255)	No	Unique user email

password\_hash	VARCHAR(255)	No	Securely hashed password

created\_at	TIMESTAMP	No	Account creation timestamp

Constraints

PRIMARY KEY

&#x20;   users.id



UNIQUE

&#x20;   users.username



UNIQUE

&#x20;   users.email



The database indexes the primary key, username, and email fields to support efficient lookups.



Trips Table



Table name:



trips



Purpose:



Stores saved travel plans belonging to authenticated users.



Column	Type	Nullable	Description

id	INTEGER	No	Primary key

user\_id	INTEGER	No	Reference to users.id

destination	VARCHAR(255)	No	Trip destination

departure\_date	VARCHAR(50)	Yes	Departure date

return\_date	VARCHAR(50)	Yes	Return date

days	INTEGER	No	Trip duration

budget	DOUBLE PRECISION	No	User travel budget

currency	VARCHAR(3)	No	Budget currency

interests	TEXT	Yes	User travel interests

itinerary	TEXT	Yes	Saved itinerary snapshot

created\_at	TIMESTAMP	No	Trip creation timestamp

Foreign Key

trips.user\_id

&#x20;       |

&#x20;       v

users.id



The foreign key uses:



ON DELETE CASCADE



Therefore, deleting a user also removes the trips belonging to that user.



Favorites Table



Table name:



favorites



Purpose:



Stores destinations that a user has marked as favorites.



Column	Type	Nullable	Description

id	INTEGER	No	Primary key

user\_id	INTEGER	No	Reference to users.id

destination	VARCHAR(255)	No	Favorite destination

created\_at	TIMESTAMP	No	Favorite creation timestamp

Foreign Key

favorites.user\_id

&#x20;       |

&#x20;       v

users.id



The foreign key uses:



ON DELETE CASCADE



Therefore, deleting a user also removes that user's favorites.



Relationship Model



The database follows a one-to-many relationship between users and trips.



One User

&#x20;  |

&#x20;  +---- Trip 1

&#x20;  |

&#x20;  +---- Trip 2

&#x20;  |

&#x20;  +---- Trip 3



Similarly, users can have multiple favorites:



One User

&#x20;  |

&#x20;  +---- Favorite 1

&#x20;  |

&#x20;  +---- Favorite 2

&#x20;  |

&#x20;  +---- Favorite 3



Therefore:



users 1 ---- N trips



users 1 ---- N favorites

Data Persistence Flow



When a user saves a journey:



React Frontend

&#x20;     |

&#x20;     v

POST /trips/save

&#x20;     |

&#x20;     v

FastAPI

&#x20;     |

&#x20;     v

Authenticated User

&#x20;     |

&#x20;     v

SQLAlchemy

&#x20;     |

&#x20;     v

PostgreSQL

&#x20;     |

&#x20;     v

trips table



When a user saves a favorite:



React Frontend

&#x20;     |

&#x20;     v

POST /favorites/

&#x20;     |

&#x20;     v

FastAPI

&#x20;     |

&#x20;     v

Authenticated User

&#x20;     |

&#x20;     v

SQLAlchemy

&#x20;     |

&#x20;     v

PostgreSQL

&#x20;     |

&#x20;     v

favorites table

User Data Isolation



Trip and favorite operations are associated with the authenticated user.



The backend obtains the current user from the JWT authentication system and uses that user identity when querying or modifying persistent data.



Conceptually:



JWT

&#x20;|

&#x20;v

Authenticated User

&#x20;|

&#x20;+----> User's Trips

&#x20;|

&#x20;+----> User's Favorites



This prevents normal authenticated requests from operating on another user's records.



Database Verification



The production PostgreSQL database was verified during deployment.



Verified tables:



users

trips

favorites



Verified foreign-key relationships:



trips.user\_id

&#x20;   -> users.id

&#x20;   ON DELETE CASCADE



favorites.user\_id

&#x20;   -> users.id

&#x20;   ON DELETE CASCADE



Database connectivity was also verified through SQLAlchemy.



Persistence Testing



The persistence layer was tested using the following workflow:



Save Journey

&#x20;    |

&#x20;    v

Get Trips

&#x20;    |

&#x20;    v

Get Individual Trip

&#x20;    |

&#x20;    v

Add Favorite

&#x20;    |

&#x20;    v

Verify Favorite

&#x20;    |

&#x20;    v

Delete Favorite



Additional persistence checks confirmed that saved data remained available after:



Page refresh

Logout

Re-login

Database Technology



The persistence stack consists of:



PostgreSQL

&#x20;    |

&#x20;    v

SQLAlchemy

&#x20;    |

&#x20;    v

FastAPI



SQLAlchemy provides:



ORM-based database access

Model definitions

Session management

Relationship mapping

Foreign-key relationships

Database Security



Database credentials are stored using environment variables.



The repository does not contain:



Database passwords

Production connection strings

API keys

JWT secrets



The .env file is excluded from Git using .gitignore.



Production database credentials are configured through the hosting environment.



Current Database Design Considerations



The current schema is intentionally simple and suitable for the current application.



Potential future improvements include:



Using native PostgreSQL DATE columns for trip dates.

Using NUMERIC instead of floating-point storage for financial values.

Adding additional indexes based on production query patterns.

Adding stronger uniqueness constraints for duplicate saved trips if required.

Separating itinerary JSON into structured relational or JSONB data.

Adding database migrations using Alembic.

Adding audit fields for important data changes.



These improvements are future considerations and are not required for the current deployed version.



Final Database Structure

&#x20;                        PostgreSQL

&#x20;                             |

&#x20;                             v

&#x20;                      +-------------+

&#x20;                      |    users    |

&#x20;                      +------+------+

&#x20;                             |

&#x20;               +-------------+-------------+

&#x20;               |                           |

&#x20;               | 1                         | 1

&#x20;               |                           |

&#x20;               | N                         | N

&#x20;               v                           v

&#x20;       +---------------+           +----------------+

&#x20;       |     trips     |           |   favorites    |

&#x20;       +---------------+           +----------------+

&#x20;       | id            |           | id             |

&#x20;       | user\_id       |           | user\_id        |

&#x20;       | destination   |           | destination    |

&#x20;       | dates         |           | created\_at     |

&#x20;       | days          |           +----------------+

&#x20;       | budget        |

&#x20;       | currency      |

&#x20;       | interests     |

&#x20;       | itinerary     |

&#x20;       | created\_at    |

&#x20;       +---------------+



The database provides persistent storage for the core VoyageMind AI application while maintaining user ownership through foreign-key relationships and authenticated access.

