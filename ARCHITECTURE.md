# ARCHITECTURE.md — LMS e-learning multi-utilisateur

> **Source** : `readme.md` (aucun fichier `api.md` n'a été trouvé dans le workspace — le document de référence utilisé est `readme.md` qui contient les spécifications complètes).  
> **Objectif** : définir une architecture suffisamment précise pour implémenter le projet phase par phase sans refactoring majeur.

---

## Table des matières

1. [Architecture globale du système](#1-architecture-globale-du-système)
2. [Architecture frontend React](#2-architecture-frontend-react)
3. [Architecture backend FastAPI](#3-architecture-backend-fastapi)
4. [Modèle de données PostgreSQL](#4-modèle-de-données-postgresql)
5. [Relations entre les entités](#5-relations-entre-les-entités)
6. [Architecture d'authentification et d'autorisation](#6-architecture-dauthentification-et-dautorisation)
7. [Stratégie d'ownership des cours](#7-stratégie-downership-des-cours)
8. [Architecture Assignment → Enrollment → Progress](#8-architecture-assignment--enrollment--progress)
9. [Architecture de génération automatique des quiz](#9-architecture-de-génération-automatique-des-quiz)
10. [Gestion et stockage des fichiers](#10-gestion-et-stockage-des-fichiers)
11. [API REST proposée](#11-api-rest-proposée)
12. [Architecture Docker](#12-architecture-docker)
13. [Stratégie de tests](#13-stratégie-de-tests)
14. [Stratégie de sécurité](#14-stratégie-de-sécurité)
15. [Arborescence complète du projet](#15-arborescence-complète-du-projet)
16. [Ambiguïtés et contradictions — analyse et résolutions](#16-ambiguïtés-et-contradictions--analyse-et-résolutions)

---

## 1. Architecture globale du système

### 1.1 Vue d'ensemble

```
                         Browser (HTTPS)
                               │
                               ▼
                     ┌─────────────────┐
                     │  Reverse Proxy  │  Nginx (port 80/443)
                     └────────┬────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
              ▼                               ▼
   ┌─────────────────────┐       ┌─────────────────────────┐
   │   React Frontend    │       │    FastAPI Backend       │
   │  (Nginx, port 3000) │       │    (Uvicorn, port 8000)  │
   └─────────────────────┘       └──────────┬──────────────┘
                                            │
                          ┌─────────────────┼──────────────────┐
                          │                 │                  │
                          ▼                 ▼                  ▼
                   ┌────────────┐   ┌──────────────┐  ┌────────────────┐
                   │ PostgreSQL │   │ File Storage │  │  AI Provider   │
                   │  (5432)    │   │ (Docker Vol) │  │ (HTTP externe) │
                   └────────────┘   └──────────────┘  └────────────────┘
```

### 1.2 Principes architecturaux retenus

| Décision | Justification |
|----------|---------------|
| **Monolithe modulaire** (pas de microservices) | Adapté à une équipe réduite ; complexité opérationnelle minimale ; extraction en services possible plus tard sans refactoring des interfaces |
| **Instance unique** (pas de multi-tenancy) | Scope du projet clairement délimité ; évite la complexité de l'isolation par tenant |
| **Frontend SPA** découplé du backend | Déploiements indépendants ; le backend devient réutilisable (mobile, CLI) |
| **PostgreSQL seul** pour la persistance | Pas besoin d'un second moteur de base de données pour le MVP ; PostgreSQL couvre JSONB, UUID, transactions ACID, index avancés |
| **Stockage fichiers sur volume Docker** (MVP) | Zéro dépendance externe ; l'abstraction `FileStorage` permet de migrer vers S3/MinIO sans toucher le code métier |
| **AI Provider externe via HTTP** | Aucun modèle hébergé en local ; séparation claire entre logique métier et capacité IA |

### 1.3 Flux d'une requête authentifiée

```
1. Browser → HTTPS → Nginx (reverse proxy)
2. Nginx → React Frontend  (assets statiques)
        → /api/v1/*  (proxy vers FastAPI)
3. FastAPI : middleware CORS → middleware logging
           → route handler → dependency injection (get_current_user)
           → service layer (logique métier + vérification ownership/permissions)
           → repository layer (SQLAlchemy, transactions)
           → PostgreSQL
4. Réponse : JSON + codes HTTP standards
```

---

## 2. Architecture frontend React

### 2.1 Principes

- **Feature-based** : chaque domaine métier est un dossier autonome sous `features/`. La logique métier est dans les hooks, jamais dans les composants.
- **Fortement typé** : TypeScript strict, pas de `any` sans justification documentée.
- **Séparation des couches** : `api.ts` (appels HTTP) → `hooks/` (TanStack Query, état) → `components/` (rendu pur) → `pages/` (composition de route).

### 2.2 Stack et justification

| Outil | Rôle | Pourquoi |
|-------|------|----------|
| React + TypeScript | UI | Écosystème, typage structurel |
| Vite | Bundler | HMR rapide, config minimale |
| React Router v6 | Navigation | Standard de facto, loaders, outlets |
| TanStack Query v5 | Data fetching + cache | Cache automatique, stale-while-revalidate, invalidation déclarative ; élimine le state management ad-hoc pour les données serveur |
| React Hook Form + Zod | Formulaires | Performances (uncontrolled), validation partagée avec le backend (même schéma Zod → types) |
| shadcn/ui + Tailwind CSS | Composants + styles | Composants accessibles copiables (pas de dépendance lourde) ; Tailwind évite les collisions CSS |
| Vitest + Testing Library | Tests | Même runner que Vite, API identique à Jest |

### 2.3 Architecture des features

Chaque feature suit la même structure interne :

```
features/courses/
├── api.ts          ← fonctions fetch (axios/fetch + types de retour)
├── types.ts        ← types spécifiques à la feature (ou dans global types/)
├── hooks/
│   ├── useCourses.ts        ← useQuery / useMutation (TanStack Query)
│   └── useCourseDetail.ts
├── components/
│   ├── CourseCard.tsx
│   └── CourseForm.tsx
└── pages/
    ├── CoursesListPage.tsx
    └── CourseDetailPage.tsx
```

### 2.4 Gestion de l'authentification côté frontend

```
AuthProvider (Context)
├── user: User | null
├── isAuthenticated: boolean
├── login() / logout()
└── isLoading: boolean
```

- Les cookies `HttpOnly` sont gérés automatiquement par le browser (aucun token stocké en JS).
- `ProtectedRoute` vérifie `isAuthenticated` et redirige vers `/login` si nécessaire.
- Le rôle (`ADMIN` | `USER`) est stocké dans le contexte Auth pour le rendu conditionnel de l'UI **uniquement** — jamais pour sécuriser des données.

### 2.5 Routing et protection des routes

```
/                       → redirect vers /dashboard
/login                  → LoginPage (public)
/register               → RegisterPage (public)
/dashboard              → DashboardPage (protégé)
/courses                → CoursesListPage (protégé)
/courses/:id            → CourseDetailPage (protégé)
/courses/:id/edit       → CourseEditPage (owner | ADMIN)
/courses/:id/contents   → ContentsPage (owner | ADMIN)
/learning-paths         → LearningPathsListPage (protégé)
/learning-paths/:id     → LearningPathDetailPage (protégé)
/assignments            → AssignmentsPage (ADMIN)
/enrollments            → EnrollmentsPage (protégé)
/enrollments/:id        → EnrollmentDetailPage (protégé)
/quizzes/:id/attempt    → QuizAttemptPage (protégé)
/admin/users            → UsersAdminPage (ADMIN)
/admin/categories       → CategoriesAdminPage (ADMIN)
```

---

## 3. Architecture backend FastAPI

### 3.1 Principes

- **Monolithe modulaire** : un seul processus, organisé en modules métier indépendants.
- **Couche API** (`api/v1/`) : routing uniquement — pas de logique métier.
- **Couche Service** : logique métier, vérifications d'autorisation/ownership.
- **Couche Repository** : accès base de données via SQLAlchemy 2.x (sessions async recommandées).
- **Couche Schémas** (Pydantic v2) : validation des entrées, sérialisation des sorties.

### 3.2 Organisation des modules

```
modules/
├── auth/               ← login, register, logout, tokens
├── users/              ← CRUD utilisateurs (ADMIN)
├── categories/         ← CRUD catégories (ADMIN pour création/édition)
├── courses/            ← CRUD cours, publication, archivage
├── contents/           ← CRUD contenus pédagogiques, réordonnancement
├── files/              ← upload, download, métadonnées, storage abstraction
├── learning_paths/     ← CRUD learning paths, gestion des cours associés
├── assignments/        ← affectations ADMIN → utilisateurs
├── enrollments/        ← inscriptions dérivées des assignments
├── progress/           ← suivi progression contenu et cours
├── quizzes/            ← quiz, tentatives, réponses, scoring
└── quiz_generation/    ← pipeline extraction → chunking → IA → validation
```

### 3.3 Structure interne d'un module

```
module/
├── router.py        ← FastAPI APIRouter, déclarations des endpoints
├── schemas.py       ← Pydantic v2 : Request/Response/Base schemas
├── models.py        ← SQLAlchemy ORM models (tables)
├── service.py       ← logique métier, règles d'autorisation
├── repository.py    ← requêtes DB (SELECT, INSERT, UPDATE, DELETE)
└── dependencies.py  ← inject. de dépendances FastAPI (get_course_or_404, etc.)
```

**Pourquoi cette séparation ?** Elle facilite les tests unitaires (mock du repository dans le service, mock du service dans les tests de route) et évite que la logique métier se retrouve dans les routes.

### 3.4 Pipeline d'une requête FastAPI

```
Request
  → CORS Middleware
  → Logging Middleware
  → Router dispatch
  → Dependencies (get_db, get_current_user, get_course_or_404, require_owner_or_admin)
  → Route Handler (validation Pydantic des inputs)
  → Service (logique métier + autorisation)
  → Repository (SQLAlchemy)
  → DB
  → Response (sérialisation Pydantic)
  → Exception Handler global (→ format d'erreur standardisé)
```

### 3.5 Gestion centralisée des exceptions

```python
# Format uniforme pour toutes les erreurs
{
  "code": "COURSE_ACCESS_DENIED",
  "message": "You do not have permission to access this course."
}
```

Un `exception_handler` global capte les exceptions métier (`CourseNotFound`, `AccessDenied`, `ValidationError`) et les mappe vers les codes HTTP appropriés (404, 403, 422).

---

## 4. Modèle de données PostgreSQL

> Tous les IDs sont des **UUID v4** (pas d'entiers auto-incrémentés).  
> **Pourquoi UUID ?** Pas d'exposition d'informations d'ordre/volume via les IDs, compatible avec des migrations ou imports futurs.

### 4.1 User

```sql
users
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── email           VARCHAR(255) UNIQUE NOT NULL
├── password_hash   TEXT NOT NULL
├── first_name      VARCHAR(100) NOT NULL
├── last_name       VARCHAR(100) NOT NULL
├── role            ENUM('ADMIN', 'USER') NOT NULL DEFAULT 'USER'
├── is_active       BOOLEAN NOT NULL DEFAULT TRUE
├── created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
└── updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
```

### 4.2 Category

```sql
categories
├── id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── name        VARCHAR(100) UNIQUE NOT NULL
├── description TEXT
└── created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

### 4.3 Course

```sql
courses
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── owner_id        UUID NOT NULL REFERENCES users(id)
├── category_id     UUID REFERENCES categories(id) ON DELETE SET NULL
├── title           VARCHAR(255) NOT NULL
├── description     TEXT
├── cover_image_id  UUID REFERENCES file_assets(id) ON DELETE SET NULL
├── status          ENUM('DRAFT', 'PUBLISHED', 'ARCHIVED') NOT NULL DEFAULT 'DRAFT'
├── created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
└── updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
```

**Pourquoi `cover_image_id` FK vers `file_assets` ?** Cohérence : toutes les images passent par le système de fichiers unifié. Évite d'avoir des URLs en dur dans la table `courses`.

### 4.4 FileAsset

> **Entité absente du readme — ajoutée ici** (voir §16 pour l'explication).

```sql
file_assets
├── id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── original_filename VARCHAR(255) NOT NULL
├── stored_filename   VARCHAR(255) NOT NULL UNIQUE  -- UUID-based, jamais le nom original
├── mime_type         VARCHAR(100) NOT NULL
├── size_bytes        BIGINT NOT NULL
├── storage_backend   ENUM('LOCAL', 'S3') NOT NULL DEFAULT 'LOCAL'
├── storage_path      TEXT NOT NULL               -- chemin relatif dans le backend
├── uploaded_by       UUID NOT NULL REFERENCES users(id)
└── created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
```

**Pourquoi `stored_filename` distinct de `original_filename` ?** Prévention de la path traversal attack et des conflits de noms. Le nom original est conservé pour l'affichage utilisateur uniquement.

### 4.5 CourseContent

```sql
course_contents
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── course_id       UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE
├── type            ENUM('TEXT', 'PDF', 'CSV', 'AUDIO', 'WEB_LINK') NOT NULL
├── title           VARCHAR(255) NOT NULL
├── text_content    TEXT                              -- si type = TEXT
├── file_asset_id   UUID REFERENCES file_assets(id)  -- si type = PDF|CSV|AUDIO
├── external_url    TEXT                              -- si type = WEB_LINK
├── position        INTEGER NOT NULL DEFAULT 0
├── created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
└── updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
```

Contrainte CHECK : exactement un des champs `text_content`, `file_asset_id`, `external_url` est non nul, selon `type`.

### 4.6 LearningPath

```sql
learning_paths
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── created_by      UUID NOT NULL REFERENCES users(id)
├── title           VARCHAR(255) NOT NULL
├── description     TEXT
├── cover_image_id  UUID REFERENCES file_assets(id) ON DELETE SET NULL
├── status          ENUM('DRAFT', 'PUBLISHED', 'ARCHIVED') NOT NULL DEFAULT 'DRAFT'
├── created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
└── updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
```

### 4.7 LearningPathCourse (table de jointure)

```sql
learning_path_courses
├── learning_path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE
├── course_id        UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE
├── position         INTEGER NOT NULL DEFAULT 0
└── PRIMARY KEY (learning_path_id, course_id)
```

### 4.8 Assignment

```sql
assignments
├── id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── user_id     UUID NOT NULL REFERENCES users(id)
├── assigned_by UUID NOT NULL REFERENCES users(id)
├── target_type ENUM('COURSE', 'LEARNING_PATH') NOT NULL
├── target_id   UUID NOT NULL
├── starts_at   TIMESTAMPTZ
├── due_date    TIMESTAMPTZ
├── status      ENUM('PENDING', 'ACTIVE', 'COMPLETED', 'EXPIRED', 'CANCELLED') NOT NULL DEFAULT 'PENDING'
└── created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
```

**Pourquoi `target_type` + `target_id` (polymorphisme) plutôt que deux colonnes nullable ?**  
Évite d'avoir `course_id NULL` et `learning_path_id NOT NULL` ou l'inverse ; une seule contrainte à valider ; extensible (ex. ajout d'un type `ASSESSMENT` plus tard).

### 4.9 Enrollment

```sql
enrollments
├── id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── user_id             UUID NOT NULL REFERENCES users(id)
├── assignment_id       UUID NOT NULL REFERENCES assignments(id)
├── course_id           UUID REFERENCES courses(id)          -- dénormalisé depuis assignment
├── learning_path_id    UUID REFERENCES learning_paths(id)   -- dénormalisé depuis assignment
├── status              ENUM('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', 'CANCELLED') NOT NULL DEFAULT 'NOT_STARTED'
├── progress_percent    SMALLINT NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100)
├── started_at          TIMESTAMPTZ
├── completed_at        TIMESTAMPTZ
├── due_date            TIMESTAMPTZ                          -- copié de l'assignment à la création
└── created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
```

**Pourquoi `course_id`/`learning_path_id` dénormalisés ?** Performance des requêtes : `WHERE enrollments.user_id = $1 AND enrollments.course_id = $2` sans JOIN sur `assignments`. La cohérence est garantie par le service lors de la création.

### 4.10 ContentProgress

```sql
content_progress
├── id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── enrollment_id    UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE
├── content_id       UUID NOT NULL REFERENCES course_contents(id) ON DELETE CASCADE
├── status           ENUM('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED') NOT NULL DEFAULT 'NOT_STARTED'
├── progress_percent SMALLINT NOT NULL DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100)
├── last_position    TEXT                                    -- ex. timestamp audio, page PDF
├── completed_at     TIMESTAMPTZ
└── UNIQUE (enrollment_id, content_id)
```

### 4.11 Quiz

```sql
quizzes
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── course_id       UUID NOT NULL REFERENCES courses(id) ON DELETE CASCADE
├── version         INTEGER NOT NULL DEFAULT 1
├── status          ENUM('DRAFT', 'ACTIVE', 'ARCHIVED') NOT NULL DEFAULT 'DRAFT'
├── difficulty      ENUM('EASY', 'MEDIUM', 'HARD') NOT NULL DEFAULT 'MEDIUM'
├── question_count  INTEGER NOT NULL
├── generated_at    TIMESTAMPTZ
└── UNIQUE (course_id, version)
```

**Pourquoi une ligne par version ?** Chaque `QuizAttempt` pointe vers un `quiz_id` précis — même si le contenu du cours change et qu'un nouveau quiz est généré (version N+1), les anciennes tentatives restent cohérentes avec leur version du quiz.

### 4.12 QuizQuestion

```sql
quiz_questions
├── id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── quiz_id           UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE
├── question          TEXT NOT NULL
├── options           JSONB NOT NULL      -- [{"id": "uuid", "text": "..."}]
├── correct_option_id UUID NOT NULL
├── explanation       TEXT NOT NULL
├── source_content_id UUID REFERENCES course_contents(id)
├── source_reference  TEXT                -- ex. "paragraphe 3", "page 12"
└── position          INTEGER NOT NULL DEFAULT 0
```

**Pourquoi `options` en JSONB ?** Le nombre d'options peut varier (3 à 5) ; pas besoin d'une table séparée `QuizOption` pour le MVP ; le JSONB reste indexable et requêtable.

### 4.13 QuizGenerationJob

```sql
quiz_generation_jobs
├── id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── course_id       UUID NOT NULL REFERENCES courses(id)
├── requested_by    UUID NOT NULL REFERENCES users(id)
├── status          ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') NOT NULL DEFAULT 'PENDING'
├── started_at      TIMESTAMPTZ
├── completed_at    TIMESTAMPTZ
├── error_message   TEXT
└── created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
```

### 4.14 QuizAttempt

```sql
quiz_attempts
├── id             UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── quiz_id        UUID NOT NULL REFERENCES quizzes(id)
├── user_id        UUID NOT NULL REFERENCES users(id)
├── enrollment_id  UUID NOT NULL REFERENCES enrollments(id)
├── score          SMALLINT CHECK (score BETWEEN 0 AND 100)
├── started_at     TIMESTAMPTZ NOT NULL DEFAULT now()
└── completed_at   TIMESTAMPTZ
```

### 4.15 QuizAnswer

```sql
quiz_answers
├── id                 UUID PRIMARY KEY DEFAULT gen_random_uuid()
├── attempt_id         UUID NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE
├── question_id        UUID NOT NULL REFERENCES quiz_questions(id)
├── selected_option_id UUID NOT NULL
└── is_correct         BOOLEAN NOT NULL
```

---

## 5. Relations entre les entités

```
users ──────────────────────── courses (owner_id)
      ──────────────────────── learning_paths (created_by)
      ──────────────────────── assignments (user_id, assigned_by)
      ──────────────────────── enrollments (user_id)
      ──────────────────────── quiz_attempts (user_id)
      ──────────────────────── file_assets (uploaded_by)

categories ─────────────────── courses (category_id, nullable)

courses ────────────────────── course_contents (course_id)
        ────────────────────── quizzes (course_id)
        ────────────────────── quiz_generation_jobs (course_id)
        ────────────────────── learning_path_courses (course_id)
        ────────────────────── file_assets ← cover_image_id

learning_paths ─────────────── learning_path_courses (learning_path_id)
               ─────────────── file_assets ← cover_image_id

assignments ────────────────── enrollments (assignment_id)

enrollments ────────────────── content_progress (enrollment_id)
            ────────────────── quiz_attempts (enrollment_id)

quizzes ────────────────────── quiz_questions (quiz_id)
        ────────────────────── quiz_attempts (quiz_id)

quiz_attempts ──────────────── quiz_answers (attempt_id)

course_contents ────────────── content_progress (content_id)
                ────────────── quiz_questions (source_content_id)
                ────────────── file_assets ← file_asset_id

file_assets ← référencés par courses, learning_paths, course_contents
```

### Cardinalités clés

| Relation | Cardinalité |
|----------|-------------|
| User → Courses | 1:N (un user est owner de N cours) |
| Course → CourseContents | 1:N |
| Course → Quizzes | 1:N (une par version) |
| Assignment → Enrollments | 1:1 (un assignment = une enrollment) |
| Enrollment → ContentProgress | 1:N (une par contenu du cours) |
| QuizAttempt → QuizAnswers | 1:N (une par question) |
| LearningPath → Courses | N:M (via learning_path_courses) |

---

## 6. Architecture d'authentification et d'autorisation

### 6.1 Authentification

**Hachage des mots de passe : Argon2id**  
Pourquoi Argon2id plutôt que bcrypt ? Vainqueur du Password Hashing Competition (2015), résistant aux attaques GPU et side-channel, paramétrage mémoire + temps + parallélisme.

**Gestion des sessions : cookies HttpOnly + Secure**

```
POST /auth/login
→ vérifie email/password (Argon2 verify)
→ génère access_token (JWT, courte durée : 15 min)
→ génère refresh_token (opaque UUID, longue durée : 7 jours, stocké en DB)
→ Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Lax; Path=/api
→ Set-Cookie: refresh_token=...; HttpOnly; Secure; SameSite=Lax; Path=/api/auth/refresh
```

**Pourquoi HttpOnly cookies ?** Immunise contre le vol de tokens par XSS (le JS ne peut pas lire le cookie).  
**Pourquoi deux tokens ?** Access token court = surface d'exposition réduite en cas de compromission. Refresh token long = expérience utilisateur fluide sans re-login fréquent.

**Rotation des refresh tokens**  
À chaque usage du refresh token, un nouveau est émis et l'ancien est invalidé (table `refresh_tokens` en DB). Détection de réutilisation : si un refresh token déjà invalidé est présenté → révocation de toute la session.

**Endpoint refresh :**
```
POST /auth/refresh
→ lit refresh_token depuis cookie
→ valide contre DB (non expiré, non révoqué)
→ émet nouveau access_token + nouveau refresh_token (rotation)
```

### 6.2 Autorisation

Deux axes indépendants :

```
1. Role-Based :  current_user.role == 'ADMIN'  →  accès global
2. Ownership :   current_user.id == resource.owner_id  →  accès à la ressource
```

**L'autorisation est toujours vérifiée côté backend.** Le frontend peut masquer des éléments UI selon le rôle, mais cette UI n'est jamais une couche de sécurité.

**Dependencies FastAPI :**

```python
# Hiérarchie des dépendances injectables

get_db()                      # session SQLAlchemy
get_current_user(db, token)   # décode JWT, retourne User ou 401
require_admin(current_user)   # vérifie role == ADMIN ou 403
get_course_or_404(id, db)     # retourne Course ou 404
require_course_owner(course, current_user)   # vérifie ownership ou 403
require_owner_or_admin(resource, current_user)  # ownership OU admin
```

### 6.3 Modèle de permissions par action

| Action | Règle |
|--------|-------|
| Voir un cours PUBLISHED | tout utilisateur authentifié |
| Voir un cours DRAFT | owner + ADMIN |
| Modifier/Supprimer un cours | owner + ADMIN |
| Créer une catégorie | ADMIN uniquement |
| Affecter un cours à un utilisateur | ADMIN uniquement |
| Générer un quiz | owner du cours + ADMIN |
| Voir les quiz attempts d'un utilisateur | l'utilisateur lui-même + ADMIN |
| Voir/Modifier tout utilisateur | ADMIN uniquement |

---

## 7. Stratégie d'ownership des cours

### 7.1 Règle d'isolation absolue

```
USER A peut : lire, modifier, supprimer ses propres cours
USER A ne peut pas : modifier ou supprimer les cours de USER B
ADMIN peut : tout
```

### 7.2 Implémentation

- `courses.owner_id` est défini au moment de la création via `current_user.id`.
- `owner_id` n'est **jamais** modifiable via l'API (champ exclu des schémas de mise à jour).
- Toute opération d'écriture (PATCH, DELETE) sur un cours appelle `require_owner_or_admin(course, current_user)` dans la dépendance FastAPI, **avant** d'entrer dans le service.
- Les tests d'ownership sont explicitement couverts dans la suite de tests.

### 7.3 Extension aux LearningPaths

Même règle appliquée via `learning_paths.created_by`. La dépendance `require_lp_owner_or_admin` est symétrique à `require_course_owner_or_admin`.

### 7.4 Ce que l'ownership ne signifie pas

> **Ownership ≠ Enrollment**  
> Créer un cours ne vous inscrit pas automatiquement à ce cours. Un owner peut accéder à son cours directement (via les endpoints de gestion) sans avoir d'`Enrollment`.

---

## 8. Architecture Assignment → Enrollment → Progress

### 8.1 Vue d'ensemble du flux

```
ADMIN crée Assignment (user, target, deadline)
         │
         ▼
 EnrollmentService.create_from_assignment()
         │
         ├── target_type == COURSE    →  crée 1 Enrollment (course_id)
         └── target_type == LEARNING_PATH
                  │
                  └── pour chaque Course dans la LP → crée 1 Enrollment (course_id)
                      + 1 Enrollment "parent" (learning_path_id) pour la progression globale
```

**Pourquoi créer des Enrollments individuels par cours dans une LP ?** La progression est toujours trackée au niveau du cours (ContentProgress), même pour les cours faisant partie d'une LP. Cela évite de dupliquer la logique de progression.

### 8.2 Machine d'états : Assignment

```
PENDING  →  ACTIVE     (starts_at atteint, ou immédiatement si starts_at = NULL)
ACTIVE   →  COMPLETED  (tous les Enrollments associés sont COMPLETED)
ACTIVE   →  EXPIRED    (due_date dépassée sans complétion)
PENDING
ACTIVE   →  CANCELLED  (action ADMIN)
```

### 8.3 Machine d'états : Enrollment

```
NOT_STARTED  →  IN_PROGRESS  (learner ouvre le premier contenu)
IN_PROGRESS  →  COMPLETED    (progress_percent atteint 100)
IN_PROGRESS  →  OVERDUE      (due_date dépassée et pas COMPLETED)
NOT_STARTED
IN_PROGRESS  →  CANCELLED    (assignment parent annulé)
```

### 8.4 Calcul de la progression

```
progress_percent (Enrollment) = 
    (nb de ContentProgress avec status=COMPLETED) / (nb total de CourseContents) × 100
```

Ce calcul est effectué par `ProgressService.recalculate_enrollment_progress(enrollment_id)` après chaque mise à jour d'un `ContentProgress`. Le résultat est persisté dans `enrollments.progress_percent` (pas recalculé à chaque lecture).

**Pourquoi persister plutôt que calculer à la volée ?**  
Performance : évite des agrégats coûteux sur `content_progress` à chaque GET. La valeur est recalculée uniquement quand un contenu est marqué comme complété.

### 8.5 Transitions de ContentProgress

```
(aucune ligne)  →  NOT_STARTED  (création automatique à l'ouverture du cours)
NOT_STARTED     →  IN_PROGRESS  (premier accès au contenu)
IN_PROGRESS     →  COMPLETED    (contenu entièrement consulté / marqué manuellement)
```

---

## 9. Architecture de génération automatique des quiz

### 9.1 Principe général

Les quiz ne sont **jamais** créés manuellement. Seul le pipeline de génération automatique produit des `QuizQuestion`.

### 9.2 Pipeline de génération

```
POST /courses/{id}/quiz/generate
        │
        ▼
QuizGenerationService.trigger(course_id, requested_by)
        │
        ├── Crée QuizGenerationJob (status=PENDING)
        ├── Retourne {job_id} immédiatement (HTTP 202 Accepted)
        │
        └── FastAPI BackgroundTask → QuizGenerationPipeline.run(job_id)
                │
                ├── [1] Collecte des CourseContents du cours
                ├── [2] Extraction par type :
                │       TEXT      → texte direct
                │       PDF       → extraction de texte (pypdf ou pdfplumber)
                │       CSV       → parsing structuré (pandas ou csv stdlib)
                │       AUDIO     → transcription (AI Provider : OpenAI Whisper ou équivalent)
                │       WEB_LINK  → HTTP GET contrôlé (timeout, whitelist, pas d'IP privée)
                ├── [3] Nettoyage + normalisation du texte
                ├── [4] Chunking (découpage en segments de taille fixe avec overlap)
                ├── [5] Envoi à AI Provider (prompt structuré → JSON Quiz)
                ├── [6] Validation Pydantic de chaque question générée :
                │       - exactement N options
                │       - pas de doublons d'options
                │       - exactement 1 bonne réponse
                │       - explication présente
                │       - référence source présente
                ├── [7] Persistance Quiz + QuizQuestions en DB
                └── [8] Mise à jour QuizGenerationJob (status=COMPLETED ou FAILED)
```

### 9.3 Implémentation asynchrone — MVP

**Choix MVP : FastAPI BackgroundTasks** (pas de Celery, pas de Redis pour le MVP).

| Aspect | BackgroundTasks (MVP) | Celery + Redis (production future) |
|--------|-----------------------|------------------------------------|
| Dépendances | Aucune | Redis + worker process |
| Survie au redémarrage | Non | Oui |
| Scalabilité | Limitée (même process) | Horizontale |
| Monitoring | Polling DB | Interface Celery |

Le frontend poll `GET /quiz-generation-jobs/{id}` toutes les 3 secondes jusqu'à `status = COMPLETED | FAILED`.

### 9.4 Versionnement des quiz

```
Cours v1 → Quiz v1 (question_count=10, generated_at=T1)
Contenu modifié → POST /courses/{id}/quiz/generate
→ Quiz v2 (version=2, status=ACTIVE)
→ Quiz v1 (status=ARCHIVED)

QuizAttempt.quiz_id → pointe toujours vers la version exacte utilisée
```

### 9.5 Sécurité de la génération WEB_LINK

Lors de la récupération d'URLs externes pour le quiz :
- Timeout HTTP strict (max 10 secondes)
- Blocage des adresses IP privées (RFC 1918), loopback, link-local
- Validation de l'URL (schéma https uniquement, pas de file://, ftp://)
- Taille de réponse limitée (max 2 MB)
- User-Agent non révélateur

---

## 10. Gestion et stockage des fichiers

### 10.1 Principe

Les fichiers binaires ne sont **jamais** stockés dans PostgreSQL. Seules les métadonnées sont en base (table `file_assets`).

### 10.2 Abstraction FileStorage

```python
class FileStorage(ABC):
    @abstractmethod
    async def save(self, file: UploadFile, stored_filename: str) -> str:
        """Retourne le storage_path"""

    @abstractmethod
    async def get_url(self, storage_path: str) -> str:
        """Retourne une URL de téléchargement"""

    @abstractmethod
    async def delete(self, storage_path: str) -> None: ...

class LocalFileStorage(FileStorage):
    """Stockage dans un Docker Volume. MVP."""

class S3FileStorage(FileStorage):
    """AWS S3 / MinIO / Azure Blob. Production future."""
```

**Pourquoi une interface abstraite dès le MVP ?** Zéro refactoring lors de la migration vers S3 — seule la configuration change.

### 10.3 Flux d'upload

```
POST /files/upload (multipart/form-data)
  → Validation backend :
      - taille ≤ MAX_UPLOAD_SIZE_MB (configurable via .env)
      - extension autorisée : .pdf, .csv, .mp3, .mp4, .wav, .jpg, .png, .webp
      - MIME type validé côté serveur (magic bytes, pas seulement l'extension)
      - extensions dangereuses refusées : .exe, .sh, .php, .js, .py, etc.
  → génération de stored_filename = UUID4 + extension originale
  → FileStorage.save(file, stored_filename)
  → INSERT INTO file_assets (...)
  → Retourne {file_asset_id, original_filename, mime_type, size_bytes}
```

### 10.4 Flux de download

```
GET /files/{id}
  → vérifie que l'utilisateur a le droit de voir ce fichier
    (uploaded_by == current_user.id  OR  ADMIN  OR  enrolled dans le cours qui référence le fichier)
  → FileStorage.get_url(file_asset.storage_path)
  → Redirect ou stream
```

### 10.5 Types autorisés par usage

| Usage | Types acceptés |
|-------|---------------|
| Couverture cours/LP | JPG, PNG, WEBP |
| Contenu PDF | PDF |
| Contenu CSV | CSV |
| Contenu Audio | MP3, MP4, WAV, OGG |

---

## 11. API REST proposée

Base URL : `/api/v1`

> `[A]` = ADMIN uniquement · `[O]` = owner du cours/LP + ADMIN · `[U]` = tout utilisateur authentifié · `[S]` = utilisateur lui-même + ADMIN

### 11.1 Authentification

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| POST | `/auth/register` | Public | Crée un USER |
| POST | `/auth/login` | Public | Set cookies access + refresh |
| POST | `/auth/logout` | `[U]` | Invalide refresh token, clear cookies |
| GET | `/auth/me` | `[U]` | Profil de l'utilisateur courant |
| POST | `/auth/refresh` | Cookie refresh | Rotation du refresh token |

### 11.2 Utilisateurs

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| GET | `/users` | `[A]` | Liste paginée |
| POST | `/users` | `[A]` | ADMIN crée un utilisateur |
| GET | `/users/{id}` | `[S]` | Profil |
| PATCH | `/users/{id}` | `[S]` | Modifier profil (ADMIN peut tout modifier) |
| PATCH | `/users/{id}/activate` | `[A]` | Activer/désactiver |
| DELETE | `/users/{id}` | `[A]` | Soft-delete (is_active = false) |

### 11.3 Catégories

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| GET | `/categories` | `[U]` | Liste complète |
| POST | `/categories` | `[A]` | Création |
| GET | `/categories/{id}` | `[U]` | Détail |
| PATCH | `/categories/{id}` | `[A]` | Modification |
| DELETE | `/categories/{id}` | `[A]` | Suppression (SET NULL sur courses.category_id) |

### 11.4 Cours

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| GET | `/courses` | `[U]` | PUBLISHED pour tous ; DRAFT visibles seulement par owner+ADMIN |
| POST | `/courses` | `[U]` | Crée un cours (owner = current_user) |
| GET | `/courses/{id}` | `[U]` | PUBLISHED : tout le monde ; DRAFT : owner+ADMIN |
| PATCH | `/courses/{id}` | `[O]` | Modification (pas de owner_id) |
| DELETE | `/courses/{id}` | `[O]` | Suppression (cascade contents, quiz) |
| PATCH | `/courses/{id}/publish` | `[O]` | DRAFT → PUBLISHED |
| PATCH | `/courses/{id}/archive` | `[O]` | PUBLISHED → ARCHIVED |
| GET | `/courses/{id}/contents` | `[U]` | Liste ordonnée des contenus |

### 11.5 Contenus

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| POST | `/courses/{id}/contents` | `[O]` | Ajout d'un contenu |
| GET | `/contents/{id}` | `[U]` | Détail d'un contenu |
| PATCH | `/contents/{id}` | `[O]` | Modification |
| DELETE | `/contents/{id}` | `[O]` | Suppression |
| PATCH | `/courses/{id}/contents/reorder` | `[O]` | Mise à jour des positions |

### 11.6 Fichiers

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| POST | `/files/upload` | `[U]` | Upload multipart, retourne file_asset_id |
| GET | `/files/{id}` | `[U]` | Download (vérif accès) |
| DELETE | `/files/{id}` | `[O uploaded_by]` + `[A]` | Suppression |

### 11.7 Learning Paths

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| GET | `/learning-paths` | `[U]` | PUBLISHED pour tous ; DRAFT : owner+ADMIN |
| POST | `/learning-paths` | `[U]` | Crée une LP (created_by = current_user) |
| GET | `/learning-paths/{id}` | `[U]` | Détail |
| PATCH | `/learning-paths/{id}` | `[O]` | Modification |
| DELETE | `/learning-paths/{id}` | `[O]` | Suppression |
| PATCH | `/learning-paths/{id}/publish` | `[O]` | Publication |
| POST | `/learning-paths/{id}/courses` | `[O]` | Ajoute un cours à la LP |
| DELETE | `/learning-paths/{id}/courses/{course_id}` | `[O]` | Retire un cours |
| PATCH | `/learning-paths/{id}/courses/reorder` | `[O]` | Réordonne les cours |

### 11.8 Assignments

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| GET | `/assignments` | `[A]` | Liste toutes les affectations |
| POST | `/assignments` | `[A]` | Crée une affectation → déclenche création Enrollment |
| GET | `/assignments/{id}` | `[A]` | Détail |
| PATCH | `/assignments/{id}` | `[A]` | Modifie deadline, statut |
| DELETE | `/assignments/{id}` | `[A]` | Annule (status=CANCELLED, cascade Enrollments) |

### 11.9 Enrollments

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| GET | `/enrollments` | `[U]` | Learner voit ses propres ; ADMIN voit tout |
| GET | `/enrollments/{id}` | `[S]` | Détail + progress_percent |
| GET | `/enrollments/{id}/progress` | `[S]` | ContentProgress de cet enrollment |
| POST | `/enrollments/{enrollment_id}/contents/{content_id}/progress` | `[S]` | Marque contenu IN_PROGRESS ou COMPLETED |

### 11.10 Quiz

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| POST | `/courses/{id}/quiz/generate` | `[O]` | Déclenche génération async, retourne job_id |
| GET | `/courses/{id}/quiz` | `[U]` | Dernier quiz ACTIVE du cours |
| GET | `/quizzes/{id}` | `[U]` | Version spécifique |
| GET | `/quiz-generation-jobs/{id}` | `[O]` | Statut du job de génération |

### 11.11 Tentatives de quiz

| Méthode | Endpoint | Permission | Notes |
|---------|----------|------------|-------|
| POST | `/quizzes/{id}/attempts` | `[U]` | Démarre une tentative |
| GET | `/quiz-attempts/{id}` | `[S]` | Détail tentative |
| POST | `/quiz-attempts/{id}/answers` | `[S]` | Soumet une réponse |
| POST | `/quiz-attempts/{id}/complete` | `[S]` | Finalise + calcule le score |
| GET | `/enrollments/{id}/quiz-attempts` | `[S]` | Historique des tentatives |

### 11.12 Format des réponses

**Succès :** HTTP 200/201/204 + JSON ou corps vide.  
**Erreur :**
```json
{
  "code": "COURSE_ACCESS_DENIED",
  "message": "You do not have permission to access this course."
}
```
**Pagination** (listes) :
```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

---

## 12. Architecture Docker

### 12.1 Services Docker Compose

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
    volumes: [postgres_data:/var/lib/postgresql/data]
    networks: [backend_net]
    healthcheck: pg_isready
    # Non exposé publiquement (pas de ports mapping en production)

  backend:
    build: ./backend (multi-stage)
    environment: DATABASE_URL, SECRET_KEY, AI_PROVIDER_KEY, ...
    volumes: [file_storage:/app/storage]
    networks: [backend_net]
    depends_on: postgres (condition: healthy)
    healthcheck: GET /health

  frontend:
    build: ./frontend (multi-stage)
    networks: [frontend_net, backend_net]
    depends_on: backend (condition: healthy)

  nginx:
    image: nginx:alpine
    ports: [80:80, 443:443]
    volumes: [./nginx/nginx.conf:/etc/nginx/nginx.conf]
    networks: [frontend_net]
    depends_on: [frontend, backend]

volumes:
  postgres_data:
  file_storage:

networks:
  backend_net:   # backend + postgres
  frontend_net:  # nginx + frontend
```

### 12.2 Dockerfiles multi-stage

**Backend (Python) :**
```
Stage 1 (builder) : install deps, compile wheels
Stage 2 (runtime) : copie uniquement les artefacts, utilisateur non-root (uid 1000)
```

**Frontend (Node + Nginx) :**
```
Stage 1 (builder) : npm ci + vite build
Stage 2 (nginx)   : copie dist/, nginx.conf, utilisateur non-root
```

**Pourquoi multi-stage ?** Image finale sans outils de build, surface d'attaque réduite, taille minimale.

### 12.3 Configuration Nginx

```nginx
# /api/v1/* → proxy vers backend:8000
# /* → servir les fichiers statiques React (SPA fallback → index.html)
# Headers de sécurité : X-Frame-Options, X-Content-Type-Options, CSP, HSTS
```

### 12.4 Variables d'environnement

Fichier `.env.example` documenté à la racine. Variables clés :

```
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/lms
SECRET_KEY=                        # ≥ 32 octets aléatoires
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
AI_PROVIDER_URL=
AI_PROVIDER_KEY=
MAX_UPLOAD_SIZE_MB=50
STORAGE_BACKEND=LOCAL              # LOCAL | S3
STORAGE_LOCAL_PATH=/app/storage
CORS_ORIGINS=http://localhost:5173 # liste séparée par virgules

# Postgres
POSTGRES_DB=lms
POSTGRES_USER=lms
POSTGRES_PASSWORD=

# Frontend
VITE_API_BASE_URL=/api/v1
```

### 12.5 Index PostgreSQL prioritaires

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_courses_owner_id ON courses(owner_id);
CREATE INDEX idx_courses_category_id ON courses(category_id);
CREATE INDEX idx_courses_status ON courses(status);
CREATE INDEX idx_course_contents_course_id ON course_contents(course_id, position);
CREATE INDEX idx_assignments_user_id ON assignments(user_id);
CREATE INDEX idx_enrollments_user_id ON enrollments(user_id);
CREATE INDEX idx_enrollments_course_id ON enrollments(course_id);
CREATE INDEX idx_enrollments_assignment_id ON enrollments(assignment_id);
CREATE INDEX idx_quiz_attempts_user_id ON quiz_attempts(user_id);
CREATE INDEX idx_quiz_attempts_enrollment_id ON quiz_attempts(enrollment_id);
CREATE INDEX idx_content_progress_enrollment_id ON content_progress(enrollment_id);
CREATE INDEX idx_quizzes_course_id ON quizzes(course_id);
CREATE INDEX idx_quiz_generation_jobs_course_id ON quiz_generation_jobs(course_id);
```

---

## 13. Stratégie de tests

### 13.1 Backend — Pytest

**Configuration :** base de données de test dédiée (SQLite en mémoire ou PostgreSQL de test), fixtures pytest pour les utilisateurs, cours, enrollments.

**Couverture cible :**

| Module | Tests prioritaires |
|--------|--------------------|
| `auth` | register, login (valide/invalide), logout, refresh token rotation, accès sans token |
| `courses` | CRUD, ownership (USER A ne peut pas modifier le cours de USER B), publication, statuts |
| `contents` | CRUD, réordonnancement, validation des types |
| `files` | upload valide, upload fichier dangereux refusé, MIME validation, size limit |
| `assignments` | création ADMIN, création non-ADMIN (403), cascade enrollment |
| `enrollments` | création via assignment, état machine, progression |
| `progress` | mise à jour ContentProgress, recalcul progress_percent |
| `quizzes` | tentative (start/answer/complete), scoring, rejet doublon tentative ouverte |
| `quiz_generation` | validation des questions (options, bonne réponse, explication), job status |

**Principe :** chaque test vérifie **une** règle métier ou **une** règle de permission.

### 13.2 Frontend — Vitest + Testing Library

**Principe :** tester le comportement utilisateur, pas l'implémentation.

| Feature | Tests prioritaires |
|---------|-------------------|
| `auth` | login form submit, redirect post-login, affichage erreur mauvais mdp |
| `routing` | routes protégées redirigent vers /login si non authentifié |
| `courses` | liste des cours chargée, création via formulaire, formulaire invalide |
| `assignments` | affichage dashboard learner (cours affectés) |
| `quizzes` | affichage question, sélection réponse, soumission, score final |

**MSW (Mock Service Worker)** pour mocker les appels API dans les tests frontend sans proxy réel.

### 13.3 Tests d'intégration

Scénarios de bout en bout couvrant les flows critiques :
1. Register → Login → Créer cours → Ajouter contenu → Publier → Générer quiz
2. ADMIN affecte cours → Enrollment créé → Learner progresse → Tente quiz → Score

---

## 14. Stratégie de sécurité

### 14.1 OWASP Top 10 — couverture explicite

| Risque OWASP | Mesure |
|--------------|--------|
| **A01 Broken Access Control** | Vérification ownership + role sur chaque endpoint d'écriture ; UUIDs non prédictibles |
| **A02 Cryptographic Failures** | Argon2id pour les mots de passe ; TLS en transit ; jamais de secret en clair dans les logs ou le dépôt |
| **A03 Injection** | SQLAlchemy ORM (requêtes paramétrées) ; Pydantic valide toutes les entrées ; pas de SQL brut |
| **A04 Insecure Design** | Séparation claire service/repository ; authorization before business logic ; principe du moindre privilège |
| **A05 Security Misconfiguration** | CORS strict ; headers de sécurité Nginx ; PostgreSQL non exposé ; utilisateurs non-root Docker |
| **A06 Vulnerable Components** | Dependabot / Renovate pour les mises à jour de dépendances |
| **A07 Auth Failures** | Rate limiting sur `/auth/login` (ex. 5 tentatives/minute) ; rotation des refresh tokens ; détection de réutilisation |
| **A08 Data Integrity Failures** | Validation Pydantic stricte ; MIME type validé côté serveur (magic bytes) ; stored_filename UUID |
| **A09 Logging Failures** | Logs structurés (JSON) sans données sensibles (jamais de hash, token, password) |
| **A10 SSRF** | Validation stricte des URLs WEB_LINK : blocage RFC1918, timeout, taille limitée, HTTPS uniquement |

### 14.2 Contrôles spécifiques

**Upload de fichiers :**
- Extensions autorisées par liste blanche (pas de liste noire)
- Validation MIME type via magic bytes (pas seulement l'extension)
- `stored_filename` = UUID4 (jamais le nom original dans le path de stockage)
- Stockage hors du répertoire web servi (pas dans `/static/` ou similaire)
- Taille maximale configurable

**Authentification :**
- CSRF protection : `SameSite=Lax` sur les cookies (protection suffisante pour la plupart des navigateurs modernes) ; envisager token CSRF double-submit si SameSite insuffisant
- Jamais de secret dans le dépôt git (`.env` dans `.gitignore`, `.env.example` fourni)
- Expiration explicite des tokens

**API :**
- Rate limiting global via middleware FastAPI (slowapi)
- Rate limiting strict sur `/auth/login` et `/auth/register`
- Validation Pydantic en mode strict sur tous les inputs
- Gestion centralisée des exceptions (pas de stack trace en production)
- Format d'erreur standardisé sans fuite d'information

---

## 15. Arborescence complète du projet

```
lms/
├── .env.example                         # toutes les variables documentées, sans valeurs
├── .gitignore
├── docker-compose.yml                   # stack complète
├── docker-compose.override.yml          # surcharges de développement (hot-reload, ports exposés)
├── README.md
├── ARCHITECTURE.md
│
├── nginx/
│   ├── nginx.conf                       # reverse proxy + SPA fallback + headers sécurité
│   └── nginx.dev.conf                   # variante dev
│
├── backend/
│   ├── Dockerfile                       # multi-stage (builder + runtime non-root)
│   ├── pyproject.toml                   # deps Python, config Ruff, config Pytest
│   ├── .env.example
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # création de l'app FastAPI, middlewares, lifespan
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                # Settings Pydantic (BaseSettings, lit .env)
│   │   │   ├── database.py              # engine, async_session, get_db dependency
│   │   │   ├── security.py              # Argon2, JWT encode/decode, cookie utils
│   │   │   ├── permissions.py           # require_admin, require_owner_or_admin
│   │   │   ├── exceptions.py            # exceptions métier + handlers FastAPI
│   │   │   └── logging.py               # logger structuré JSON
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── router.py            # agrège tous les routers de modules
│   │   │
│   │   └── modules/
│   │       ├── auth/
│   │       │   ├── router.py
│   │       │   ├── schemas.py           # LoginRequest, RegisterRequest, TokenResponse
│   │       │   ├── service.py
│   │       │   └── dependencies.py      # get_current_user
│   │       │
│   │       ├── users/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # User ORM model
│   │       │   ├── service.py
│   │       │   └── repository.py
│   │       │
│   │       ├── categories/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py
│   │       │   ├── service.py
│   │       │   └── repository.py
│   │       │
│   │       ├── courses/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py
│   │       │   ├── service.py
│   │       │   ├── repository.py
│   │       │   └── dependencies.py      # get_course_or_404, require_course_owner
│   │       │
│   │       ├── contents/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # CourseContent ORM model
│   │       │   ├── service.py
│   │       │   └── repository.py
│   │       │
│   │       ├── files/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # FileAsset ORM model
│   │       │   ├── service.py
│   │       │   ├── repository.py
│   │       │   ├── storage.py           # ABC FileStorage
│   │       │   ├── local_storage.py     # LocalFileStorage (MVP)
│   │       │   └── s3_storage.py        # S3FileStorage (production future)
│   │       │
│   │       ├── learning_paths/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # LearningPath + LearningPathCourse
│   │       │   ├── service.py
│   │       │   └── repository.py
│   │       │
│   │       ├── assignments/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # Assignment ORM model
│   │       │   ├── service.py           # déclenche création enrollment
│   │       │   └── repository.py
│   │       │
│   │       ├── enrollments/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # Enrollment ORM model
│   │       │   ├── service.py
│   │       │   └── repository.py
│   │       │
│   │       ├── progress/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # ContentProgress ORM model
│   │       │   ├── service.py           # recalculate_enrollment_progress()
│   │       │   └── repository.py
│   │       │
│   │       ├── quizzes/
│   │       │   ├── router.py
│   │       │   ├── schemas.py
│   │       │   ├── models.py            # Quiz, QuizQuestion, QuizAttempt, QuizAnswer
│   │       │   ├── service.py           # start_attempt, submit_answer, complete_attempt
│   │       │   └── repository.py
│   │       │
│   │       └── quiz_generation/
│   │           ├── router.py
│   │           ├── schemas.py
│   │           ├── models.py            # QuizGenerationJob ORM model
│   │           ├── service.py           # trigger(), poll status
│   │           ├── pipeline.py          # orchestrateur du pipeline
│   │           ├── chunker.py           # découpage texte en chunks
│   │           ├── ai_provider.py       # appel HTTP vers AI Provider
│   │           ├── validator.py         # validation Pydantic des questions générées
│   │           └── extractors/
│   │               ├── base.py
│   │               ├── text_extractor.py
│   │               ├── pdf_extractor.py
│   │               ├── csv_extractor.py
│   │               ├── audio_extractor.py
│   │               └── web_extractor.py
│   │
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/                    # fichiers Alembic générés
│   │
│   └── tests/
│       ├── conftest.py                  # fixtures : db, users, cours, enrollments
│       ├── test_auth.py
│       ├── test_users.py
│       ├── test_categories.py
│       ├── test_courses.py
│       ├── test_contents.py
│       ├── test_files.py
│       ├── test_learning_paths.py
│       ├── test_assignments.py
│       ├── test_enrollments.py
│       ├── test_progress.py
│       ├── test_quizzes.py
│       └── test_quiz_generation.py
│
└── frontend/
    ├── Dockerfile                       # multi-stage : build Node + serve Nginx
    ├── package.json
    ├── tsconfig.json
    ├── tsconfig.app.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── components.json                  # configuration shadcn/ui
    ├── .env.example
    │
    ├── public/
    │   └── favicon.svg
    │
    └── src/
        ├── main.tsx                     # point d'entrée : ReactDOM.createRoot
        │
        ├── app/
        │   ├── router/
        │   │   └── index.tsx            # createBrowserRouter, toutes les routes + ProtectedRoute
        │   ├── providers/
        │   │   └── index.tsx            # QueryClientProvider + AuthProvider
        │   └── config/
        │       └── index.ts             # constantes globales, base URL API
        │
        ├── features/
        │   ├── auth/
        │   │   ├── api.ts
        │   │   ├── hooks/
        │   │   │   └── useAuth.ts
        │   │   ├── components/
        │   │   │   └── LoginForm.tsx
        │   │   └── pages/
        │   │       ├── LoginPage.tsx
        │   │       └── RegisterPage.tsx
        │   │
        │   ├── dashboard/
        │   │   ├── hooks/
        │   │   └── pages/
        │   │       └── DashboardPage.tsx
        │   │
        │   ├── users/                   # (même structure)
        │   ├── categories/
        │   ├── courses/
        │   │   ├── api.ts
        │   │   ├── hooks/
        │   │   │   ├── useCourses.ts
        │   │   │   └── useCourse.ts
        │   │   ├── components/
        │   │   │   ├── CourseCard.tsx
        │   │   │   ├── CourseForm.tsx
        │   │   │   └── CourseStatusBadge.tsx
        │   │   └── pages/
        │   │       ├── CoursesListPage.tsx
        │   │       ├── CourseDetailPage.tsx
        │   │       └── CourseEditPage.tsx
        │   │
        │   ├── contents/
        │   ├── learning-paths/
        │   ├── assignments/
        │   ├── enrollments/
        │   ├── progress/
        │   └── quizzes/
        │       ├── api.ts
        │       ├── hooks/
        │       ├── components/
        │       │   ├── QuizQuestion.tsx
        │       │   └── QuizResults.tsx
        │       └── pages/
        │           └── QuizAttemptPage.tsx
        │
        ├── components/
        │   ├── ui/                      # composants shadcn/ui (Button, Card, Dialog...)
        │   ├── layout/
        │   │   ├── AppLayout.tsx
        │   │   ├── Sidebar.tsx
        │   │   └── Header.tsx
        │   └── common/
        │       ├── ProtectedRoute.tsx
        │       ├── AdminRoute.tsx
        │       ├── ErrorBoundary.tsx
        │       ├── LoadingSpinner.tsx
        │       └── Pagination.tsx
        │
        ├── lib/
        │   ├── api-client.ts            # instance fetch/axios configurée (base URL, cookies)
        │   ├── auth.ts                  # AuthContext, AuthProvider
        │   └── utils.ts                 # cn(), formatDate(), etc.
        │
        ├── types/
        │   ├── auth.ts                  # User, Role
        │   ├── course.ts                # Course, CourseContent, CourseStatus
        │   ├── learning-path.ts
        │   ├── assignment.ts
        │   ├── enrollment.ts
        │   ├── progress.ts
        │   ├── quiz.ts                  # Quiz, QuizQuestion, QuizAttempt
        │   └── api.ts                   # PaginatedResponse<T>, ErrorResponse
        │
        └── tests/
            ├── setup.ts                 # vitest setup, MSW server
            ├── mocks/
            │   └── handlers.ts          # MSW request handlers
            └── features/
                ├── auth.test.tsx
                ├── courses.test.tsx
                └── quizzes.test.tsx
```

---

## 16. Ambiguïtés et contradictions — analyse et résolutions

### #1 — Entité `FileAsset` absente du modèle de données

**Constat :** `CourseContent.file_asset_id` est référencé dans le modèle, mais la table `FileAsset` n'est jamais définie dans le readme. La section "Gestion des fichiers" décrit les backends de stockage mais pas la structure de métadonnées en base.

**Résolution :** Ajout d'une table `file_assets` explicite (§4.4 de ce document) avec les champs : `id, original_filename, stored_filename, mime_type, size_bytes, storage_backend, storage_path, uploaded_by, created_at`. Référencée par `course_contents.file_asset_id`, `courses.cover_image_id`, `learning_paths.cover_image_id`.

---

### #2 — `cover_image` sur Course et LearningPath : string ou FK ?

**Constat :** Le readme nomme le champ `cover_image` sans préciser si c'est une URL, un chemin, ou une FK vers `FileAsset`.

**Résolution :** Le champ est renommé `cover_image_id` (UUID FK vers `file_assets`) pour cohérence avec le système de fichiers unifié. Cela garantit que toutes les images passent par les mêmes contrôles de validation et de sécurité.

---

### #3 — Endpoint `/auth/refresh` absent de la liste API

**Constat :** Le readme mentionne "rotation des refresh tokens" et "Expiration des sessions" mais l'endpoint `POST /auth/refresh` n'apparaît pas dans la liste des endpoints.

**Résolution :** Ajout explicite de `POST /auth/refresh` (§11.1) qui lit le refresh token depuis le cookie, valide en DB, émet de nouveaux tokens (rotation), et invalide l'ancien.

---

### #4 — Endpoints Learning Paths absents de la liste API

**Constat :** Le readme définit le modèle `LearningPath` et le module `learning_paths/` backend, mais aucun endpoint n'est listé dans la section "API REST".

**Résolution :** Ajout d'un groupe complet d'endpoints `/learning-paths` (§11.7) incluant CRUD, publication, gestion des cours associés et réordonnancement.

---

### #5 — Endpoints de suivi de progression absents

**Constat :** `GET /progress` est listé mais sans détail. L'endpoint pour qu'un learner marque un contenu comme "consulté/complété" est absent.

**Résolution :** Ajout de `POST /enrollments/{enrollment_id}/contents/{content_id}/progress` (§11.9) pour la mise à jour du `ContentProgress`, et `GET /enrollments/{id}/progress` pour récupérer la progression détaillée par contenu.

---

### #6 — Ambiguïté Assignment → Enrollment pour les Learning Paths

**Constat :** Quand un `Assignment` cible une `LEARNING_PATH`, combien d'Enrollments sont créés ? Une par LP, ou une par cours dans la LP ?

**Résolution retenue :** Une `Enrollment` par cours dans la LP (pour tracker la progression au niveau granulaire des contenus) + une `Enrollment` "parent" avec `learning_path_id` non null pour la progression globale de la LP. Justification : la progression `ContentProgress` est toujours liée à un `Enrollment` + `CourseContent`, donc la granularité cours est nécessaire.

---

### #7 — Politique de retentatives de quiz non définie

**Constat :** Le modèle permet plusieurs `QuizAttempt` par utilisateur/quiz, mais le readme ne précise pas si un learner peut retenter, combien de fois, et quel score est retenu.

**Résolution retenue :** Tentatives illimitées autorisées (sujet à une politique configurable). Le meilleur score est retenu pour la progression. Toutes les tentatives sont conservées en historique. Contrainte : une seule tentative peut être "ouverte" (sans `completed_at`) à la fois par utilisateur+quiz.

---

### #8 — Ownership de LearningPath non explicitement défini

**Constat :** Le readme définit `LearningPath.created_by` mais n'indique pas explicitement si la règle d'isolation "USER A ne peut pas modifier la LP de USER B" s'applique (alors qu'elle est explicitement définie pour les cours).

**Résolution :** La même règle d'isolation s'applique aux LearningPaths via `created_by`. Les dépendances FastAPI `require_lp_owner_or_admin` sont symétriques à `require_course_owner_or_admin`.

---

### #9 — Transcription AUDIO : provider non spécifié, complexité MVP

**Constat :** La stratégie d'extraction pour les contenus `AUDIO` est "Transcription" mais aucun provider n'est mentionné. La transcription peut coûter cher et être complexe à intégrer.

**Résolution :** Pour le MVP (Phase 8), la transcription audio est **optionnelle** : si aucun provider de transcription n'est configuré (`AUDIO_TRANSCRIPTION_PROVIDER` vide), les contenus AUDIO sont ignorés dans le pipeline de génération (les questions sont générées à partir des autres types de contenu). Le provider est configurable via `.env` (ex. OpenAI Whisper API). L'extraction est découplée via l'interface `BaseExtractor`, donc ajout sans impact sur le reste du pipeline.

---

### #10 — SSRF via contenus WEB_LINK

**Constat :** Le pipeline de génération récupère les URLs des contenus `WEB_LINK` côté serveur (Server-Side Request Forgery risk). Le readme mentionne "récupération contrôlée" sans détailler les garde-fous.

**Résolution :** Contrôles listés en §9.5 : HTTPS uniquement, blocage RFC1918/loopback/link-local, timeout 10s, taille max 2MB, résolution DNS avant connexion pour vérifier l'IP. Ces contrôles sont **obligatoires**, pas optionnels.

---

### #11 — Qui peut accéder aux quiz attempts d'un utilisateur ?

**Constat :** Non précisé dans le readme.

**Résolution :** L'utilisateur lui-même (`user_id == current_user.id`) et l'ADMIN. Le course owner ne voit **pas** les tentatives individuelles des learners (confidentialité). Des statistiques agrégées anonymisées pourraient être ajoutées dans une phase ultérieure.

---

### #12 — Génération de quiz sur un cours DRAFT

**Constat :** Aucune précision sur les statuts de cours autorisant la génération de quiz.

**Résolution :** La génération de quiz est autorisée sur un cours `DRAFT` ou `PUBLISHED` (le owner doit pouvoir tester avant publication). Les quiz générés sur un cours `DRAFT` sont en statut `DRAFT` et ne sont accessibles qu'au owner et à l'ADMIN. Ils passent en `ACTIVE` automatiquement quand le cours est publié.

---

### #13 — Dénormalisation `enrollment.course_id` : risque d'incohérence

**Constat :** `Enrollment.course_id` est dénormalisé depuis `Assignment.target_id`. Si l'assignment est modifié, cette valeur peut devenir incohérente.

**Résolution :** `course_id` et `learning_path_id` dans `Enrollment` sont définis **à la création uniquement** et ne sont jamais modifiables après. Si un assignment est annulé et recréé, un nouvel enrollment est créé. Cela est garanti par le service (pas de PATCH sur ces champs).

---

*Document produit à partir de `readme.md`. Toute modification substantielle des spécifications doit être répercutée dans ce document avant implémentation.*
