#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour récupérer les événements du Larzac de la semaine prochaine
et les envoyer par email avec mise en forme HTML
"""

import requests
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, TypedDict
import re
import html
from io import BytesIO
from PIL import Image
from PIL.Image import Resampling
import base64
from dotenv import load_dotenv
import os
import subprocess
from jinja2 import Environment, FileSystemLoader

class LarzacEvent(TypedDict):
    title: str
    description: str
    start_date: str
    url: str
    image: str | dict[str, str] | None


class LarzacEventsMailer:
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        """
        Initialise le mailer avec les paramètres SMTP
        
        Args:
            smtp_server: Serveur SMTP (ex: smtp.gmail.com)
            smtp_port: Port SMTP (ex: 587 pour TLS)
            email: Adresse email d'envoi
            password: Mot de passe ou mot de passe d'application
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.api_url = "https://larzac.org/wp-json/tribe/events/v1/events"
    
    def get_next_week_dates(self) -> tuple[str, str]:
        """
        Calcule les dates du mercredi de la semaine prochaine au mercredi suivant
        
        Returns:
            tuple: (date_debut, date_fin) au format ISO
        """
        today = datetime.now().date()
        
        # Trouver le mercredi de la semaine prochaine
        days_until_next_wednesday = (2 - today.weekday() + 7) % 7  # 2 = mercredi (lundi=0)
        if days_until_next_wednesday == 0:  # Si on est mercredi, prendre le suivant
            days_until_next_wednesday = 7
        
        next_wednesday = today + timedelta(days=days_until_next_wednesday)
        
        # Mercredi de la semaine d'après
        following_wednesday = next_wednesday + timedelta(days=7)
        
        # Format ISO pour l'API
        start_date = next_wednesday.strftime("%Y-%m-%d")
        end_date = following_wednesday.strftime("%Y-%m-%d")
        
        return start_date, end_date
    
    def fetch_events(self) -> List[LarzacEvent]:
        """
        Récupère les événements via l'API Larzac
        
        Returns:
            List[Dict]: Liste des événements
        """
        start_date, end_date = self.get_next_week_dates()
        
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'per_page': 50,  # Récupérer jusqu'à 50 événements
            'orderby': 'start_date',
            'order': 'asc'
        }
        
        try:
            print(f"Récupération des événements du {start_date} au {end_date}...")
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            # The API returns a dictionary with an 'events' key containing the list of events
            events = data.get('events', [])
            print(f"✓ {len(events)} événement(s) trouvé(s)")
            return events
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des événements: {e}")
            return []
    
    def truncate_description(self, description: str, max_length: int = 200) -> str:
        """
        Tronque la description et retire les balises HTML
        
        Args:
            description: Description originale
            max_length: Longueur maximale
            
        Returns:
            str: Description tronquée et nettoyée
        """
        if not description:
            return "Aucune description disponible."
        
        # Retirer les balises HTML
        clean_desc = re.sub(r'<[^>]+>', '', description)
        # Nettoyer les entités HTML
        clean_desc = html.unescape(clean_desc)
        # Retirer les espaces multiples et les retours à la ligne
        clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
        
        if len(clean_desc) > max_length:
            clean_desc = clean_desc[:max_length] + "..."
        
        return clean_desc
    
    def format_date(self, date_str: str) -> str:
        """
        Formate la date pour l'affichage
        
        Args:
            date_str: Date au format ISO
            
        Returns:
            str: Date formatée en français
        """
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            # Format français
            months = {
                1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
                5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
                9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
            }
            
            day = date_obj.day
            month = months[date_obj.month]
            year = date_obj.year
            hour = date_obj.hour
            minute = date_obj.minute
            
            if hour == 0 and minute == 0:
                return f"{day} {month} {year}"
            else:
                return f"{day} {month} {year} à {hour:02d}h{minute:02d}"
                
        except (ValueError, AttributeError):
            return date_str
    
    def clean_html_entities(self, text: str) -> str:
        """
        Nettoie les entités HTML d'un texte
        
        Args:
            text: Texte à nettoyer
            
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return ""
        return html.unescape(text)
    
    def process_image(self, image_url: str) -> str:
        """
        Télécharge une image, la redimensionne et la convertit en base64
        
        Args:
            image_url: URL de l'image à traiter
            
        Returns:
            str: Image en base64 ou chaîne vide si erreur
        """
        try:
            # Télécharger l'image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Ouvrir l'image avec PIL
            img = Image.open(BytesIO(response.content))
            
            # Calculer les nouvelles dimensions en conservant le ratio
            width, height = img.size
            ratio = min(150/width, 150/height)
            new_size = (int(width * ratio), int(height * ratio))
            
            # Redimensionner l'image
            img = img.resize(new_size, Resampling.LANCZOS) # type: ignore
            
            # Convertir en base64
            buffered = BytesIO()
            img.save(buffered, format=img.format if img.format else 'JPEG')
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Déterminer le type MIME
            mime_type = img.format.lower() if img.format else 'jpeg'
            if mime_type == 'jpeg':
                mime_type = 'jpg'
            
            return f"data:image/{mime_type};base64,{img_str}"
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de l'image {image_url}: {e}")
            return ""
    
    def render_mjml_template(self, logo_base64: str, header_title: str, header_subtitle: str, events: List[LarzacEvent]) -> str:
        """
        Charge le template MJML et le remplit avec les données
        """
        # Préparer les événements pour le template
        template_events: List[Dict[str, Any]] = []
        for event in events:
            title: str = self.clean_html_entities(event.get('title', 'Événement sans titre'))
            description: str = self.truncate_description(event.get('description', ''))
            start_date_formatted: str = self.format_date(event.get('start_date', ''))
            event_url: str = event.get('url', '')
            
            # Traiter l'image
            image_url: str | None = ""
            if 'image' in event and event['image']:
                if isinstance(event['image'], dict):
                    image_url = event['image'].get('url', "")
                else:
                    image_url = str(event['image'])
            image_base64 = self.process_image(image_url) if image_url else ""

            template_events.append({
                'title': title,
                'description': description,
                'start_date_formatted': start_date_formatted,
                'url': event_url,
                'image_base64': image_base64
            })

        # Charger le template avec Jinja2
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template('template.mjml')
        
        # Rendre le template avec les données
        return template.render(
            logo_base64=logo_base64,
            header_title=header_title,
            header_subtitle=header_subtitle,
            events=template_events
        )

    def mjml_to_html(self, mjml_code: str) -> str:
        """
        Convertit du MJML en HTML en appelant le binaire mjml
        """
        import tempfile
        with tempfile.NamedTemporaryFile('w+', suffix='.mjml', delete=False) as mjml_file:
            mjml_file.write(mjml_code)
            mjml_file.flush()
            mjml_path = mjml_file.name
        html_path = mjml_path.replace('.mjml', '.html')
        try:
            # Supprimer les avertissements de dépréciation Node.js
            subprocess.run(['mjml', mjml_path, '-o', html_path], check=True)
            with open(html_path, 'r', encoding='utf-8') as f:
                html = f.read()
            return html
        finally:
            import os
            try:
                os.remove(mjml_path)
                os.remove(html_path)
            except Exception:
                pass

    def send_email(self, recipient_email: str, events: List[LarzacEvent], logo_base64_uri: str) -> bool:
        """
        Envoie l'email avec les événements
        Args:
            recipient_email: Adresse du destinataire
            events: Liste des événements
            logo_base64_uri: Logo encodé en base64 à injecter dans le template
        Returns:
            bool: True si l'envoi a réussi
        """
        try:
            # Préparation des variables dynamiques pour le template
            start_date, end_date = self.get_next_week_dates()
            header_title = "Les événements à venir"
            header_subtitle = f"du {self.format_date(start_date + 'T00:00:00')} au {self.format_date(end_date + 'T00:00:00')}"

            # Générer le MJML à partir du template externe
            mjml_code = self.render_mjml_template(
                logo_base64=logo_base64_uri,
                header_title=header_title,
                header_subtitle=header_subtitle,
                events=events
            )
            html_content = self.mjml_to_html(mjml_code)

            # Création du message
            msg = MIMEMultipart('related')
            msg['From'] = self.email
            msg['To'] = recipient_email
            subject = f"L'agenda de la brebis du {self.format_date(start_date + 'T00:00:00')}"
            msg['Subject'] = subject

            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Envoi via SMTP
            print(f"Connexion au serveur SMTP {self.smtp_server} sur le port {self.smtp_port}...")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_port == 587:
                    server.starttls()
                if self.smtp_port == 465:
                    server.set_debuglevel(1)
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                if self.email and self.password:
                    server.login(self.email, self.password)
                server.send_message(msg)

            print(f"✓ Email envoyé avec succès à {recipient_email}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi de l'email: {e}")
            return False


def load_logo_base64_uri(logo_path: str) -> str:
    """
    Charge un fichier image et retourne une URI base64 utilisable dans le HTML/MJML
    """
    try:
        with open(logo_path, 'rb') as f:
            img_bytes = f.read()
        # Utiliser PIL pour détecter le format d'image
        img = Image.open(BytesIO(img_bytes))
        img_type = img.format.lower() if img.format else 'png'
        if img_type == 'jpeg':
            img_type = 'jpg'
        img_b64 = base64.b64encode(img_bytes).decode()
        return f"data:image/{img_type};base64,{img_b64}"
    except Exception as e:
        print(f"❌ Erreur lors du chargement du logo : {e}")
        return ""


def main():
    """
    Fonction principale
    """
    # Charger les variables d'environnement depuis .env
    load_dotenv()
    SMTP_CONFIG = {
        'smtp_server': str(os.getenv('SMTP_SERVER', '127.0.0.1')),
        'smtp_port': int(os.getenv('SMTP_PORT', 1025)),
        'email': str(os.getenv('SMTP_EMAIL', '')),
        'password': str(os.getenv('SMTP_PASSWORD', ''))
    }
    # Email du destinataire
    RECIPIENT_EMAIL = str(os.getenv('RECIPIENT_EMAIL', ''))
    print("=== 🎭 Récupération des événements Larzac ===")
    # Initialisation du mailer
    mailer = LarzacEventsMailer(
        smtp_server=str(SMTP_CONFIG['smtp_server']) if SMTP_CONFIG['smtp_server'] else '',
        smtp_port=int(SMTP_CONFIG['smtp_port']) if SMTP_CONFIG['smtp_port'] else 1025,
        email=str(SMTP_CONFIG['email']) if SMTP_CONFIG['email'] else '',
        password=str(SMTP_CONFIG['password']) if SMTP_CONFIG['password'] else ''
    )
    # Récupération des événements
    events = mailer.fetch_events()
    # Charger le logo en base64 URI
    logo_base64_uri = load_logo_base64_uri('logo.jpg')
    # Envoi de l'email
    if mailer.send_email(RECIPIENT_EMAIL, events, logo_base64_uri):
        print("✅ Processus terminé avec succès!")
    else:
        print("❌ Échec de l'envoi de l'email")


if __name__ == "__main__":
    main()