Pour la creation de la base de donnees et l'accord des privileges a l'utilisateur

# psql -U postgres -p 5433 

creation d'un utilisateur dedie
# CREATE USER palmeraie_user WITH PASSWORD 'Palmeraie26@04#';

Limiter la capacite de creation de base :
# ALTER USER palmeraie_user NOCREATEDB;
# ALTER USER palmeraie_user NOSUPERUSER;
# ALTER USER palmeraie_user NOCREATEROLE;

creation de la base de donnees :
# CREATE DATABASE gestion_palmeraie OWNER palmeraie_user ENCODING 'UTF8';

Se connecter a la base de donnees
# \c gestion_palmeraie

Donner acces au schema public
# GRANT USAGE, CREATE ON SCHEMA public TO palmeraie_user;

Privileges sur les tables
# GRANT SELCT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO palmeraie_user;

Privileges sur les sequences:
# GRANT USAGE, SELECT , UPDATE ON ALL SEQUENCES IN SCHEMA public TO palmeraie_user;

Privileges pour les futures tables:
# ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO palmeraie_user;

# ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO palmeraie_user;


Migrations:
# python manage.py makemigrations
# python manage.py migrate



Lancer le serveur Django avec la commande suivante :
# python manage.py runserver
"# Projet-Gestion-Palmeraie" 
