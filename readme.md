# LMS — Plateforme e-learning multi-utilisateur avec génération automatique de quiz

Application web d'entreprise de type **Learning Management System (LMS)** — moderne, sécurisée, maintenable et évolutive.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Rôles et capacités](#rôles-et-capacités)
3. [Stack technique](#stack-technique)
4. [Architecture](#architecture)
5. [Modules backend](#modules-backend)
6. [Structure frontend](#structure-frontend)
7. [Modèles de données](#modèles-de-données)
8. [Authentification et autorisation](#authentification-et-autorisation)
9. [Gestion des fichiers](#gestion-des-fichiers)
10. [Moteur de quiz IA](#moteur-de-quiz-ia)
11. [API REST](#api-rest)
12. [Docker et infrastructure](#docker-et-infrastructure)
13. [Tests](#tests)
14. [Plan de développement](#plan-de-développement)
15. [Critères d'acceptation](#critères-dacceptation)
16. [Vision future](#vision-future)

---

## Vue d'ensemble

La plateforme permet à des utilisateurs de :

- créer et gérer leurs propres cours ;
- ajouter différents types de contenus pédagogiques ;
- publier et gérer leurs cours ;
- suivre des cours qui leur sont affectés ;
- suivre leur progression ;
- répondre à des quiz générés automatiquement à partir des contenus pédagogiques.

Un **administrateur global** dispose d'un accès complet à l'application.

L'architecture est conçue pour évoluer vers des fonctionnalités avancées : learning paths, adaptive learning, statistiques, gamification, certificats, recommandations, etc.

> **Instance unique** — pas de multi-tenancy. Aucune notion d'organisation, tenant, company, department, team ou group.

---

## Rôles et capacités

```
ADMIN   — accès complet à toute l'application
USER
├── LEARNER         — apprendre, suivre des cours affectés, répondre aux quiz
└── COURSE CREATOR  — créer, gérer et publier ses propres cours
```

Tout utilisateur authentifié peut simultanément apprendre et créer des cours.

**Règle d'isolation absolue :** un USER ne peut jamais modifier ou supprimer le cours d'un autre utilisateur.

Le modèle de sécurité repose sur : `User` · `Role` · `Ownership` · `Assignment` · `Enrollment` · `Permissions`

---

## Stack technique

### Frontend

| Outil | Usage |
|-------|-------|
| React + TypeScript | Framework UI |
| Vite | Bundler |
| React Router | Navigation |
| TanStack Query | Data fetching et cache |
| React Hook Form + Zod | Formulaires et validation |
| shadcn/ui + Tailwind CSS | Composants et styles |
| Vitest + Testing Library | Tests |

Le frontend doit être fortement typé. Éviter `any` sauf nécessité exceptionnelle et documentée.

### Backend

| Outil | Usage |
|-------|-------|
| Python + FastAPI | API REST |
| Pydantic v2 | Validation et sérialisation |
| SQLAlchemy 2.x + Alembic | ORM et migrations |
| PostgreSQL | Base de données |
| Pytest + Ruff | Tests et linting |

### Infrastructure

| Outil | Usage |
|-------|-------|
| Docker + Docker Compose | Containerisation |
| Nginx ou Traefik | Reverse proxy |
| PostgreSQL (Docker) | Base de données persistante |
| Docker Volume | Stockage fichiers (MVP, remplaçable par S3) |

---

## Architecture

```
                     Browser
                        │
                        │ HTTPS
                        ▼
                Reverse Proxy (Nginx)
                        │
         ┌──────────────┴──────────────┐
         │                             │
         ▼                             ▼
    React Frontend               FastAPI Backend
                                        │
                     ┌──────────────────┼──────────────────┐
                     │                  │                   │
                     ▼                  ▼                   ▼
                PostgreSQL         File Storage         AI Provider
                     │
                     ▼
               Volume persistant
```

Le backend est un **monolithe modulaire** organisé par domaines métier — pas de microservices.

---

## Modules backend

```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py
│   │       └── ...
│   └── modules/
│       ├── auth/
│       ├── users/
│       ├── categories/
│       ├── courses/
│       ├── contents/
│       ├── files/
│       ├── learning_paths/
│       ├── assignments/
│       ├── enrollments/
│       ├── progress/
│       ├── quizzes/
│       └── quiz_generation/
├── migrations/
├── tests/
├── pyproject.toml
└── Dockerfile
```

Chaque module peut contenir : `router.py` · `schemas.py` · `models.py` · `service.py` · `repository.py` · `dependencies.py`

---

## Structure frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── router/
│   │   ├── providers/
│   │   └── config/
│   ├── features/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── users/
│   │   ├── categories/
│   │   ├── courses/
│   │   ├── contents/
│   │   ├── learning-paths/
│   │   ├── assignments/
│   │   ├── enrollments/
│   │   ├── progress/
│   │   └── quizzes/
│   ├── components/
│   │   ├── ui/
│   │   ├── layout/
│   │   └── common/
│   ├── lib/
│   │   ├── api-client.ts
│   │   ├── auth.ts
│   │   └── utils.ts
│   ├── types/
│   └── main.tsx
└── public/
```

Architecture orientée **feature**. La logique métier ne doit pas résider dans les composants React.

---

## Modèles de données

### User

```
User
├── id
├── email
├── password_hash
├── first_name · last_name
├── role          (ADMIN | USER)
├── is_active
└── created_at · updated_at
```

### Course

```
Course
├── id
├── owner_id      (obligatoire)
├── category_id
├── title · description
├── cover_image
├── status        (DRAFT | PUBLISHED | ARCHIVED)
└── created_at · updated_at
```

### CourseContent

```
CourseContent
├── id
├── course_id
├── type          (TEXT | PDF | CSV | AUDIO | WEB_LINK)
├── title
├── text_content · file_asset_id · external_url
├── position
└── created_at
```

Les contenus sont ordonnés et réordonnables.

### LearningPath

```
LearningPath                    LearningPathCourse
├── id                          ├── learning_path_id
├── title · description         ├── course_id
├── cover_image                 └── position
├── created_by
├── status
└── created_at · updated_at
```

### Assignment

```
Assignment
├── id
├── user_id
├── target_type   (COURSE | LEARNING_PATH)
├── target_id
├── assigned_by
├── starts_at · due_date
├── status        (PENDING | ACTIVE | COMPLETED | EXPIRED | CANCELLED)
└── created_at
```

Un seul `target_type` par affectation — jamais `course_id` et `learning_path_id` simultanément.

### Enrollment

> **Ownership ≠ Enrollment** : créer un cours ne signifie pas être inscrit à ce cours.

```
Assignment → Enrollment → User learning
```

```
Enrollment
├── id
├── user_id
├── assignment_id
├── course_id / learning_path_id
├── status        (NOT_STARTED | IN_PROGRESS | COMPLETED | OVERDUE | CANCELLED)
├── started_at · completed_at · due_date
└── progress_percent
```

### Progress

```
ContentProgress
├── id
├── enrollment_id
├── content_id
├── status · progress_percent
├── last_position
└── completed_at
```

La progression est calculée de 0 % à 100 % et persistée en base.

### Quiz

```
Quiz                            QuizGenerationJob
├── id                          ├── id
├── course_id                   ├── course_id
├── version                     ├── status   (PENDING | PROCESSING | COMPLETED | FAILED)
├── status                      ├── started_at · completed_at
├── difficulty (EASY|MEDIUM|HARD)└── error_message
├── question_count
└── generated_at

QuizQuestion                    QuizAttempt
├── id                          ├── id
├── quiz_id                     ├── quiz_id
├── question                    ├── user_id · enrollment_id
├── options                     ├── score
├── correct_option_id           └── started_at · completed_at
├── explanation
├── source_content_id           QuizAnswer
└── source_reference            ├── id
                                ├── attempt_id · question_id
                                ├── selected_option_id
                                └── is_correct
```

---

## Authentification et autorisation

### Authentification

- Hachage des mots de passe avec **Argon2**
- Cookies `HttpOnly` et `Secure`, protection CSRF si nécessaire
- Expiration des sessions et rotation des refresh tokens
- Jamais de mot de passe en clair, jamais de secrets dans le dépôt
- Fichier `.env.example` fourni sans valeurs réelles

### Autorisation

L'autorisation est appliquée **côté backend uniquement** — le frontend n'est jamais une couche de sécurité.

```
current_user.id == resource.owner_id  →  accès autorisé
current_user.role == ADMIN            →  accès autorisé
```

Un utilisateur ne peut pas accéder à une ressource en connaissant simplement son UUID.

---

## Gestion des fichiers

Les binaires ne sont **jamais** stockés dans PostgreSQL. PostgreSQL stocke uniquement les métadonnées.

```
FileStorage
├── LocalFileStorage   (MVP — Docker Volume)
└── S3FileStorage      (production future — S3 / MinIO / Azure Blob)
```

Types autorisés : `PDF` · `CSV` · `Audio` · `Images`

Contrôles backend obligatoires : taille maximale, extension + MIME type validés côté serveur, nom de fichier interne généré, extensions dangereuses interdites, stockage hors du code source.

---

## Moteur de quiz IA

**Les quiz ne sont jamais créés manuellement.** Le système analyse le contenu et génère les questions automatiquement.

### Pipeline de génération

```
Course Contents → Extraction → Nettoyage → Normalisation → Chunking → AI Provider → Validation → Persistance
```

### Stratégie d'extraction par type

| Type | Stratégie |
|------|-----------|
| `TEXT` | Texte directement disponible |
| `PDF` | Extraction de texte |
| `CSV` | Parsing structuré |
| `AUDIO` | Transcription |
| `WEB_LINK` | Récupération contrôlée |

### Génération asynchrone

```
FastAPI → Job Queue → Worker → Content Processing → AI Provider
```

Le job expose un statut consultable : `PENDING` → `PROCESSING` → `COMPLETED` / `FAILED`

### Validation des questions générées

La sortie du modèle IA n'est jamais considérée comme valide automatiquement. Chaque question est validée sur :

- nombre d'options, absence de doublons
- exactement une réponse correcte
- présence d'une explication et d'une référence au contenu source
- structure Pydantic valide et règles métier

### Source grounding

```
QuizQuestion
├── source_content_id
├── source_reference
└── (source_page · source_section · source_chunk si disponibles)
```

### Versionnement

Si le contenu pédagogique change, un nouveau quiz est généré (version N+1). Les anciennes tentatives restent liées à la version du quiz utilisée au moment de la tentative.

---

## API REST

Base URL : `/api/v1`

```
# Auth
POST   /auth/register
POST   /auth/login
POST   /auth/logout
GET    /auth/me

# Users (ADMIN)
GET    /users
GET    /users/{id}

# Categories
GET    /categories
POST   /categories          (ADMIN)

# Courses
GET    /courses
POST   /courses
GET    /courses/{id}
PATCH  /courses/{id}
DELETE /courses/{id}

# Contents
POST   /courses/{id}/contents
PATCH  /contents/{id}
DELETE /contents/{id}

# Quiz
POST   /courses/{id}/quiz/generate
GET    /courses/{id}/quiz

# Assignments (ADMIN)
POST   /assignments
GET    /assignments

# Enrollments & Progress
GET    /enrollments
GET    /progress

# Quiz Attempts
POST   /quizzes/{id}/attempts
POST   /quiz-attempts/{id}/answers
POST   /quiz-attempts/{id}/complete
```

### Sécurité des API

- Validation Pydantic sur toutes les entrées
- Rate limiting sur les endpoints sensibles, protection brute-force sur le login
- CORS strictement configuré, headers de sécurité
- Logs sans données sensibles (jamais de hash, token ou secret)
- Gestion centralisée des exceptions

Format d'erreur standardisé :

```json
{
  "code": "COURSE_ACCESS_DENIED",
  "message": "You do not have permission to access this course."
}
```

---

## Docker et infrastructure

Services Docker Compose :

```
frontend   — React (Nginx)
backend    — FastAPI
postgres   — PostgreSQL avec volume persistant
```

Exigences :
- healthchecks sur tous les services
- réseaux internes, PostgreSQL non exposé publiquement
- Dockerfiles multi-stage, utilisateurs non-root
- variables d'environnement via `.env`

### Index PostgreSQL prioritaires

```sql
users.email
courses.owner_id · courses.category_id
assignments.user_id
enrollments.user_id
quiz_attempts.user_id
content_progress.enrollment_id
```

### Environnements

```
development · test · production
```

Fichier `.env.example` fourni avec toutes les variables documentées.

- **Développement** : `docker compose up --build` (applique automatiquement `docker-compose.override.yml` — reload, port Postgres exposé)
- **Production** : `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build` (`COOKIE_SECURE=true`, pas de reload, Postgres non exposé)

---

## Tests

### Backend (Pytest)

Authentification, autorisation, ownership, CRUD des cours, affectations, inscriptions, calcul de progression, scoring des quiz, validation de la génération, validation des uploads.

### Frontend (Vitest + Testing Library)

Login, routes protégées, création et listage des cours, affichage des affectations, interaction avec les quiz.

Tests d'intégration ajoutés là où pertinent.

---

## Plan de développement

| Phase | Périmètre |
|-------|-----------|
| **1** | Infrastructure — Docker, PostgreSQL, FastAPI, React, healthchecks, migrations, linting |
| **2** | Authentification — register, login, logout, rôles, routes protégées |
| **3** | Cours — catégories, CRUD, ownership, publication, UI |
| **4** | Contenus — texte, PDF, CSV, audio, liens web, upload, validation |
| **5** | Learning Paths — création, ajout de cours, ordre, publication |
| **6** | Affectations — ADMIN assignment, enrollment, deadlines, dashboard learner |
| **7** | Progression — suivi contenu, progression cours, statuts enrollment |
| **8** | Moteur quiz IA — extraction, normalisation, AI provider, génération async, validation |
| **9** | Expérience quiz — UI quiz, tentatives, scoring, feedback, historique |
| **10** | Hardening — sécurité, tests, performance, Docker production, documentation |

Après chaque phase : `docker compose up` doit démarrer le projet sans erreur.

Avant chaque fonctionnalité importante : approche → modèles → endpoints → permissions → implémentation → tests → migrations → intégration.

---

## Critères d'acceptation

### Scénario ADMIN

```
Connexion
→ Créer catégorie → Créer learning path
→ Créer cours → Ajouter image + texte + PDF + CSV + audio + lien web
→ Publier → Générer quiz → Vérifier quiz
→ Affecter à USER A avec deadline
```

### Scénario USER — Learner

```
Connexion → Voir cours affecté → Ouvrir cours → Consulter contenus
→ Progression enregistrée → Répondre au quiz
→ Obtenir score + feedback → Voir progression → Terminer le cours
```

### Scénario USER — Course Creator

```
Connexion → Créer cours → Ajouter contenu
→ Générer quiz automatiquement → Publier → Gérer le cours
```

### Règle d'isolation

```
USER A  →  peut modifier Course A (le sien)
USER A  →  NE PEUT PAS modifier Course B (appartenant à USER B)
ADMIN   →  peut modifier Course A et Course B
```

---

## Vision future

Fonctionnalités prévues (hors MVP) — l'architecture doit les permettre sans réécriture du cœur :

```
Adaptive Learning · Gamification · Badges · Certificats · Leaderboards
Recommandations · Spaced Repetition · Analytics avancées
Notifications · Email · Application mobile
Stockage S3 · Moteur de recherche
AI Tutor · Résumés IA · Flashcards IA
```

---

## Priorités

```
Sécurité > Exactitude > Maintenabilité > Architecture > UX > Performance > Fonctionnalités
```

- L'autorisation est **toujours** appliquée côté backend
- Le frontend n'est **jamais** une couche de sécurité
- Les outputs IA ne sont **jamais** automatiquement valides
- La connaissance d'un UUID ne suffit **jamais** à accéder à une ressource
