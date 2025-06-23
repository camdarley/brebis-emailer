# 🎭 Larzac.org - Brebis Emailer

Un système automatisé d'envoi d'emails pour l'Info de la Brebis. Ce projet récupère les événements de la semaine prochaine depuis l'API de larzac.org et les envoie par email avec une mise en forme HTML élégante.

## ✨ Fonctionnalités

- 📅 **Récupération automatique** des événements de la semaine prochaine (mercredi à mercredi)
- 🎨 **Template d'email élégant** utilisant MJML pour un rendu professionnel
- 🖼️ **Traitement d'images** automatique avec redimensionnement et intégration
- 📧 **Envoi d'emails** via SMTP avec support des serveurs sécurisés
- 🌐 **Intégration API** avec le site larzac.org
- 🎯 **Configuration flexible** via variables d'environnement

## 🚀 Installation

### Prérequis

- Python 3.12 ou supérieur
- [uv](https://docs.astral.sh/uv/) (gestionnaire de packages Python moderne)
- [MJML CLI](https://mjml.io/documentation/#installation) pour la conversion des templates

#### Installation de MJML
```bash
npm install -g mjml
```

### Installation du projet

1. **Cloner le projet**
```bash
git clone <url-du-repo>
cd "Larzac.org - Brebis Emailer"
```

2. **Installer les dépendances**
```bash
uv sync
```

## ⚙️ Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet avec la configuration SMTP :

```env
# Configuration du serveur SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=votre-email@gmail.com
SMTP_PASSWORD=votre-mot-de-passe-application

# Pour Gmail, utilisez un mot de passe d'application
# Guide : https://support.google.com/accounts/answer/185833
```

### Configuration du destinataire

Modifiez la variable `RECIPIENT_EMAIL` dans le fichier `main.py` :

```python
RECIPIENT_EMAIL = 'destinataire@example.com'  # Remplacez par l'email cible
```

### Logo personnalisé

Remplacez le fichier `logo.jpg` par votre propre logo (formats supportés : JPG, PNG, GIF).

## 🎯 Utilisation

### Exécution manuelle

```bash
uv run python main.py
```

### Automatisation avec cron

Pour envoyer les emails automatiquement chaque mardi (pour la semaine suivante) :

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour exécuter chaque mardi à 10h00
0 10 * * 2 cd /chemin/vers/le/projet && uv run python main.py
```

## 📁 Structure du projet

```
Larzac.org - Brebis Emailer/
├── main.py                 # Script principal
├── template.mjml           # Template d'email MJML
├── logo.jpg               # Logo inclus dans les emails
├── pyproject.toml         # Configuration du projet et dépendances
├── uv.lock               # Fichier de verrouillage des versions
└── README.md             # Documentation
```

## 🔧 Fonctionnement technique

### Récupération des événements

Le script utilise l'API REST de WordPress du site larzac.org :
- **Endpoint** : `https://larzac.org/wp-json/tribe/events/v1/events`
- **Période** : Du mercredi de la semaine prochaine au mercredi suivant
- **Tri** : Par date de début croissante

### Traitement des données

1. **Nettoyage** : Suppression des balises HTML et entités
2. **Troncature** : Limitation des descriptions à 200 caractères
3. **Images** : Redimensionnement automatique (150px max) et conversion en base64
4. **Dates** : Formatage en français avec gestion des heures

### Génération d'email

1. **Template MJML** : Utilisation de Jinja2 pour l'injection des données
2. **Conversion HTML** : Via le CLI MJML pour un rendu cross-client
3. **Intégration d'images** : Logos et images d'événements en base64

## 🎨 Personnalisation du template

Le fichier `template.mjml` peut être modifié pour changer :
- 🎨 **Couleurs** : Modifiez les valeurs hexadécimales
- 📐 **Mise en page** : Ajustez les colonnes et espacements
- 🖼️ **Images** : Changez les tailles et styles
- 📝 **Contenu** : Adaptez les textes et structure

Exemple de modification des couleurs :
```mjml
<!-- Couleur principale : bleu vers vert -->
<mj-text color="#10b981" font-size="18px">
```

## 🐛 Dépannage

### Erreurs SMTP courantes

- **Authentification Gmail** : Utilisez un [mot de passe d'application](https://support.google.com/accounts/answer/185833)
- **Port bloqué** : Essayez le port 465 (SSL) au lieu de 587 (TLS)
- **Firewall** : Vérifiez que les ports SMTP ne sont pas bloqués

### Erreurs MJML

- **MJML non trouvé** : Installez MJML globalement avec `npm install -g mjml`
- **Template invalide** : Validez votre MJML sur [mjml.io/try-it-live](https://mjml.io/try-it-live)

### Erreurs API

- **Pas d'événements** : Normal si aucun événement n'est programmé
- **Timeout API** : Le site larzac.org peut être temporairement indisponible

## 📄 Licence

Ce projet est sous licence libre. Vous pouvez l'utiliser, le modifier et le distribuer selon vos besoins.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- 🐛 Signaler des bugs
- 💡 Proposer des améliorations  
- 🔧 Soumettre des pull requests

---

*Développé avec ❤️ pour l'Info de la Brebis*
