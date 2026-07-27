# StageFlow — API de gestion sécurisée des stages data

StageFlow est une API REST développée avec FastAPI dans le cadre de la gestion des offres de stage, des candidatures étudiantes, des validations pédagogiques et des avis des encadrants. Celle ci, tout en garantissant qu'une entreprise ne puisse jamais accéder aux données d'une autre.

## Contexte fonctionnel

Un étudiant peut consulter les offres publiées, déposer une candidature et suivre son statut au fil du temps. Un responsable pédagogique valide ou refuse les offres avant leur publication, et arbitre les candidatures en les acceptant ou en les refusant. Une entreprise propose ses propres offres de stage et ne peut consulter que les candidatures liées à ces offres, jamais celles d'une autre entreprise. Un administrateur gère les comptes utilisateurs et les rôles qui leur sont attribués.

## Rôles et permissions

Le rôle `student` permet de lire les offres publiées, de créer ses propres candidatures et de les retirer tant qu'elles n'ont pas été acceptées. 
Le rôle `company` permet de créer des offres à l'état de brouillon, de les soumettre pour validation, et de consulter uniquement les candidatures reçues sur ses propres offres. 
Le rôle `program_manager` permet de publier ou de refuser une offre qui a été soumise, d'accepter ou de refuser une candidature, et de consulter des statistiques globales sur l'activité de la plateforme. 
Le rôle `admin` permet de gérer les comptes utilisateurs ainsi que les rôles qui leur sont associés.

Toutes ces vérifications de permissions sont centralisées dans une seule dépendance FastAPI, `require_role`, définie dans `app/dependencies/permissions.py`.

## Architecture du projet

Le code applicatif vit dans le dossier `app/`, organisé en couches dont chacune a une responsabilité unique. 
Le fichier `app/main.py` se limite à assembler les middlewares et les routers, sans contenir de logique métier. 
Le dossier `app/core/` regroupe la configuration lue depuis les variables d'environnement, la connexion asynchrone à la base de données, ainsi que les fonctions de hachage des mots de passe et de génération des tokens JWT. 
Le dossier `app/dependencies/` contient la vérification centralisée des rôles évoquée plus haut. 
Le dossier `app/middleware/` contient trois middlewares : un qui limite le débit de requêtes par utilisateur ou par adresse IP, un qui ajoute un identifiant unique à chaque requête pour faciliter le suivi dans les journaux, et un qui ajoute des en-têtes de sécurité HTTP à chaque réponse.

Le dossier `app/models/` définit les tables de la base de données à l'aide de SQLAlchemy, à savoir les utilisateurs, les rôles, les offres et les candidatures. 
Le dossier `app/repositories/` est le seul endroit du code autorisé à interroger directement la base de données ; chaque route passe systématiquement par un repository plutôt que d'exécuter une requête SQLAlchemy elle-même. 
Le dossier `app/routes/` contient les points d'entrée HTTP de l'API, répartis entre l'authentification, les utilisateurs, les offres et les candidatures. 
Le dossier `app/schemas/` définit les schémas Pydantic qui valident les données entrantes et qui contrôlent précisément ce qui est renvoyé au client, en s'assurant par exemple qu'un mot de passe haché n'est jamais exposé dans une réponse.

Les tests automatisés se trouvent dans `tests/`, séparés entre tests unitaires et tests d'intégration qui appellent l'API de bout en bout via un client HTTP asynchrone. Les migrations de base de données sont gérées par Alembic dans le dossier `alembic/`, configuré pour fonctionner en mode asynchrone avec le pilote PostgreSQL utilisé par le projet.

## Stack technique

Le projet repose sur FastAPI pour le framework web et la génération automatique de la documentation OpenAPI. La persistance des données utilise SQLAlchemy 2.0 en mode asynchrone, couplé au pilote asyncpg pour dialoguer avec PostgreSQL 16. Les migrations de schéma sont gérées par Alembic. La validation des données et la sérialisation des réponses reposent sur Pydantic v2. L'authentification utilise des tokens JWT générés et vérifiés avec python-jose, tandis que les mots de passe sont hachés avec bcrypt via passlib. Les tests s'appuient sur pytest, son extension pytest-asyncio pour les tests asynchrones, et httpx comme client HTTP de test. L'ensemble est conteneurisé avec Docker et Docker Compose, et l'intégration continue passe par GitHub Actions couplé à Codecov pour le suivi de la couverture de tests.

## Installation

Le projet nécessite Python 3.11 ou une version plus récente, ainsi que Docker Desktop avec le support WSL2 activé sous Windows. Il a été testé et validé avec Python 3.11 à l'intérieur du conteneur Docker, et fonctionne également avec Python 3.14 en environnement local à condition d'épingler la version `bcrypt==4.0.1`, pour éviter une incompatibilité connue entre `passlib` et les versions plus récentes de `bcrypt`.

Après avoir cloné le dépôt et s'être placé dans le dossier du projet, créez un environnement virtuel avec `python -m venv .venv`, puis activez-le selon votre système d'exploitation. Une fois activé, installez les dépendances du projet avec `pip install -r requirements.txt`.

## Variables d'environnement

Un fichier `.env` doit être créé à la racine du projet, et ne doit jamais être commité sur Git puisqu'il est listé dans `.gitignore`. Il doit définir `DATABASE_URL`, l'adresse de connexion à la base de données de développement, `TEST_DATABASE_URL`, l'adresse de connexion à une base dédiée aux tests automatisés, `SECRET_KEY`, la clé utilisée pour signer les tokens JWT, et `ACCESS_TOKEN_EXPIRE_MINUTES`, la durée de validité d'un token. Si le mot de passe de la base de données contient le caractère `@`, celui-ci doit être remplacé par son équivalent encodé `%40` dans l'URL de connexion, puisque ce caractère sert normalement de séparateur dans le format d'une URL.

## Lancement de l'application

La méthode recommandée consiste à lancer l'ensemble via Docker Compose avec la commande `docker compose up -d --build`, qui démarre à la fois le service de base de données PostgreSQL, muni d'une vérification de santé garantissant que l'API n'essaiera de s'y connecter qu'une fois celle-ci réellement prête à accepter des connexions, et le service applicatif FastAPI, lancé avec rechargement à chaud pour faciliter le développement. Une fois les conteneurs démarrés, la disponibilité du service peut être vérifiée en interrogeant `http://localhost:8000/health`, et la documentation interactive de l'API est accessible sur `http://localhost:8000/docs`.

Avant la première utilisation, les quatre rôles de base doivent être insérés manuellement dans la base de données, à l'aide d'une commande SQL exécutée dans le conteneur de la base de données, insérant les rôles `student`, `company`, `program_manager` et `admin` dans la table correspondante.

## Migrations de base de données

Les migrations sont gérées par Alembic, configuré en mode asynchrone pour rester cohérent avec l'usage d'asyncpg dans le reste du projet. Une nouvelle migration se génère automatiquement en comparant les modèles SQLAlchemy à l'état actuel de la base, puis s'applique réellement à l'aide de la commande de mise à niveau d'Alembic, les deux étant exécutées à l'intérieur du conteneur applicatif.

## Lancement des tests

L'ensemble de la suite de tests se lance avec `pytest`, exécuté à l'intérieur du conteneur applicatif pour garantir qu'il tourne dans les mêmes conditions que l'environnement de production. La mesure de la couverture de code s'obtient en ajoutant les options appropriées à cette même commande. Les tests couvrent actuellement l'authentification, avec une connexion réussie, une connexion échouée et un accès refusé en l'absence de token ; l'isolation des données entre entreprises, en vérifiant qu'une entreprise ne peut pas consulter les candidatures d'une offre qui ne lui appartient pas mais peut bien consulter les siennes ; le respect d'un invariant métier interdisant la soumission d'une offre dont le titre, la mission ou les compétences ne sont pas renseignés ; le parcours complet d'une offre de bout en bout, depuis sa création jusqu'à l'acceptation d'une candidature ; et enfin le bon déclenchement de la limitation de débit lorsque le nombre de requêtes autorisées est dépassé. Chaque test s'exécute sur une base de données dédiée, entièrement purgée et recréée avant et après chaque exécution, afin de garantir une isolation complète entre les tests.

## Endpoints principaux

L'inscription d'un nouvel utilisateur et l'obtention d'un token se font via une requête POST sur `/auth/register`, tandis que la connexion d'un utilisateur existant se fait via POST sur `/auth/login`. Les informations sur l'utilisateur actuellement connecté s'obtiennent avec une requête GET sur `/users/me`, accessible à tout utilisateur authentifié.

La création d'une offre, réservée au rôle `company`, se fait via POST sur `/offers`, et produit une offre à l'état de brouillon. Sa soumission, réservée à l'entreprise propriétaire, se fait via PATCH sur `/offers/{id}/submit`. La décision de publier ou de refuser une offre soumise, réservée au responsable pédagogique, se fait via PATCH sur `/offers/{id}/review`. La consultation des candidatures liées à une offre se fait via GET sur `/offers/{id}/applications`, accessible à l'entreprise propriétaire de l'offre ainsi qu'au responsable pédagogique.

Le dépôt d'une candidature à une offre publiée, réservé au rôle `student`, se fait via POST sur `/offers/{id}/applications`. La consultation de ses propres candidatures se fait via GET sur `/applications/me`. La décision d'accepter ou de refuser une candidature, réservée au responsable pédagogique, se fait via PATCH sur `/applications/{id}/decision`. Le retrait d'une candidature par l'étudiant qui l'a déposée, possible uniquement si elle n'a pas encore été acceptée, se fait via une requête DELETE sur `/applications/{id}`. Enfin, la disponibilité générale du service peut être vérifiée à tout moment via une simple requête GET sur `/health`, sans authentification requise.

La documentation OpenAPI complète, détaillant les schémas de requête et de réponse ainsi que les codes d'erreur possibles pour chaque route, est disponible directement sur `/docs` une fois l'application lancée.

## Limites observees

Le middleware de limitation de débit conserve ses compteurs de requêtes en mémoire du processus applicatif. Cette approche fonctionne correctement tant qu'une seule instance de l'application tourne, mais ne serait pas partagée entre plusieurs instances dans un déploiement en production comportant plusieurs workers ou plusieurs conteneurs répliqués ; un store partagé, par exemple Redis, serait alors nécessaire. Par ailleurs, la bibliothèque `passlib` déclenche un avertissement de dépréciation concernant le module `crypt` sous Python 3.13 et versions ultérieures, sans que cela n'affecte le fonctionnement actuel de l'application.
