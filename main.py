# ====================================================
# NOVA AGORA BOT — VERSIÓN FINAL COMPLETA CORREGIDA
# CON SISTEMA DE DROGAS, GRAMOS, BLANQUEO, INFINITY
# TODOS LOS COGS, FUNCIONES Y COMANDOS
# ROL CIUDADANO: 1450592204849418294
# CORREGIDO ERROR DE fetchone EN LA CLASE Database
# ====================================================

import os
import random
import asyncio
import json
import threading
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
from flask import Flask, render_template_string, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# ---------- CONFIGURACIÓN GLOBAL ----------
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("No se ha configurado DISCORD_TOKEN")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", secrets.token_urlsafe(16))
print(f"🔐 Panel web token: {ADMIN_TOKEN}")

DEFAULT_PREFIX = '-'
CANAL_LOGS = 0
CANAL_PERIODICO = 0
CANAL_VOICE_CATEGORY = 0

# IDs de roles (actualizadas)
ROL_LSPD_ID = 1450592202165321759
OWNER_IDS = [1059183337832468510, 729054497233436775, 1259792008248037442]

ROL_INICIADOR_ID = 1450592126491558131
ROL_EQUIPO_ESPECIAL_ID = 1450592064365658134
ROL_ADMIN_ID = 1450592064365658134  # Mismo que equipo especial o cambia por tu ID de admin
ROL_MIEMBRO_BANDA_ID = 1512759486568468621  # 🎭 Rol Miembro Banda
ROL_DASHBOARD_ID = 1450592204849418294
ROL_LSPD_OPERATIVO_ID = 1450592202165321759
ROL_LSMD_ID = 1450592186600128567
ROL_SHERIFF_ID = 1511846976889815232
ROL_USUARIO_ID = 1450592204849418294          # 👤 NUEVO ROL CIUDADANO OFICIAL
ROL_MAFIA_ID = 1479210255564013588
ROL_MAFIA_ADMIN_ID = 0  # ⚠️ REEMPLAZAR CON EL ID DEL ROL "MAFIA ADMIN"
ROL_MINERO_ID = 1450592196351885344
ROL_AUTOBUSERO_ID = 1450592190089920563
ROL_CHATARRERO_ID = 1450592178018455738

# Precios drogas
PRECIOS_DROGAS_BASE = {
    "Marihuana": {"compra": 50, "venta": 100},
    "Cocaína":   {"compra": 250, "venta": 500},
    "Meta":      {"compra": 150, "venta": 300},
    "Éxtasis":   {"compra": 75,  "venta": 150},
    "Heroína":   {"compra": 400, "venta": 800},
}
EMOJIS_DROGA = {"Marihuana": "🌿", "Cocaína": "❄️", "Meta": "💊", "Éxtasis": "🔵", "Heroína": "💉"}

TIPOS_ARMAS = {
    "Pistola":  {"emoji": "🔫", "municion_tipo": "9mm",    "durabilidad_max": 100, "licencia": "licencia_pistola"},
    "Escopeta": {"emoji": "🔫", "municion_tipo": "12gauge", "durabilidad_max": 80,  "licencia": "licencia_escopeta"},
    "Rifle":    {"emoji": "🔫", "municion_tipo": "556mm",   "durabilidad_max": 150, "licencia": "licencia_rifle"},
}
TIPOS_MUNICION = {
    "9mm":    {"emoji": "🔹", "precio": 5},
    "12gauge":{"emoji": "🔸", "precio": 15},
    "556mm":  {"emoji": "🔺", "precio": 25},
}

# Items de la tienda (lista completa)
TIENDA_ITEMS_BASE = [
    ("Hacha", 750, "🪓", "Arma blanca básica"),
    ("Machete", 1500, "🔪", "Arma cortante"),
    ("Puño americano", 2225, "👊", "Aumenta daño"),
    ("SNS", 16000, "🔫", "Pistola compacta"),
    ("Normal", 18500, "🔫", "Pistola estándar"),
    ("Vintage", 22000, "🔫", "Pistola de colección"),
    ("Calibre .50", 25100, "🔫", "Alto poder"),
    ("Pesada", 28000, "🔫", "Gran retroceso"),
    ("Revólver Pesado", 34000, "🔫", "Devastador"),
    ("Perforante", 36850, "🔫", "Anti-chalecos"),
    ("Mini SMG", 120000, "🔫", "Subfusil ligero"),
    ("Micro Uzi", 150000, "🔫", "Muy rápido"),
    ("Subfusil", 180000, "🔫", "Versátil"),
    ("Subfusil de asalto", 200000, "🔫", "Letal"),
    ("ADP", 250000, "🔫", "Táctica"),
    ("Mosquete", 100000, "🔫", "Antiguo"),
    ("Escopeta recortada", 200000, "🔫", "Cerca"),
    ("MiniAk47", 220000, "🔫", "Potente"),
    ("Escopeta corredera", 230000, "🔫", "Alto poder"),
    ("Ak47", 283000, "🔫", "Legendario"),
    ("Rifle bullpup", 297110, "🔫", "Preciso"),
    ("Coctel molotov", 6000, "🔥", "Incendio"),
    ("Granada casera", 12000, "💣", "Explosión"),
    ("Granada", 15000, "💣", "Letal"),
    ("C4", 20000, "🧨", "Demolición"),
    ("Licencia de camión", 1600, "🚚", "Camiones"),
    ("Licencia de vehiculo", 3000, "🚗", "Coches"),
    ("Licencia de moto", 2500, "🏍️", "Motos"),
    ("Licencia de armas blancas", 5000, "🔪", "Cuchillos"),
    ("Licencia de armas cortas", 12000, "🔫", "Pistolas"),
    ("DNI", 500, "🪪", "Documento"),
    ("Sprunk", 8, "🥤", "Bebida"),
    ("Hotdog", 10, "🌭", "Comida"),
    ("Burger", 15, "🍔", "Hamburguesa"),
    ("Pizza", 12, "🍕", "Pizza"),
    ("Papas", 5, "🍟", "Patatas"),
    ("Empanada", 8, "🥟", "Empanada"),
    ("Chocolate", 11, "🍫", "Chocolate"),
    ("Agua", 3, "🧃", "Agua"),
    ("Gaseosa", 9, "🥤", "Refresco"),
    ("E-Cola", 5, "🥤", "Energética"),
    ("Cigs", 20, "🚬", "Cigarrillos"),
    ("Encendedor", 25, "🚬", "Fuego"),
    ("Botiquin", 75, "🩹", "Curas"),
    ("Kit", 150, "🔧", "Herramientas"),
    ("Gasolina", 100, "⛽", "Combustible"),
    ("Phone", 500, "📱", "Teléfono"),
    ("Linterna", 25, "🔦", "Luz"),
    ("Mochila", 200, "🎒", "Capacidad"),
    ("GPS", 300, "🚗", "Navegación"),
    ("Radio", 150, "📻", "Comunicación"),
    ("Auriculares", 75, "🎧", "Música"),
    ("Cámara", 400, "📷", "Fotos"),
    ("Guantes", 30, "🧤", "Protección"),
    ("Zapatillas", 120, "👟", "Velocidad"),
    ("Chaqueta", 250, "🧥", "Abrigo"),
    ("Mascara", 50, "🎭", "Disfraz"),
    ("Ganzúa", 650, "🔑", "Cerradura"),
    ("Llave Inglesa", 100, "🔧", "Aprieta"),
    ("Herramientas", 150, "🔧", "Multiusos"),
    ("9mm", 1200, "🔫", "Munición"),
    ("Tarjeta de crédito", 300, "💳", "Clonada"),
    ("Bolsas Atraco", 300, "🛍️", "Botín"),
    ("Pasamontañas", 75, "😷", "Anonimato"),
    ("Esposas", 500, "⛓️", "Inmoviliza"),
    ("Dispositivo de hackeo", 1800, "🛠️", "Hackeo"),
    ("Termita", 700, "🔥", "Funde"),
    ("Gas lacrimógeno", 450, "😷", "Control"),
    ("Desfibrilador", 800, "🩺", "Reanima"),
    ("Traje Ignifugo", 600, "🔥", "Resiste fuego"),
    ("Manguera", 180, "💧", "Apaga"),
    ("Kit Médico", 500, "💊", "Cura grave"),
    ("Placa Policial", 0, "🪪", "Identificación"),
]

CUSTOM_ITEMS_FILE = "custom_items.json"
_custom_items = []
if os.path.exists(CUSTOM_ITEMS_FILE):
    with open(CUSTOM_ITEMS_FILE, "r", encoding="utf-8") as f:
        _custom_items = json.load(f)
TIENDA_ITEMS_FULL = list(TIENDA_ITEMS_BASE) + [tuple(c) for c in _custom_items]
TIENDA_ITEMS_DICT = {name.lower(): (name, precio, emoji, desc) for name, precio, emoji, desc in TIENDA_ITEMS_FULL}
ILLEGAL_TIENDA_ITEMS = {"dispositivo de hackeo", "termita", "tarjeta de crédito", "gas lacrimógeno", "pasamontañas", "bolsas atraco", "ganzúa", "mascaras"}

# Definición completa de atracos con preparatorias
HEIST_DEFINITIONS = {
    "badu": {
        "nombre": "Badu", "cooldown": 600, "items": ["Bolsas Atraco", "Pasamontañas"],
        "police": "2 policías", "reward": (1200,2800), "min_level":1, "description":"Atraco básico",
        "image":"https://i.imgur.com/6q1z4wP.png",
        "preparations": [
            "🚗 Roba un vehículo de huida."
        ]
    },
    "yellowjack": {
        "nombre": "Yellow Jack", "cooldown": 1800, "items": ["Mascaras", "Ganzúa"],
        "police": "3 policías", "reward": (3000,5500), "min_level":5, "description":"Tienda nocturna",
        "image":"https://i.imgur.com/9BkYy3M.png",
        "preparations": [
            "🚗 Roba un vehículo de huida.",
            "🔧 Consigue herramientas para forzar acceso."
        ]
    },
    "ammu": {
        "nombre": "Ammu-Nation", "cooldown": 3600, "items": ["Dispositivo de hackeo", "Gas lacrimógeno"],
        "police": "4 policías", "reward": (6000,12000), "min_level":10, "description":"Tienda de armas",
        "image":"https://i.imgur.com/5XkZq5p.png",
        "preparations": [
            "🚐 Roba una furgoneta.",
            "🪪 Roba credenciales de acceso.",
            "📦 Consigue equipamiento para transportar mercancía."
        ]
    },
    "vanilla": {
        "nombre": "Vanilla Unicorn", "cooldown": 7200, "items": ["Termita", "Pasamontañas"],
        "police": "5 policías", "reward": (12000,18000), "min_level":15, "description":"Club nocturno",
        "image":"https://i.imgur.com/3pG7F2d.png",
        "preparations": [
            "🚗 Roba vehículo discreto.",
            "📹 Consigue información interna.",
            "🔑 Obtén acceso al almacén."
        ]
    },
    "yate": {
        "nombre": "Yate", "cooldown": 9000, "items": ["Tarjeta de crédito", "Mascaras"],
        "police": "5 policías", "reward": (18000,26000), "min_level":20, "description":"Emboscada en alta mar",
        "image":"https://i.imgur.com/h8G7Y2V.png",
        "preparations": [
            "🚁 Roba un helicóptero.",
            "🔫 Consigue armamento.",
            "📡 Intercepta comunicaciones.",
            "🗺️ Obtén coordenadas del objetivo."
        ]
    },
    "centro": {
        "nombre": "Centro Comercial", "cooldown": 10800, "items": ["Termita", "Gas lacrimógeno", "Pasamontañas"],
        "police": "6 policías", "reward": (22000,32000), "min_level":25, "description":"Centro comercial",
        "image":"https://i.imgur.com/JY4N7Qc.png",
        "preparations": [
            "🚐 Vehículo de carga.",
            "📹 Desactivar cámaras.",
            "🔑 Conseguir acceso.",
            "📦 Equipamiento de transporte."
        ]
    },
    "joyeria": {
        "nombre": "Joyería", "cooldown": 259200, "items": ["Ganzúa", "Termita", "Mascaras"],
        "police": "7 policías", "reward": (45000,65000), "min_level":30, "description":"Joyería",
        "image":"https://i.imgur.com/2aUxZcN.png",
        "preparations": [
            "🚗 Vehículo de huida.",
            "📹 Información de seguridad.",
            "🔧 Herramientas de corte.",
            "💻 Equipo electrónico.",
            "🎭 Material para ocultar identidad."
        ]
    },
    "paleto": {
        "nombre": "Banco Paleto", "cooldown": 1036800, "items": ["Dispositivo de hackeo", "Pasamontañas", "Bolsas Atraco"],
        "police": "8 policías", "reward": (120000,160000), "min_level":50, "description":"Atraco rural",
        "image":"https://i.imgur.com/4XKlj8K.png",
        "preparations": [
            "🚐 Furgón de transporte.",
            "📡 Interceptar comunicaciones.",
            "💳 Conseguir tarjetas de acceso.",
            "🔧 Herramientas de perforación.",
            "📹 Neutralizar vigilancia.",
            "🗺️ Reconocimiento de la zona."
        ]
    },
    "central": {
        "nombre": "Banco Central", "cooldown": 1209600, "items": ["Dispositivo de hackeo", "Termita", "Tarjeta de crédito"],
        "police": "10 policías", "reward": (180000,240000), "min_level":60, "description":"Operación final",
        "image":"https://i.imgur.com/7W6c3qB.png",
        "preparations": [
            "🚛 Vehículo blindado.",
            "📹 Información interna.",
            "💳 Credenciales.",
            "🔧 Equipamiento especializado.",
            "📡 Sabotaje de comunicaciones.",
            "🗺️ Reconocimiento.",
            "📦 Material para extracción del dinero."
        ]
    },
    "pacific": {
        "nombre": "Pacific Bank", "cooldown": 1209600, "items": ["Dispositivo de hackeo", "Termita", "Tarjeta de crédito"],
        "police": "10 policías", "reward": (250000,350000), "min_level":60, "description":"Golpe maestro",
        "image":"https://i.imgur.com/1rQn0pL.png",
        "preparations": [
            "🚛 Roba una furgoneta de asalto.",
            "🚁 Roba un helicóptero.",
            "📹 Consigue acceso a las cámaras.",
            "🔧 Consigue herramientas avanzadas.",
            "💳 Roba credenciales bancarias.",
            "📡 Intercepta comunicaciones.",
            "🗺️ Obtén planos internos.",
            "📦 Consigue equipo para transportar el dinero."
        ]
    }
}

APUESTA_MIN, APUESTA_MAX, MAX_DROGA_POR_COMPRA = 100, 50000, 27
CANAL_LOG_ECONOMIA = CANAL_LOG_SANCIONES = 0
ROL_MUTED = CATEGORIA_TICKETS = ROL_STAFF = TICKET_PANEL_CHANNEL = 0

MENSAJES_POR_NIVEL = 300
COOLDOWN_MENSAJE_XP = 500
COOLDOWN_COMANDO_XP = 3000
XP_POR_TIEMPO = 10
DIAS_PARA_SUBIR_NIVEL = 14
ROLES_POR_NIVEL = {5:0,10:0,15:0,20:0,25:0,30:0}

MINERALES = {
    "Carbón":{"probabilidad":25,"valor":5,"emoji":"⚫"}, "Hierro":{"probabilidad":20,"valor":15,"emoji":"⚙️"},
    "Cobre":{"probabilidad":18,"valor":20,"emoji":"🔶"}, "Estaño":{"probabilidad":12,"valor":25,"emoji":"🔘"},
    "Plata":{"probabilidad":10,"valor":50,"emoji":"🥈"}, "Oro":{"probabilidad":7,"valor":100,"emoji":"🥇"},
    "Platino":{"probabilidad":4,"valor":200,"emoji":"⚪"}, "Rubí":{"probabilidad":2,"valor":500,"emoji":"🔴"},
    "Zafiro":{"probabilidad":1.2,"valor":800,"emoji":"🔵"}, "Esmeralda":{"probabilidad":0.6,"valor":1200,"emoji":"🟢"},
    "Diamante":{"probabilidad":0.2,"valor":3000,"emoji":"💎"}, "Fragmento Estelar":{"probabilidad":0.05,"valor":10000,"emoji":"✨"},
}

DEFAULT_EMOJIS = {
    "money":"💰","bank":"🏦","black_money":"💶","inventory":"🎒","shop":"🏪","work":"⚙️","rob":"💰",
    "casino":"🎰","drugs":"💊","vehicle":"🚗","weapon":"🔫","pda":"🚨","phone":"📱","ig":"📸",
    "twitter":"🐦","facebook":"📘","deepweb":"🕸️","whatsapp":"💬","ticket":"📩","admin":"🔧","mod":"🔨",
}

PRECIO_INFINITO = 10**12  # Representa precio infinito

# ==================== FUNCIONES AUXILIARES ====================
def embed_error(msg): return discord.Embed(title="❌ Error", description=msg, color=0xFF0000)
def embed_success(titulo, desc="", color=0x00FF00): return discord.Embed(title=titulo, description=desc, color=color)
def embed_info(titulo, desc="", color=0x3498DB): return discord.Embed(title=titulo, description=desc, color=color)
def embed_help(comando, desc, uso, ej, perm=""):
    e = discord.Embed(title=f"📖 Ayuda: `{comando}`", color=discord.Color.blue())
    e.add_field(name="📝 Descripción", value=desc, inline=False)
    e.add_field(name="📌 Uso", value=f"`{uso}`", inline=False)
    e.add_field(name="📋 Ejemplo", value=f"`{ej}`", inline=False)
    if perm: e.add_field(name="🔒 Permisos", value=perm, inline=False)
    return e

async def get_emoji(key):
    row = await db.fetchone("SELECT emoji FROM emoji_settings WHERE key = ?", (key,))
    return row[0] if row and row[0] else DEFAULT_EMOJIS.get(key, "⚙️")

def es_precio_infinito(precio):
    return precio >= PRECIO_INFINITO

def formatear_precio(precio):
    if es_precio_infinito(precio):
        return "INFINITY"
    return f"${precio:,}"

# ==================== BASE DE DATOS ====================
class Database:
    def __init__(self, db_path="nova.db"):
        self.db_path = db_path
        self._cache = {}
        self._cache_time = {}

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Bot config
            await db.execute("CREATE TABLE IF NOT EXISTS bot_config (key TEXT PRIMARY KEY, value TEXT)")
            expiry = (datetime.now() + timedelta(days=30)).isoformat()
            await db.execute("INSERT OR IGNORE INTO bot_config (key, value) VALUES ('expiry', ?)", (expiry,))
            # Usuarios
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    banned BOOLEAN DEFAULT 0,
                    ban_reason TEXT,
                    banned_by INTEGER,
                    ban_date TEXT,
                    phone_number TEXT,
                    airplane_mode BOOLEAN DEFAULT 0,
                    wifi_connected BOOLEAN DEFAULT 1,
                    ig_public BOOLEAN DEFAULT 1,
                    ig_bio TEXT DEFAULT '',
                    placa TEXT,
                    rango TEXT,
                    encarcelado_hasta TEXT,
                    dni_nombre TEXT,
                    dni_apellidos TEXT,
                    dni_edad INTEGER,
                    dni_genero TEXT,
                    dni_nacionalidad TEXT,
                    dni_color_ojos TEXT,
                    dni_altura TEXT,
                    dni_profesion TEXT,
                    dni_numero TEXT,
                    dni_fecha_creacion TEXT
                )
            """)
            # Licencias conducción
            await db.execute("""
                CREATE TABLE IF NOT EXISTS licencias_conduccion (
                    user_id INTEGER,
                    tipo TEXT,
                    fecha_obtencion TEXT,
                    PRIMARY KEY (user_id, tipo)
                )
            """)
            # Economía
            await db.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                    user_id INTEGER PRIMARY KEY,
                    cash INTEGER DEFAULT 0,
                    bank INTEGER DEFAULT 0,
                    black_money INTEGER DEFAULT 0
                )
            """)
            # Inventario
            await db.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id INTEGER,
                    inv_type TEXT,
                    item TEXT,
                    quantity INTEGER,
                    PRIMARY KEY (user_id, inv_type, item)
                )
            """)
            # Gramos de droga (nueva tabla)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS drug_grams (
                    user_id INTEGER,
                    drug_type TEXT,
                    grams INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, drug_type)
                )
            """)
            # Evidencia
            await db.execute("""
                CREATE TABLE IF NOT EXISTS evidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agente_id INTEGER,
                    target_id INTEGER,
                    item TEXT,
                    quantity INTEGER,
                    fecha TEXT
                )
            """)
            # Armas
            await db.execute("""
                CREATE TABLE IF NOT EXISTS armas_licencias (user_id INTEGER, licencia TEXT, tiene BOOLEAN, PRIMARY KEY (user_id, licencia))
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS armas_equipadas (user_id INTEGER, arma TEXT, durabilidad INTEGER, municion INTEGER, PRIMARY KEY (user_id, arma))
            """)
            # Vehículos
            await db.execute("""
                CREATE TABLE IF NOT EXISTS vehiculos (
                    user_id INTEGER, matricula TEXT, modelo TEXT, seguro BOOLEAN, itv TEXT, combustible INTEGER,
                    PRIMARY KEY (user_id, matricula)
                )
            """)
            # Multas y caja
            await db.execute("""
                CREATE TABLE IF NOT EXISTS multas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, cantidad INTEGER, motivo TEXT, fecha TEXT,
                    pagada BOOLEAN DEFAULT 0, agente TEXT, placa_agente TEXT
                )
            """)
            await db.execute("CREATE TABLE IF NOT EXISTS caja_municipal (id INTEGER PRIMARY KEY CHECK (id=1), monto INTEGER DEFAULT 0)")
            await db.execute("INSERT OR IGNORE INTO caja_municipal (id, monto) VALUES (1,0)")
            # Cooldowns, rachas, estadísticas
            await db.execute("CREATE TABLE IF NOT EXISTS cooldowns (user_id INTEGER, comando TEXT, expires TIMESTAMP, PRIMARY KEY (user_id, comando))")
            await db.execute("CREATE TABLE IF NOT EXISTS rachas (user_id INTEGER PRIMARY KEY, racha INTEGER DEFAULT 0, tipo TEXT)")
            await db.execute("CREATE TABLE IF NOT EXISTS estadisticas (key TEXT PRIMARY KEY, value TEXT)")
            # Mercado
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mercado (
                    id TEXT PRIMARY KEY, vendedor INTEGER, item TEXT, descripcion TEXT, precio INTEGER, fecha TEXT
                )
            """)
            # DeepWeb
            await db.execute("""
                CREATE TABLE IF NOT EXISTS deepweb (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender INTEGER,
                    receiver INTEGER,
                    message TEXT,
                    sent_at TEXT,
                    anonymous BOOLEAN DEFAULT 1,
                    decoded_by INTEGER,
                    decoded_at TEXT
                )
            """)
            # Atracos logs
            await db.execute("""
                CREATE TABLE IF NOT EXISTS atracos_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    heist TEXT,
                    result TEXT,
                    reward INTEGER,
                    black_reward INTEGER,
                    items TEXT,
                    timestamp TEXT
                )
            """)
            # Redes sociales
            await db.execute("""
                CREATE TABLE IF NOT EXISTS posts_ig (id TEXT PRIMARY KEY, user_id INTEGER, texto TEXT, tiempo TEXT, likes TEXT)
            """)
            await db.execute("CREATE TABLE IF NOT EXISTS seguidores_ig (follower INTEGER, following INTEGER, PRIMARY KEY (follower, following))")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS wa_contactos (user_id INTEGER, numero TEXT, nombre TEXT, PRIMARY KEY (user_id, numero))
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS wa_chats (id INTEGER PRIMARY KEY AUTOINCREMENT, de INTEGER, para INTEGER, mensaje TEXT, tiempo TEXT)
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS twitter_dms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user INTEGER,
                    to_user INTEGER,
                    message TEXT,
                    sent_at TEXT
                )
            """)
            # Web users y PDA
            await db.execute("""
                CREATE TABLE IF NOT EXISTS web_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    discord_id INTEGER,
                    is_staff BOOLEAN DEFAULT 0,
                    created_at TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pda_permissions (
                    user_id INTEGER PRIMARY KEY,
                    granted_by INTEGER,
                    granted_at TEXT
                )
            """)
            # Precios drogas
            await db.execute("CREATE TABLE IF NOT EXISTS precios_drogas (droga TEXT PRIMARY KEY, precio_compra INTEGER, precio_venta INTEGER)")
            for droga, datos in PRECIOS_DROGAS_BASE.items():
                await db.execute("INSERT OR IGNORE INTO precios_drogas (droga, precio_compra, precio_venta) VALUES (?, ?, ?)",
                                 (droga, datos["compra"], datos["venta"]))
            # Twitter, Facebook
            await db.execute("CREATE TABLE IF NOT EXISTS posts_tw (id TEXT PRIMARY KEY, user_id INTEGER, texto TEXT, tiempo TEXT)")
            await db.execute("CREATE TABLE IF NOT EXISTS seguidores_tw (follower INTEGER, following INTEGER, since TEXT, PRIMARY KEY (follower, following))")
            await db.execute("CREATE TABLE IF NOT EXISTS posts_fb (id TEXT PRIMARY KEY, user_id INTEGER, texto TEXT, tiempo TEXT)")
            # Moderación
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    razon TEXT,
                    fecha TEXT,
                    agente_id INTEGER,
                    agente_nombre TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mutes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    razon TEXT,
                    fecha_inicio TEXT,
                    fecha_fin TEXT,
                    agente_id INTEGER,
                    agente_nombre TEXT,
                    activo BOOLEAN DEFAULT 1
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    channel_id INTEGER,
                    category TEXT,
                    status TEXT DEFAULT 'abierto',
                    created_at TEXT,
                    closed_at TEXT,
                    rating INTEGER,
                    rating_comment TEXT,
                    staff_id INTEGER
                )
            """)
            # Niveles
            await db.execute("""
                CREATE TABLE IF NOT EXISTS niveles (
                    user_id INTEGER PRIMARY KEY,
                    xp INTEGER DEFAULT 0,
                    nivel INTEGER DEFAULT 0,
                    last_message_time TEXT,
                    last_command_time TEXT,
                    last_time_time TEXT,
                    mensajes INTEGER DEFAULT 0,
                    last_message_content TEXT,
                    last_level_up TEXT
                )
            """)
            # Blacklist y antiraid
            await db.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    banned_by INTEGER,
                    ban_date TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS antiraid_actions (
                    user_id INTEGER,
                    action_type TEXT,
                    timestamp TIMESTAMP,
                    guild_id INTEGER
                )
            """)
            # Emojis personalizables
            await db.execute("""
                CREATE TABLE IF NOT EXISTS emoji_settings (
                    key TEXT PRIMARY KEY,
                    emoji TEXT
                )
            """)
            for key, emoji in DEFAULT_EMOJIS.items():
                await db.execute("INSERT OR IGNORE INTO emoji_settings (key, emoji) VALUES (?, ?)", (key, emoji))
            # Preparatorias de atracos (nueva tabla genérica)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS heist_preparations (
                    user_id INTEGER,
                    heist_id TEXT,
                    prep_num INTEGER,
                    completed BOOLEAN DEFAULT 0,
                    PRIMARY KEY (user_id, heist_id, prep_num)
                )
            """)
            # Emojis animados
            await db.execute("""
                CREATE TABLE IF NOT EXISTS animated_emojis (
                    name TEXT,
                    emoji_id INTEGER,
                    added_by INTEGER,
                    added_at TEXT,
                    PRIMARY KEY (name, emoji_id)
                )
            """)
            # Índices
            await db.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_warnings_user ON warnings(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_niveles_nivel ON niveles(nivel)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_antiraid_user ON antiraid_actions(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_antiraid_timestamp ON antiraid_actions(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_drug_grams_user ON drug_grams(user_id)")

            # 🔁 Migración de datos antiguos de heist_prep a la nueva tabla (CORREGIDO)
            cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='heist_prep'")
            if await cursor.fetchone():
                rows = await db.execute("SELECT user_id, pacific_prep1, pacific_prep2, pacific_prep3 FROM heist_prep")
                async for uid, p1, p2, p3 in rows:
                    if p1:
                        await db.execute("INSERT OR IGNORE INTO heist_preparations (user_id, heist_id, prep_num, completed) VALUES (?, ?, ?, ?)",
                                           (uid, "pacific", 1, True))
                    if p2:
                        await db.execute("INSERT OR IGNORE INTO heist_preparations (user_id, heist_id, prep_num, completed) VALUES (?, ?, ?, ?)",
                                           (uid, "pacific", 2, True))
                    if p3:
                        await db.execute("INSERT OR IGNORE INTO heist_preparations (user_id, heist_id, prep_num, completed) VALUES (?, ?, ?, ?)",
                                           (uid, "pacific", 3, True))
                await db.execute("DROP TABLE heist_prep")
                print("✅ Datos migrados de heist_prep a heist_preparations")

            await db.commit()
            print("✅ Base de datos inicializada con todas las tablas e índices.")

    # Métodos de acceso
    async def execute(self, query, params=()):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()

    async def fetchone(self, query, params=()):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(query, params)
            return await cur.fetchone()

    async def fetchall(self, query, params=()):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(query, params)
            return await cur.fetchall()

    async def invalidate_cache(self, pattern=None):
        if pattern is None:
            self._cache.clear()
            self._cache_time.clear()
        else:
            to_remove = [k for k in self._cache if pattern in k[0]]
            for k in to_remove:
                del self._cache[k]
                del self._cache_time[k]

    # Economía
    async def get_economy(self, user_id):
        row = await self.fetchone("SELECT cash, bank, black_money FROM economy WHERE user_id = ?", (user_id,))
        if row:
            return {"cash": row[0], "bank": row[1], "black_money": row[2]}
        await self.execute("INSERT INTO economy (user_id) VALUES (?)", (user_id,))
        return {"cash": 0, "bank": 0, "black_money": 0}

    async def add_cash(self, user_id, amount):
        await self.execute("UPDATE economy SET cash = cash + ? WHERE user_id = ?", (amount, user_id))
        await self.invalidate_cache("economy")

    async def add_bank(self, user_id, amount):
        await self.execute("UPDATE economy SET bank = bank + ? WHERE user_id = ?", (amount, user_id))
        await self.invalidate_cache("economy")

    async def add_black(self, user_id, amount):
        await self.execute("UPDATE economy SET black_money = black_money + ? WHERE user_id = ?", (amount, user_id))
        await self.invalidate_cache("economy")

    # Gramos de droga
    async def add_drug_grams(self, user_id, drug_type, grams):
        await self.execute("""
            INSERT INTO drug_grams (user_id, drug_type, grams)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, drug_type) DO UPDATE SET grams = grams + ?
        """, (user_id, drug_type, grams, grams))
        await self.invalidate_cache("drug_grams")

    async def remove_drug_grams(self, user_id, drug_type, grams):
        row = await self.fetchone("SELECT grams FROM drug_grams WHERE user_id = ? AND drug_type = ?", (user_id, drug_type))
        if not row or row[0] < grams:
            return False
        if row[0] == grams:
            await self.execute("DELETE FROM drug_grams WHERE user_id = ? AND drug_type = ?", (user_id, drug_type))
        else:
            await self.execute("UPDATE drug_grams SET grams = grams - ? WHERE user_id = ? AND drug_type = ?", (grams, user_id, drug_type))
        await self.invalidate_cache("drug_grams")
        return True

    async def get_drug_grams(self, user_id):
        rows = await self.fetchall("SELECT drug_type, grams FROM drug_grams WHERE user_id = ?", (user_id,))
        return {drug_type: grams for drug_type, grams in rows}

    # Inventario
    async def add_item(self, user_id, inv_type, item, cantidad=1):
        await self.execute("""
            INSERT INTO inventory (user_id, inv_type, item, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, inv_type, item) DO UPDATE SET quantity = quantity + ?
        """, (user_id, inv_type, item, cantidad, cantidad))
        await self.invalidate_cache("inventory")

    async def remove_item(self, user_id, inv_type, item, cantidad=1):
        row = await self.fetchone("SELECT quantity FROM inventory WHERE user_id = ? AND inv_type = ? AND item = ?", (user_id, inv_type, item))
        if not row or row[0] < cantidad:
            return 0
        if row[0] == cantidad:
            await self.execute("DELETE FROM inventory WHERE user_id = ? AND inv_type = ? AND item = ?", (user_id, inv_type, item))
        else:
            await self.execute("UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND inv_type = ? AND item = ?", (cantidad, user_id, inv_type, item))
        await self.invalidate_cache("inventory")
        return cantidad

    async def get_inventory(self, user_id, inv_type):
        rows = await self.fetchall("SELECT item, quantity FROM inventory WHERE user_id = ? AND inv_type = ?", (user_id, inv_type))
        return {item: qty for item, qty in rows}

    # Evidencia
    async def add_evidence(self, agente_id, target_id, item, quantity=1):
        fecha = datetime.now().isoformat()
        await self.execute("INSERT INTO evidence (agente_id, target_id, item, quantity, fecha) VALUES (?, ?, ?, ?, ?)",
                           (agente_id, target_id, item, quantity, fecha))

    async def get_evidence(self, target_id):
        rows = await self.fetchall("SELECT id, agente_id, item, quantity, fecha FROM evidence WHERE target_id = ?", (target_id,))
        return [{"id": r[0], "agente_id": r[1], "item": r[2], "quantity": r[3], "fecha": r[4]} for r in rows]

    # Estado de usuario
    async def get_user_state(self, user_id):
        row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        if not row:
            await self.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("PRAGMA table_info(users)")
            columns = [desc[1] for desc in await cur.fetchall()]
        return {col: row[i] for i, col in enumerate(columns)} if row else {}

    async def update_user_state(self, user_id, **kwargs):
        VALID_COLUMNS = {'banned', 'encarcelado_hasta', 'placa', 'airplane_mode', 'wifi_connected', 'phone_number', 'rango', 'ban_reason', 'banned_by', 'ban_date'}
        for key, value in kwargs.items():
            if key not in VALID_COLUMNS:
                raise ValueError(f"Columna no valida: {key}")
            await self.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
        await self.invalidate_cache("users")

    # DNI
    async def get_dni(self, user_id):
        row = await self.fetchone("SELECT dni_nombre, dni_apellidos, dni_edad, dni_genero, dni_nacionalidad, dni_color_ojos, dni_altura, dni_profesion, dni_numero, dni_fecha_creacion FROM users WHERE user_id = ?", (user_id,))
        if row and row[0]:
            return {
                "nombre": row[0], "apellidos": row[1], "edad": row[2], "genero": row[3],
                "nacionalidad": row[4], "color_ojos": row[5], "altura": row[6],
                "profesion": row[7], "numero": row[8], "fecha_creacion": row[9]
            }
        return None

    async def set_dni(self, user_id, data):
        await self.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await self.execute("""
            UPDATE users SET dni_nombre=?, dni_apellidos=?, dni_edad=?, dni_genero=?, dni_nacionalidad=?,
            dni_color_ojos=?, dni_altura=?, dni_profesion=?, dni_numero=?, dni_fecha_creacion=?
            WHERE user_id=?
        """, (data["nombre"], data["apellidos"], data["edad"], data["genero"], data["nacionalidad"],
              data["color_ojos"], data["altura"], data["profesion"], data["numero"], data["fecha_creacion"], user_id))

    async def delete_dni(self, user_id):
        await self.execute("""
            UPDATE users SET dni_nombre=NULL, dni_apellidos=NULL, dni_edad=NULL, dni_genero=NULL,
            dni_color_ojos=NULL, dni_altura=NULL, dni_profesion=NULL,
            dni_numero=NULL, dni_fecha_creacion=NULL WHERE user_id=?
        """, (user_id,))

    # Multas
    async def add_multa(self, user_id, cantidad, motivo, agente, placa_agente):
        fecha = datetime.now().isoformat()
        await self.execute("INSERT INTO multas (user_id, cantidad, motivo, fecha, agente, placa_agente) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, cantidad, motivo, fecha, agente, placa_agente))
        await self.execute("UPDATE caja_municipal SET monto = monto + ? WHERE id = 1", (cantidad,))

    async def get_multas_pendientes(self, user_id):
        rows = await self.fetchall("SELECT id, cantidad, motivo, fecha, agente FROM multas WHERE user_id = ? AND pagada = 0", (user_id,))
        return [{"id": r[0], "cantidad": r[1], "motivo": r[2], "fecha": r[3], "agente": r[4]} for r in rows]

    async def pagar_multa(self, multa_id):
        await self.execute("UPDATE multas SET pagada = 1 WHERE id = ?", (multa_id,))

    async def get_caja_municipal(self):
        row = await self.fetchone("SELECT monto FROM caja_municipal WHERE id = 1")
        return row[0] if row else 0

    # Vehículos
    async def add_vehiculo(self, user_id, matricula, modelo):
        await self.execute("INSERT INTO vehiculos (user_id, matricula, modelo, seguro, itv, combustible) VALUES (?, ?, ?, 1, ?, 100)",
                           (user_id, matricula, modelo, (datetime.now() + timedelta(days=30)).isoformat()))

    async def get_vehiculos(self, user_id):
        rows = await self.fetchall("SELECT matricula, modelo, seguro, itv, combustible FROM vehiculos WHERE user_id = ?", (user_id,))
        return {r[0]: {"modelo": r[1], "seguro": bool(r[2]), "itv": r[3], "combustible": r[4]} for r in rows}

    async def update_vehiculo(self, user_id, matricula, **kwargs):
        for key, value in kwargs.items():
            await self.execute(f"UPDATE vehiculos SET {key} = ? WHERE user_id = ? AND matricula = ?", (value, user_id, matricula))

    # Armas y licencias
    async def dar_licencia(self, user_id, licencia):
        await self.execute("INSERT INTO armas_licencias (user_id, licencia, tiene) VALUES (?, ?, 1) ON CONFLICT(user_id, licencia) DO UPDATE SET tiene = 1", (user_id, licencia))

    async def quitar_licencia(self, user_id, licencia):
        await self.execute("UPDATE armas_licencias SET tiene = 0 WHERE user_id = ? AND licencia = ?", (user_id, licencia))

    async def get_licencias(self, user_id):
        rows = await self.fetchall("SELECT licencia, tiene FROM armas_licencias WHERE user_id = ?", (user_id,))
        return {r[0]: bool(r[1]) for r in rows}

    async def get_armas_equipadas(self, user_id):
        rows = await self.fetchall("SELECT arma, durabilidad, municion FROM armas_equipadas WHERE user_id = ?", (user_id,))
        return {r[0]: {"durabilidad": r[1], "municion": r[2]} for r in rows}

    async def dar_licencia_conduccion(self, user_id, tipo):
        await self.execute("INSERT OR REPLACE INTO licencias_conduccion (user_id, tipo, fecha_obtencion) VALUES (?, ?, ?)",
                           (user_id, tipo, datetime.now().isoformat()))

    async def tiene_licencia_conduccion(self, user_id, tipo):
        row = await self.fetchone("SELECT 1 FROM licencias_conduccion WHERE user_id = ? AND tipo = ?", (user_id, tipo))
        return row is not None

    async def get_licencias_conduccion(self, user_id):
        rows = await self.fetchall("SELECT tipo, fecha_obtencion FROM licencias_conduccion WHERE user_id = ?", (user_id,))
        return [{"tipo": r[0], "fecha_obtencion": r[1]} for r in rows]

    # Cooldowns
    async def check_cooldown(self, user_id, comando, segundos):
        row = await self.fetchone("SELECT expires FROM cooldowns WHERE user_id = ? AND comando = ?", (user_id, comando))
        ahora = datetime.now()
        if row and row[0]:
            expires = datetime.fromisoformat(row[0])
            if expires > ahora:
                return False, int((expires - ahora).total_seconds())
        nueva_expira = ahora + timedelta(seconds=segundos)
        await self.execute("INSERT INTO cooldowns (user_id, comando, expires) VALUES (?, ?, ?) ON CONFLICT(user_id, comando) DO UPDATE SET expires = ?",
                           (user_id, comando, nueva_expira.isoformat(), nueva_expira.isoformat()))
        return True, 0

    # DeepWeb
    async def add_deepweb_message(self, sender, receiver, message):
        sent_at = datetime.now().isoformat()
        await self.execute("INSERT INTO deepweb (sender, receiver, message, sent_at) VALUES (?, ?, ?, ?)", (sender, receiver, message, sent_at))
        row = await self.fetchone("SELECT last_insert_rowid()")
        return int(row[0]) if row else 0

    async def decode_deepweb_message(self, message_id, decoder_id):
        row = await self.fetchone("SELECT sender, message, anonymous FROM deepweb WHERE id = ?", (message_id,))
        if not row:
            return None
        if random.randint(1, 10) == 1:
            await self.execute("UPDATE deepweb SET anonymous = 0, decoded_by = ?, decoded_at = ? WHERE id = ?",
                               (decoder_id, datetime.now().isoformat(), message_id))
            return {"sender": row[0], "message": row[1], "anonymous": False, "decoded": True}
        return {"sender": row[0], "message": row[1], "anonymous": bool(row[2]), "decoded": False}

    # Atracos logs
    async def add_heist_log(self, user_id, heist, result, reward, black_reward, items):
        await self.execute("INSERT INTO atracos_logs (user_id, heist, result, reward, black_reward, items, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (user_id, heist, result, reward, black_reward, items, datetime.now().isoformat()))

    # Rachas casino
    async def actualizar_racha(self, user_id, ganado):
        tipo = "win" if ganado else "loss"
        row = await self.fetchone("SELECT racha, tipo FROM rachas WHERE user_id = ?", (user_id,))
        if row and row[1] == tipo:
            nueva_racha = row[0] + 1
        else:
            nueva_racha = 1
        await self.execute("INSERT INTO rachas (user_id, racha, tipo) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET racha = ?, tipo = ?",
                           (user_id, nueva_racha, tipo, nueva_racha, tipo))

    async def get_racha(self, user_id):
        row = await self.fetchone("SELECT racha, tipo FROM rachas WHERE user_id = ?", (user_id,))
        return {"racha": row[0] if row else 0, "tipo": row[1] if row else None}

    # Estadísticas
    async def inc_estadistica(self, key, inc=1):
        row = await self.fetchone("SELECT value FROM estadisticas WHERE key = ?", (key,))
        if row:
            val = int(row[0]) + inc
            await self.execute("UPDATE estadisticas SET value = ? WHERE key = ?", (str(val), key))
        else:
            await self.execute("INSERT INTO estadisticas (key, value) VALUES (?, ?)", (key, str(inc)))

    async def get_estadistica(self, key):
        row = await self.fetchone("SELECT value FROM estadisticas WHERE key = ?", (key,))
        return int(row[0]) if row else 0

    # Redes sociales
    async def add_post_ig(self, user_id, texto):
        pid = ''.join(random.choices('0123456789abcdef', k=8))
        await self.execute("INSERT INTO posts_ig (id, user_id, texto, tiempo, likes) VALUES (?, ?, ?, ?, ?)",
                           (pid, user_id, texto, datetime.now().isoformat(), json.dumps([])))
        return pid

    async def get_posts_ig(self, user_id):
        rows = await self.fetchall("SELECT id, texto, tiempo, likes FROM posts_ig WHERE user_id = ? ORDER BY tiempo DESC", (user_id,))
        return [{"id": r[0], "texto": r[1], "tiempo": r[2], "likes": json.loads(r[3]) if r[3] else []} for r in rows]

    async def add_like_ig(self, post_id, user_id):
        row = await self.fetchone("SELECT likes FROM posts_ig WHERE id = ?", (post_id,))
        if row:
            likes = json.loads(row[0]) if row[0] else []
            if user_id not in likes:
                likes.append(user_id)
                await self.execute("UPDATE posts_ig SET likes = ? WHERE id = ?", (json.dumps(likes), post_id))
                return True
        return False

    async def follow_ig(self, follower, following):
        await self.execute("INSERT OR IGNORE INTO seguidores_ig (follower, following) VALUES (?, ?)", (follower, following))

    async def unfollow_ig(self, follower, following):
        await self.execute("DELETE FROM seguidores_ig WHERE follower = ? AND following = ?", (follower, following))

    async def get_followers_ig(self, user_id):
        row = await self.fetchone("SELECT COUNT(*) FROM seguidores_ig WHERE following = ?", (user_id,))
        return row[0] if row else 0

    async def get_following_ig(self, user_id):
        row = await self.fetchone("SELECT COUNT(*) FROM seguidores_ig WHERE follower = ?", (user_id,))
        return row[0] if row else 0

    async def is_following_ig(self, follower, following):
        row = await self.fetchone("SELECT 1 FROM seguidores_ig WHERE follower = ? AND following = ?", (follower, following))
        return row is not None

    async def add_post_tw(self, user_id, texto):
        pid = ''.join(random.choices('0123456789abcdef', k=8))
        await self.execute("INSERT INTO posts_tw (id, user_id, texto, tiempo) VALUES (?, ?, ?, ?)", (pid, user_id, texto, datetime.now().isoformat()))
        return pid

    async def follow_tw(self, follower, following):
        await self.execute("INSERT OR IGNORE INTO seguidores_tw (follower, following, since) VALUES (?, ?, ?)",
                           (follower, following, datetime.now().isoformat()))

    async def unfollow_tw(self, follower, following):
        await self.execute("DELETE FROM seguidores_tw WHERE follower = ? AND following = ?", (follower, following))

    async def get_followers_tw(self, user_id):
        row = await self.fetchone("SELECT COUNT(*) FROM seguidores_tw WHERE following = ?", (user_id,))
        return row[0] if row else 0

    async def is_following_tw(self, follower, following):
        row = await self.fetchone("SELECT 1 FROM seguidores_tw WHERE follower = ? AND following = ?", (follower, following))
        return row is not None

    async def add_post_fb(self, user_id, texto):
        pid = ''.join(random.choices('0123456789abcdef', k=8))
        await self.execute("INSERT INTO posts_fb (id, user_id, texto, tiempo) VALUES (?, ?, ?, ?)", (pid, user_id, texto, datetime.now().isoformat()))
        return pid

    # WhatsApp
    async def add_wa_contact(self, user_id, numero, nombre):
        await self.execute("INSERT OR IGNORE INTO wa_contactos (user_id, numero, nombre) VALUES (?, ?, ?)", (user_id, numero, nombre))

    async def get_wa_contacts(self, user_id):
        rows = await self.fetchall("SELECT numero, nombre FROM wa_contactos WHERE user_id = ?", (user_id,))
        return {r[0]: r[1] for r in rows}

    async def add_wa_chat(self, de, para, mensaje):
        await self.execute("INSERT INTO wa_chats (de, para, mensaje, tiempo) VALUES (?, ?, ?, ?)",
                           (de, para, mensaje, datetime.now().isoformat()))

    async def get_wa_chats(self, user1, user2):
        rows = await self.fetchall("""
            SELECT de, mensaje, tiempo FROM wa_chats
            WHERE (de = ? AND para = ?) OR (de = ? AND para = ?)
            ORDER BY tiempo ASC
        """, (user1, user2, user2, user1))
        return [{"de": r[0], "mensaje": r[1], "tiempo": r[2]} for r in rows]

    # Precios drogas
    async def get_precio_droga(self, droga, es_compra=True):
        row = await self.fetchone("SELECT precio_compra, precio_venta FROM precios_drogas WHERE droga = ?", (droga,))
        if row:
            return row[0] if es_compra else row[1]
        return PRECIOS_DROGAS_BASE[droga]["compra"] if es_compra else PRECIOS_DROGAS_BASE[droga]["venta"]

    async def actualizar_precio_droga(self, droga, cantidad_vendida):
        compra_actual = await self.get_precio_droga(droga, True)
        venta_actual = await self.get_precio_droga(droga, False)
        if cantidad_vendida >= 5:
            compra_nuevo = int(compra_actual * 1.05)
            venta_nuevo = int(venta_actual * 1.07)
        elif cantidad_vendida >= 2:
            compra_nuevo = int(compra_actual * 1.02)
            venta_nuevo = int(venta_actual * 1.03)
        else:
            compra_nuevo = max(1, int(compra_actual * 0.99))
            venta_nuevo = max(1, int(venta_actual * 0.98))
        compra_base = PRECIOS_DROGAS_BASE[droga]["compra"]
        venta_base = PRECIOS_DROGAS_BASE[droga]["venta"]
        compra_nuevo = max(compra_base // 2, min(compra_base * 3, compra_nuevo))
        venta_nuevo = max(venta_base // 2, min(venta_base * 3, venta_nuevo))
        await self.execute("UPDATE precios_drogas SET precio_compra = ?, precio_venta = ? WHERE droga = ?", (compra_nuevo, venta_nuevo, droga))

    # Mercado
    async def add_mercado(self, pub_id, vendedor, item, descripcion, precio):
        await self.execute("INSERT INTO mercado (id, vendedor, item, descripcion, precio, fecha) VALUES (?, ?, ?, ?, ?, ?)",
                           (pub_id, vendedor, item, descripcion, precio, datetime.now().isoformat()))

    async def get_mercado(self):
        rows = await self.fetchall("SELECT id, vendedor, item, descripcion, precio, fecha FROM mercado ORDER BY fecha DESC")
        return [{"id": r[0], "vendedor": r[1], "item": r[2], "descripcion": r[3], "precio": r[4], "fecha": r[5]} for r in rows]

    async def remove_mercado(self, pub_id):
        await self.execute("DELETE FROM mercado WHERE id = ?", (pub_id,))

    async def get_mercado_by_id(self, pub_id):
        return await self.fetchone("SELECT vendedor, item, precio FROM mercado WHERE id = ?", (pub_id,))

    # Niveles
    async def add_xp(self, user_id, xp, tipo="message"):
        now = datetime.now().isoformat()
        row = await self.fetchone("SELECT xp, nivel, last_level_up FROM niveles WHERE user_id = ?", (user_id,))
        if not row:
            await self.execute("INSERT INTO niveles (user_id, xp, nivel, last_level_up) VALUES (?, ?, 0, ?)", (user_id, xp, now))
            xp_actual = xp
            nivel_actual = 0
            last_level_up = None
        else:
            xp_actual = row[0] + xp
            nivel_actual = row[1]
            last_level_up = row[2]
            await self.execute("UPDATE niveles SET xp = ? WHERE user_id = ?", (xp_actual, user_id))
            if tipo == "message":
                await self.execute("UPDATE niveles SET last_message_time = ? WHERE user_id = ?", (now, user_id))
            elif tipo == "command":
                await self.execute("UPDATE niveles SET last_command_time = ? WHERE user_id = ?", (now, user_id))
            elif tipo == "time":
                await self.execute("UPDATE niveles SET last_time_time = ? WHERE user_id = ?", (now, user_id))

        nuevo_nivel = int((xp_actual ** 0.5) / 10)
        if nuevo_nivel > nivel_actual:
            puede_subir = True
            if last_level_up:
                ultima_subida = datetime.fromisoformat(last_level_up)
                if (datetime.now() - ultima_subida).days < DIAS_PARA_SUBIR_NIVEL:
                    puede_subir = False
            if puede_subir:
                await self.execute("UPDATE niveles SET nivel = ?, last_level_up = ? WHERE user_id = ?", (nuevo_nivel, now, user_id))
                return nuevo_nivel
            else:
                return None
        return None

    async def get_nivel(self, user_id):
        row = await self.fetchone("SELECT xp, nivel, last_level_up FROM niveles WHERE user_id = ?", (user_id,))
        if row:
            return {"xp": row[0], "nivel": row[1], "last_level_up": row[2]}
        return {"xp": 0, "nivel": 0, "last_level_up": None}

    async def get_ranking_niveles(self, limit=10):
        return await self.fetchall("SELECT user_id, xp, nivel FROM niveles ORDER BY xp DESC LIMIT ?", (limit,))

    # Blacklist
    async def add_to_blacklist(self, user_id, reason, banned_by):
        await self.execute("INSERT OR IGNORE INTO blacklist (user_id, reason, banned_by, ban_date) VALUES (?, ?, ?, ?)",
                           (user_id, reason, banned_by, datetime.now().isoformat()))

    async def remove_from_blacklist(self, user_id):
        await self.execute("DELETE FROM blacklist WHERE user_id = ?", (user_id,))

    async def is_blacklisted(self, user_id):
        row = await self.fetchone("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,))
        return row is not None

    async def get_blacklist(self):
        rows = await self.fetchall("SELECT user_id, reason, banned_by, ban_date FROM blacklist")
        return [{"user_id": r[0], "reason": r[1], "banned_by": r[2], "ban_date": r[3]} for r in rows]

    # Web users
    async def create_web_user(self, username, password_hash, discord_id=None, is_staff=False):
        await self.execute("INSERT INTO web_users (username, password_hash, discord_id, is_staff, created_at) VALUES (?, ?, ?, ?, ?)",
                           (username, password_hash, discord_id, is_staff, datetime.now().isoformat()))

    async def get_web_user(self, username):
        row = await self.fetchone("SELECT id, username, password_hash, discord_id, is_staff FROM web_users WHERE username = ?", (username,))
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2], "discord_id": row[3], "is_staff": bool(row[4])}
        return None

    async def get_web_user_by_id(self, user_id):
        row = await self.fetchone("SELECT id, username, password_hash, discord_id, is_staff FROM web_users WHERE id = ?", (user_id,))
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2], "discord_id": row[3], "is_staff": bool(row[4])}
        return None

    async def get_web_user_by_discord(self, discord_id):
        row = await self.fetchone("SELECT id, username, password_hash, is_staff FROM web_users WHERE discord_id = ?", (discord_id,))
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2], "is_staff": bool(row[3])}
        return None

    # PDA permissions
    async def grant_pda_permission(self, user_id, granted_by):
        await self.execute("INSERT OR REPLACE INTO pda_permissions (user_id, granted_by, granted_at) VALUES (?, ?, ?)",
                           (user_id, granted_by, datetime.now().isoformat()))

    async def revoke_pda_permission(self, user_id):
        await self.execute("DELETE FROM pda_permissions WHERE user_id = ?", (user_id,))

    async def has_pda_permission(self, user_id):
        row = await self.fetchone("SELECT 1 FROM pda_permissions WHERE user_id = ?", (user_id,))
        return row is not None

    async def get_pda_permissions(self):
        rows = await self.fetchall("SELECT user_id, granted_by, granted_at FROM pda_permissions")
        return [{"user_id": r[0], "granted_by": r[1], "granted_at": r[2]} for r in rows]

    # Antiraid
    async def log_antiraid_action(self, user_id, action_type, guild_id):
        await self.execute("INSERT INTO antiraid_actions (user_id, action_type, timestamp, guild_id) VALUES (?, ?, ?, ?)",
                           (user_id, action_type, datetime.now().isoformat(), guild_id))

    async def count_actions_last_minute(self, user_id, action_type, guild_id, minutes=1):
        cutoff = datetime.now() - timedelta(minutes=minutes)
        row = await self.fetchone("SELECT COUNT(*) FROM antiraid_actions WHERE user_id = ? AND action_type = ? AND guild_id = ? AND timestamp > ?",
                                   (user_id, action_type, guild_id, cutoff.isoformat()))
        return row[0] if row else 0

    # Emojis personalizables
    async def set_emoji(self, key, emoji):
        await self.execute("INSERT OR REPLACE INTO emoji_settings (key, emoji) VALUES (?, ?)", (key, emoji))

    async def get_all_emojis(self):
        rows = await self.fetchall("SELECT key, emoji FROM emoji_settings")
        return {row[0]: row[1] for row in rows}

    # Twitter DMs
    async def add_twitter_dm(self, from_user, to_user, message):
        await self.execute("INSERT INTO twitter_dms (from_user, to_user, message, sent_at) VALUES (?, ?, ?, ?)",
                           (from_user, to_user, message, datetime.now().isoformat()))

    async def get_twitter_dms(self, user1, user2):
        rows = await self.fetchall("""
            SELECT from_user, message, sent_at FROM twitter_dms
            WHERE (from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?)
            ORDER BY sent_at ASC
        """, (user1, user2, user2, user1))
        return [{"from": r[0], "message": r[1], "sent_at": r[2]} for r in rows]

    # Preparatorias de atracos
    async def get_heist_preparations(self, user_id, heist_id):
        rows = await self.fetchall("SELECT prep_num, completed FROM heist_preparations WHERE user_id = ? AND heist_id = ?",
                                   (user_id, heist_id))
        return {row[0]: bool(row[1]) for row in rows}

    async def get_all_heist_preparations(self, user_id):
        rows = await self.fetchall("SELECT heist_id, prep_num, completed FROM heist_preparations WHERE user_id = ?", (user_id,))
        result = {}
        for heist_id, prep_num, completed in rows:
            if heist_id not in result:
                result[heist_id] = {}
            result[heist_id][prep_num] = bool(completed)
        return result

    async def complete_preparation(self, user_id, heist_id, prep_num):
        await self.execute("INSERT OR REPLACE INTO heist_preparations (user_id, heist_id, prep_num, completed) VALUES (?, ?, ?, 1)",
                           (user_id, heist_id, prep_num))

    async def is_preparation_completed(self, user_id, heist_id, prep_num):
        row = await self.fetchone("SELECT completed FROM heist_preparations WHERE user_id = ? AND heist_id = ? AND prep_num = ?",
                                  (user_id, heist_id, prep_num))
        return row is not None and bool(row[0])

    async def are_all_preparations_completed(self, user_id, heist_id, total_preps):
        if total_preps == 0:
            return True
        completed_count = await self.fetchone("SELECT COUNT(*) FROM heist_preparations WHERE user_id = ? AND heist_id = ? AND completed = 1",
                                               (user_id, heist_id))
        return completed_count[0] >= total_preps if completed_count else False

    async def reset_heist_preparations(self, user_id, heist_id):
        await self.execute("DELETE FROM heist_preparations WHERE user_id = ? AND heist_id = ?", (user_id, heist_id))

    # Emojis animados
    async def add_animated_emoji(self, name, emoji_id, added_by):
        await self.execute("INSERT INTO animated_emojis (name, emoji_id, added_by, added_at) VALUES (?, ?, ?, ?)",
                           (name, emoji_id, added_by, datetime.now().isoformat()))

    async def get_all_animated_emojis(self):
        rows = await self.fetchall("SELECT name, emoji_id, added_by, added_at FROM animated_emojis")
        return [{"name": r[0], "emoji_id": r[1], "added_by": r[2], "added_at": r[3]} for r in rows]

    # Expiración (hosting)
    async def get_expiry(self):
        row = await self.fetchone("SELECT value FROM bot_config WHERE key = 'expiry'")
        if row:
            return datetime.fromisoformat(row[0])
        return None

    async def set_expiry(self, expiry):
        await self.execute("UPDATE bot_config SET value = ? WHERE key = 'expiry'", (expiry.isoformat(),))

db = Database()

# ==================== DECORADORES ====================
def tiene_dni():
    async def predicate(ctx):
        dni = await db.get_dni(ctx.author.id)
        if not dni:
            await ctx.send(embed=embed_error("No tienes DNI. Crea uno con `/dni`"))
            return False
        return True
    return commands.check(predicate)

def tiene_profesion(*profesiones):
    async def predicate(ctx):
        dni = await db.get_dni(ctx.author.id)
        if not dni:
            await ctx.send(embed=embed_error("No tienes DNI."))
            return False
        prof = dni.get('profesion', '').lower()
        if not any(p.lower() in prof for p in profesiones):
            await ctx.send(embed=embed_error(f"Necesitas ser: {', '.join(profesiones)}"))
            return False
        return True
    return commands.check(predicate)

def check_encarcelado():
    async def predicate(ctx):
        state = await db.get_user_state(ctx.author.id)
        enc = state.get('encarcelado_hasta')
        if enc:
            try:
                hasta = datetime.fromisoformat(enc)
                if hasta > datetime.now():
                    mins = int((hasta - datetime.now()).total_seconds() / 60)
                    await ctx.send(embed=embed_error(f"🔒 Encarcelado. Tiempo restante: {mins} minutos"))
                    return False
                else:
                    await db.update_user_state(ctx.author.id, encarcelado_hasta=None)
            except:
                await db.update_user_state(ctx.author.id, encarcelado_hasta=None)
        return True
    return commands.check(predicate)

def check_ban():
    async def predicate(ctx):
        state = await db.get_user_state(ctx.author.id)
        if state.get('banned'):
            await ctx.send(embed=embed_error("Estás baneado del sistema."))
            return False
        return True
    return commands.check(predicate)

def is_owner():
    async def predicate(ctx):
        if ctx.author.id not in OWNER_IDS:
            await ctx.send(embed=embed_error("No tienes permiso para usar este comando."))
            return False
        return True
    return commands.check(predicate)

def tiene_rol_o_owner(role_id):
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        role = ctx.guild.get_role(role_id)
        if role and role in ctx.author.roles:
            return True
        await ctx.send(embed=embed_error("No tienes el rol necesario para usar este comando."))
        return False
    return commands.check(predicate)

def tiene_rol_iniciador(): return tiene_rol_o_owner(ROL_INICIADOR_ID)
def tiene_rol_equipo_especial(): return tiene_rol_o_owner(ROL_EQUIPO_ESPECIAL_ID)
def tiene_rol_dashboard(): return tiene_rol_o_owner(ROL_DASHBOARD_ID)
def tiene_rol_lspd_operativo(): return tiene_rol_o_owner(ROL_LSPD_OPERATIVO_ID)
def tiene_rol_mafia(): return tiene_rol_o_owner(ROL_MAFIA_ID)
def tiene_rol_mafia_admin(): return tiene_rol_o_owner(ROL_MAFIA_ADMIN_ID)
def tiene_rol_minero(): return tiene_rol_o_owner(ROL_MINERO_ID)
def tiene_rol_autobusero(): return tiene_rol_o_owner(ROL_AUTOBUSERO_ID)
def tiene_rol_chatarrero(): return tiene_rol_o_owner(ROL_CHATARRERO_ID)

def tiene_rol_usuario():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        role = ctx.guild.get_role(ROL_USUARIO_ID)
        if role:
            return role in ctx.author.roles
        return True
    return commands.check(predicate)

def es_owner_o_mafia():
    async def predicate(ctx):
        if ctx.author.id in OWNER_IDS:
            return True
        role = ctx.guild.get_role(ROL_MAFIA_ID)
        if role and role in ctx.author.roles:
            return True
        return False
    return commands.check(predicate)

class ConfirmView(discord.ui.View):
    def __init__(self, user_id, timeout=30):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.value = None

    @discord.ui.button(label="✅ Sí", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No eres el dueño de esta solicitud", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="❌ No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No eres el dueño de esta solicitud", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()

# ==================== CLASE BASE ====================
class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log(self, accion, detalles):
        channel = self.bot.get_channel(CANAL_LOGS)
        if channel:
            await channel.send(f"📝 `{accion}`: {detalles}")
        try:
            with open('rtu_logs.json', 'a', encoding='utf-8') as f:
                json.dump({"time": datetime.now().isoformat(), "accion": accion, "detalles": detalles}, f)
                f.write('\n')
        except:
            pass

    async def dm_user(self, user_id, embed):
        user = self.bot.get_user(user_id)
        if user:
            try:
                await user.send(embed=embed)
                return True
            except discord.Forbidden:
                pass
        return False

    async def obtener_nombre_dni(self, uid):
        try:
            dni = await db.get_dni(uid)
            if dni and dni.get('nombre') and dni.get('apellidos'):
                return f"{dni['nombre']} {dni['apellidos']}".strip()
        except Exception:
            pass
        return None

    async def log_economia(self, mensaje):
        canal = self.bot.get_channel(CANAL_LOG_ECONOMIA)
        if canal:
            await canal.send(f"💰 **Economía** • {mensaje}")

    async def registrar_log_moderacion(self, ctx, accion, target, razon, duracion=None):
        canal = self.bot.get_channel(CANAL_LOG_SANCIONES)
        if not canal:
            return
        embed = discord.Embed(
            title=f"🔨 {accion}",
            description=f"**Usuario:** {target.mention}\n**Razón:** {razon}\n**Moderador:** {ctx.author.mention}",
            color=discord.Color.red() if "baneado" in accion.lower() else discord.Color.orange(),
            timestamp=datetime.now()
        )
        if duracion:
            embed.add_field(name="Duración", value=duracion)
        await canal.send(embed=embed)

# ==================== COG: Principal ====================
class Principal(BaseCog):
    @commands.hybrid_command(name='inv', description="Ver inventario")
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def inv(self, ctx, tipo: Optional[str] = None):
        uid = ctx.author.id
        tipo_map = {'banda': 'ilegal', 'encima': 'personal'}
        if not tipo:
            return await ctx.send(embed=embed_info("🎒 Inventarios", "Tipos: encima · vehiculo · propiedad · negocios · banda\nUsa `-inv [tipo]`"))
        t = tipo.lower()
        t = tipo_map.get(t, t)
        if t not in ['personal', 'vehiculo', 'propiedad', 'negocios', 'ilegal']:
            return await ctx.send(embed=embed_error("Tipos: encima, vehiculo, propiedad, negocios, banda"))
        if t == 'ilegal':
            grams = await db.get_drug_grams(uid)
            if not grams:
                return await ctx.send(embed=embed_info("🎭 Inventario Banda", "No tienes gramos de droga acumulados."))
            desc = "\n".join([f"{EMOJIS_DROGA.get(droga, '💊')} **{droga}:** {gramos} gramos" for droga, gramos in grams.items()])
            embed = discord.Embed(title="🎭 INVENTARIO BANDA (Gramos)", description=desc, color=0x8B0000)
            embed.set_footer(text="Usa -inv banda transferir para enviar gramos a otro usuario")
            view = InvIlegalView(ctx.author.id, grams)
            await ctx.send(embed=embed, view=view)
            return
        inv = await db.get_inventory(uid, t)
        txt = "\n".join([f"{await get_emoji('inventory')} **{it}** x{c}" for it, c in sorted(inv.items())]) if inv else "*Vacío*"
        embed = discord.Embed(title=f"{'Encima' if t == 'personal' else t.capitalize()}", description=txt, color=0x3498DB)
        economy = await db.get_economy(uid)
        emoji_money = await get_emoji('money')
        emoji_bank = await get_emoji('bank')
        embed.set_footer(text=f"{emoji_money} Saldo: **${economy['cash']:,}** | {emoji_bank} Banco: **${economy['bank']:,}**")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='balance-top')
    @tiene_rol_usuario()
    async def bal_top(self, ctx, pagina: int = 1):
        rows = await db.fetchall("SELECT user_id, cash, bank FROM economy")
        if not rows:
            return await ctx.send(embed=embed_error("No hay usuarios con saldo."))
        totales = [(r[0], r[1] + r[2]) for r in rows]
        totales.sort(key=lambda x: x[1], reverse=True)
        por_pagina = 10
        total_pags = max(1, (len(totales) + por_pagina - 1) // por_pagina)
        pagina = max(1, min(pagina, total_pags))
        inicio = (pagina - 1) * por_pagina
        top = totales[inicio:inicio + por_pagina]

        medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
        desc = ""
        for i, (uid, saldo) in enumerate(top, start=inicio + 1):
            usuario = ctx.guild.get_member(uid)
            if not usuario:
                try:
                    usuario = await ctx.guild.fetch_member(uid)
                except:
                    pass
            nombre = usuario.display_name if usuario else f"Usuario {uid}"
            desc += f"{medallas.get(i, f'`#{i}`')} **{nombre}**\n**${saldo:,}**\n\n"

        uid_autor = ctx.author.id
        eco_autor = await db.get_economy(uid_autor)
        saldo_autor = eco_autor['cash'] + eco_autor['bank']
        pos_autor = next((i+1 for i, (u, _) in enumerate(totales) if u == uid_autor), "?")
        embed = discord.Embed(
            title=f"{await get_emoji('money')} TOP DINERO — Nova Agora",
            description=desc or "*Sin datos*",
            color=0xFFD700,
            timestamp=datetime.now()
        )
        embed.add_field(name="📊 Tu posición:", value=f"```\n#{pos_autor} — ${saldo_autor:,}\n```", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Página {pagina}/{total_pags}  ·  {len(totales)} usuarios  ·  NOVA AGORA")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.hybrid_command(name='tienda', description="Abrir tienda")
    @check_ban()
    @tiene_rol_usuario()
    async def shop(self, ctx):
        view = TiendaPaginator(ctx.author.id)
        await view.send(ctx)

    @commands.command(name='comprar')
    @check_ban()
    @tiene_rol_usuario()
    async def comprar(self, ctx, *, pedido: str):
        uid = ctx.author.id
        texto = pedido.strip()
        if not texto:
            return await ctx.send(embed=embed_error("Debes especificar el artículo a comprar."))

        cantidad = 1
        partes = texto.split()
        if partes[0].isdigit() and len(partes) > 1:
            cantidad = int(partes[0])
            texto = " ".join(partes[1:])
        elif partes[-1].isdigit() and len(partes) > 1:
            cantidad = int(partes[-1])
            texto = " ".join(partes[:-1])

        item_data = TIENDA_ITEMS_DICT.get(texto.lower())
        if not item_data:
            return await ctx.send(embed=embed_error("Artículo no encontrado."))
        item_norm, precio_unitario, emoji, desc = item_data
        if es_precio_infinito(precio_unitario):
            return await ctx.send(embed=embed_error("No se puede comprar un artículo de valor infinito."))
        precio = precio_unitario * cantidad
        eco = await db.get_economy(uid)
        use_black = item_norm.lower() in ILLEGAL_TIENDA_ITEMS

        if use_black:
            if eco['black_money'] < precio:
                return await ctx.send(embed=embed_error(f"Necesitas **${precio:,}** en dinero negro. Tienes: **${eco['black_money']:,}**"))
            await db.add_black(uid, -precio)
            metodo = "dinero negro"
        else:
            if eco['cash'] < precio:
                return await ctx.send(embed=embed_error(f"Necesitas **${precio:,}**. Tienes: **${eco['cash']:,}**"))
            await db.add_cash(uid, -precio)
            metodo = "efectivo"

        await db.add_item(uid, "personal", item_norm, cantidad)
        embed = discord.Embed(
            title="✅ Compra realizada",
            description=f"{cantidad}x {item_norm} por **${precio:,}** ({metodo}).\n*{desc}*",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("COMPRA", f"{ctx.author.name} compró {cantidad}x {item_norm} por ${precio:,} ({metodo})")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='comprar-licencia')
    @check_ban()
    @tiene_rol_usuario()
    async def comprar_licencia(self, ctx, *, pedido: str = None):
        if not pedido:
            return await ctx.send(embed=embed_help(
                "comprar-licencia",
                "Compra una licencia directamente desde la tienda.",
                "-comprar-licencia <tipo_licencia> [cantidad]",
                "-comprar-licencia coche 1\n-comprar-licencia armas_cortas",
                ""
            ))

        partes = pedido.split()
        cantidad = 1
        if partes[-1].isdigit():
            cantidad = int(partes[-1])
            partes = partes[:-1]

        tipo = " ".join(partes).strip().lower()
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("La cantidad debe ser al menos 1."))
        if cantidad != 1:
            return await ctx.send(embed=embed_error("Solo puedes comprar una licencia por comando."))

        aliases = {
            "camion": ("Licencia de camión", "conduccion", "camion"),
            "coche": ("Licencia de coche", "conduccion", "coche"),
            "moto": ("Licencia de moto", "conduccion", "moto"),
            "armas blancas": ("Licencia de armas blancas", "armas", "licencia_blanca"),
            "armas cortas": ("Licencia de armas cortas", "armas", "licencia_corta"),
            "licencia de camión": ("Licencia de camión", "conduccion", "camion"),
            "licencia de coche": ("Licencia de coche", "conduccion", "coche"),
            "licencia de moto": ("Licencia de moto", "conduccion", "moto"),
            "licencia de armas blancas": ("Licencia de armas blancas", "armas", "licencia_blanca"),
            "licencia de armas cortas": ("Licencia de armas cortas", "armas", "licencia_corta"),
        }

        if tipo not in aliases:
            return await ctx.send(embed=embed_error("Tipo de licencia no válido. Usa: coche, moto, camion, armas blancas, armas cortas."))

        item_name, categoria, clave = aliases[tipo]
        precio_unitario = TIENDA_ITEMS_DICT[item_name.lower()][1]
        if es_precio_infinito(precio_unitario):
            return await ctx.send(embed=embed_error("No se puede comprar una licencia de valor infinito."))
        precio_total = precio_unitario * cantidad
        eco = await db.get_economy(ctx.author.id)
        if eco['cash'] < precio_total:
            return await ctx.send(embed=embed_error(f"Necesitas **${precio_total:,}**. Tienes: **${eco['cash']:,}**"))

        await db.add_cash(ctx.author.id, -precio_total)
        if categoria == "conduccion":
            await db.dar_licencia_conduccion(ctx.author.id, clave)
            descripcion = f"Has comprado {cantidad}x {item_name} y ahora tienes la licencia de {clave}."
        else:
            await db.dar_licencia(ctx.author.id, clave)
            descripcion = f"Has comprado {cantidad}x {item_name} y ahora tienes la licencia {clave}."

        embed = discord.Embed(
            title="✅ Licencia comprada",
            description=f"{descripcion}\nCosto: **${precio_total:,}**",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("COMPRA_LICENCIA", f"{ctx.author.name} compró {cantidad}x {item_name} por ${precio_total:,}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='licencia')
    @check_ban()
    @tiene_rol_usuario()
    async def licencia(self, ctx, usuario: discord.Member = None):
        if usuario is None:
            usuario = ctx.author

        uid = usuario.id
        dni = await db.get_dni(uid)
        licencias_armas = await db.get_licencias(uid)
        licencias_conduccion = await db.get_licencias_conduccion(uid)

        txt_dni = "✅ Registrado" if dni else "❌ No registrado"
        if usuario != ctx.author:
            txt_dni = f"{txt_dni} ({usuario.display_name})"

        txt_armas = "\n".join([
            f"{'✅' if tiene else '❌'} {lic.replace('_', ' ').title()}"
            for lic, tiene in licencias_armas.items()
        ]) if licencias_armas else "Ninguna"
        txt_conduccion = "\n".join([
            f"✅ {lic['tipo'].title()} (obtenida: {lic['fecha_obtencion'][:10]})"
            for lic in licencias_conduccion
        ]) if licencias_conduccion else "Ninguna"

        embed = discord.Embed(
            title="📜 Licencias",
            description=f"DNI: {txt_dni}",
            color=0x3498DB
        )
        embed.add_field(name="🚗 Licencias de conducción", value=txt_conduccion, inline=False)
        embed.add_field(name="🔪 Licencias de armas", value=txt_armas, inline=False)
        embed.set_footer(text="Usa -comprar-licencia <tipo> [cantidad] para comprar una licencia directamente")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='use')
    @check_ban()
    @tiene_rol_usuario()
    async def use_item(self, ctx, *, item: str):
        uid = ctx.author.id
        if item.lower() in ('dinero negro', 'dinero_negro', 'blackmoney'):
            eco = await db.get_economy(uid)
            if eco['black_money'] <= 0:
                return await ctx.send(embed=embed_error("No tienes dinero negro."))
            TASA = 0.65
            limpio = int(eco['black_money'] * TASA)
            comision = eco['black_money'] - limpio
            await db.add_black(uid, -eco['black_money'])
            await db.add_cash(uid, limpio)
            embed = discord.Embed(
                title="💶 Blanqueo de dinero",
                description=f"Has blanqueado **${eco['black_money']:,}** → +**${limpio:,}** (comisión **${comision:,}**)",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
            await self.log("BLANQUEO", f"{ctx.author.name} blanqueó ${eco['black_money']:,}")
            return

        inv = await db.get_inventory(uid, "personal")
        item_real = next((k for k in inv if k.lower() == item.lower()), None)
        if not item_real:
            return await ctx.send(embed=embed_error("No tienes ese artículo."))

        if item_real.startswith("Licencia de"):
            if "armas blancas" in item_real.lower():
                await db.dar_licencia(uid, "licencia_blanca")
                mensaje = "Has obtenido la licencia para armas blancas."
            elif "armas cortas" in item_real.lower():
                await db.dar_licencia(uid, "licencia_corta")
                mensaje = "Has obtenido la licencia para armas cortas."
            elif "camión" in item_real.lower():
                await db.dar_licencia_conduccion(uid, "camion")
                mensaje = "Has obtenido la licencia de camión."
            elif "coche" in item_real.lower():
                await db.dar_licencia_conduccion(uid, "coche")
                mensaje = "Has obtenido la licencia de coche."
            elif "moto" in item_real.lower():
                await db.dar_licencia_conduccion(uid, "moto")
                mensaje = "Has obtenido la licencia de moto."
            else:
                mensaje = f"Has usado {item_real}."
            await db.remove_item(uid, "personal", item_real, 1)
            embed = discord.Embed(description=f"📜 **{mensaje}**", color=0x00FF00)
            await ctx.send(embed=embed)
            await self.log("USE_LICENCIA", f"{ctx.author.name} usó {item_real}")
            return

        efectos = {
            "sprunk": "bebe un Sprunk refrescante.", "ecola": "bebe una E-Cola.", "agua": "bebe agua y se hidrata.",
            "hotdog": "se come un hotdog.", "burger": "devora una hamburguesa.", "pizza": "se come una pizza.",
            "cigs": "enciende un cigarrillo.", "encendedor": "usa el encendedor.", "mascara": "se pone la máscara.",
            "guantes": "se pone los guantes de látex.", "zapatillas": "se ata las zapatillas.",
            "chaqueta": "se pone la chaqueta.", "auriculares": "se pone los auriculares.", "kit": "usa el kit de herramientas.",
            "botiquin": "usa el botiquín y se venda las heridas.", "linterna": "enciende la linterna.",
            "radio": "sintoniza la radio.", "gps": "activa el GPS.", "camara": "saca una foto del entorno.",
            "ganzua": "usa la ganzúa para forzar la cerradura.", "mochila": "abre la mochila y revisa su contenido.",
            "gasolina": "reposta el vehículo con gasolina.", "9mm": "empuña la pistola 9mm.",
            "phone": "saca el teléfono.", "papas": "come unas papas fritas.", "gaseosa": "bebe una gaseosa.",
            "empanada": "se come una empanada.", "chocolate": "come un chocolate.",
            "bolsas atraco": "prepara las bolsas para el atraco.", "pasamontañas": "se pone el pasamontañas.",
            "esposas": "coloca las esposas.", "llave inglesa": "usa la llave inglesa.",
            "herramientas": "usa las herramientas.", "desfibrilador": "usa el desfibrilador.",
            "traje ignifugo": "se pone el traje ignífugo.", "hacha": "empuña el hacha.",
            "manguera": "usa la manguera.", "placa policial": "muestra su placa policial.",
            "kit médico": "usa el kit médico para curar heridas graves.",
        }
        accion = efectos.get(item_real.lower(), f"usa {item_real}.")
        await db.remove_item(uid, "personal", item_real, 1)
        nombre = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        embed = discord.Embed(description=f"**{nombre}** {accion}", color=0x800080, timestamp=datetime.now())
        embed.set_author(name="🎮 Acción de Item", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        await self.log("USE_ITEM", f"{ctx.author.name} usó {item_real}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='blanquear', aliases=['lavar'])
    @check_ban()
    @tiene_rol_mafia()
    async def blanquear(self, ctx, tipo: str = None, gramos: int = None):
        """Convierte gramos de droga en dinero limpio o negro.
        Uso: -blanquear limpio <gramos>  o  -blanquear negro <gramos>"""
        if tipo is None or gramos is None:
            return await ctx.send(embed=embed_error("Error: -blanquear dinero limpio o dinero negro (gramos)"))
        tipo = tipo.lower()
        if tipo not in ['limpio', 'negro']:
            return await ctx.send(embed=embed_error("Error: -blanquear dinero limpio o dinero negro (gramos)"))
        if gramos <= 0:
            return await ctx.send(embed=embed_error("La cantidad de gramos debe ser positiva."))
        uid = ctx.author.id
        drug_grams = await db.get_drug_grams(uid)
        total_grams = sum(drug_grams.values())
        if total_grams < gramos:
            return await ctx.send(embed=embed_error(f"No tienes suficientes gramos. Disponibles: {total_grams} gramos."))
        remaining = gramos
        for drug, g in sorted(drug_grams.items(), key=lambda x: -x[1]):
            if remaining <= 0:
                break
            take = min(g, remaining)
            await db.remove_drug_grams(uid, drug, take)
            remaining -= take
        if tipo == 'limpio':
            ganancia = gramos * 100
            await db.add_cash(uid, ganancia)
            mensaje = f"Has convertido {gramos} gramos en **${ganancia:,}** de dinero limpio."
        else:
            ganancia = gramos * 50
            await db.add_black(uid, ganancia)
            mensaje = f"Has convertido {gramos} gramos en **${ganancia:,}** de dinero negro."
        embed = discord.Embed(title="💱 BLANQUEO DE GRAMOS", description=mensaje, color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("BLANQUEO_GRAMOS", f"{ctx.author.name} convirtió {gramos}g en {tipo}: +${ganancia}")

    @commands.command(name='tienda-ilegal', aliases=['ilegal-shop', 'tiendailegal'])
    @check_ban()
    @tiene_rol_usuario()
    async def tienda_ilegal(self, ctx):
        ITEMS_ILEGALES = [
            ("Dispositivo de hackeo", 1800, "🛠️", "Permite hackear sistemas de seguridad."),
            ("Termita", 700, "🔥", "Funde cerraduras y cajas fuertes."),
            ("Tarjeta de crédito", 120, "💳", "Clonada, para compras ilegales."),
            ("Gas lacrimógeno", 450, "😷", "Control de masas."),
            ("Pasamontañas", 75, "😷", "Oculta tu identidad."),
            ("Bolsas Atraco", 300, "🛍️", "Transporta dinero sucio."),
            ("Ganzúa", 80, "🔑", "Abre cerraduras sencillas."),
            ("Mascaras", 50, "🎭", "Disfraza tu rostro."),
        ]

        desc = ""
        for nombre, precio, emoji, desc_item in ITEMS_ILEGALES:
            desc += f"{emoji} **{nombre}** — **${precio}**\n*{desc_item}*\n"

        embed = discord.Embed(
            title="🔓 TIENDA ILEGAL — Operación Encubierta",
            description=desc,
            color=0x1a1a1a
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3124/3124564.png")
        embed.set_footer(text="⚠️ Usa -comprar <item> [cantidad] para adquirir | TOTALMENTE ANÓNIMO")
        embed.add_field(name="⚠️ ADVERTENCIA", value="Estos items son para actividades ilegales. Trae dinero negro. 💶", inline=False)

        await ctx.send(embed=embed)
        await self.log("TIENDA_ILEGAL", f"{ctx.author.name} abrió la tienda ilegal")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='intercambio')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def intercambio(self, ctx, usuario: discord.Member, cantidad: int, *, item: str):
        uid, tid = ctx.author.id, usuario.id
        if uid == tid:
            return await ctx.send(embed=embed_error("No puedes intercambiar contigo mismo."))
        inv = await db.get_inventory(uid, "personal")
        item_real = next((k for k in inv if k.lower() == item.lower()), None)
        if not item_real:
            return await ctx.send(embed=embed_error(f"No tienes {item}."))
        if inv[item_real] < cantidad:
            return await ctx.send(embed=embed_error(f"Solo tienes {inv[item_real]}."))
        await db.remove_item(uid, "personal", item_real, cantidad)
        await db.add_item(tid, "personal", item_real, cantidad)
        embed = discord.Embed(
            title="🔄 Intercambio",
            description=f"{ctx.author.mention} ha dado {cantidad}x {item_real} a {usuario.mention}.",
            color=0x3498DB
        )
        await ctx.send(embed=embed)
        await self.log("INTERCAMBIO", f"{ctx.author.name} dio {cantidad}x {item_real} a {usuario.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='mover')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def move(self, ctx, item: str, cantidad: int, origen: str, destino: str):
        uid = ctx.author.id
        o, d = origen.lower(), destino.lower()
        tipos_validos = ['personal', 'vehiculo', 'propiedad', 'negocios']
        if o not in tipos_validos or d not in tipos_validos:
            return await ctx.send(embed=embed_error("Tipos: personal, vehiculo, propiedad, negocios"))
        inv_o = await db.get_inventory(uid, o)
        if inv_o.get(item, 0) < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes {item} en {o}."))
        await db.remove_item(uid, o, item, cantidad)
        await db.add_item(uid, d, item, cantidad)
        await ctx.send(embed=embed_success("✅ Movido", f"{cantidad}x {item} de {o} a {d}."))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='trabajo')
    @check_encarcelado()
    @tiene_rol_usuario()
    async def trabajo_cmd(self, ctx):
        embed = discord.Embed(
            title=f"{await get_emoji('work')} SISTEMA DE TRABAJO",
            description="✅ **Entrar a trabajar** — Simula tu jornada laboral (sin remuneración, solo roleplay)\n⏹️ **Salir del trabajo** — Finaliza tu turno",
            color=discord.Color.blue()
        )
        view = TrabajoView()
        await ctx.send(embed=embed, view=view)
        try:
            await ctx.message.delete()
        except:
            pass

class TrabajoView(discord.ui.View):
    trabajo_data = {}

    @discord.ui.button(label="Entrar a trabajar", style=discord.ButtonStyle.green, emoji="✅")
    async def entrar_trabajo(self, interaction: discord.Interaction, button):
        uid = str(interaction.user.id)
        enc = await db.get_user_state(interaction.user.id)
        if enc.get('encarcelado_hasta') and datetime.fromisoformat(enc['encarcelado_hasta']) > datetime.now():
            return await interaction.response.send_message(embed=embed_error("No puedes trabajar mientras estás encarcelado."), ephemeral=True)
        if uid in self.trabajo_data and self.trabajo_data[uid]['estado'] == 'trabajando':
            return await interaction.response.send_message(embed=embed_error("Ya estás trabajando."), ephemeral=True)
        self.trabajo_data[uid] = {'estado': 'trabajando', 'inicio': datetime.now()}
        embed = discord.Embed(
            title="✅ ¡BIENVENIDO AL TRABAJO!",
            description="Estás en horario laboral (roleplay).\nPulsa **Salir** cuando termines tu jornada.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Salir del trabajo", style=discord.ButtonStyle.red, emoji="⏹️")
    async def salir_trabajo(self, interaction: discord.Interaction, button):
        uid = str(interaction.user.id)
        if uid not in self.trabajo_data or self.trabajo_data[uid]['estado'] != 'trabajando':
            return await interaction.response.send_message(embed=embed_error("Primero debes entrar a trabajar."), ephemeral=True)
        minutos = max(1, (datetime.now() - self.trabajo_data[uid]['inicio']).total_seconds() / 60)
        embed = discord.Embed(
            title="⌛ FIN DEL TURNO",
            description=f"Has trabajado durante {minutos:.1f} minutos. ¡Gracias por tu esfuerzo! (Sin remuneración económica)",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        del self.trabajo_data[uid]
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TiendaPaginator(discord.ui.View):
    def __init__(self, user_id: int, items_por_pagina: int = 9):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.items_por_pagina = items_por_pagina
        self.pagina_actual = 0
        self.total_items = len(TIENDA_ITEMS_FULL)
        self.total_paginas = (self.total_items + items_por_pagina - 1) // items_por_pagina
        self.message = None
        self.update_buttons()

    async def get_embed(self):
        emoji_shop = await get_emoji('shop')
        inicio = self.pagina_actual * self.items_por_pagina
        fin = min(inicio + self.items_por_pagina, self.total_items)
        items_pagina = TIENDA_ITEMS_FULL[inicio:fin]
        desc = ""
        for nombre, precio, emoji, descripcion in items_pagina:
            precio_str = formatear_precio(precio)
            desc += f"「{emoji}」 **{nombre}** — **{precio_str}**\n*{descripcion}*\n\n"
        embed = discord.Embed(
            title=f"{emoji_shop} TIENDA NOVA AGORA — Página {self.pagina_actual + 1}/{self.total_paginas}",
            description=desc if desc else "*No hay items en esta página*",
            color=0xFFD700
        )
        embed.set_footer(text="Usa -comprar <item> [cantidad] para comprar")
        return embed

    def update_buttons(self):
        self.clear_items()
        if self.pagina_actual > 0:
            self.add_item(TiendaBoton("◀️ Anterior", self.pagina_actual - 1))
        if self.pagina_actual < self.total_paginas - 1:
            self.add_item(TiendaBoton("Siguiente ▶️", self.pagina_actual + 1))
        self.add_item(TiendaBotonCerrar())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=embed_error("No eres el dueño de esta tienda."), ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(content="La tienda ha expirado por inactividad.", embed=None, view=None)
            except discord.NotFound:
                pass

    async def send(self, ctx):
        embed = await self.get_embed()
        self.message = await ctx.send(embed=embed, view=self)

class TiendaBoton(discord.ui.Button):
    def __init__(self, label, pagina):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.pagina = pagina

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.pagina_actual = self.pagina
        view.update_buttons()
        embed = await view.get_embed()
        await interaction.response.edit_message(embed=embed, view=view)

class TiendaBotonCerrar(discord.ui.Button):
    def __init__(self):
        super().__init__(label="❌ Cerrar", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Tienda cerrada.", embed=None, view=None)
        self.view.stop()

# Vista para inventario ilegal (transferencia de gramos)
class InvIlegalView(discord.ui.View):
    def __init__(self, user_id, drug_grams: dict):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.drug_grams = drug_grams
        options = []
        for drug, grams in drug_grams.items():
            if grams > 0:
                emoji = EMOJIS_DROGA.get(drug, "💊")
                options.append(discord.SelectOption(label=f"{drug} ({grams}g)", value=drug, emoji=emoji))
        if options:
            select = discord.ui.Select(placeholder="Selecciona una droga para transferir", options=options)
            select.callback = self.select_drug
            self.add_item(select)
        self.add_item(discord.ui.Button(label="❌ Cerrar", style=discord.ButtonStyle.red, custom_id="close"))

    async def select_drug(self, interaction: discord.Interaction):
        drug = interaction.data['values'][0]
        modal = TransferirGramosModal(self.user_id, drug)
        await interaction.response.send_modal(modal)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No puedes usar este menú.", ephemeral=True)
            return False
        return True

class TransferirGramosModal(discord.ui.Modal, title="Transferir gramos"):
    def __init__(self, user_id, drug_type):
        super().__init__()
        self.user_id = user_id
        self.drug_type = drug_type
    destinatario = discord.ui.TextInput(label="ID o mención del destinatario", placeholder="@usuario o ID")
    cantidad = discord.ui.TextInput(label="Cantidad de gramos", placeholder="Ej: 50")

    async def on_submit(self, interaction: discord.Interaction):
        uid = self.user_id
        target_input = self.destinatario.value.strip()
        try:
            if target_input.startswith('<@') and target_input.endswith('>'):
                target_id = int(target_input[2:-1])
            else:
                target_id = int(target_input)
            target = interaction.guild.get_member(target_id)
            if not target:
                await interaction.response.send_message("Usuario no encontrado.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("ID o mención inválida.", ephemeral=True)
            return
        if target.id == uid:
            await interaction.response.send_message("No puedes transferirte a ti mismo.", ephemeral=True)
            return
        try:
            grams = int(self.cantidad.value)
            if grams <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("Cantidad inválida.", ephemeral=True)
            return
        drug_grams = await db.get_drug_grams(uid)
        if drug_grams.get(self.drug_type, 0) < grams:
            await interaction.response.send_message(f"No tienes suficientes gramos de {self.drug_type}.", ephemeral=True)
            return
        await db.remove_drug_grams(uid, self.drug_type, grams)
        await db.add_drug_grams(target.id, self.drug_type, grams)
        await interaction.response.send_message(f"✅ Has transferido {grams} gramos de **{self.drug_type}** a {target.mention}.", ephemeral=True)
        await db.log_antiraid_action(uid, f"transferir_gramos_{self.drug_type}", interaction.guild.id)

# ==================== COG: Drogas ====================
class Drogas(BaseCog):
    ventas_sin_fallo = {}

    @commands.group(name='droga', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def droga(self, ctx):
        embed = discord.Embed(title=f"{await get_emoji('drugs')} Mercado de Drogas (Precios Dinámicos)", color=discord.Color.dark_green())
        for droga, emoji in EMOJIS_DROGA.items():
            precio_compra = await db.get_precio_droga(droga, True)
            precio_venta = await db.get_precio_droga(droga, False)
            embed.add_field(
                name=f"{emoji} {droga}",
                value=f"🛒 Compra: **${precio_compra}**\n💵 Venta: **${precio_venta}**",
                inline=False
            )
        embed.set_footer(text="Precios dinámicos según oferta/demanda")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @droga.command(name='comprar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def drg_buy(self, ctx, tipo: str, cantidad: int = 1):
        uid = ctx.author.id
        tipo_norm = tipo.capitalize()
        if tipo_norm not in EMOJIS_DROGA:
            return await ctx.send(embed=embed_error(f"Tipos válidos: {', '.join(EMOJIS_DROGA.keys())}"))
        if cantidad <= 0 or cantidad > MAX_DROGA_POR_COMPRA:
            return await ctx.send(embed=embed_error(f"Cantidad entre 1 y {MAX_DROGA_POR_COMPRA}."))
        precio_unitario = await db.get_precio_droga(tipo_norm, True)
        costo = precio_unitario * cantidad
        eco = await db.get_economy(uid)
        if eco['cash'] < costo:
            return await ctx.send(embed=embed_error(f"Necesitas **${costo:,}**. Tienes: **${eco['cash']:,}**"))
        await db.add_cash(uid, -costo)
        await db.add_item(uid, "personal", tipo_norm, cantidad)
        embed = discord.Embed(title="✅ Compra realizada", description=f"{cantidad}x {tipo_norm} por **${costo:,}**", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("COMPRA_DROGA", f"{ctx.author.name}: {cantidad}x {tipo_norm} -> -${costo:,}")
        try:
            await ctx.message.delete()
        except:
            pass

    @droga.command(name='vender')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_mafia_admin()
    async def drg_sell(self, ctx, tipo: str, cantidad: int = 1):
        uid = ctx.author.id
        tipo_norm = tipo.capitalize()
        if tipo_norm not in EMOJIS_DROGA:
            return await ctx.send(embed=embed_error(f"Tipos válidos: {', '.join(EMOJIS_DROGA.keys())}"))

        inv = await db.get_inventory(uid, "personal")
        if inv.get(tipo_norm, 0) < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes {cantidad}x {tipo_norm}."))

        contador = self.ventas_sin_fallo.get(uid, 0)
        forzar_fallo = (contador >= 5 and random.randint(0, 1) == 0) or contador >= 6

        if forzar_fallo:
            unidades_vendidas = 0
        else:
            unidades_vendidas = random.randint(0, 7)
            if unidades_vendidas == 0 and contador < 3:
                unidades_vendidas = random.randint(1, 7)

        if unidades_vendidas > inv[tipo_norm]:
            unidades_vendidas = inv[tipo_norm]

        if unidades_vendidas == 0:
            self.ventas_sin_fallo[uid] = 0
        else:
            self.ventas_sin_fallo[uid] = contador + 1

        if unidades_vendidas > 0:
            await db.remove_item(uid, "personal", tipo_norm, unidades_vendidas)
            await db.add_drug_grams(uid, tipo_norm, unidades_vendidas)
            await db.actualizar_precio_droga(tipo_norm, unidades_vendidas)
            embed = discord.Embed(
                title="✅ Venta realizada",
                description=f"***Has vendido {unidades_vendidas} unidades de {tipo_norm}. Has acumulado {unidades_vendidas} gramos en tu inventario ilegal.***",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
            await self.log("VENTA_DROGA_GRAMOS", f"{ctx.author.name}: {unidades_vendidas}x {tipo_norm} -> +{unidades_vendidas}g")
        else:
            rol_lspd = ctx.guild.get_role(ROL_LSPD_ID)
            if rol_lspd:
                await ctx.send(rol_lspd.mention)
            embed = discord.Embed(
                title="🚨 REPORTE CIUDADANO",
                description="***🚨 POSIBLE ACTIVIDAD ILEGAL REPORTADA POR VARIOS CIUDADANOS EN LA ZONA.***",
                color=0xFF0000,
                timestamp=datetime.now()
            )
            embed.add_field(name="📍 Ubicación", value="***Zona de venta de drogas***", inline=False)
            embed.set_footer(text="NOVA AGORA · Sistema de Vigilancia Ciudadana")
            await ctx.send(embed=embed)
            await self.log("VENTA_DROGA_FALLIDA", f"{ctx.author.name} intentó vender {tipo_norm} y activó alerta policial")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Vehiculos ====================
class Vehiculos(BaseCog):
    @commands.group(name='vehiculo', aliases=['coche', 'car'], invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def vehiculo(self, ctx):
        uid = ctx.author.id
        vehiculos = await db.get_vehiculos(uid)
        if not vehiculos:
            return await ctx.send(embed=embed_info(f"{await get_emoji('vehicle')} Vehículos", "No tienes vehículos."))
        embed = discord.Embed(title=f"{await get_emoji('vehicle')} MIS VEHÍCULOS", color=discord.Color.blue())
        for mat, info in vehiculos.items():
            seguro = "✅" if info['seguro'] else "❌"
            itv = "✅" if info['itv'] and datetime.fromisoformat(info['itv']) > datetime.now() else "❌"
            embed.add_field(
                name=f"🚗 {info['modelo']} — `{mat}`",
                value=f"Seguro: {seguro} | ITV: {itv}\n⛽ Combustible: {info['combustible']}%",
                inline=False
            )
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @vehiculo.command(name='conducir')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def veh_conducir(self, ctx, matricula: str):
        uid = ctx.author.id
        vehiculos = await db.get_vehiculos(uid)
        if matricula not in vehiculos:
            return await ctx.send(embed=embed_error("No tienes ese vehículo."))
        info = vehiculos[matricula]
        if info['itv'] and datetime.fromisoformat(info['itv']) < datetime.now():
            return await ctx.send(embed=embed_error("ITV caducada."))
        if info['combustible'] <= 0:
            return await ctx.send(embed=embed_error("Sin combustible."))
        gasto = random.randint(10, 20)
        nuevo_comb = max(0, info['combustible'] - gasto)
        await db.update_vehiculo(uid, matricula, combustible=nuevo_comb)
        embed = discord.Embed(
            title="🚗 CONDUCIENDO",
            description=f"Vehículo: {info['modelo']} — {matricula}\nCombustible restante: {nuevo_comb}%",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("VEHICULO_CONDUCIR", f"{ctx.author.name}: {info['modelo']} ({matricula}), gas: {nuevo_comb}%")
        try:
            await ctx.message.delete()
        except:
            pass

    @vehiculo.command(name='repostar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def veh_repostar(self, ctx, matricula: str, cantidad: int = 100):
        uid = ctx.author.id
        vehiculos = await db.get_vehiculos(uid)
        if matricula not in vehiculos:
            return await ctx.send(embed=embed_error("No tienes ese vehículo."))
        info = vehiculos[matricula]
        max_comb = 100
        actual = info['combustible']
        necesarios = min(cantidad, max_comb - actual)
        if necesarios <= 0:
            return await ctx.send(embed=embed_error("Depósito lleno."))
        costo = necesarios * 2
        eco = await db.get_economy(uid)
        if eco['cash'] < costo:
            return await ctx.send(embed=embed_error(f"Necesitas **${costo:,}**."))
        await db.add_cash(uid, -costo)
        nuevo_comb = actual + necesarios
        await db.update_vehiculo(uid, matricula, combustible=nuevo_comb)
        embed = discord.Embed(
            title="⛽ REPOSTAJE",
            description=f"Vehículo: {info['modelo']} — {matricula}\nCombustible: {nuevo_comb}%\nCosto: **${costo:,}**",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("VEHICULO_REPOSTAR", f"{ctx.author.name}: {info['modelo']}, +{necesarios}%, ${costo}")
        try:
            await ctx.message.delete()
        except:
            pass

    @vehiculo.command(name='itv')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def veh_itv(self, ctx, matricula: str):
        uid = ctx.author.id
        vehiculos = await db.get_vehiculos(uid)
        if matricula not in vehiculos:
            return await ctx.send(embed=embed_error("No tienes ese vehículo."))
        costo = 500
        eco = await db.get_economy(uid)
        if eco['cash'] < costo:
            return await ctx.send(embed=embed_error(f"La ITV cuesta **${costo:,}**."))
        await db.add_cash(uid, -costo)
        nueva_itv = (datetime.now() + timedelta(days=30)).isoformat()
        await db.update_vehiculo(uid, matricula, itv=nueva_itv)
        embed = discord.Embed(
            title="✅ ITV APROBADA",
            description=f"Vehículo: {vehiculos[matricula]['modelo']} — {matricula}\nVálida hasta: {nueva_itv[:10]}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("VEHICULO_ITV", f"{ctx.author.name}: {matricula}")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Armas ====================
class Armas(BaseCog):
    @commands.group(name='arma', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def arma(self, ctx):
        uid = ctx.author.id
        licencias = await db.get_licencias(uid)
        armas = await db.get_armas_equipadas(uid)
        embed = discord.Embed(title=f"{await get_emoji('weapon')} SISTEMA DE ARMAS", color=discord.Color.dark_red())
        txt_lic = "\n".join([f"{'✅' if v else '❌'} {l.replace('_', ' ').title()}" for l, v in licencias.items()]) if licencias else "Ninguna"
        embed.add_field(name="📋 Licencias:", value=txt_lic, inline=False)
        txt_armas = "\n".join([f"🔫 {a} — Dur: {info['durabilidad']}% | Munición: {info['municion']}" for a, info in armas.items()]) if armas else "Ninguna"
        embed.add_field(name="🔫 Armas equipadas:", value=txt_armas, inline=False)
        embed.add_field(name="Comandos:", value="`-arma equipar <tipo>`\n`-arma disparar`\n`-arma recargar <tipo> <cantidad>`", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @arma.command(name='equipar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def arma_equipar(self, ctx, tipo_arma: str):
        tipo = tipo_arma.capitalize()
        inv = await db.get_inventory(ctx.author.id, "personal")
        if tipo not in inv:
            return await ctx.send(embed=embed_error(f"No tienes {tipo} en tu inventario."))
        licencias = await db.get_licencias(ctx.author.id)
        licencia_necesaria = None
        if tipo in ["Hacha", "Machete", "Puño americano"]:
            licencia_necesaria = "licencia_blanca"
        elif tipo in ["SNS", "Normal", "Vintage", "Calibre .50", "Pesada", "Revólver Pesado", "Perforante", "9mm"]:
            licencia_necesaria = "licencia_corta"
        elif tipo in ["Mini SMG", "Micro Uzi", "Subfusil", "Subfusil de asalto", "ADP"]:
            licencia_necesaria = "licencia_corta"
        elif tipo in ["Mosquete", "Escopeta recortada", "MiniAk47", "Escopeta corredera", "Ak47", "Rifle bullpup"]:
            licencia_necesaria = "licencia_rifle"
        else:
            for arma_tipo, datos in TIPOS_ARMAS.items():
                if arma_tipo.lower() == tipo.lower():
                    licencia_necesaria = datos.get("licencia")
                    break
        if licencia_necesaria and not licencias.get(licencia_necesaria, False):
            return await ctx.send(embed=embed_error("No tienes la licencia necesaria para equipar esta arma."))
        durabilidad = 100
        municion = 0
        await db.execute("INSERT OR REPLACE INTO armas_equipadas (user_id, arma, durabilidad, municion) VALUES (?, ?, ?, ?)",
                         (ctx.author.id, tipo, durabilidad, municion))
        embed = discord.Embed(title="🔫 ARMA EQUIPADA", description=f"**{tipo}** equipada.", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("ARMA_EQUIPAR", f"{ctx.author.name}: {tipo}")
        try:
            await ctx.message.delete()
        except:
            pass

    @arma.command(name='disparar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def arma_disparar(self, ctx):
        uid = ctx.author.id
        row = await db.fetchone("SELECT arma, durabilidad, municion FROM armas_equipadas WHERE user_id = ?", (uid,))
        if not row:
            return await ctx.send(embed=embed_error("No tienes armas equipadas."))
        arma, durabilidad, municion = row
        if municion <= 0:
            return await ctx.send(embed=embed_error("Sin munición."))
        if durabilidad <= 0:
            return await ctx.send(embed=embed_error("Arma rota."))
        nueva_municion = municion - 1
        nueva_durabilidad = max(0, durabilidad - random.randint(1, 3))
        await db.execute("UPDATE armas_equipadas SET municion = ?, durabilidad = ? WHERE user_id = ? AND arma = ?",
                         (nueva_municion, nueva_durabilidad, uid, arma))
        embed = discord.Embed(title="💥 ¡DISPARO!", description=f"**{ctx.author.display_name}** dispara con **{arma}**\nMunición restante: {nueva_municion}\nDurabilidad: {nueva_durabilidad}%", color=0xFFA500)
        await ctx.send(embed=embed)
        await self.log("ARMA_DISPARAR", f"{ctx.author.name}: {arma}")
        try:
            await ctx.message.delete()
        except:
            pass

    @arma.command(name='recargar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def arma_recargar(self, ctx, tipo_arma: str, cantidad: int):
        tipo = tipo_arma.capitalize()
        row = await db.fetchone("SELECT arma FROM armas_equipadas WHERE user_id = ? AND arma = ?", (ctx.author.id, tipo))
        if not row:
            return await ctx.send(embed=embed_error("Esa arma no está equipada."))
        precio_por_bala = 10
        costo = precio_por_bala * cantidad
        eco = await db.get_economy(ctx.author.id)
        if eco['cash'] < costo:
            return await ctx.send(embed=embed_error(f"Necesitas **${costo:,}**."))
        await db.add_cash(ctx.author.id, -costo)
        await db.execute("UPDATE armas_equipadas SET municion = municion + ? WHERE user_id = ? AND arma = ?",
                         (cantidad, ctx.author.id, tipo))
        embed = discord.Embed(title="🔫 ARMA RECARGADA", description=f"{tipo} recargada con {cantidad} balas.\nCosto: **${costo:,}**", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("ARMA_RECARGAR", f"{ctx.author.name}: {tipo}, +{cantidad} balas")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Mercado ====================
class Mercado(BaseCog):
    @commands.group(name='mercado', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def mercado(self, ctx):
        publicaciones = await db.get_mercado()
        if not publicaciones:
            return await ctx.send(embed=embed_info("🏪 Mercado", "No hay publicaciones."))
        embed = discord.Embed(title="🏪 MERCADO — Publicaciones", color=0xFFD700)
        for pub in publicaciones[:10]:
            vendedor = ctx.guild.get_member(pub['vendedor'])
            vendedor_nombre = vendedor.display_name if vendedor else f"Usuario {pub['vendedor']}"
            precio_str = formatear_precio(pub['precio'])
            embed.add_field(
                name=f"📦 ID: `{pub['id']}` — {pub['item']}",
                value=f"📝 {pub['descripcion'][:50]}...\n💵 **{precio_str}** | 👤 {vendedor_nombre}\n_Publicado: {pub['fecha'][:10]}_",
                inline=False
            )
        embed.set_footer(text="Usa -mercado comprar <id> para comprar")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @mercado.command(name='publicar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def mercado_publicar(self, ctx, item: str, precio, *, descripcion: str):
        uid = ctx.author.id
        inv = await db.get_inventory(uid, "personal")
        item_real = next((k for k in inv if k.lower() == item.lower()), None)
        if not item_real:
            return await ctx.send(embed=embed_error("No tienes ese item."))
        if isinstance(precio, str) and precio.upper() == "INFINITY":
            precio_int = PRECIO_INFINITO
        else:
            try:
                precio_int = int(precio)
                if precio_int <= 0:
                    raise ValueError
            except ValueError:
                return await ctx.send(embed=embed_error("Precio debe ser número positivo o INFINITY."))
        pub_id = ''.join(random.choices('0123456789ABCDEF', k=6))
        await db.remove_item(uid, "personal", item_real, 1)
        await db.add_mercado(pub_id, uid, item_real, descripcion, precio_int)
        embed = discord.Embed(
            title="✅ Publicación creada",
            description=f"Item: {item_real}\nPrecio: {formatear_precio(precio_int)}\nID: {pub_id}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("MERCADO_PUBLICAR", f"{ctx.author.name}: {item_real} por {precio_int}")
        try:
            await ctx.message.delete()
        except:
            pass

    @mercado.command(name='comprar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def mercado_comprar(self, ctx, pub_id: str):
        pub = await db.get_mercado_by_id(pub_id)
        if not pub:
            return await ctx.send(embed=embed_error("Publicación no encontrada."))
        vendedor, item, precio = pub
        if vendedor == ctx.author.id:
            return await ctx.send(embed=embed_error("No puedes comprar tu propia publicación."))
        if es_precio_infinito(precio):
            return await ctx.send(embed=embed_error("No puedes comprar un artículo de valor infinito."))
        eco = await db.get_economy(ctx.author.id)
        if eco['cash'] < precio:
            return await ctx.send(embed=embed_error(f"Necesitas **${precio:,}**."))
        await db.add_cash(ctx.author.id, -precio)
        await db.add_cash(vendedor, precio)
        await db.add_item(ctx.author.id, "personal", item)
        await db.remove_mercado(pub_id)
        embed = discord.Embed(title="✅ Compra realizada", description=f"Has comprado {item} por **${precio:,}**", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("MERCADO_COMPRA", f"{ctx.author.name} compró {item} a {vendedor} por ${precio:,}")
        try:
            await ctx.message.delete()
        except:
            pass

    @mercado.command(name='mispub')
    @check_ban()
    @tiene_rol_usuario()
    async def mercado_mis_pub(self, ctx):
        rows = await db.fetchall("SELECT id, item, precio, descripcion FROM mercado WHERE vendedor = ?", (ctx.author.id,))
        if not rows:
            return await ctx.send(embed=embed_info("🏪 Mis publicaciones", "No tienes publicaciones."))
        embed = discord.Embed(title="🏪 MIS PUBLICACIONES", color=0x3498DB)
        for r in rows:
            precio_str = formatear_precio(r[2])
            embed.add_field(name=f"📦 ID: `{r[0]}` — {r[1]}", value=f"💵 **{precio_str}**\n📝 {r[3][:30]}...", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @mercado.command(name='cancelar')
    @check_ban()
    @tiene_rol_usuario()
    async def mercado_cancelar(self, ctx, pub_id: str):
        pub = await db.get_mercado_by_id(pub_id)
        if not pub:
            return await ctx.send(embed=embed_error("Publicación no encontrada."))
        if pub[0] != ctx.author.id:
            return await ctx.send(embed=embed_error("No es tu publicación."))
        await db.add_item(ctx.author.id, "personal", pub[1])
        await db.remove_mercado(pub_id)
        embed = discord.Embed(title="✅ Publicación cancelada", description=f"Recuperaste {pub[1]}.", color=0x00FF00)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Casino ====================
class Casino(BaseCog):
    async def _validar_apuesta(self, uid, apuesta) -> Optional[str]:
        if apuesta <= 0:
            return "La apuesta debe ser mayor a 0."
        if apuesta < APUESTA_MIN:
            return f"Apuesta mínima: **${APUESTA_MIN:,}**"
        if apuesta > APUESTA_MAX:
            return f"Apuesta máxima: **${APUESTA_MAX:,}**"
        eco = await db.get_economy(uid)
        if eco['cash'] < apuesta:
            return f"Saldo insuficiente. Tienes: **${eco['cash']:,}**"
        return None

    async def _animacion_casino(self, ctx, frames, delay=0.55):
        msg = await ctx.send(f"```\n{frames[0]}\n```")
        for frame in frames[1:]:
            await asyncio.sleep(delay)
            await msg.edit(content=f"```\n{frame}\n```")
        return msg

    @commands.group(name='casino', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def casino(self, ctx):
        embed = discord.Embed(
            title=f"{await get_emoji('casino')} Golden Coast · Legendary Casino's",
            description=(
                f"**Apuestas:** **${APUESTA_MIN:,}** — **${APUESTA_MAX:,}**\n\n"
                "`-casino slots <apuesta>` — Tragaperras\n"
                "`-casino ruleta <apuesta> <tipo>` — Ruleta\n"
                "`-casino dados <apuesta>` — Dados\n"
                "`-bj <apuesta>` — Blackjack\n"
                "`-casino racha` — Ver racha\n"
                "`-casino ruleta-info` — Tipos de apuesta"
            ),
            color=discord.Color.gold()
        )
        eco = await db.get_economy(ctx.author.id)
        embed.set_footer(text=f"💰 Saldo: **${eco['cash']:,}**  ·  NOVA AGORA")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @casino.command(name='ruleta-info')
    @tiene_rol_usuario()
    async def ruleta_info(self, ctx):
        embed = discord.Embed(
            title="🎡 Ruleta — Tipos de apuesta",
            description=(
                "**rojo · negro · verde** (×2)\n"
                "**par · impar** (×2)\n"
                "**0 al 36 · 00** (×34)\n"
                "**col1 · col2 · col3** (×3)\n"
                "**1-12 · 13-24 · 25-36** (×3)"
            ),
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @casino.command(name='racha')
    @tiene_rol_usuario()
    async def ver_racha(self, ctx):
        uid = ctx.author.id
        racha = await db.get_racha(uid)
        if racha['racha'] == 0:
            return await ctx.send(embed=embed_info("📊 Racha", "Sin partidas aún."))
        tipo_txt = "victorias 🏆" if racha['tipo'] == "win" else "derrotas 💀"
        color = discord.Color.green() if racha['tipo'] == "win" else discord.Color.red()
        embed = discord.Embed(
            title="📊 Tu racha",
            description=f"Racha: **{racha['racha']} {tipo_txt}**",
            color=color
        )
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @casino.command(name='slots')
    @tiene_rol_usuario()
    async def slots(self, ctx, apuesta: int):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))

        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 3.0 if racha['racha'] >= 7 else (2.5 if racha['racha'] >= 5 else 1.75)

        await db.add_cash(uid, -apuesta)

        SIMBOLOS = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣", "🃏"]
        MULTS = {"💎": 15, "7️⃣": 10, "⭐": 7, "🍇": 5, "🍊": 4, "🍋": 3, "🍒": 2, "🃏": 20}

        msg = await self._animacion_casino(ctx, [
            "🎰  GIRANDO...",
            "🎰  [ 🎲 | ??? | ??? | ??? ]",
            "🎰  [ 🍒 | 🎲  | ??? | ??? ]",
            "🎰  [ 🍒 | 🍋  | 🎲  | ??? ]",
            "🎰  Parando...",
        ])

        res = [random.choice(SIMBOLOS) for _ in range(4)]
        no_joker = [s for s in res if s != "🃏"]
        jokers = res.count("🃏")
        disp = f"[ {' | '.join(res)} ]"

        if jokers == 4:
            mult_fin = 50 * mult_racha
            ganancia = int(apuesta * mult_fin)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo, color, resultado = "¡¡MEGA JACKPOT!! 🃏×4", 0xFFD700, f"+${ganancia - apuesta:,}"
        elif len(set(no_joker)) == 1 and len(no_joker) >= 3:
            sym = no_joker[0]
            mult_fin = MULTS.get(sym, 3) * mult_racha * (1 + jokers * 0.5)
            ganancia = int(apuesta * mult_fin)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo, color, resultado = f"¡¡JACKPOT!! {sym}×{4 - jokers}" + ("🃏" * jokers if jokers else ""), 0xFFD700, f"+${ganancia - apuesta:,}"
        elif jokers >= 2:
            ganancia = int(apuesta * 3 * mult_racha)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo, color, resultado = "¡Doble comodín! 🃏🃏", 0x00FF00, f"+${ganancia - apuesta:,}"
        elif len(set(no_joker)) <= 2 and (len(no_joker) + jokers) >= 3:
            ganancia = int((apuesta // 2) * mult_racha)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo, color, resultado = "¡Par!", 0x00FF00, f"+${ganancia - apuesta:,}"
        else:
            await db.actualizar_racha(uid, False)
            titulo, color, resultado = "Sin suerte...", 0xFF0000, f"-${apuesta:,}"
        embed = discord.Embed(
            title=f"🎰 {titulo}",
            description=f"**{disp}**\n{resultado}",
            color=color
        )
        await msg.edit(content=None, embed=embed)
        await self.log("CASINO_SLOTS", f"{ctx.author.name}: ${apuesta} → {disp}")
        try:
            await ctx.message.delete()
        except:
            pass

    @casino.command(name='ruleta')
    @tiene_rol_usuario()
    async def ruleta(self, ctx, apuesta: int, *, tipo: str):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))

        tipo_norm = tipo.lower().strip()
        tipos_validos = ['rojo', 'negro', 'verde', 'par', 'impar', '00', 'col1', 'col2', 'col3', '1-12', '13-24', '25-36'] + [str(i) for i in range(37)]
        if tipo_norm not in tipos_validos:
            return await ctx.send(embed=embed_error("Tipo no válido. Usa `-casino ruleta-info`"))

        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 3.0 if racha['racha'] >= 7 else (2.5 if racha['racha'] >= 5 else 1.75)

        msg = await self._animacion_casino(ctx, [
            "🎡  LA RULETA GIRA...",
            "🎡  ●○○○○○○○○○○○○○○○○○○○○○",
            "🎡  ○○○○○●○○○○○○○○○○○○○○○○",
            "🎡  ○○○○○○○○○○●○○○○○○○○○○○",
            "🎡  ○○○○○○○○○○○○○○○●○○○○○○",
            "🎡  ○○○○○○○○○○○○○○○○○○○●○○",
            "🎡  Cayendo...",
        ], delay=0.35)

        numero = random.randint(0, 37)
        ROJOS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
        color_real = "verde" if numero in (0, 37) else ("rojo" if numero in ROJOS else "negro")

        gano, multiplicador = False, 0

        if tipo_norm in ('rojo', 'negro', 'verde'):
            if tipo_norm == color_real:
                gano, multiplicador = True, 14 if tipo_norm == 'verde' else 2
        elif tipo_norm in ('par', 'impar'):
            if numero not in (0, 37):
                if (tipo_norm == 'par' and numero % 2 == 0) or (tipo_norm == 'impar' and numero % 2 == 1):
                    gano, multiplicador = True, 2
        elif tipo_norm == '00':
            if numero == 37:
                gano, multiplicador = True, 34
        elif tipo_norm.isdigit():
            if int(tipo_norm) == numero:
                gano, multiplicador = True, 34
        elif tipo_norm in ('col1', 'col2', 'col3'):
            COL = {
                'col1': {1,4,7,10,13,16,19,22,25,28,31,34},
                'col2': {2,5,8,11,14,17,20,23,26,29,32,35},
                'col3': {3,6,9,12,15,18,21,24,27,30,33,36}
            }
            if numero in COL[tipo_norm]:
                gano, multiplicador = True, 3
        elif tipo_norm in ('1-12', '13-24', '25-36'):
            RANGOS = {'1-12': (1,12), '13-24': (13,24), '25-36': (25,36)}
            lo, hi = RANGOS[tipo_norm]
            if lo <= numero <= hi:
                gano, multiplicador = True, 3

        await db.add_cash(uid, -apuesta)

        if gano:
            ganancia = int(apuesta * multiplicador * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado, color = f"+${ganancia:,}", 0x00FF00
        else:
            await db.actualizar_racha(uid, False)
            resultado, color = f"-${apuesta:,}", 0xFF0000

        num_display = "00" if numero == 37 else str(numero)
        embed = discord.Embed(
            title="🎡 Ruleta",
            description=f"Número: **{num_display}** ({color_real})\nResultado: {resultado}",
            color=color
        )
        await msg.edit(content=None, embed=embed)
        await self.log("CASINO_RULETA", f"{ctx.author.name}: ${apuesta} → {num_display} {'WIN' if gano else 'LOSS'}")
        try:
            await ctx.message.delete()
        except:
            pass

    @casino.command(name='dados')
    @tiene_rol_usuario()
    async def dados(self, ctx, apuesta: int):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))

        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 3.0 if racha['racha'] >= 7 else (2.5 if racha['racha'] >= 5 else 1.75)

        msg = await self._animacion_casino(ctx, [
            "🎲  LANZANDO DADOS...",
            "🎲  [ ? | ? ]",
            "🎲  Parando...",
        ])

        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        total = d1 + d2
        await db.add_cash(uid, -apuesta)

        if d1 == d2:
            ganancia = int(apuesta * 3 * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado, color, titulo = f"+${ganancia:,}", 0x00FF00, f"¡DOBLES! {d1}+{d2}={total}"
        elif total >= 10:
            ganancia = int(apuesta * 2 * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado, color, titulo = f"+${ganancia:,}", 0x00FF00, f"¡Número alto! {d1}+{d2}={total}"
        else:
            await db.actualizar_racha(uid, False)
            resultado, color, titulo = f"-${apuesta:,}", 0xFF0000, f"Sin suerte... {d1}+{d2}={total}"
        embed = discord.Embed(
            title=f"🎲 {titulo}",
            description=f"Dados: {d1} + {d2} = {total}\nResultado: {resultado}",
            color=color
        )
        await msg.edit(content=None, embed=embed)
        await self.log("CASINO_DADOS", f"{ctx.author.name}: ${apuesta} → {d1}+{d2}={total}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='bj')
    @tiene_rol_usuario()
    async def blackjack(self, ctx, apuesta: int):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))

        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 3.0 if racha['racha'] >= 7 else (2.5 if racha['racha'] >= 5 else 1.75)

        cartas = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
        random.shuffle(cartas)
        j1, j2 = cartas.pop(), cartas.pop()
        c1, c2 = cartas.pop(), cartas.pop()
        jugador = j1 + j2
        casa = c1 + c2
        await db.add_cash(uid, -apuesta)

        if jugador == 21:
            ganancia = int(apuesta * 2.5 * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado, color = f"🃏 **¡BLACKJACK!** +${ganancia:,}", 0xFFD700
        elif casa == 21:
            await db.actualizar_racha(uid, False)
            resultado, color = f"❌ **La casa tiene Blackjack.** -${apuesta:,}", 0xFF0000
        elif jugador > 21:
            await db.actualizar_racha(uid, False)
            resultado, color = f"❌ **¡Te pasaste!** -${apuesta:,}", 0xFF0000
        elif jugador > casa or casa > 21:
            ganancia = int(apuesta * 2 * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado, color = f"✅ **¡Ganaste!** +${ganancia:,}", 0x00FF00
        elif jugador == casa:
            await db.add_cash(uid, apuesta)
            resultado, color = "🤝 **¡Empate!** Recuperas tu apuesta", 0x3498DB
        else:
            await db.actualizar_racha(uid, False)
            resultado, color = f"❌ **La casa gana.** -${apuesta:,}", 0xFF0000
        embed = discord.Embed(
            title="🃏 Blackjack",
            description=f"Tu mano: {jugador}\nCasa: {casa}\n{resultado}",
            color=color
        )
        await ctx.send(embed=embed)
        await self.log("CASINO_BJ", f"{ctx.author.name}: ${apuesta} → J:{jugador} C:{casa}")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Atracos ====================
class Atracos(BaseCog):
    @commands.group(name='rob', aliases=['atraco'], invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def rob(self, ctx):
        embed = discord.Embed(title=f"{await get_emoji('rob')} SISTEMA PROFESIONAL DE ATRACOS", description="**Comandos disponibles:**", color=0xFF0000)
        for heist_name, info in HEIST_DEFINITIONS.items():
            nivel = f"Lv.{info['min_level']}+"
            segundos = info['cooldown']
            if segundos >= 86400:
                cd = f"{segundos // 86400}d"
            elif segundos >= 3600:
                cd = f"{segundos // 3600}h"
            else:
                cd = f"{segundos // 60}m"
            embed.add_field(
                name=f"`-rob {heist_name}` — {info['nombre']}",
                value=f"{info['description']}\n💰 ${info['reward'][0]:,}–${info['reward'][1]:,} | ⏱️ {cd} | {nivel} | 📋 {len(info['preparations'])} preparatorias",
                inline=False
            )
        embed.set_footer(text="Usa -rob <nombre> para iniciar | Requiere items en inventario y preparatorias completadas")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @rob.command(name='status')
    @tiene_rol_usuario()
    async def rob_status(self, ctx):
        uid = ctx.author.id
        nivel = await db.get_nivel(uid)
        eco = await db.get_economy(uid)
        embed = discord.Embed(title="📊 Tu Estatus de Atracos", color=0x00FF00)
        embed.add_field(name="Nivel", value=f"{nivel['nivel']}", inline=True)
        embed.add_field(name="Dinero Negro", value=f"${eco['black_money']:,}", inline=True)
        embed.add_field(name="Dinero Total", value=f"${eco['cash'] + eco['bank']:,}", inline=True)
        atracos = await db.fetchone("SELECT COUNT(*) FROM atracos_logs WHERE user_id = ?", (uid,))
        embed.add_field(name="Atracos Realizados", value=f"{atracos[0] if atracos else 0}", inline=True)
        prep_data = await db.get_all_heist_preparations(uid)
        if prep_data:
            prep_text = ""
            for heist_id, preps in prep_data.items():
                total = len(HEIST_DEFINITIONS[heist_id]["preparations"])
                completadas = len([p for p in preps.values() if p])
                prep_text += f"**{HEIST_DEFINITIONS[heist_id]['nombre']}:** {completadas}/{total}\n"
            embed.add_field(name="📋 Progreso de Preparatorias", value=prep_text or "Ninguna", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    async def _mostrar_info_atraco(self, ctx, heist_name: str) -> bool:
        heist = HEIST_DEFINITIONS[heist_name]
        if ctx.author.id not in OWNER_IDS:
            ok, rest = await db.check_cooldown(ctx.author.id, f"rob_{heist_name}", heist['cooldown'])
            if not ok:
                d, h, m, s = rest // 86400, (rest % 86400) // 3600, (rest % 3600) // 60, rest % 60
                tiempo = (f"{d}d " if d > 0 else "") + (f"{h}h " if h > 0 or d > 0 else "") + f"{m}m {s}s"
                await ctx.send(embed=embed_error(f"Espera **{tiempo}** para repetir este atraco."))
                return False
            inv = await db.get_inventory(ctx.author.id, 'personal')
            for item in heist.get('items', []):
                if item not in inv or inv[item] <= 0:
                    await ctx.send(embed=embed_error(f"Necesitas: **{item}**\nCompra en `-tienda` o `-tienda-ilegal`"))
                    return False
            if not await self._verificar_preparatorias(ctx, heist_name):
                return False

        embed = discord.Embed(
            title=f"🏴‍☠️ {heist['nombre']} — Información del Atraco",
            color=0xFFA500
        )
        embed.set_thumbnail(url=heist.get('image', 'https://i.imgur.com/8Km9tLL.png'))
        embed.add_field(name="📍 Objetivo", value=heist['nombre'], inline=True)
        embed.add_field(name="⚠️ Nivel de Riesgo", value=f"🔴 {'Alto' if heist['min_level'] >= 50 else 'Medio' if heist['min_level'] >= 20 else 'Bajo'}", inline=True)
        embed.add_field(name="💰 Recompensa Estimada", value=f"${heist['reward'][0]:,} - ${heist['reward'][1]:,}", inline=True)
        embed.add_field(name="⏱️ Tiempo Estimado", value=f"{heist['cooldown'] // 60} minutos", inline=True)
        embed.add_field(name="🚔 Participación Policial", value=heist['police'], inline=True)
        embed.add_field(name="📝 Descripción", value=heist['description'], inline=False)
        if heist.get('items'):
            embed.add_field(name="🔧 Items Necesarios", value=", ".join(heist['items']), inline=False)
        embed.add_field(name="📋 Preparatorias requeridas", value=f"{len(heist['preparations'])}/{len(heist['preparations'])} completadas" if await self._verificar_preparatorias(ctx, heist_name) else f"{await self._contar_preparatorias_completadas(ctx.author.id, heist_name)}/{len(heist['preparations'])} completadas", inline=False)
        embed.set_footer(text="Responde con ✅ para comenzar el atraco o ❌ para cancelar.")
        view = ConfirmView(ctx.author.id, timeout=30)
        await ctx.send(embed=embed, view=view)
        await view.wait()
        return view.value is True

    async def _verificar_preparatorias(self, ctx, heist_name: str) -> bool:
        if ctx.author.id in OWNER_IDS or (ctx.guild.get_role(ROL_MAFIA_ID) in ctx.author.roles):
            return True
        total_preps = len(HEIST_DEFINITIONS[heist_name]["preparations"])
        if total_preps == 0:
            return True
        completadas = await db.are_all_preparations_completed(ctx.author.id, heist_name, total_preps)
        if not completadas:
            await ctx.send(embed=embed_error(f"❌ Debes completar todas las preparatorias de **{HEIST_DEFINITIONS[heist_name]['nombre']}** antes de realizar el atraco.\nUsa `-preparacion {heist_name} <número>` para avanzar."))
            return False
        return True

    async def _contar_preparatorias_completadas(self, user_id: int, heist_name: str) -> int:
        preps = await db.get_heist_preparations(user_id, heist_name)
        return len([p for p in preps.values() if p])

    async def validate_heist(self, ctx, heist_name: str) -> tuple:
        if ctx.author.id in OWNER_IDS:
            heist = HEIST_DEFINITIONS[heist_name]
            return heist, ctx.author.id

        if heist_name not in HEIST_DEFINITIONS:
            await ctx.send(embed=embed_error("Atraco desconocido."))
            return None, None
        heist = HEIST_DEFINITIONS[heist_name]
        uid = ctx.author.id

        if not (ctx.author.id in OWNER_IDS or (ctx.guild.get_role(ROL_MAFIA_ID) in ctx.author.roles)):
            if not await db.are_all_preparations_completed(uid, heist_name, len(heist["preparations"])):
                await ctx.send(embed=embed_error(f"❌ Debes completar todas las preparatorias de **{heist['nombre']}** antes de realizar el atraco."))
                return None, None

        ok, rest = await db.check_cooldown(uid, f"rob_{heist_name}", heist['cooldown'])
        if not ok:
            d, h, m, s = rest // 86400, (rest % 86400) // 3600, (rest % 3600) // 60, rest % 60
            tiempo = (f"{d}d " if d > 0 else "") + (f"{h}h " if h > 0 or d > 0 else "") + f"{m}m {s}s"
            await ctx.send(embed=embed_error(f"Espera **{tiempo}** para repetir este atraco."))
            return None, None
        if heist.get('items'):
            inv = await db.get_inventory(uid, 'personal')
            for item in heist['items']:
                if item not in inv or inv[item] <= 0:
                    await ctx.send(embed=embed_error(f"Necesitas: **{item}**\nCompra en `-tienda` o `-tienda-ilegal`"))
                    return None, None
        return heist, uid

    async def execute_heist(self, ctx, heist_name: str):
        if not await self._mostrar_info_atraco(ctx, heist_name):
            return

        heist, uid = await self.validate_heist(ctx, heist_name)
        if not heist:
            return
        msg = await ctx.send(embed=discord.Embed(title=f"🎭 {heist['nombre']}", description="⏳ **En progreso...**\nObtendré más información en breve.", color=0xFFA500))
        await asyncio.sleep(random.randint(2, 4))
        exito = random.random() < 0.80
        if exito:
            dinero = random.randint(heist['reward'][0], heist['reward'][1])
            items_bonus = []
            if random.random() < 0.15:
                droga = random.choice(list(PRECIOS_DROGAS_BASE.keys()))
                gramos = random.randint(3, 12)
                await db.add_item(uid, 'personal', droga, gramos)
                items_bonus.append(f"{gramos}g {droga}")
            await db.add_black(uid, dinero)
            xp_ganado = random.randint(50, 150)
            await db.add_xp(uid, xp_ganado, "heist")
            await db.inc_estadistica('robos_totales')
            await db.add_heist_log(uid, heist_name, "success", dinero, dinero, json.dumps(items_bonus))
            await db.reset_heist_preparations(uid, heist_name)
            descripcion = f"✅ **¡ATRACO EXITOSO!**\n\n💶 **+${dinero:,}** en dinero negro"
            if items_bonus:
                descripcion += f"\n📦 **Botín adicional:** {', '.join(items_bonus)}"
            descripcion += f"\n⭐ +{xp_ganado} XP"
            embed = discord.Embed(title=f"🏆 {heist['nombre']} — EXITOSO", description=descripcion, color=0x00FF00)
            await msg.edit(embed=embed)
            await self.log("ROB_SUCCESS", f"{ctx.author.name} completó {heist_name}: +${dinero}")
        else:
            embed = discord.Embed(title=f"❌ {heist['nombre']} — FALLIDO", description="La seguridad detectó movimiento sospechoso. **Operación abortada.**", color=0xFF0000)
            await msg.edit(embed=embed)
            await self.log("ROB_FAIL", f"{ctx.author.name} falló {heist_name}")
        if ctx.author.id not in OWNER_IDS:
            for item in heist.get('items', []):
                await db.remove_item(uid, 'personal', item, 1)
        try:
            await ctx.message.delete()
        except:
            pass

    @rob.command(name='badu')
    async def rob_badu(self, ctx): await self.execute_heist(ctx, 'badu')
    @rob.command(name='yellowjack')
    async def rob_yellowjack(self, ctx): await self.execute_heist(ctx, 'yellowjack')
    @rob.command(name='ammu')
    async def rob_ammu(self, ctx): await self.execute_heist(ctx, 'ammu')
    @rob.command(name='vanilla')
    async def rob_vanilla(self, ctx): await self.execute_heist(ctx, 'vanilla')
    @rob.command(name='yate')
    async def rob_yate(self, ctx): await self.execute_heist(ctx, 'yate')
    @rob.command(name='centro')
    async def rob_centro(self, ctx): await self.execute_heist(ctx, 'centro')
    @rob.command(name='joyeria')
    async def rob_joyeria(self, ctx): await self.execute_heist(ctx, 'joyeria')
    @rob.command(name='pacific')
    async def rob_pacific(self, ctx): await self.execute_heist(ctx, 'pacific')
    @rob.command(name='paleto')
    async def rob_paleto(self, ctx): await self.execute_heist(ctx, 'paleto')
    @rob.command(name='central')
    async def rob_central(self, ctx): await self.execute_heist(ctx, 'central')

# ==================== COG: Preparatorias ====================
class Preparatorias(BaseCog):
    @commands.group(name='preparacion', aliases=['prep'], invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def preparacion(self, ctx):
        uid = ctx.author.id
        preps = await db.get_all_heist_preparations(uid)
        embed = discord.Embed(title="📋 TUS PREPARATORIAS", color=0x00A8FF)
        for heist_id, info in HEIST_DEFINITIONS.items():
            total = len(info["preparations"])
            completadas = len([p for p in preps.get(heist_id, {}).values() if p])
            embed.add_field(
                name=f"{info['nombre']} ({completadas}/{total})",
                value=f"`-preparacion {heist_id} <1-{total}>` para realizar una preparatoria",
                inline=False
            )
        embed.set_footer(text="Usa -preparacion <atraco> <número> para comenzar una preparatoria")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @preparacion.command(name='badu')
    async def prep_badu(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "badu", numero)
    @preparacion.command(name='yellowjack')
    async def prep_yellowjack(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "yellowjack", numero)
    @preparacion.command(name='ammu')
    async def prep_ammu(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "ammu", numero)
    @preparacion.command(name='vanilla')
    async def prep_vanilla(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "vanilla", numero)
    @preparacion.command(name='yate')
    async def prep_yate(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "yate", numero)
    @preparacion.command(name='centro')
    async def prep_centro(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "centro", numero)
    @preparacion.command(name='joyeria')
    async def prep_joyeria(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "joyeria", numero)
    @preparacion.command(name='paleto')
    async def prep_paleto(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "paleto", numero)
    @preparacion.command(name='central')
    async def prep_central(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "central", numero)
    @preparacion.command(name='pacific')
    async def prep_pacific(self, ctx, numero: int):
        await self._realizar_preparacion(ctx, "pacific", numero)

    async def _realizar_preparacion(self, ctx, heist_id: str, numero: int):
        uid = ctx.author.id
        heist = HEIST_DEFINITIONS.get(heist_id)
        if not heist:
            return await ctx.send(embed=embed_error("Atraco no encontrado."))
        total_preps = len(heist["preparations"])
        if numero < 1 or numero > total_preps:
            return await ctx.send(embed=embed_error(f"Número de preparatoria inválido. Debe ser entre 1 y {total_preps}."))

        if not (ctx.author.id in OWNER_IDS or (ctx.guild.get_role(ROL_MAFIA_ID) in ctx.author.roles)):
            if numero > 1:
                prev_completed = await db.is_preparation_completed(uid, heist_id, numero - 1)
                if not prev_completed:
                    return await ctx.send(embed=embed_error(f"❌ Debes completar primero la preparatoria {numero-1} de **{heist['nombre']}** para continuar."))

        if await db.is_preparation_completed(uid, heist_id, numero):
            return await ctx.send(embed=embed_error(f"Ya has completado la preparatoria {numero} de **{heist['nombre']}**."))

        rol_lspd = ctx.guild.get_role(ROL_LSPD_ID)
        if rol_lspd:
            await ctx.send(f"🚨 **ALERTA: Actividad sospechosa en {heist['nombre']}** 🚨\n{rol_lspd.mention}")

        descripcion = heist["preparations"][numero-1]
        embed_progress = discord.Embed(
            title=f"🏴 PREPARATORIA {numero} — {heist['nombre']}",
            description=f"**Objetivo:** {descripcion}\n\n⏳ **En progreso...**",
            color=0xFFA500,
            timestamp=datetime.now()
        )
        embed_progress.set_thumbnail(url=heist.get('image', 'https://i.imgur.com/8Km9tLL.png'))
        msg = await ctx.send(embed=embed_progress)

        await asyncio.sleep(random.randint(5, 10))

        await db.complete_preparation(uid, heist_id, numero)
        xp_reward = 50 + (numero * 10)
        await db.add_xp(uid, xp_reward, "heist")

        embed_complete = discord.Embed(
            title=f"✅ PREPARATORIA {numero} COMPLETADA — {heist['nombre']}",
            description=f"**Objetivo completado:** {descripcion}\n\n⭐ +{xp_reward} XP\n📋 Progreso: {numero}/{total_preps}",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        embed_complete.set_thumbnail(url=heist.get('image', 'https://i.imgur.com/8Km9tLL.png'))
        await msg.edit(embed=embed_complete)
        await self.log("PREPARATORIA", f"{ctx.author.name} completó preparatoria {numero} de {heist_id}")

        if numero == total_preps and await db.are_all_preparations_completed(uid, heist_id, total_preps):
            await ctx.send(embed=embed_success(f"🏆 {heist['nombre']} LISTO", f"Has completado todas las preparatorias. Ya puedes realizar el atraco con `-rob {heist_id}`."))

        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Banco ====================
class Banco(BaseCog):
    @commands.group(name='banco', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def banco(self, ctx):
        uid = ctx.author.id
        eco = await db.get_economy(uid)
        emoji_money = await get_emoji('money')
        emoji_bank = await get_emoji('bank')
        embed = discord.Embed(
            title=f"{emoji_bank} BANCO CENTRAL",
            description=(
                f"{emoji_money} Efectivo: **${eco['cash']:,}**\n"
                f"{emoji_bank} En banco: **${eco['bank']:,}**\n"
                f"💰 Total:    **${eco['cash'] + eco['bank']:,}**"
            ),
            color=0x3498DB
        )
        if eco['black_money'] > 0:
            embed.add_field(
                name=f"{await get_emoji('black_money')} Dinero negro",
                value=f"Tienes **${eco['black_money']:,}** pendiente de blanquear. Usa `-blanquear` (solo Mafia).",
                inline=False
            )
        embed.add_field(
            name="Comandos",
            value=(
                "`-banco ingresar <cantidad>`\n"
                "`-banco retirar <cantidad>`\n"
                "`-banco transferir @usuario <cantidad>`"
            ),
            inline=False
        )
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @banco.command(name='ingresar')
    @tiene_rol_usuario()
    async def banco_ingresar(self, ctx, cantidad: int):
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("Cantidad mayor a 0."))
        eco = await db.get_economy(ctx.author.id)
        if eco['cash'] < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes **${cantidad:,}** en efectivo."))
        await db.add_cash(ctx.author.id, -cantidad)
        await db.add_bank(ctx.author.id, cantidad)
        await ctx.send(embed=embed_success("🏦 Ingreso", f"Has ingresado **${cantidad:,}**."))
        try:
            await ctx.message.delete()
        except:
            pass

    @banco.command(name='retirar')
    @tiene_rol_usuario()
    async def banco_retirar(self, ctx, cantidad: int):
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("Cantidad mayor a 0."))
        eco = await db.get_economy(ctx.author.id)
        if eco['bank'] < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes **${cantidad:,}** en el banco."))
        await db.add_bank(ctx.author.id, -cantidad)
        await db.add_cash(ctx.author.id, cantidad)
        await ctx.send(embed=embed_success("🏦 Retiro", f"Has retirado **${cantidad:,}**."))
        try:
            await ctx.message.delete()
        except:
            pass

    @banco.command(name='transferir')
    @tiene_rol_usuario()
    async def banco_transferir(self, ctx, usuario: discord.Member, cantidad: int):
        uid, tid = ctx.author.id, usuario.id
        if uid == tid:
            return await ctx.send(embed=embed_error("No puedes transferirte a ti mismo."))
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("Cantidad mayor a 0."))
        eco = await db.get_economy(uid)
        if eco['bank'] < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes **${cantidad:,}** en el banco."))
        await db.add_bank(uid, -cantidad)
        await db.add_bank(tid, cantidad)
        await ctx.send(embed=embed_success(
            "🏦 Transferencia",
            f"Has transferido **${cantidad:,}** a {usuario.mention}."
        ))
        await self.log("BANCO_TRANSFERENCIA", f"{ctx.author.name} transfirió ${cantidad} a {usuario.name}")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Multas ====================
class Multas(BaseCog):
    @commands.group(name='multa', invoke_without_command=True)
    @check_ban()
    @tiene_rol_usuario()
    async def multa(self, ctx):
        uid = ctx.author.id
        multas = await db.get_multas_pendientes(uid)
        if not multas:
            return await ctx.send(embed=embed_info("📄 Multas", "No tienes multas pendientes."))
        embed = discord.Embed(title="📄 MIS MULTAS", color=0xFFA500)
        total = 0
        for i, m in enumerate(multas, 1):
            embed.add_field(
                name=f"#{i} — **${m['cantidad']:,}**",
                value=(
                    f"Motivo: {m['motivo']}\n"
                    f"Agente: {m['agente']}\n"
                    f"Fecha:  {m['fecha'][:10]}"
                ),
                inline=False
            )
            total += m['cantidad']
        embed.add_field(name="Total pendiente", value=f"**${total:,}**", inline=False)
        embed.set_footer(text="Usa -multa pagar <número> para pagar una multa")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @multa.command(name='pagar')
    @tiene_rol_usuario()
    async def multa_pagar(self, ctx, numero: int = None):
        uid = ctx.author.id
        multas = await db.get_multas_pendientes(uid)
        if not multas:
            return await ctx.send(embed=embed_info("📄 Multas", "No tienes multas pendientes."))
        if numero is None:
            total = sum(m['cantidad'] for m in multas)
            eco = await db.get_economy(uid)
            if eco['cash'] < total:
                return await ctx.send(embed=embed_error(f"Necesitas **${total:,}**."))
            await db.add_cash(uid, -total)
            for m in multas:
                await db.pagar_multa(m['id'])
            await ctx.send(embed=embed_success("✅ Multas pagadas", f"Has pagado **${total:,}** en multas."))
            await self.log("MULTA_PAGAR", f"{ctx.author.name} pagó todas las multas: ${total}")
        else:
            if numero < 1 or numero > len(multas):
                return await ctx.send(embed=embed_error("Número inválido."))
            m = multas[numero - 1]
            eco = await db.get_economy(uid)
            if eco['cash'] < m['cantidad']:
                return await ctx.send(embed=embed_error(f"Necesitas **${m['cantidad']:,}**."))
            await db.add_cash(uid, -m['cantidad'])
            await db.pagar_multa(m['id'])
            await ctx.send(embed=embed_success(
                "✅ Multa pagada",
                f"Has pagado **${m['cantidad']:,}** por: {m['motivo']}."
            ))
            await self.log("MULTA_PAGAR", f"{ctx.author.name} pagó multa #{numero}: ${m['cantidad']}")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: PDA ====================
class PDA(BaseCog):
    RANGOS = ["Cadete", "Agente", "Agente de Primera", "Cabo", "Sargento", "Teniente", "Capitán", "Comandante", "Jefe de Policía"]
    RANGO_EMOJIS = {
        "Cadete": "👮", "Agente": "🚔", "Agente de Primera": "🚔", "Cabo": "⭐",
        "Sargento": "⭐⭐", "Teniente": "🎖️", "Capitán": "🎖️🎖️", "Comandante": "👑",
        "Jefe de Policía": "👑🛡️"
    }

    async def cog_check(self, ctx):
        user_state = await db.get_user_state(ctx.author.id)
        has_placa = bool(user_state.get('placa'))
        has_lspd_role = any(role.id == ROL_LSPD_ID or "LSPD" in role.name.upper() for role in ctx.author.roles)
        has_owner = ctx.author.id in OWNER_IDS
        if not (has_placa or has_lspd_role or has_owner):
            await ctx.send(embed=embed_error("No tienes placa policial, rol LSPD ni permisos de owner para abrir la PDA."))
            return False
        return True

    @commands.group(name='pda', invoke_without_command=True)
    async def pda(self, ctx):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        placa = user_state['placa'] or "Sin placa"
        rango = user_state['rango'] or "Agente"
        caja = await db.get_caja_municipal()
        nombre = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        emoji = self.RANGO_EMOJIS.get(rango, "🚔")
        embed = discord.Embed(
            title=f"{await get_emoji('pda')} PANEL PDA — NOVA AGORA",
            description="💎 PDA premium, brillante y lista para operaciones policiales.",
            color=0xE91E63
        )
        embed.set_author(name="NOVA AGORA", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url="https://images.emojiterra.com/twitter/v14.0/512px/1f4f1.png")
        embed.set_footer(text="✨ NOVA AGORA")
        embed.add_field(name="👤 Agente", value=f"{nombre}", inline=True)
        embed.add_field(name="🪪 Placa", value=f"{placa}", inline=True)
        embed.add_field(name=f"{emoji} Rango", value=f"{rango}", inline=True)
        embed.add_field(name="🏦 Caja Municipal", value=f"**${caja:,}**", inline=False)
        embed.add_field(
            name="Comandos",
            value="`-pda detener @u <motivo>`\n`-pda encarcelar @u <min> <motivo>`\n`-pda multar @u <cantidad> <motivo>`\n`-pda quitar-multa @u`\n`-pda requisar @u <arma>`\n`-pda guardar @u <item>`\n`-pda evidencia @u`\n`-pda buscar <nombre>`\n`-crear-placa @u LSPD-0001`\n`-multas`\n`-esposar @u <motivo>`\n`-des-esposar @u <motivo>`",
            inline=False
        )
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='detener')
    async def pda_detener(self, ctx, usuario: discord.Member, *, motivo: str):
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        nombre_det = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        embed = discord.Embed(title="🚨 DETENCIÓN", description=f"{nombre_ag} ha detenido a {nombre_det}. Motivo: {motivo}", color=0xFF0000)
        await ctx.send(embed=embed)
        await self.log("PDA_DETENER", f"{nombre_ag} detuvo a {nombre_det}: {motivo}")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='encarcelar')
    async def pda_encarcelar(self, ctx, usuario: discord.Member, minutos: int, *, motivo: str):
        if minutos <= 0 or minutos > 10080:
            return await ctx.send(embed=embed_error("Los minutos deben estar entre 1 y 10080 (7 días)."))
        if usuario.bot:
            return await ctx.send(embed=embed_error("No puedes encarcelar a bots."))
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        nombre_det = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        hasta = datetime.now() + timedelta(minutes=minutos)
        await db.update_user_state(usuario.id, encarcelado_hasta=hasta.isoformat())
        embed = discord.Embed(title="🔒 ENCARCELAMIENTO", description=f"{nombre_ag} ha encarcelado a {nombre_det} por {minutos} minutos.\nMotivo: {motivo}", color=0xFF0000)
        await ctx.send(embed=embed)
        await self.log("PDA_ENCARCELAR", f"{nombre_ag} encarceló a {nombre_det} por {minutos}min: {motivo}")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='multar')
    async def pda_multar(self, ctx, usuario: discord.Member, cantidad: int, *, motivo: str):
        if cantidad <= 0 or cantidad > 1000000:
            return await ctx.send(embed=embed_error("La multa debe estar entre $1 y $1,000,000."))
        if usuario.bot:
            return await ctx.send(embed=embed_error("No puedes multar a bots."))
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        placa = (await db.get_user_state(ctx.author.id)).get('placa', '')
        await db.add_multa(usuario.id, cantidad, motivo, nombre_ag, placa)
        embed = discord.Embed(title="📄 MULTA", description=f"{nombre_ag} ha multado a {usuario.mention} con **${cantidad:,}**.\nMotivo: {motivo}", color=0xFFA500)
        await ctx.send(embed=embed)
        await self.log("PDA_MULTAR", f"{nombre_ag} multó a {usuario.name}: ${cantidad} - {motivo}")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='requisar')
    async def pda_requisar(self, ctx, usuario: discord.Member, *, arma: str):
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        armas = await db.get_armas_equipadas(usuario.id)
        arma_real = next((k for k in armas if k.lower() == arma.lower()), None)
        if not arma_real:
            return await ctx.send(embed=embed_error(f"{usuario.display_name} no tiene {arma} equipada."))
        await db.execute("DELETE FROM armas_equipadas WHERE user_id = ? AND arma = ?", (usuario.id, arma_real))
        embed = discord.Embed(title="🔫 ARMA REQUISADA", description=f"{nombre_ag} requisó {arma_real} a {usuario.mention}.", color=0xFF0000)
        await ctx.send(embed=embed)
        await self.log("PDA_REQUISAR", f"{nombre_ag} requisó {arma_real} a {usuario.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='guardar')
    async def pda_guardar(self, ctx, usuario: discord.Member, *, item: str):
        if usuario.bot:
            return await ctx.send(embed=embed_error("No puedes guardar evidencia de un bot."))
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        nombre_target = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        armas = await db.get_armas_equipadas(usuario.id)
        item_real = next((k for k in armas if k.lower() == item.lower()), None)
        if item_real:
            await db.execute("DELETE FROM armas_equipadas WHERE user_id = ? AND arma = ?", (usuario.id, item_real))
            await db.add_evidence(ctx.author.id, usuario.id, item_real, 1)
            embed = discord.Embed(title="📦 EVIDENCIA GUARDADA", description=f"{nombre_ag} guardó **{item_real}** de {nombre_target}.", color=0x3498DB)
            await ctx.send(embed=embed)
            await self.log("PDA_GUARDAR", f"{nombre_ag} guardó {item_real} de {usuario.name}")
            return
        inv = await db.get_inventory(usuario.id, "personal")
        item_real = next((k for k in inv if k.lower() == item.lower()), None)
        if not item_real:
            return await ctx.send(embed=embed_error(f"{nombre_target} no tiene {item}."))
        await db.remove_item(usuario.id, "personal", item_real, 1)
        await db.add_evidence(ctx.author.id, usuario.id, item_real, 1)
        embed = discord.Embed(title="📦 EVIDENCIA GUARDADA", description=f"{nombre_ag} guardó **{item_real}** de {nombre_target}.", color=0x3498DB)
        await ctx.send(embed=embed)
        await self.log("PDA_GUARDAR", f"{nombre_ag} guardó {item_real} de {usuario.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='evidencia')
    async def pda_evidencia(self, ctx, usuario: Optional[discord.Member] = None):
        if usuario is None:
            usuario = ctx.author
        evidencias = await db.get_evidence(usuario.id)
        if not evidencias:
            return await ctx.send(embed=embed_info("📦 Evidencia", f"No hay evidencia registrada para {usuario.display_name}."))
        descripcion = ""
        for evidencia in evidencias[:10]:
            agente = ctx.guild.get_member(evidencia['agente_id'])
            nombre_agente = agente.display_name if agente else str(evidencia['agente_id'])
            descripcion += f"• **{evidencia['item']}** x{evidencia['quantity']} — Guardado por {nombre_agente} el {evidencia['fecha'][:16]}\n"
        embed = discord.Embed(title=f"📦 Evidencia de {usuario.display_name}", description=descripcion, color=0x3498DB)
        embed.set_footer(text="Usa -pda guardar @usuario <item> para agregar evidencia")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='licencia')
    async def pda_licencia(self, ctx, usuario: discord.Member, tipo_licencia: str, accion: str = "dar"):
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        licencia = tipo_licencia.lower()
        if accion.lower() == "dar":
            await db.dar_licencia(usuario.id, licencia)
            embed = discord.Embed(title="📋 LICENCIA OTORGADA", description=f"{nombre_ag} concedió {licencia} a {usuario.mention}.", color=0x00FF00)
        else:
            await db.quitar_licencia(usuario.id, licencia)
            embed = discord.Embed(title="📋 LICENCIA REVOCADA", description=f"{nombre_ag} revocó {licencia} a {usuario.mention}.", color=0xFF0000)
        await ctx.send(embed=embed)
        await self.log("PDA_LICENCIA", f"{nombre_ag} {accion} {licencia} a {usuario.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='quitar-multa')
    @tiene_rol_lspd_operativo()
    async def pda_quitar_multa(self, ctx, usuario: discord.Member):
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        nombre_u = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        multas = await db.fetchall("SELECT id, cantidad, motivo FROM multas WHERE user_id = ? AND pagada = 0", (usuario.id,))
        if not multas:
            return await ctx.send(embed=embed_error(f"{nombre_u} no tiene multas pendientes."))
        total = sum(m[1] for m in multas)
        await db.execute("UPDATE multas SET pagada = 1 WHERE user_id = ? AND pagada = 0", (usuario.id,))
        embed = discord.Embed(title="✅ MULTA ELIMINADA", description=f"Se han eliminado **{len(multas)} multa(s)** de {nombre_u} por un total de **${total:,}**.", color=0x00FF00)
        embed.set_footer(text=f"Agente: {nombre_ag}")
        await ctx.send(embed=embed)
        await self.log("PDA_QUITAR_MULTA", f"{nombre_ag} quitó multas a {nombre_u} (${total:,})")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='buscar')
    async def pda_buscar(self, ctx, *, nombre: str):
        rows = await db.fetchall("SELECT user_id, dni_nombre, dni_apellidos FROM users WHERE dni_nombre LIKE ? OR dni_apellidos LIKE ?", (f'%{nombre}%', f'%{nombre}%'))
        if not rows:
            return await ctx.send(embed=embed_error("No se encontraron resultados."))
        embed = discord.Embed(title=f"🔍 Resultados para '{nombre}'", color=0x3498DB)
        for uid, nombre, apellidos in rows[:5]:
            user = ctx.guild.get_member(uid)
            nombre_completo = f"{nombre} {apellidos}".strip()
            embed.add_field(name=nombre_completo, value=f"ID: {uid}\nUsuario: {user.mention if user else uid}", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='crear-placa')
    async def crear_placa(self, ctx, usuario: discord.Member, numero: str):
        has_lspd_role = any(role.id == ROL_LSPD_ID or "LSPD" in role.name.upper() for role in ctx.author.roles)
        has_owner = ctx.author.id in OWNER_IDS
        if not (has_lspd_role or has_owner):
            return await ctx.send(embed=embed_error("Necesitas rol LSPD o ser owner para crear una placa policial."))
        numero = numero.strip().upper()
        if numero.startswith("LSPD-") or numero.startswith("LPSD-"):
            numero = numero.split('-', 1)[1]
        if not numero.isdigit() or len(numero) != 4:
            return await ctx.send(embed=embed_error("El número de placa debe ser exactamente 4 dígitos (ej: 0001 o LSPD-0001)."))
        placa_completa = f"LSPD-{numero}"
        user_state = await db.get_user_state(usuario.id)
        if user_state.get('placa'):
            return await ctx.send(embed=embed_error(f"{usuario.display_name} ya tiene una placa asignada: {user_state['placa']}. Usa `-pda quitar-placa` si quieres cambiarla."))
        await db.update_user_state(usuario.id, placa=placa_completa)
        embed = discord.Embed(title="✅ PLACA ASIGNADA", description=f"Se ha asignado la placa **{placa_completa}** a {usuario.mention}.", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("CREAR_PLACA", f"{ctx.author.name} asignó placa {placa_completa} a {usuario.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='multas')
    async def multas(self, ctx):
        uid = ctx.author.id
        multas = await db.get_multas_pendientes(uid)
        if not multas:
            return await ctx.send(embed=embed_info("📄 Multas", "No tienes multas pendientes."))
        embed = discord.Embed(title="📄 MIS MULTAS", color=0xFFA500)
        total = 0
        for i, m in enumerate(multas, 1):
            embed.add_field(name=f"#{i} — **${m['cantidad']:,}**", value=f"Motivo: {m['motivo']}\nAgente: {m['agente']}\nFecha: {m['fecha'][:10]}", inline=False)
            total += m['cantidad']
        embed.add_field(name="Total pendiente", value=f"**${total:,}**", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='esposar')
    @tiene_rol_lspd_operativo()
    async def esposar(self, ctx, usuario: discord.Member, *, motivo: str):
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        nombre_det = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        embed = discord.Embed(
            title="🔗 ESPOSADO",
            description=f"***{nombre_ag} ha esposado a {nombre_det}.***\n\n**Motivo:** {motivo}",
            color=0xFF6600,
            timestamp=datetime.now()
        )
        embed.set_footer(text="LSPD — Nova Agora RP")
        await ctx.send(embed=embed)
        await self.log("ESPOSAR", f"{nombre_ag} esposó a {nombre_det}: {motivo}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='des-esposar')
    async def des_esposar(self, ctx, usuario: discord.Member, *, motivo: str):
        nombre_ag = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
        nombre_det = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        embed = discord.Embed(title="🔓 DES-ESPOSADO", description=f"{nombre_ag} ha des-esposado a {nombre_det}. Motivo: {motivo}", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("PDA_DES-ESPOSAR", f"{nombre_ag} des-esposó a {nombre_det}: {motivo}")
        try:
            await ctx.message.delete()
        except:
            pass

    @pda.command(name='quitar-placa')
    async def pda_quitar_placa(self, ctx):
        user_state = await db.get_user_state(ctx.author.id)
        if not user_state.get('placa'):
            return await ctx.send(embed=embed_error("No tienes una placa asignada."))
        await db.update_user_state(ctx.author.id, placa=None)
        embed = discord.Embed(title="🗑️ PLACA ELIMINADA", description="Tu placa policial ha sido eliminada.", color=0xFF6600)
        await ctx.send(embed=embed)
        await self.log("QUITAR_PLACA", f"{ctx.author.name} eliminó su placa")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Móvil ====================
class Movil(BaseCog):
    @app_commands.command(name='movil', description="Abre el móvil con NOVA AGORA V2")
    async def movil(self, interaction: discord.Interaction):
        uid = interaction.user.id
        user_state = await db.get_user_state(uid)
        if user_state['airplane_mode']:
            return await interaction.response.send_message(embed=embed_error("Modo avión activado. Desactívalo con `/avion off`"))
        numero = user_state['phone_number'] or "Sin número"
        wifi = "📶 Conectado" if user_state['wifi_connected'] else "📶 Desconectado"
        await interaction.response.send_message("✨ **** ABRE TÚ MÓVIL EN NOVA AGORA V2 ****")
        embed = discord.Embed(title=f"{await get_emoji('phone')} Móvil de {interaction.user.name}", description=f"📞 Número: `{numero}`\n{wifi}", color=0x00BCD4)
        view = MovilView(interaction.user.id)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name='avion', description="Modo avión - NOVA AGORA V2")
    async def avion(self, interaction: discord.Interaction, estado: str):
        if estado.lower() not in ['on', 'off']:
            return await interaction.response.send_message(embed=embed_error("Usa `on` o `off`"))
        uid = interaction.user.id
        on = estado.lower() == 'on'
        await db.update_user_state(uid, airplane_mode=on)
        await interaction.response.send_message("✨ **** MODO AVIÓN " + ("ACTIVADO" if on else "DESACTIVADO") + " EN NOVA AGORA V2 ****")
        await interaction.followup.send(embed=embed_success("✈️ Modo avión", f"{'Activado' if on else 'Desactivado'}"))

    @app_commands.command(name='wifi', description="Gestiona WiFi - NOVA AGORA V2")
    async def wifi(self, interaction: discord.Interaction, accion: str = None):
        uid = interaction.user.id
        user_state = await db.get_user_state(uid)
        if not accion:
            return await interaction.response.send_message(embed=embed_info("📶 WiFi", f"Estado: {'Conectado' if user_state['wifi_connected'] else 'Desconectado'}\nUsa `/wifi conectar` o `/wifi desconectar`"))
        if accion.lower() == 'conectar':
            if user_state['wifi_connected']:
                return await interaction.response.send_message(embed=embed_error("Ya estás conectado."))
            await db.update_user_state(uid, wifi_connected=True)
            await interaction.response.send_message("✨ **** CONECTADO A WIFI EN NOVA AGORA V2 ****")
            await interaction.followup.send(embed=embed_success("📶 WiFi", "Conectado a la red."))
        elif accion.lower() == 'desconectar':
            if not user_state['wifi_connected']:
                return await interaction.response.send_message(embed=embed_error("Ya estás desconectado."))
            await db.update_user_state(uid, wifi_connected=False)
            await interaction.response.send_message("✨ **** DESCONECTADO DEL WIFI EN NOVA AGORA V2 ****")
            await interaction.followup.send(embed=embed_success("📶 WiFi", "Desconectado de la red.", color=0xFFA500))
        else:
            await interaction.response.send_message(embed=embed_error("Usa `conectar` o `desconectar`"))

    @app_commands.command(name='comprar-sim', description="Compra SIM - NOVA AGORA V2")
    async def comprar_sim(self, interaction: discord.Interaction):
        uid = interaction.user.id
        eco = await db.get_economy(uid)
        if eco['cash'] < 500:
            return await interaction.response.send_message(embed=embed_error("Necesitas $500."))
        numero = f"+34 6{random.randint(10,99)} {random.randint(100,999)} {random.randint(100,999)}"
        await db.add_cash(uid, -500)
        await db.update_user_state(uid, phone_number=numero)
        await interaction.response.send_message("✨ **** COMPRA SIM EN NOVA AGORA V2 ****")
        await interaction.followup.send(embed=embed_success(f"{await get_emoji('phone')} SIM comprada", f"Número: `{numero}`\nCosto: $500"))
        await self.log("COMPRA_SIM", f"{interaction.user.name} compró SIM: {numero}")

    @commands.command(name='movil', aliases=['tel', 'telefono', 'celular'])
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def movil_prefix(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        if user_state['airplane_mode']:
            return await ctx.send(embed=embed_error("Modo avión activado. Desactívalo con `-avion off`"))
        numero = user_state['phone_number'] or "Sin número"
        wifi = "📶 Conectado" if user_state['wifi_connected'] else "📶 Desconectado"
        await ctx.send("✨ **** ABRE TÚ MÓVIL EN NOVA AGORA V2 ****")
        embed = discord.Embed(title=f"{await get_emoji('phone')} Móvil de {ctx.author.name}", description=f"📞 Número: `{numero}`\n{wifi}", color=0x00BCD4)
        view = MovilView(ctx.author.id)
        await ctx.send(embed=embed, view=view)
        await self.log("MOVIL_PREFIX", f"{ctx.author.name} abrió el móvil con -movil")

    @commands.command(name='avion', aliases=['airplane', 'avionmode'])
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def avion_prefix(self, ctx, estado: str = None):
        try:
            await ctx.message.delete()
        except:
            pass
        if not estado or estado.lower() not in ['on', 'off']:
            return await ctx.send(embed=embed_error("Usa `-avion on` o `-avion off`"))
        uid = ctx.author.id
        on = estado.lower() == 'on'
        await db.update_user_state(uid, airplane_mode=on)
        await ctx.send("✨ **** MODO AVIÓN " + ("ACTIVADO" if on else "DESACTIVADO") + " EN NOVA AGORA V2 ****")
        await ctx.send(embed=embed_success("✈️ Modo avión", f"{'Activado' if on else 'Desactivado'}"))
        await self.log("AVION_PREFIX", f"{ctx.author.name} cambió modo avión a {estado}")

    @commands.command(name='wifi', aliases=['redwifi', 'internet'])
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def wifi_prefix(self, ctx, accion: str = None):
        try:
            await ctx.message.delete()
        except:
            pass
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        if not accion:
            return await ctx.send(embed=embed_info("📶 WiFi", f"Estado: {'Conectado' if user_state['wifi_connected'] else 'Desconectado'}\nUsa `-wifi conectar` o `-wifi desconectar`"))
        if accion.lower() == 'conectar':
            if user_state['wifi_connected']:
                return await ctx.send(embed=embed_error("Ya estás conectado."))
            await db.update_user_state(uid, wifi_connected=True)
            await ctx.send("✨ **** CONECTADO A WIFI EN NOVA AGORA V2 ****")
            await ctx.send(embed=embed_success("📶 WiFi", "Conectado a la red."))
        elif accion.lower() == 'desconectar':
            if not user_state['wifi_connected']:
                return await ctx.send(embed=embed_error("Ya estás desconectado."))
            await db.update_user_state(uid, wifi_connected=False)
            await ctx.send("✨ **** DESCONECTADO DEL WIFI EN NOVA AGORA V2 ****")
            await ctx.send(embed=embed_success("📶 WiFi", "Desconectado de la red.", color=0xFFA500))
        else:
            await ctx.send(embed=embed_error("Usa `-wifi conectar` o `-wifi desconectar`"))
        await self.log("WIFI_PREFIX", f"{ctx.author.name} cambió estado de wifi a {accion}")

    @commands.command(name='comprar-sim', aliases=['comprar_sim', 'buysim', 'sim'])
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def comprar_sim_prefix(self, ctx):
        try:
            await ctx.message.delete()
        except:
            pass
        uid = ctx.author.id
        eco = await db.get_economy(uid)
        if eco['cash'] < 500:
            return await ctx.send(embed=embed_error("Necesitas $500."))
        numero = f"+34 6{random.randint(10,99)} {random.randint(100,999)} {random.randint(100,999)}"
        await db.add_cash(uid, -500)
        await db.update_user_state(uid, phone_number=numero)
        await ctx.send("✨ **** COMPRA SIM EN NOVA AGORA V2 ****")
        await ctx.send(embed=embed_success(f"{await get_emoji('phone')} SIM comprada", f"Número: `{numero}`\nCosto: $500"))
        await self.log("COMPRA_SIM_PREFIX", f"{ctx.author.name} compró SIM: {numero}")

class MovilView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=120)
        self.uid = uid

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.uid:
            await interaction.response.send_message(embed=embed_error("No es tu móvil."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Instagram", style=discord.ButtonStyle.danger, row=0)
    async def btn_ig(self, interaction, button):
        emoji = await get_emoji('ig')
        await interaction.response.send_message(embed=embed_info(f"{emoji} Instagram", "Comandos:\n`-ig perfil`\n`-ig post \"texto\"`\n`-ig like <id>`\n`-ig seguir @user`\n`-ig priv @user msg`\n`-ig trending`", 0xE4405F), ephemeral=True)

    @discord.ui.button(label="Twitter", style=discord.ButtonStyle.secondary, row=0)
    async def btn_tw(self, interaction, button):
        emoji = await get_emoji('twitter')
        await interaction.response.send_message(embed=embed_info(f"{emoji} Twitter", "Comandos:\n`-tw perfil`\n`-tw tweet \"texto\"`\n`-tw seguir @user`\n`-tw priv @user msg`", 0x1DA1F2), ephemeral=True)

    @discord.ui.button(label="Facebook", style=discord.ButtonStyle.primary, row=0)
    async def btn_fb(self, interaction, button):
        emoji = await get_emoji('facebook')
        await interaction.response.send_message(embed=embed_info(f"{emoji} Facebook", "Comandos:\n`-fb post \"texto\"`\n`-fb priv @user msg`\n`-fb perfil`", 0x1877F2), ephemeral=True)

    @discord.ui.button(label="WhatsApp", style=discord.ButtonStyle.success, row=1)
    async def btn_wa(self, interaction, button):
        emoji = await get_emoji('whatsapp')
        await interaction.response.send_message(embed=embed_info(f"{emoji} WhatsApp", "Comandos:\n`-wa contactos`\n`-wa agregar +34... Nombre`\n`-wa chat @user msg`\n`-wa llamar @user`", 0x25D366), ephemeral=True)

    @discord.ui.button(label="DeepWeb", style=discord.ButtonStyle.danger, row=1)
    async def btn_dw(self, interaction, button):
        emoji = await get_emoji('deepweb')
        await interaction.response.send_message(embed=embed_info(f"{emoji} DeepWeb", "Anónimo.\n`-deepweb @user mensaje`", 0x2C2F33), ephemeral=True)

    @discord.ui.button(label="Config", style=discord.ButtonStyle.secondary, row=2)
    async def btn_cfg(self, interaction, button):
        user_state = await db.get_user_state(self.uid)
        n = user_state['phone_number'] or "❌ Sin número"
        av = "✈️ ON" if user_state['airplane_mode'] else "✈️ OFF"
        wf = "📶 ON" if user_state['wifi_connected'] else "📶 OFF"
        await interaction.response.send_message(embed=embed_info("⚙️ Configuración", f"📱 {n}\n{av}\n{wf}\n\n`-avion on/off`\n`-wifi conectar/desconectar`\n`-comprar-sim`", 0x95A5A6), ephemeral=True)

# ==================== COG: Redes Sociales ====================
class Redes(BaseCog):
    @commands.group(name='ig', invoke_without_command=True)
    @tiene_rol_usuario()
    async def ig(self, ctx):
        emoji = await get_emoji('ig')
        await ctx.send(f"{emoji} **** INSTAGRAM EN NOVA AGORA V2 ****\nUsa los subcomandos: `/ig perfil`, `/ig post`, `/ig like`, `/ig seguir`, `/ig priv`, `/ig trending`")

    @ig.command(name='perfil')
    async def ig_perfil(self, interaction: discord.Interaction, usuario: discord.Member = None):
        objetivo = usuario or interaction.user
        uid = objetivo.id
        user_state = await db.get_user_state(uid)
        seguidores = await db.get_followers_ig(uid)
        siguiendo = await db.get_following_ig(uid)
        posts = await db.get_posts_ig(uid)
        likes_totales = sum(len(p['likes']) for p in posts)
        embed = discord.Embed(title=f"{await get_emoji('ig')} @{objetivo.name}", color=0xE4405F)
        embed.add_field(name="Seguidores", value=f"{seguidores}", inline=True)
        embed.add_field(name="Siguiendo", value=f"{siguiendo}", inline=True)
        embed.add_field(name="Posts", value=f"{len(posts)}", inline=True)
        embed.add_field(name="Likes recibidos", value=f"{likes_totales}", inline=True)
        embed.add_field(name="Privacidad", value="Pública" if user_state['ig_public'] else "Privada", inline=True)
        embed.add_field(name="Bio", value=user_state['ig_bio'] or "Sin bio", inline=False)
        embed.set_thumbnail(url=objetivo.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @ig.command(name='post')
    async def ig_post(self, interaction: discord.Interaction, texto: str):
        uid = interaction.user.id
        pid = await db.add_post_ig(uid, texto)
        await interaction.response.send_message(f"{await get_emoji('ig')} **** PUBLICA EN INSTAGRAM EN NOVA AGORA V2 ****")
        await interaction.followup.send(embed=embed_success(f"{await get_emoji('ig')} Publicado", f"ID: `{pid}`\n{texto[:200]}"))

    @ig.command(name='like')
    async def ig_like(self, interaction: discord.Interaction, post_id: str):
        uid = interaction.user.id
        if await db.add_like_ig(post_id, uid):
            await interaction.response.send_message(f"{await get_emoji('ig')} **** LIKE EN INSTAGRAM EN NOVA AGORA V2 ****")
            await interaction.followup.send(embed=embed_success("❤️ Like", f"Has dado like al post `{post_id}`.", 0xE4405F))
            await self.log("IG_LIKE", f"{interaction.user.name} dio like al post {post_id}")
        else:
            await interaction.response.send_message(embed=embed_error("Post no encontrado o ya le diste like."))

    @ig.command(name='seguir')
    async def ig_seguir(self, interaction: discord.Interaction, usuario: discord.Member):
        uid, tid = interaction.user.id, usuario.id
        if uid == tid:
            return await interaction.response.send_message(embed=embed_error("No puedes seguirte a ti mismo."))
        if await db.is_following_ig(uid, tid):
            await db.unfollow_ig(uid, tid)
            await interaction.response.send_message(f"{await get_emoji('ig')} **** DEJÓ DE SEGUIR EN INSTAGRAM EN NOVA AGORA V2 ****")
            await interaction.followup.send(embed=embed_success(f"{await get_emoji('ig')} Dejado de seguir", f"Dejaste de seguir a {usuario.display_name}.", 0xFFA500))
        else:
            await db.follow_ig(uid, tid)
            await interaction.response.send_message(f"{await get_emoji('ig')} **** SIGUE EN INSTAGRAM EN NOVA AGORA V2 ****")
            await interaction.followup.send(embed=embed_success(f"{await get_emoji('ig')} Siguiendo", f"Ahora sigues a {usuario.display_name}.", 0x00FF00))
            await self.dm_user(tid, discord.Embed(title=f"{await get_emoji('ig')} Nuevo seguidor", description=f"{interaction.user.display_name} te sigue ahora en Instagram.", color=0xE4405F))

    @ig.command(name='trending')
    async def ig_trending(self, interaction: discord.Interaction):
        rows = await db.fetchall("SELECT id, user_id, texto, tiempo, likes FROM posts_ig")
        posts = []
        for row in rows:
            likes = json.loads(row[4]) if row[4] else []
            if len(likes) > 0:
                posts.append({"user_id": row[1], "texto": row[2], "likes": len(likes), "id": row[0]})
        posts.sort(key=lambda x: x['likes'], reverse=True)
        embed = discord.Embed(title=f"{await get_emoji('ig')} TRENDING SEMANAL", color=0xE4405F)
        for i, p in enumerate(posts[:5], 1):
            user = interaction.guild.get_member(p['user_id'])
            nombre = user.display_name if user else f"Usuario {p['user_id']}"
            embed.add_field(name=f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'#{i}'} {nombre} — ❤️ {p['likes']}", value=f"{p['texto'][:50]}...\n🆔 `{p['id']}`", inline=False)
        await interaction.response.send_message(embed=embed)

    @ig.command(name='priv')
    async def ig_priv(self, interaction: discord.Interaction, user: discord.Member, msg: str):
        if interaction.user.id == user.id:
            return await interaction.response.send_message(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        await interaction.response.send_message(f"{await get_emoji('ig')} **** ENVÍA DM EN INSTAGRAM EN NOVA AGORA V2 ****")
        dm = discord.Embed(title=f"{await get_emoji('ig')} Instagram — Mensaje privado", description=msg, color=0xE4405F, timestamp=datetime.now())
        dm.set_author(name=f"@{interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await self.dm_user(user.id, dm)
        await interaction.followup.send(embed=embed_success("📨 Mensaje enviado", f"Enviado a @{user.display_name}"))

    @commands.group(name='tw', invoke_without_command=True)
    @tiene_rol_usuario()
    async def tw(self, ctx):
        emoji = await get_emoji('twitter')
        await ctx.send(f"{emoji} **** TWITTER EN NOVA AGORA V2 ****\nUsa los subcomandos: `/tw perfil`, `/tw tweet`, `/tw seguir`, `/tw priv`")

    @tw.command(name='perfil')
    async def tw_perfil(self, interaction: discord.Interaction, usuario: discord.Member = None):
        objetivo = usuario or interaction.user
        uid = objetivo.id
        seguidores = await db.get_followers_tw(uid)
        siguiendo = await db.get_following_tw(uid)
        posts = await db.fetchall("SELECT id FROM posts_tw WHERE user_id = ?", (uid,))
        embed = discord.Embed(title=f"{await get_emoji('twitter')} @{objetivo.name}", color=0x1DA1F2)
        embed.add_field(name="Seguidores", value=f"{seguidores}", inline=True)
        embed.add_field(name="Siguiendo", value=f"{siguiendo}", inline=True)
        embed.add_field(name="Tweets", value=f"{len(posts)}", inline=True)
        embed.set_thumbnail(url=objetivo.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @tw.command(name='tweet')
    async def tw_tweet(self, interaction: discord.Interaction, texto: str):
        uid = interaction.user.id
        pid = await db.add_post_tw(uid, texto)
        await interaction.response.send_message(f"{await get_emoji('twitter')} **** PUBLICA EN TWITTER EN NOVA AGORA V2 ****")
        await interaction.followup.send(embed=embed_success(f"{await get_emoji('twitter')} Tweet", f"{texto[:200]}\nID: `{pid}`", 0x1DA1F2))

    @tw.command(name='seguir')
    async def tw_seguir(self, interaction: discord.Interaction, usuario: discord.Member):
        uid, tid = interaction.user.id, usuario.id
        if uid == tid:
            return await interaction.response.send_message(embed=embed_error("No puedes seguirte a ti mismo."))
        if await db.is_following_tw(uid, tid):
            await db.unfollow_tw(uid, tid)
            await interaction.response.send_message(f"{await get_emoji('twitter')} **** DEJÓ DE SEGUIR EN TWITTER EN NOVA AGORA V2 ****")
            await interaction.followup.send(embed=embed_success(f"{await get_emoji('twitter')} Dejado de seguir", f"Dejaste de seguir a {usuario.display_name} en Twitter.", 0xFFA500))
        else:
            await db.follow_tw(uid, tid)
            await interaction.response.send_message(f"{await get_emoji('twitter')} **** SIGUE EN TWITTER EN NOVA AGORA V2 ****")
            await interaction.followup.send(embed=embed_success(f"{await get_emoji('twitter')} Siguiendo", f"Ahora sigues a {usuario.display_name} en Twitter.", 0x00FF00))
            await self.dm_user(tid, discord.Embed(title=f"{await get_emoji('twitter')} Nuevo seguidor", description=f"{interaction.user.display_name} te sigue ahora en Twitter.", color=0x1DA1F2))

    @tw.command(name='priv')
    async def tw_priv(self, interaction: discord.Interaction, user: discord.Member, msg: str):
        if interaction.user.id == user.id:
            return await interaction.response.send_message(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        await interaction.response.send_message(f"{await get_emoji('twitter')} **** ENVÍA DM EN TWITTER EN NOVA AGORA V2 ****")
        dm = discord.Embed(title=f"{await get_emoji('twitter')} Twitter — DM", description=msg, color=0x1DA1F2, timestamp=datetime.now())
        dm.set_author(name=f"@{interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        await self.dm_user(user.id, dm)
        await interaction.followup.send(embed=embed_success("📨 DM enviado", f"A @{user.display_name}"))

    @commands.command(name='x')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def twitter_dm(self, ctx, usuario: discord.Member, *, mensaje: str):
        if usuario.id == ctx.author.id:
            return await ctx.send(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        await db.add_twitter_dm(ctx.author.id, usuario.id, mensaje)
        embed_notif = discord.Embed(
            title=f"✉️ Nuevo mensaje directo de Twitter",
            description=f"**{ctx.author.display_name}** te ha enviado un mensaje:\n\n> {mensaje}",
            color=0x1DA1F2,
            timestamp=datetime.now()
        )
        embed_notif.set_footer(text=f"Usa -x @{ctx.author.name} para responder.")
        await self.dm_user(usuario.id, embed_notif)
        await ctx.send(embed=embed_success("✅ Mensaje enviado", f"Tu mensaje ha sido enviado a {usuario.display_name} por Twitter DM."))
        await self.log("TWITTER_DM", f"{ctx.author.name} -> {usuario.name}: {mensaje}")
        try:
            await ctx.message.delete()
        except:
            pass

    fb = app_commands.Group(name='fb', description='Facebook - NOVA AGORA V2')

    @fb.command(name='post', description='Publicar en Facebook')
    async def fb_post(self, interaction: discord.Interaction, texto: str):
        uid = interaction.user.id
        pid = await db.add_post_fb(uid, texto)
        await interaction.response.send_message(f"{await get_emoji('facebook')} **** PUBLICA EN FACEBOOK EN NOVA AGORA V2 ****")
        await interaction.followup.send(embed=embed_success(f"{await get_emoji('facebook')} Publicado", f"ID: `{pid}`\n{texto[:200]}", 0x1877F2))

    @fb.command(name='perfil', description='Ver perfil de Facebook')
    async def fb_perfil(self, interaction: discord.Interaction):
        uid = interaction.user.id
        posts = await db.fetchall("SELECT id FROM posts_fb WHERE user_id = ?", (uid,))
        await interaction.response.send_message(embed=embed_info(f"{await get_emoji('facebook')} {interaction.user.name}", f"Tienes {len(posts)} publicaciones.", 0x1877F2))

    @fb.command(name='priv', description='Enviar mensaje privado en Facebook')
    async def fb_priv(self, interaction: discord.Interaction, user: discord.Member, msg: str):
        if interaction.user.id == user.id:
            return await interaction.response.send_message(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        await interaction.response.send_message(f"{await get_emoji('facebook')} **** ENVÍA MENSAJE EN FACEBOOK EN NOVA AGORA V2 ****")
        dm = discord.Embed(title=f"{await get_emoji('facebook')} Facebook — Mensaje privado", description=msg, color=0x1877F2, timestamp=datetime.now())
        dm.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        await self.dm_user(user.id, dm)
        await interaction.followup.send(embed=embed_success("📨 Mensaje enviado", f"A {user.display_name}"))

    @app_commands.command(name='deepweb', description="Sistema DeepWeb - NOVA AGORA V2")
    async def deepweb(self, interaction: discord.Interaction, target: discord.Member = None, msg: str = None):
        if target is None or msg is None:
            embed = discord.Embed(title=f"{await get_emoji('deepweb')} DEEPWEB — Sistema Anónimo", description="Envía un mensaje anónimo seguro usando el formato correcto.", color=0x2C2F33)
            embed.add_field(name="📨 **/deepweb @usuario <mensaje>**", value="Envía un mensaje anónimo encriptado directamente a un usuario.", inline=False)
            embed.add_field(name="🔓 **/descifrar <id>** 🔒 **(FBI)**", value="Intenta descifrar un mensaje (1/10 éxito).", inline=False)
            embed.add_field(name="ℹ️ Características", value="✅ Identidad anónima\n✅ ID de seguimiento\n✅ Encriptación asimétrica\n✅ FBI puede descifrar (1/10)", inline=False)
            embed.set_footer(text="Uso responsable requerido • NOVA AGORA")
            return await interaction.response.send_message(embed=embed)
        if target.id == interaction.user.id:
            return await interaction.response.send_message(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        text = msg.strip()
        if not text:
            return await interaction.response.send_message(embed=embed_error("Debes escribir un mensaje después de mencionar al usuario."))
        msg_id = await db.add_deepweb_message(interaction.user.id, target.id, text)
        await interaction.response.send_message(f"{await get_emoji('deepweb')} **** ENVÍA MENSAJE DEEPWEB EN NOVA AGORA V2 ****")
        dm = discord.Embed(title=f"{await get_emoji('deepweb')} Mensaje Anónimo — DeepWeb", description=text, color=0x2C2F33, timestamp=datetime.now())
        dm.set_footer(text=f"ID: {msg_id} — Identidad oculta")
        await self.dm_user(target.id, dm)
        await interaction.followup.send(embed=embed_success(f"{await get_emoji('deepweb')} Mensaje enviado", f"Anónimo | ID: `{msg_id}`"))
        await self.log("DEEPWEB", f"{interaction.user.name} → {target.name}: {text[:50]}...")

    @app_commands.command(name='descifrar', description="Descifra mensajes DeepWeb - FBI NOVA AGORA V2")
    async def descifrar(self, interaction: discord.Interaction, mensaje_id: int = None):
        fbi_role = discord.utils.get(interaction.guild.roles, name="FBI")
        if not fbi_role or fbi_role not in interaction.user.roles:
            return await interaction.response.send_message(embed=embed_error("Solo agentes del FBI pueden usar este comando."))
        if mensaje_id is None:
            embed = discord.Embed(title="🔐 DESCIFRADOR DeepWeb — FBI Confidencial", description="Sistema de inteligencia para descifrar mensajes DeepWeb anónimos.", color=0x3498DB)
            embed.add_field(name="📋 Uso", value="`/descifrar <id_del_mensaje>`", inline=False)
            embed.add_field(name="📊 Probabilidad de Éxito", value="**1/10** (10%) de descifrar la identidad del remitente", inline=False)
            embed.add_field(name="🔍 Cómo obtener IDs", value="Los IDs se proporcionan cuando se envían mensajes DeepWeb:\n`ID: 12345` (en el mensaje anónimo)", inline=False)
            embed.add_field(name="✅ Éxito", value="Se revela el nombre del remitente\n📝 Se registra en logs del FBI", inline=False)
            embed.add_field(name="❌ Fallo", value="La identidad permanece oculta\n🔄 Puedes intentar nuevamente más tarde", inline=False)
            embed.set_footer(text="Información Clasificada • FBI NOVA AGORA")
            return await interaction.response.send_message(embed=embed)
        decode_result = await db.decode_deepweb_message(mensaje_id, interaction.user.id)
        if not decode_result:
            return await interaction.response.send_message(embed=embed_error("Mensaje DeepWeb no encontrado."))
        if decode_result['decoded']:
            autor = interaction.guild.get_member(decode_result['sender'])
            nombre = autor.display_name if autor else f"Usuario {decode_result['sender']}"
            await interaction.response.send_message(f"{await get_emoji('deepweb')} **** DESCIFRA MENSAJE DEEPWEB EN NOVA AGORA V2 ****")
            embed = discord.Embed(title="🔓 MENSAJE DESCIFRADO", description=f"**Remitente Identificado:** {nombre}\n\n{decode_result['message']}", color=0x3498DB, timestamp=datetime.now())
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"Descifrado exitoso • ID: {mensaje_id}")
            await interaction.followup.send(embed=embed)
            await self.log("DESCIFRAR_EXIT", f"{interaction.user.name} descifró mensaje {mensaje_id} de {nombre}")
        else:
            await interaction.response.send_message(embed=discord.Embed(title="❌ DESCIFRADO FALLIDO", description="La identidad del remitente sigue protegida por encriptación.\nIntenta nuevamente más tarde con otro mensaje.", color=0xFF0000, timestamp=datetime.now()))
            await self.log("DESCIFRAR_FAIL", f"{interaction.user.name} falló en descifrar mensaje {mensaje_id}")

class WhatsApp(BaseCog):
    wa = app_commands.Group(name='wa', description='WhatsApp - NOVA AGORA V2')

    @wa.command(name='contactos', description='Ver contactos de WhatsApp')
    async def wa_contactos(self, interaction: discord.Interaction):
        uid = interaction.user.id
        contactos = await db.get_wa_contacts(uid)
        if not contactos:
            return await interaction.response.send_message(embed=embed_info(f"{await get_emoji('whatsapp')} Contactos", "No tienes contactos."))
        txt = "\n".join([f"📱 `{num}` — {nom}" for num, nom in contactos.items()])
        await interaction.response.send_message(embed=embed_info(f"{await get_emoji('whatsapp')} Contactos", txt, 0x25D366))

    @wa.command(name='agregar', description='Agregar contacto en WhatsApp')
    async def wa_agregar(self, interaction: discord.Interaction, numero: str, nombre: str):
        uid = interaction.user.id
        if not numero.startswith("+"):
            numero = "+" + numero
        await db.add_wa_contact(uid, numero, nombre)
        await interaction.response.send_message(f"{await get_emoji('whatsapp')} **** AÑADE CONTACTO EN WHATSAPP EN NOVA AGORA V2 ****")
        await interaction.followup.send(embed=embed_success("✅ Contacto añadido", f"**{nombre}**: `{numero}`"))

    @wa.command(name='chat', description='Enviar mensaje en WhatsApp')
    async def wa_chat(self, interaction: discord.Interaction, user: discord.Member, msg: str):
        uid, tid = interaction.user.id, user.id
        unum = (await db.get_user_state(uid)).get('phone_number')
        tnum = (await db.get_user_state(tid)).get('phone_number')
        if not unum:
            return await interaction.response.send_message(embed=embed_error("Necesitas una SIM. Usa `/comprar-sim`"))
        if not tnum:
            return await interaction.response.send_message(embed=embed_error(f"{user.display_name} no tiene SIM."))
        await db.add_wa_chat(uid, tid, msg)
        await interaction.response.send_message(f"{await get_emoji('whatsapp')} **** ENVÍA MENSAJE EN WHATSAPP EN NOVA AGORA V2 ****")
        dm = discord.Embed(title=f"{await get_emoji('whatsapp')} WhatsApp — Mensaje", description=msg, color=0x25D366, timestamp=datetime.now())
        dm.set_author(name=f"{interaction.user.display_name} ({unum})", icon_url=interaction.user.display_avatar.url)
        dm.set_footer(text=f"Número: {unum}")
        await self.dm_user(tid, dm)
        await interaction.followup.send(embed=embed_success("📨 Mensaje enviado", f"A {user.display_name} (`{tnum}`)"))

    @wa.command(name='llamar', description='Hacer llamada en WhatsApp')
    async def wa_llamar(self, interaction: discord.Interaction, user: discord.Member, duracion: int = 5):
        uid, tid = interaction.user.id, user.id
        if uid == tid:
            return await interaction.response.send_message(embed=embed_error("No puedes llamarte a ti mismo."))
        unum = (await db.get_user_state(uid)).get('phone_number')
        tnum = (await db.get_user_state(tid)).get('phone_number')
        if not unum:
            return await interaction.response.send_message(embed=embed_error("Necesitas una SIM. Usa `/comprar-sim`"))
        if not tnum:
            return await interaction.response.send_message(embed=embed_error(f"{user.display_name} no tiene SIM."))
        if not interaction.user.voice:
            return await interaction.response.send_message(embed=embed_error("Debes estar en un canal de voz para llamar."))
        categoria = interaction.guild.get_channel(CANAL_VOICE_CATEGORY)
        if not categoria:
            categoria = discord.utils.get(interaction.guild.categories, name="Llamadas")
            if not categoria:
                categoria = await interaction.guild.create_category("Llamadas")
        canal_nombre = f"📞 Llamada-{interaction.user.name[:5]}-{user.name[:5]}"
        try:
            canal_voz = await interaction.guild.create_voice_channel(name=canal_nombre, category=categoria, user_limit=2)
            await interaction.user.move_to(canal_voz)
            if user.voice:
                await user.move_to(canal_voz)
            await interaction.response.send_message(f"{await get_emoji('whatsapp')} **** LLAMADA EN WHATSAPP EN NOVA AGORA V2 ****")
            embed = discord.Embed(title="📞 LLAMADA INICIADA", description=f"De: {interaction.user.mention}\nPara: {user.mention}\nDuración: {duracion} minutos\nCanal: {canal_voz.mention}", color=0x25D366)
            await interaction.followup.send(embed=embed)
            await self.dm_user(tid, discord.Embed(title="📞 Llamada entrante", description=f"{interaction.user.display_name} te está llamando. Duración: {duracion} min.", color=0x25D366))
            await asyncio.sleep(duracion * 60)
            await canal_voz.delete()
        except Exception as e:
            await interaction.followup.send(embed=embed_error(str(e)))

# ==================== COG: Periódico ====================
class Periodico(BaseCog):
    @commands.command(name='periodico')
    @commands.has_permissions(administrator=True)
    async def publicar_periodico(self, ctx):
        if not any(role.name.lower() == "periodista" for role in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
            return await ctx.send(embed=embed_error("Solo los **Periodistas** pueden publicar el periódico."))
        canal = self.bot.get_channel(CANAL_PERIODICO)
        if not canal:
            return await ctx.send(embed=embed_error("Canal de periódico no configurado. Edita la variable `CANAL_PERIODICO` en el código."))
        embed = discord.Embed(title="📰 LOS SANTOS OBSERVER", description=f"*Edición del {datetime.now().strftime('%d/%m/%Y %H:%M')}*", color=0x2C3E50, timestamp=datetime.now())
        atracos_hoy = await db.get_estadistica('atracos_hoy')
        embed.add_field(name="🚨 Criminalidad", value=f"{atracos_hoy} atracos en las últimas 24h", inline=False)
        rows = await db.fetchall("SELECT user_id, cash, bank FROM economy ORDER BY (cash+bank) DESC LIMIT 3")
        if rows:
            top_txt = ""
            for i, row in enumerate(rows, 1):
                user = self.bot.get_user(row[0])
                nombre = user.display_name if user else f"Usuario {row[0]}"
                total = row[1] + row[2]
                medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
                top_txt += f"{medallas[i]} **{nombre}** — **${total:,}**\n"
            embed.add_field(name="💵 Top Económico", value=top_txt, inline=False)
        embed.set_footer(text="NOVA AGORA · Los Santos Observer")
        await canal.send(embed=embed)
        await self.log("PERIODICO", f"{ctx.author.name} publicó una edición del periódico")
        await ctx.send(embed=embed_success("✅ Periódico publicado", "La edición ha sido publicada."))
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Admin ====================
class Admin(BaseCog):
    @commands.command(name='say')
    @tiene_rol_equipo_especial()
    async def say(self, ctx, *, mensaje: str = None):
        if not mensaje:
            return await ctx.send(embed=embed_help("say", "Repite el mensaje en negrita.", "-say <mensaje>", "-say Hola a todos", "Equipo Especial"))
        await ctx.send(f"**{mensaje}**")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='kick')
    @tiene_rol_equipo_especial()
    async def kick(self, ctx, miembro: discord.Member, *, razon: str = "Sin razón"):
        if miembro.id == ctx.author.id:
            return await ctx.send(embed=embed_error("No puedes expulsarte a ti mismo."))
        if miembro.guild_permissions.administrator:
            return await ctx.send(embed=embed_error("No puedes expulsar a un administrador."))
        if not ctx.guild.me.guild_permissions.kick_members:
            return await ctx.send(embed=embed_error("No tengo permiso para expulsar miembros."))
        await miembro.kick(reason=f"{razon} - Expulsado por {ctx.author}")
        await self.registrar_log_moderacion(ctx, "KICK", miembro, razon)
        await ctx.send(embed=embed_success("👢 Usuario expulsado", f"{miembro.mention} ha sido expulsado.\nRazón: {razon}", 0xFF6600))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.group(name='ban', invoke_without_command=True)
    @tiene_rol_equipo_especial()
    async def ban(self, ctx):
        await ctx.send(embed=embed_help("ban", "Banea a un usuario. Usa el subcomando 'definitivo' para baneo permanente + blacklist.", "-ban @usuario [razón]\n-ban definitivo @usuario [razón]", "-ban @Juan Spam", "Equipo Especial"))

    @ban.command(name='definitivo')
    @tiene_rol_equipo_especial()
    async def ban_definitivo(self, ctx, miembro: discord.Member, *, razon: str = "Sin razón"):
        if miembro.id == ctx.author.id:
            return await ctx.send(embed=embed_error("No puedes banearte a ti mismo."))
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.send(embed=embed_error("No tengo permiso para banear miembros en este servidor."))
        await db.add_to_blacklist(miembro.id, razon, ctx.author.id)
        await db.update_user_state(miembro.id, banned=True, ban_reason=razon, banned_by=ctx.author.id, ban_date=datetime.now().isoformat())
        await db.delete_dni(miembro.id)
        try:
            await ctx.guild.ban(miembro, reason=razon, delete_message_days=0)
            discord_ban = "✅ Baneado del servidor"
        except Exception as e:
            discord_ban = f"❌ Error al banear del servidor: {str(e)[:100]}"
        embed = discord.Embed(title="🔨 BANEO DEFINITIVO EJECUTADO", description=f"Usuario: {miembro.mention}\nRazón: {razon}\n{discord_ban}\n🖤 Añadido a la blacklist global.", color=0xFF0000)
        await ctx.send(embed=embed)
        await self.log("BAN_DEFINITIVO", f"{ctx.author.name} baneó permanentemente a {miembro.name}: {razon}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='unban')
    @tiene_rol_equipo_especial()
    async def unban(self, ctx, uid: int = None):
        if not uid:
            return await ctx.send(embed=embed_help("unban", "Desbanea a un usuario por su ID y lo elimina de la blacklist global.", "-unban <id>", "-unban 123456789012345678", "Equipo Especial"))
        await db.remove_from_blacklist(uid)
        await db.update_user_state(uid, banned=False, ban_reason=None)
        try:
            user = await self.bot.fetch_user(uid)
            await ctx.guild.unban(user)
            discord_unban = "✅ Desbaneado del servidor y eliminado de la blacklist"
        except discord.NotFound:
            discord_unban = "⚠️ Usuario no encontrado en Discord, pero eliminado de la blacklist."
        except Exception as e:
            discord_unban = f"❌ Error al desbanear: {str(e)[:100]}"
        embed = discord.Embed(title="✅ DESBANEO EJECUTADO", description=f"Usuario: {user.mention if 'user' in locals() else uid}\n{discord_unban}", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("UNBAN", f"{ctx.author.name} desbaneó ID: {uid} (eliminado de blacklist)")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='money')
    @tiene_rol_equipo_especial()
    async def money(self, ctx, accion: str = None, miembro: discord.Member = None, cantidad: int = None, tipo: str = "cash"):
        if not accion or not miembro or not cantidad:
            return await ctx.send(embed=embed_help("money", "Añade o quita dinero de un usuario (cash, bank o black).", "-money add/remove @usuario <cantidad> [tipo]", "-money add @Juan 5000", "Equipo Especial"))
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("La cantidad debe ser mayor a 0."))
        tipo = tipo.lower()
        if tipo not in ["cash", "bank", "black"]:
            return await ctx.send(embed=embed_error("Tipo inválido. Usa: cash, bank, black."))
        if accion.lower() == 'add':
            if tipo == "cash":
                await db.add_cash(miembro.id, cantidad)
            elif tipo == "bank":
                await db.add_bank(miembro.id, cantidad)
            else:
                await db.add_black(miembro.id, cantidad)
            await ctx.send(embed=embed_success(f"{await get_emoji('money')} Dinero añadido ({tipo})", f"**${cantidad:,}** a {miembro.mention}"))
            await self.log("MONEY_ADD", f"{ctx.author.name} dio ${cantidad:,} ({tipo}) a {miembro.name}")
        elif accion.lower() == 'remove':
            if tipo == "cash":
                eco = await db.get_economy(miembro.id)
                if eco['cash'] < cantidad:
                    return await ctx.send(embed=embed_error("Saldo insuficiente."))
                await db.add_cash(miembro.id, -cantidad)
            elif tipo == "bank":
                eco = await db.get_economy(miembro.id)
                if eco['bank'] < cantidad:
                    return await ctx.send(embed=embed_error("Saldo insuficiente en banco."))
                await db.add_bank(miembro.id, -cantidad)
            else:
                eco = await db.get_economy(miembro.id)
                if eco['black_money'] < cantidad:
                    return await ctx.send(embed=embed_error("Saldo insuficiente en dinero negro."))
                await db.add_black(miembro.id, -cantidad)
            await ctx.send(embed=embed_success(f"{await get_emoji('money')} Dinero removido ({tipo})", f"**${cantidad:,}** de {miembro.mention}", 0xFF6600))
            await self.log("MONEY_REMOVE", f"{ctx.author.name} quitó ${cantidad:,} ({tipo}) a {miembro.name}")
        else:
            await ctx.send(embed=embed_error("Acción debe ser `add` o `remove`."))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='setprefix')
    @tiene_rol_equipo_especial()
    async def setpre(self, ctx, p: str = None):
        if not p:
            return await ctx.send(embed=embed_help("setprefix", "Cambia el prefijo del bot en este servidor.", "-setprefix <nuevo_prefijo>", "-setprefix !", "Equipo Especial"))
        if len(p) > 5:
            return await ctx.send(embed=embed_error("Máximo 5 caracteres."))
        with open('prefixes.json', 'w') as f:
            json.dump({str(ctx.guild.id): p}, f)
        await ctx.send(embed=embed_success("✅ Prefijo cambiado", f"Nuevo prefijo: `{p}`"))
        await self.log("SETPREFIX", f"{ctx.author.name} cambió prefijo a '{p}'")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='add-inv')
    @tiene_rol_equipo_especial()
    async def addinv(self, ctx, miembro: discord.Member = None, tipo: str = None, item: str = None, cantidad: int = 1):
        if not miembro or not tipo or not item:
            return await ctx.send(embed=embed_help("add-inv", "Añade un item al inventario de un usuario.", "-add-inv @usuario <tipo> <item> [cantidad]", "-add-inv @Juan personal Pistola 1", "Equipo Especial"))
        t = tipo.lower()
        if t not in ['personal', 'vehiculo', 'propiedad', 'negocios']:
            return await ctx.send(embed=embed_error("Tipo inválido. Usa: personal, vehiculo, propiedad, negocios"))
        await db.add_item(miembro.id, t, item, cantidad)
        await ctx.send(embed=embed_success("✅ Item añadido", f"{cantidad}x {item} a {miembro.mention} ({t})"))
        await self.log("ADD_INV", f"{ctx.author.name} añadió {cantidad}x {item} ({t}) a {miembro.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='rem-inv')
    @tiene_rol_equipo_especial()
    async def reminv(self, ctx, miembro: discord.Member = None, tipo: str = None, item: str = None, cantidad: int = 1):
        if not miembro or not tipo or not item:
            return await ctx.send(embed=embed_help("rem-inv", "Elimina un item del inventario de un usuario.", "-rem-inv @usuario <tipo> <item> [cantidad]", "-rem-inv @Juan personal Pistola 1", "Equipo Especial"))
        t = tipo.lower()
        if t not in ['personal', 'vehiculo', 'propiedad', 'negocios']:
            return await ctx.send(embed=embed_error("Tipo inválido. Usa: personal, vehiculo, propiedad, negocios"))
        eliminado = await db.remove_item(miembro.id, t, item, cantidad)
        if eliminado == 0:
            return await ctx.send(embed=embed_error(f"{miembro.name} no tiene {item} en {t}."))
        await ctx.send(embed=embed_success("🗑️ Item eliminado", f"{eliminado}x {item} de {miembro.mention} ({t})", 0xFF6600))
        await self.log("REM_INV", f"{ctx.author.name} eliminó {eliminado}x {item} ({t}) de {miembro.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='add-coche')
    @tiene_rol_equipo_especial()
    async def addcar(self, ctx, miembro: discord.Member = None, modelo: str = None):
        if not miembro or not modelo:
            return await ctx.send(embed=embed_help("add-coche", "Registra un vehículo para un usuario (matrícula aleatoria).", "-add-coche @usuario <modelo>", "-add-coche @Juan Turismo", "Equipo Especial"))
        matricula = f"{random.randint(1000,9999)} {''.join(random.choices('BCDFGHJKLMNPQRSTVWXYZ', k=3))}"
        await db.add_vehiculo(miembro.id, matricula, modelo)
        embed = discord.Embed(title="✅ VEHÍCULO REGISTRADO", description=f"Modelo: {modelo}\nMatrícula: {matricula}\nPropietario: {miembro.mention}", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("ADD_COCHE", f"{ctx.author.name} añadió {modelo} ({matricula}) a {miembro.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='remove-coche')
    @tiene_rol_equipo_especial()
    async def remcar(self, ctx, miembro: discord.Member = None, matricula: str = None):
        if not miembro or not matricula:
            return await ctx.send(embed=embed_help("remove-coche", "Elimina un vehículo de un usuario por matrícula.", "-remove-coche @usuario <matrícula>", "-remove-coche @Juan 1234 ABC", "Equipo Especial"))
        await db.execute("DELETE FROM vehiculos WHERE user_id = ? AND matricula = ?", (miembro.id, matricula))
        await ctx.send(embed=embed_success("🗑️ Vehículo eliminado", f"Matrícula {matricula} de {miembro.mention}", 0xFF6600))
        await self.log("REM_COCHE", f"{ctx.author.name} quitó {matricula} a {miembro.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='add-droga')
    @tiene_rol_equipo_especial()
    async def adddrg(self, ctx, miembro: discord.Member = None, tipo: str = None, cantidad: int = 1):
        if not miembro or not tipo:
            return await ctx.send(embed=embed_help("add-droga", "Añade droga al inventario personal de un usuario.", "-add-droga @usuario <tipo> [cantidad]", "-add-droga @Juan Marihuana 5", "Equipo Especial"))
        tipo_norm = tipo.capitalize()
        if tipo_norm not in EMOJIS_DROGA:
            return await ctx.send(embed=embed_error(f"Tipo no válido. Opciones: {', '.join(EMOJIS_DROGA.keys())}"))
        await db.add_item(miembro.id, "personal", tipo_norm, cantidad)
        await ctx.send(embed=embed_success("✅ Droga añadida", f"{cantidad}x {tipo_norm} a {miembro.mention}"))
        await self.log("ADD_DROGA", f"{ctx.author.name} añadió {cantidad}x {tipo_norm} a {miembro.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='add-licencia')
    @tiene_rol_equipo_especial()
    async def addlicencia(self, ctx, miembro: discord.Member = None, licencia: str = None):
        if not miembro or not licencia:
            return await ctx.send(embed=embed_help("add-licencia", "Otorga una licencia de armas.", "-add-licencia @usuario <tipo_licencia>", "-add-licencia @Juan licencia_pistola", "Equipo Especial"))
        await db.dar_licencia(miembro.id, licencia.lower())
        await ctx.send(embed=embed_success("✅ Licencia otorgada", f"{licencia} a {miembro.mention}"))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='rem-licencia')
    @tiene_rol_equipo_especial()
    async def remlicencia(self, ctx, miembro: discord.Member = None, licencia: str = None):
        if not miembro or not licencia:
            return await ctx.send(embed=embed_help("rem-licencia", "Revoca una licencia de armas.", "-rem-licencia @usuario <tipo_licencia>", "-rem-licencia @Juan licencia_pistola", "Equipo Especial"))
        await db.quitar_licencia(miembro.id, licencia.lower())
        await ctx.send(embed=embed_success("🗑️ Licencia revocada", f"{licencia} a {miembro.mention}", 0xFF6600))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='quitar-warn')
    @tiene_rol_equipo_especial()
    async def quitar_warn(self, ctx, miembro: discord.Member = None, id_warn: int = None):
        if not miembro or not id_warn:
            return await ctx.send(embed=embed_help("quitar-warn", "Elimina una advertencia de un usuario por su ID.", "-quitar-warn @usuario <id_warn>", "-quitar-warn @Juan 3", "Equipo Especial"))
        row = await db.fetchone("SELECT id FROM warnings WHERE id = ? AND user_id = ?", (id_warn, miembro.id))
        if not row:
            return await ctx.send(embed=embed_error("Advertencia no encontrada."))
        await db.execute("DELETE FROM warnings WHERE id = ?", (id_warn,))
        await self.registrar_log_moderacion(ctx, f"WARN #{id_warn} ELIMINADA", miembro, "Eliminada por administrador")
        await ctx.send(embed=embed_success("🗑️ Advertencia eliminada", f"Se eliminó la advertencia #{id_warn} de {miembro.mention}.", 0xFF6600))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='economy-reset')
    @tiene_rol_equipo_especial()
    async def economy_reset(self, ctx, target: str = None, cantidad: int = 0):
        if not target:
            return await ctx.send(embed=embed_help("economy-reset", "Resetea la economía de un usuario o de todos los miembros con un rol.", "-economy-reset @usuario [cantidad]\n-economy-reset @rol [cantidad]", "-economy-reset @Juan 1000\n-economy-reset @Nuevos 500", "Equipo Especial"))
        if cantidad < 0:
            return await ctx.send(embed=embed_error("La cantidad no puede ser negativa."))
        try:
            user = await commands.MemberConverter().convert(ctx, target)
            await db.execute("UPDATE economy SET cash = ?, bank = ?, black_money = ? WHERE user_id = ?", (cantidad, cantidad, cantidad, user.id))
            await ctx.send(embed=embed_success("✅ Economía reseteada", f"Se ha reseteado la economía de {user.mention} a **${cantidad:,}**."))
            await self.log("ECONOMY_RESET", f"{ctx.author.name} reseteó economía de {user.name} a ${cantidad}")
            return
        except commands.BadArgument:
            pass
        try:
            role = await commands.RoleConverter().convert(ctx, target)
            members = [m for m in ctx.guild.members if role in m.roles and not m.bot]
            if not members:
                return await ctx.send(embed=embed_error(f"No hay miembros con el rol {role.mention}."))
            view = ConfirmView(ctx.author.id)
            embed_confirm = discord.Embed(title="⚠️ Confirmar reseteo masivo", description=f"¿Estás seguro de que quieres resetear la economía de **{len(members)}** miembros con el rol {role.mention} a **${cantidad:,}**?", color=0xFFA500)
            await ctx.send(embed=embed_confirm, view=view)
            await view.wait()
            if not view.value:
                return await ctx.send(embed=embed_info("Operación cancelada."))
            for member in members:
                await db.execute("UPDATE economy SET cash = ?, bank = ?, black_money = ? WHERE user_id = ?", (cantidad, cantidad, cantidad, member.id))
            await ctx.send(embed=embed_success("✅ Economías reseteadas", f"Se ha reseteado la economía de {len(members)} miembros a **${cantidad:,}**."))
            await self.log("ECONOMY_RESET_MASS", f"{ctx.author.name} reseteó economía de {len(members)} miembros con rol {role.name} a ${cantidad}")
            return
        except commands.BadArgument:
            pass
        await ctx.send(embed=embed_error("No se encontró un usuario o rol con ese nombre. Usa @usuario o @rol."))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='reset-user')
    @tiene_rol_equipo_especial()
    async def reset_user(self, ctx, miembro: discord.Member, flags: str = ""):
        uid = miembro.id
        full_reset = "--full" in flags.lower()
        try:
            await db.execute("UPDATE economy SET cash=0, bank=0, black_money=0 WHERE user_id=?", (uid,))
            await db.execute("DELETE FROM inventory WHERE user_id=?", (uid,))
            await db.execute("DELETE FROM vehiculos WHERE user_id=?", (uid,))
            await db.execute("DELETE FROM armas_equipadas WHERE user_id=?", (uid,))
            await db.execute("DELETE FROM armas_licencias WHERE user_id=?", (uid,))
            await db.execute("DELETE FROM multas WHERE user_id=? AND pagada=0", (uid,))
            await db.update_user_state(uid, encarcelado_hasta=None)
            if full_reset:
                await db.delete_dni(uid)
            embed = discord.Embed(title="✅ Usuario Reseteado", color=discord.Color.green())
            embed.add_field(name="Limpiado", value="Dinero, Inventario, Vehículos, Armas, Multas", inline=False)
            embed.add_field(name="Mantenido", value="PDA, Nivel, DNI (a menos que --full)", inline=False)
            await ctx.send(embed=embed)
            await self.log("RESET_USER", f"{ctx.author.name} reseteó {miembro.name}")
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error: {str(e)[:100]}"))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='create-item')
    @tiene_rol_equipo_especial()
    async def create_item(self, ctx, nombre: str, precio, emoji: str, *, descripcion: str = ""):
        global TIENDA_ITEMS_FULL, TIENDA_ITEMS_DICT
        nombre = nombre.strip()
        if not nombre:
            return await ctx.send(embed=embed_error("Debes especificar un nombre para el item."))
        if isinstance(precio, str) and precio.upper() == "INFINITY":
            precio = PRECIO_INFINITO
        else:
            try:
                precio = int(precio)
                if precio <= 0:
                    raise ValueError
            except ValueError:
                return await ctx.send(embed=embed_error("El precio debe ser un número positivo o INFINITY."))
        if len(emoji) > 2:
            emoji = emoji[:2]
        if nombre.lower() in TIENDA_ITEMS_DICT:
            return await ctx.send(embed=embed_error(f"Ya existe un item con nombre '{nombre}'. Usa otro nombre."))
        custom_items = []
        if os.path.exists(CUSTOM_ITEMS_FILE):
            with open(CUSTOM_ITEMS_FILE, "r", encoding="utf-8") as f:
                custom_items = json.load(f)
        custom_items.append([nombre, precio, emoji, descripcion])
        with open(CUSTOM_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_items, f, indent=2, ensure_ascii=False)
        TIENDA_ITEMS_FULL = TIENDA_ITEMS_BASE + custom_items
        TIENDA_ITEMS_DICT = {name.lower(): (name, pr, em, desc) for name, pr, em, desc in TIENDA_ITEMS_FULL}
        embed = discord.Embed(title=f"{await get_emoji('shop')} Item creado", description=f"**{nombre}** agregado a la tienda con precio {formatear_precio(precio)} {emoji}\nDescripción: {descripcion if descripcion else 'Sin descripción'}", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("CREATE_ITEM", f"{ctx.author.name} creó item '{nombre}' ({formatear_precio(precio)})")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='delete-item')
    @tiene_rol_equipo_especial()
    async def delete_item(self, ctx, *, nombre: str):
        global TIENDA_ITEMS_FULL, TIENDA_ITEMS_DICT
        nombre = nombre.strip()
        if not nombre:
            return await ctx.send(embed=embed_error("Debes especificar el nombre del item a eliminar."))
        for item in TIENDA_ITEMS_BASE:
            if item[0].lower() == nombre.lower():
                return await ctx.send(embed=embed_error("No puedes eliminar un item estándar. Solo items personalizados."))
        if not os.path.exists(CUSTOM_ITEMS_FILE):
            return await ctx.send(embed=embed_error("No hay items personalizados."))
        with open(CUSTOM_ITEMS_FILE, "r", encoding="utf-8") as f:
            custom_items = json.load(f)
        original_len = len(custom_items)
        new_custom = [item for item in custom_items if item[0].lower() != nombre.lower()]
        if len(new_custom) == original_len:
            return await ctx.send(embed=embed_error(f"No se encontró el item personalizado '{nombre}'."))
        with open(CUSTOM_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(new_custom, f, indent=2, ensure_ascii=False)
        TIENDA_ITEMS_FULL = TIENDA_ITEMS_BASE + new_custom
        TIENDA_ITEMS_DICT = {name.lower(): (name, pr, em, desc) for name, pr, em, desc in TIENDA_ITEMS_FULL}
        embed = discord.Embed(title="✅ Item eliminado", description=f"**{nombre}** ha sido eliminado de la tienda.", color=0xFF6600)
        await ctx.send(embed=embed)
        await self.log("DELETE_ITEM", f"{ctx.author.name} eliminó item '{nombre}'")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='give-item')
    @tiene_rol_equipo_especial()
    async def give_item(self, ctx, miembro: discord.Member, item: str, cantidad: int = 1):
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("La cantidad debe ser mayor a 0."))
        await db.add_item(miembro.id, "personal", item, cantidad)
        embed = discord.Embed(title="✅ Item regalado", description=f"{cantidad}x **{item}** entregado a {miembro.mention}.", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("GIVE_ITEM", f"{ctx.author.name} dio {cantidad}x {item} a {miembro.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='take-item')
    @tiene_rol_equipo_especial()
    async def take_item(self, ctx, miembro: discord.Member, item: str, cantidad: int = 1):
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("La cantidad debe ser mayor a 0."))
        eliminado = await db.remove_item(miembro.id, "personal", item, cantidad)
        if eliminado == 0:
            return await ctx.send(embed=embed_error(f"{miembro.mention} no tiene {item} o cantidad insuficiente."))
        embed = discord.Embed(title="🗑️ Item quitado", description=f"{eliminado}x **{item}** quitado a {miembro.mention}.", color=0xFF6600)
        await ctx.send(embed=embed)
        await self.log("TAKE_ITEM", f"{ctx.author.name} quitó {eliminado}x {item} a {miembro.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='mass-economy')
    @tiene_rol_equipo_especial()
    async def mass_economy(self, ctx, rol: discord.Role, cantidad: int):
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("La cantidad debe ser mayor a 0."))
        miembros = [m for m in ctx.guild.members if rol in m.roles and not m.bot]
        if not miembros:
            return await ctx.send(embed=embed_error(f"No hay miembros con el rol {rol.mention}."))
        view = ConfirmView(ctx.author.id)
        embed_confirm = discord.Embed(title="⚠️ Confirmar asignación masiva", description=f"¿Estás seguro de que quieres dar **${cantidad:,}** a **{len(miembros)}** miembros con el rol {rol.mention}?", color=0xFFA500)
        await ctx.send(embed=embed_confirm, view=view)
        await view.wait()
        if not view.value:
            return await ctx.send(embed=embed_info("Operación cancelada."))
        for member in miembros:
            await db.add_cash(member.id, cantidad)
        embed = discord.Embed(title="✅ Asignación masiva completada", description=f"Se ha dado **${cantidad:,}** a **{len(miembros)}** miembros con el rol {rol.mention}.", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("MASS_ECONOMY", f"{ctx.author.name} dio ${cantidad} a {len(miembros)} miembros con rol {rol.name}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='purge')
    @tiene_rol_equipo_especial()
    async def purge(self, ctx, cantidad: int = None):
        if not cantidad or cantidad <= 0:
            return await ctx.send(embed=embed_help("purge", "Elimina mensajes en el canal.", "-purge <cantidad>", "-purge 10", "Equipo Especial"))
        cantidad = min(cantidad, 100)
        await ctx.channel.purge(limit=cantidad + 1)
        await ctx.send(embed=embed_success("🗑️ Mensajes eliminados", f"Se han eliminado {cantidad} mensajes."), delete_after=5)

    @commands.command(name='editar-item')
    @tiene_rol_equipo_especial()
    async def editar_item(self, ctx, *, nombre_item: str):
        global TIENDA_ITEMS_FULL, TIENDA_ITEMS_DICT
        nombre_item = nombre_item.strip()
        item_data = TIENDA_ITEMS_DICT.get(nombre_item.lower())
        if not item_data:
            await ctx.send(embed=embed_error("***No se encontró el item especificado.***"))
            return
        item_original = item_data

        view = EditarItemView(ctx.author.id, nombre_item, item_original)
        embed = discord.Embed(
            title="📝 ***Editar Item***",
            description=f"***Selecciona qué deseas modificar de `{nombre_item}`.***",
            color=0x3498DB
        )
        await ctx.send(embed=embed, view=view)
        try:
            await ctx.message.delete()
        except:
            pass

class EditarItemView(discord.ui.View):
    def __init__(self, user_id, item_name, item_data):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.item_name = item_name
        self.item_data = item_data

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("***No eres el dueño de esta solicitud.***", ephemeral=True)
            return False
        return True

    @discord.ui.select(placeholder="***Selecciona una opción***", options=[
        discord.SelectOption(label="***Editar Nombre***", value="nombre"),
        discord.SelectOption(label="***Editar Precio***", value="precio"),
        discord.SelectOption(label="***Editar Descripción***", value="descripcion"),
    ])
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        opcion = select.values[0]
        if opcion == "nombre":
            modal = EditarNombreModal(self.item_name, self.item_data)
            await interaction.response.send_modal(modal)
        elif opcion == "precio":
            modal = EditarPrecioModal(self.item_name, self.item_data)
            await interaction.response.send_modal(modal)
        elif opcion == "descripcion":
            modal = EditarDescripcionModal(self.item_name, self.item_data)
            await interaction.response.send_modal(modal)

class EditarNombreModal(discord.ui.Modal, title="***Editar Nombre del Item***"):
    def __init__(self, item_name, item_data):
        super().__init__()
        self.item_name = item_name
        self.item_data = item_data
    nuevo_nombre = discord.ui.TextInput(label="***Nuevo nombre***", placeholder="Ej: Súper Hacha", max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        global TIENDA_ITEMS_FULL, TIENDA_ITEMS_DICT
        nuevo = self.nuevo_nombre.value.strip()
        if not nuevo:
            await interaction.response.send_message("***El nombre no puede estar vacío.***", ephemeral=True)
            return
        if nuevo.lower() in TIENDA_ITEMS_DICT and nuevo.lower() != self.item_name.lower():
            await interaction.response.send_message("***Ya existe un item con ese nombre.***", ephemeral=True)
            return
        custom_items = []
        if os.path.exists(CUSTOM_ITEMS_FILE):
            with open(CUSTOM_ITEMS_FILE, "r", encoding="utf-8") as f:
                custom_items = json.load(f)
        encontrado = False
        for i, ci in enumerate(custom_items):
            if ci[0].lower() == self.item_name.lower():
                custom_items[i][0] = nuevo
                encontrado = True
                break
        if not encontrado:
            custom_items.append([nuevo, self.item_data[1], self.item_data[2], self.item_data[3]])
        with open(CUSTOM_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_items, f, indent=2, ensure_ascii=False)
        TIENDA_ITEMS_FULL = list(TIENDA_ITEMS_BASE) + [tuple(c) for c in custom_items]
        TIENDA_ITEMS_DICT = {name.lower(): (name, pr, em, desc) for name, pr, em, desc in TIENDA_ITEMS_FULL}
        await interaction.response.send_message(f"***Nombre del item actualizado a `{nuevo}`.***", ephemeral=True)

class EditarPrecioModal(discord.ui.Modal, title="***Editar Precio del Item***"):
    def __init__(self, item_name, item_data):
        super().__init__()
        self.item_name = item_name
        self.item_data = item_data
    nuevo_precio = discord.ui.TextInput(label="***Nuevo precio***", placeholder="Ej: 1500 o INFINITY", max_length=12)

    async def on_submit(self, interaction: discord.Interaction):
        global TIENDA_ITEMS_FULL, TIENDA_ITEMS_DICT
        precio_str = self.nuevo_precio.value.strip().upper()
        if precio_str == "INFINITY":
            nuevo = PRECIO_INFINITO
        else:
            try:
                nuevo = int(precio_str)
                if nuevo <= 0:
                    raise ValueError
            except ValueError:
                await interaction.response.send_message("***El precio debe ser un número entero positivo o INFINITY.***", ephemeral=True)
                return
        custom_items = []
        if os.path.exists(CUSTOM_ITEMS_FILE):
            with open(CUSTOM_ITEMS_FILE, "r", encoding="utf-8") as f:
                custom_items = json.load(f)
        encontrado = False
        for i, ci in enumerate(custom_items):
            if ci[0].lower() == self.item_name.lower():
                custom_items[i][1] = nuevo
                encontrado = True
                break
        if not encontrado:
            custom_items.append([self.item_name, nuevo, self.item_data[2], self.item_data[3]])
        with open(CUSTOM_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_items, f, indent=2, ensure_ascii=False)
        TIENDA_ITEMS_FULL = list(TIENDA_ITEMS_BASE) + [tuple(c) for c in custom_items]
        TIENDA_ITEMS_DICT = {name.lower(): (name, pr, em, desc) for name, pr, em, desc in TIENDA_ITEMS_FULL}
        await interaction.response.send_message(f"***Precio del item actualizado a {formatear_precio(nuevo)}.***", ephemeral=True)

class EditarDescripcionModal(discord.ui.Modal, title="***Editar Descripción del Item***"):
    def __init__(self, item_name, item_data):
        super().__init__()
        self.item_name = item_name
        self.item_data = item_data
    nueva_desc = discord.ui.TextInput(label="***Nueva descripción***", placeholder="Describe el item", style=discord.TextStyle.paragraph, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        global TIENDA_ITEMS_FULL, TIENDA_ITEMS_DICT
        nueva = self.nueva_desc.value.strip()
        if not nueva:
            nueva = "Sin descripción"
        custom_items = []
        if os.path.exists(CUSTOM_ITEMS_FILE):
            with open(CUSTOM_ITEMS_FILE, "r", encoding="utf-8") as f:
                custom_items = json.load(f)
        encontrado = False
        for i, ci in enumerate(custom_items):
            if ci[0].lower() == self.item_name.lower():
                custom_items[i][3] = nueva
                encontrado = True
                break
        if not encontrado:
            custom_items.append([self.item_name, self.item_data[1], self.item_data[2], nueva])
        with open(CUSTOM_ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(custom_items, f, indent=2, ensure_ascii=False)
        TIENDA_ITEMS_FULL = list(TIENDA_ITEMS_BASE) + [tuple(c) for c in custom_items]
        TIENDA_ITEMS_DICT = {name.lower(): (name, pr, em, desc) for name, pr, em, desc in TIENDA_ITEMS_FULL}
        await interaction.response.send_message(f"***Descripción del item actualizada.***", ephemeral=True)

# ==================== COG: Roleplay ====================
class Roleplay(BaseCog):
    @commands.command(name='me')
    @tiene_rol_usuario()
    async def me(self, ctx, *, accion: str):
        try:
            nombre = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
            embed = discord.Embed(description=f"✦ **{nombre}** {accion.strip()}", color=discord.Color.purple(), timestamp=datetime.now())
            embed.set_author(name="⚔️ Acción", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -me: {str(e)[:100]}"))

    @commands.command(name='do')
    @tiene_rol_usuario()
    async def do(self, ctx, *, pensamiento: str):
        try:
            nombre = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
            embed = discord.Embed(description=f"💭 *{nombre} piensa: \"{pensamiento.strip()}\"*", color=0x1ABC9C, timestamp=datetime.now())
            embed.set_author(name="💭 Pensamiento", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -do: {str(e)[:100]}"))

    @commands.command(name='entorno')
    @tiene_rol_usuario()
    async def entorno(self, ctx, *, descripcion: str):
        try:
            rol_lspd = ctx.guild.get_role(ROL_LSPD_ID)
            if rol_lspd:
                await ctx.send(f"🚨 **NUEVO AVISO CIUDADANO RECIBIDO** 🚨\n{rol_lspd.mention}")
            partes = descripcion.split("|", 1)
            desc = partes[0].strip()
            lugar = partes[1].strip().upper() if len(partes) > 1 else "Desconocida"
            embed = discord.Embed(title="🌍 ALERTA DE ENTORNO", description=f"**📍 Ubicación:** {lugar}\n**📞 Información:** {desc}\n**🕒 Hora:** {datetime.now().strftime('%H:%M')}\n**🚓 Unidades requeridas:** Todas disponibles", color=0xFF4500, timestamp=datetime.now())
            embed.set_author(name="Narrador del Entorno", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -entorno: {str(e)[:100]}"))

    @commands.command(name='reparar')
    @tiene_profesion("mecánico", "mecanico")
    @tiene_rol_usuario()
    async def reparar(self, ctx, objetivo: discord.Member, *, descripcion: str = "Reparación completada."):
        try:
            nombre_mec = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
            nombre_obj = await self.obtener_nombre_dni(objetivo.id) or objetivo.display_name
            embed = discord.Embed(title="🔧 REPARACIÓN COMPLETADA", description=f"**{nombre_mec}** ha reparado el vehículo de **{nombre_obj}**.\n\n*{descripcion.strip()}*", color=0xE67E22, timestamp=datetime.now())
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -reparar: {str(e)[:100]}"))

    @commands.command(name='curar')
    @tiene_profesion("médico", "medico", "doctor", "enfermero", "ems")
    @tiene_rol_usuario()
    async def curar(self, ctx, objetivo: discord.Member, *, descripcion: str = "Tratamiento completado."):
        try:
            nombre_med = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
            nombre_obj = await self.obtener_nombre_dni(objetivo.id) or objetivo.display_name
            embed = discord.Embed(title="🏥 CURACIÓN COMPLETADA", description=f"**{nombre_med}** ha atendido a **{nombre_obj}**.\n\n*{descripcion.strip()}*", color=0x2ECC71, timestamp=datetime.now())
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -curar: {str(e)[:100]}"))

# ==================== COG: Hosting ====================
class Hosting(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot_active = False

    @commands.command(name='bot', aliases=['Bot'])
    @is_owner()
    async def hosting_comando(self, ctx, dias: int = None):
        if dias is None:
            expiry = await db.get_expiry()
            if expiry and self.bot_active:
                tiempo_restante = expiry - datetime.now()
                dias_restantes = tiempo_restante.days
                horas_restantes = tiempo_restante.seconds // 3600
                embed = discord.Embed(
                    title="✅ Bot activo",
                    description=f"**Estado:** Activo ✓\n\n"
                                f"**Expira:** <t:{int(expiry.timestamp())}:F>\n"
                                f"**Tiempo restante:** {dias_restantes}d {horas_restantes}h"
                                f"\n\n**Renovar:** `{ctx.prefix}bot <días>` (máx 30).",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
            elif expiry and not self.bot_active:
                embed = discord.Embed(
                    title="⏰ Bot expirado",
                    description=f"El bot expiró el <t:{int(expiry.timestamp())}:F>.\n\n"
                                f"**Reactivar:** `{ctx.prefix}bot <días>` (máx 30).",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
            else:
                embed = discord.Embed(
                    title="⚠️ Bot no configurado",
                    description=f"Usa `{ctx.prefix}bot <días>` (máx 30) para activar el bot.\n\n"
                                f"**Ejemplo:** `{ctx.prefix}bot 5` (activa por 5 días).",
                    color=discord.Color.orange(),
                    timestamp=datetime.now()
                )
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
            return
        if dias < 1:
            return await ctx.send(embed=embed_error("❌ Debes especificar al menos 1 día."))
        if dias > 30:
            return await ctx.send(embed=embed_error("❌ No puedes activar por más de 30 días."))
        nueva_expiry = datetime.now() + timedelta(days=dias)
        await db.set_expiry(nueva_expiry)
        self.bot_active = True
        embed = discord.Embed(
            title="✅ Bot activado con éxito",
            description=f"**Duración:** {dias} días\n"
                       f"**Expira:** <t:{int(nueva_expiry.timestamp())}:F>\n\n"
                       f"El bot seguirá activo incluso si cierras el programa (a menos que lo actualices).",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text="Para detener: Cierra la terminal manualmente")
        await ctx.send(embed=embed)
        await self.log("HOSTING", f"{ctx.author.name} activó el bot por {dias} días. Expira: {nueva_expiry}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='bot-off', aliases=['Bot-off', 'botoff', 'botStop', 'botstop'])
    @is_owner()
    async def botoff_comando(self, ctx):
        embed = discord.Embed(
            title="⛔ Bot detenido",
            description="El bot se está apagando...\nNota: Para que el bot funcione 24/7 necesita un servidor o VPS encendido. Si el PC está apagado, no puede ejecutarse hasta que se encienda de nuevo.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await ctx.send(embed=embed)
        await self.log("HOSTING", f"{ctx.author.name} detuvo el bot manualmente.")
        await asyncio.sleep(1)
        await self.bot.close()

    @tasks.loop(hours=1)
    async def check_expiry(self):
        expiry = await db.get_expiry()
        if expiry:
            if datetime.now() < expiry:
                self.bot_active = True
                print(f"✅ Bot activo - Expira: {expiry}")
            else:
                self.bot_active = False
                print(f"❌ Bot expirado - Última expiración: {expiry}")
                await self.log("HOSTING", "⏰ El bot ha expirado. Desactivado.")
        else:
            self.bot_active = False

    @check_expiry.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()
        expiry = await db.get_expiry()
        if expiry and datetime.now() < expiry:
            self.bot_active = True
            print(f"✅ Bot reactivado al iniciar - Expira: {expiry}")
        else:
            self.bot_active = False
            if expiry:
                print(f"❌ Bot ha expirado - Última expiración fue: {expiry}")

# ==================== COG: Soporte ====================
class Soporte(BaseCog):
    @commands.command(name='status')
    @tiene_rol_iniciador()
    async def status(self, ctx, iniciador: str = None, ciudadanos: int = None, policias: int = None, soporte: int = 0):
        if iniciador is None or ciudadanos is None or policias is None:
            embed = embed_help("status", "Publica el estado de la sesión de rol en el canal actual.", "-status <iniciador> <ciudadanos> <policías> [soporte]", "-status Juan 10 5 2", "Iniciador de rol")
            return await ctx.send(embed=embed)
        if any(x < 0 for x in [ciudadanos, policias, soporte]):
            return await ctx.send(embed=embed_error("Los números no pueden ser negativos."))
        total = ciudadanos + policias + soporte
        embed = discord.Embed(title="🚨 ESTAMOS EN ROL 🚨", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="📌 Iniciador:", value=f"```\n{iniciador}\n```", inline=False)
        embed.add_field(name="🧑 Personas en rol:", value=f"```\n{ciudadanos}\n```", inline=False)
        embed.add_field(name="🚔 Policías en rol:", value=f"```\n{policias}\n```", inline=False)
        embed.add_field(name="🛠️ Soporte en rol:", value=f"```\n{soporte}\n```", inline=False)
        embed.add_field(name="📊 Total en sesión:", value=f"```\n{total}\n```", inline=False)
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzFwNGl2ajRzM3p4d2Zmd2Z5cGxvbjE2dHJlZnYxM2ZkMjZzNjZ5bCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/6T7IlHrbxl7MOye7Hn/giphy.gif")
        embed.set_footer(text=f"Soporte: {ctx.author.display_name}  ·  NOVA AGORA", icon_url=ctx.author.display_avatar.url)
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(content=f"<@&{ROL_USUARIO_ID}>", embed=embed)
        await self.log("STATUS", f"{ctx.author.name} — {iniciador} | {ciudadanos}p {policias}pol {soporte}sop")

    @commands.command(name='votacion')
    @tiene_rol_iniciador()
    async def votacion(self, ctx, hora: str = None, *, tema: str = None):
        if not hora:
            embed = embed_help("votacion", "Crea una votación de rol en el canal actual con reacciones.", "-votacion <hora> [tema]", "-votacion 20:00", "Iniciador de rol")
            return await ctx.send(embed=embed)
        try:
            datetime.strptime(hora, "%H:%M")
        except (ValueError, TypeError):
            return await ctx.send(embed=embed_error("Hora inválida. Formato: HH:MM"))
        try:
            await ctx.message.delete()
        except:
            pass
        await self._publicar_votacion(ctx.channel, ctx.author, {"hora": hora, "tema": tema})

    async def _publicar_votacion(self, canal, autor, datos):
        embed = discord.Embed(title="📌 VOTACIÓN DE ROL 📌", color=discord.Color.blue(), timestamp=datetime.now())
        embed.add_field(name="📌 → Hora:", value=f"```\n{datos['hora']}\n```", inline=False)
        if datos.get("tema"):
            embed.add_field(name="📝 → Tema:", value=f"```\n{datos['tema']}\n```", inline=False)
        embed.add_field(name="\u200b", value="✅ → **Si te vas a unir.**\n🚔 → **Si te unes como policía.**\n❌ → **No te unes.**\n😅 → **Si te vas a unir tarde.**", inline=False)
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzFwNGl2ajRzM3p4d2Zmd2Z5cGxvbjE2dHJlZnYxM2ZkMjZzNjZ5bCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/6T7IlHrbxl7MOye7Hn/giphy.gif")
        embed.set_footer(text=f"Soporte: {autor.display_name}  ·  NOVA AGORA", icon_url=autor.display_avatar.url)
        msg = await canal.send(content="@rol", embed=embed)
        for emoji in ["✅", "🚔", "❌", "😅"]:
            await msg.add_reaction(emoji)
        await self.log("VOTACION", f"{autor.name} → {datos['hora']}")

    @commands.command(name='cierre-rol')
    @tiene_rol_iniciador()
    async def cierre_rol(self, ctx):
        canal_votacion = ctx.guild.get_channel(1450592843751100622)
        rol_usuario = ctx.guild.get_role(ROL_USUARIO_ID)
        mensaje = (
            "@everyone\n\n"
            "# 📢 CIERRE DE ROL\n\n"
            "El rol de hoy ha finalizado.\n"
            "Se ha cerrado el rol por el momento.\n\n"
            f"🗳️ **Vota aquí:** {canal_votacion.mention if canal_votacion else 'Canal 1450592843751100622'}\n\n"
            "Gracias por participar.\n\n"
            "🇪🇸 Estate atento a las próximas aperturas programadas para las 16:00 (hora española).\n\n"
            "Cuantos más usuarios participen, más actividad y rol tendremos mañana.\n\n"
            f"{rol_usuario.mention if rol_usuario else '<@&1450592204849418294>'}"
        )
        await ctx.send(mensaje)
        try:
            await ctx.message.delete()
        except:
            pass
        await self.log("CIERRE_ROL", f"{ctx.author.display_name if ctx.author else 'Desconocido'} cerró el rol")

# ==================== COG: Ayuda ====================
class Ayuda(BaseCog):
    CATEGORIAS = {
        "roleplay": {"emoji": "🚔", "nombre": "Roleplay", "comandos": [("-me <acción>", "Acción en primera persona"), ("-do <pensamiento>", "Pensamiento en voz alta"), ("-entorno <descripción> [| lugar]", "Describe el entorno y alerta a LSPD"), ("-reparar @user [desc]", "Repara un vehículo (mecánico)"), ("-curar @user [desc]", "Cura a un paciente (médico)")]},
        "economia": {"emoji": "🏦", "nombre": "Economía", "comandos": [("-banco", "Gestiona tu dinero"), ("-balance-top", "Top de dinero"), ("-blanquear", "Convierte gramos de droga (solo MAFIA)"), ("-inv [tipo]", "Muestra inventario"), ("-tienda", "Compra items"), ("-comprar <item> [cantidad]", "Compra artículo"), ("-comprar-licencia <tipo>", "Compra licencias"), ("-licencia [@usuario]", "Ver licencias"), ("-use <item>", "Usa un item"), ("-intercambio @user <cantidad> <item>", "Da items"), ("-mover <item> <cant> <origen> <destino>", "Mueve items")]},
        "trabajos": {"emoji": "💼", "nombre": "Trabajos", "comandos": [("-trabajo", "Simula jornada laboral"), ("-bus", "Conduce autobús [AUTOBUSERO]"), ("-chatarrero", "Recolecta chatarra [CHATARRERO]"), ("-minar", "Extrae minerales [MINERO]"), ("-terminar-trabajo", "Finaliza trabajo")]},
        "atracos": {"emoji": "🏴", "nombre": "Atracos", "comandos": [("-rob", "Ver atracos"), ("-rob badu", "Badu"), ("-rob yellowjack", "Yellow Jack"), ("-rob ammu", "Ammu-Nation"), ("-rob vanilla", "Vanilla Unicorn"), ("-rob yate", "Yate"), ("-rob centro", "Centro Comercial"), ("-rob joyeria", "Joyería"), ("-rob paleto", "Banco Paleto"), ("-rob central", "Banco Central"), ("-rob pacific", "Pacific Bank (requiere 8 prep)"), ("-rob status", "Estado de atracos")]},
        "preparatorias": {"emoji": "🏴", "nombre": "Preparatorias", "comandos": [("-preparacion", "Ver estado general"), ("-preparacion badu <1>", "Prepara Badu"), ("-preparacion yellowjack <1-2>", "Prepara Yellow Jack"), ("-preparacion ammu <1-3>", "Prepara Ammu-Nation"), ("-preparacion vanilla <1-3>", "Prepara Vanilla Unicorn"), ("-preparacion yate <1-4>", "Prepara Yate"), ("-preparacion centro <1-4>", "Prepara Centro Comercial"), ("-preparacion joyeria <1-5>", "Prepara Joyería"), ("-preparacion paleto <1-6>", "Prepara Banco Paleto"), ("-preparacion central <1-7>", "Prepara Banco Central"), ("-preparacion pacific <1-8>", "Prepara Pacific Bank")]},
        "drogas": {"emoji": "💊", "nombre": "Drogas e Ilegal", "comandos": [("-droga", "Ver precios"), ("-droga comprar <tipo> [cantidad]", "Compra droga"), ("-droga vender <tipo> [cantidad]", "Vende droga (solo MAFIA ADMIN)"), ("-tienda-ilegal", "Mercado negro")]},
        "redes": {"emoji": "📱", "nombre": "Redes Sociales", "comandos": [("/movil", "Abre móvil"), ("/avion on/off", "Modo avión"), ("/wifi conectar/desconectar", "WiFi"), ("/comprar-sim", "Compra SIM"), ("/ig", "Instagram"), ("/tw", "Twitter"), ("/fb", "Facebook"), ("/deepweb", "DeepWeb anónimo"), ("/wa", "WhatsApp"), ("-x @user <msg>", "Twitter DM")]},
        "admin": {"emoji": "⚙️", "nombre": "Administración", "comandos": [("-say <msg> 🔒", "Repite"), ("-kick @user 🔒", "Expulsa"), ("-warn @user <razón> 🔒", "Advierte"), ("-ban @user 🔒", "Banea"), ("-unban <id> 🔒", "Desbanea"), ("-money add/remove 🔒", "Modifica dinero"), ("-anuncio <msg> 🔒", "Anuncio"), ("-setprefix <p> 🔒", "Cambia prefijo"), ("-add-inv 🔒", "Añade item"), ("-rem-inv 🔒", "Quita item"), ("-add-coche 🔒", "Registra coche"), ("-remove-coche 🔒", "Elimina coche"), ("-add-droga 🔒", "Añade droga"), ("-add-licencia 🔒", "Da licencia"), ("-rem-licencia 🔒", "Quita licencia"), ("-quitar-warn 🔒", "Quita advertencia"), ("-economy-reset 🔒", "Resetea economía"), ("-reset-user 🔒", "Resetea usuario"), ("-create-item 🔒", "Crea item (precio INFINITY)"), ("-delete-item 🔒", "Elimina item"), ("-give-item 🔒", "Regala item"), ("-take-item 🔒", "Quita item"), ("-mass-economy 🔒", "Dinero masivo"), ("-purge <cantidad> 🔒", "Borra mensajes"), ("/dashboard", "Panel de control")]},
        "moderacion": {"emoji": "🛡️", "nombre": "Moderación", "comandos": [("-mute @user 🔒", "Mutea"), ("-unmute @user 🔒", "Desmutea"), ("-delwarn @user <id> 🔒", "Elimina advertencia"), ("-history @user", "Historial sanciones"), ("-warnings @user", "Ver advertencias")]},
        "web": {"emoji": "🌐", "nombre": "Panel Web", "comandos": [("http://localhost:5000", "Accede a la web"), ("/register", "Registro"), ("/login", "Login"), ("/perfil", "Perfil")]}
    }

    @commands.command(name='ayuda', aliases=['help'])
    @tiene_rol_usuario()
    async def ayuda(self, ctx, cat: Optional[str] = None):
        if cat and cat.lower() in self.CATEGORIAS:
            cat_info = self.CATEGORIAS[cat.lower()]
            embed = discord.Embed(title=f"{cat_info['emoji']} · TODOS LOS COMANDOS DE {cat_info['nombre'].upper()}", color=discord.Color.blue(), timestamp=datetime.now())
            desc = ""
            for cmd, desc_cmd in cat_info["comandos"]:
                desc += f"» **{cmd}**\n— {desc_cmd}\n\n"
            embed.description = desc
            embed.set_footer(text=f"Prefijo: {get_pre(self.bot, ctx.message)}  ·  🔒 = Solo admins/mods  ·  NOVA AGORA")
            await ctx.send(embed=embed)
            return
        prefijo = get_pre(self.bot, ctx.message)
        eco = await db.get_economy(ctx.author.id)
        saldo = eco['cash'] + eco['bank']
        embed = discord.Embed(title="📚 NOVA AGORA — Panel de Ayuda", description=f"**Prefijo:** `{prefijo}` — Selecciona una categoría en el menú de abajo.\n\n🚔 · **Roleplay**\n🏦 · **Economía**\n💼 · **Trabajos**\n🏴 · **Atracos**\n🏴 · **Preparatorias**\n💊 · **Drogas e Ilegal**\n📱 · **Redes Sociales**\n⚙️ · **Administración**\n🛡️ · **Moderación**\n🌐 · **Panel Web**\n\n🔒 = Solo administradores/moderadores", color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_footer(text=f"Saldo: **${saldo:,}**  ·  NOVA AGORA")
        view = AyudaView(prefijo, self.CATEGORIAS, ctx.author.id)
        await ctx.send(embed=embed, view=view)

class AyudaView(discord.ui.View):
    def __init__(self, prefijo, categorias, user_id):
        super().__init__(timeout=120)
        self.prefijo = prefijo
        self.categorias = categorias
        self.user_id = user_id
        options = [discord.SelectOption(label=info["nombre"], description=f"Comandos de {info['nombre']}", emoji=info["emoji"], value=key) for key, info in categorias.items()]
        select = discord.ui.Select(placeholder="📂 Selecciona una categoría...", options=options, row=0)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=embed_error("No eres el dueño de este menú."), ephemeral=True)
            return
        key = interaction.data['values'][0]
        cat_info = self.categorias[key]
        embed = discord.Embed(title=f"{cat_info['emoji']} · TODOS LOS COMANDOS DE {cat_info['nombre'].upper()}", color=discord.Color.blue(), timestamp=datetime.now())
        desc = ""
        for cmd, desc_cmd in cat_info["comandos"]:
            desc += f"» **{cmd}**\n— {desc_cmd}\n\n"
        embed.description = desc
        embed.set_footer(text=f"Prefijo: {self.prefijo}  ·  🔒 = Solo admins/mods  ·  NOVA AGORA")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

# ==================== COG: Moderacion ====================
class Moderacion(BaseCog):
    async def ensure_muted_role(self, guild: discord.Guild) -> discord.Role:
        role = discord.utils.get(guild.roles, name="Muted")
        if not role:
            try:
                role = await guild.create_role(name="Muted", reason="Rol para mute del bot")
                for channel in guild.channels:
                    try:
                        await channel.set_permissions(role, send_messages=False, add_reactions=False, speak=False)
                    except:
                        pass
                global ROL_MUTED
                ROL_MUTED = role.id
            except:
                pass
        return role

    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, miembro: discord.Member = None, *, razon: str = "Sin razón"):
        if not miembro:
            return await ctx.send(embed=embed_help("mute", "Silencia a un usuario por tiempo indefinido (30 días).", "-mute @usuario [razón]", "-mute @Juan Spam en el chat", "Gestionar roles"))
        muted_role = await self.ensure_muted_role(ctx.guild)
        if muted_role in miembro.roles:
            return await ctx.send(embed=embed_error("El usuario ya está muteado."))
        await miembro.add_roles(muted_role, reason=f"Mute por {ctx.author}: {razon}")
        fecha_fin = (datetime.now() + timedelta(days=30)).isoformat()
        await db.execute("INSERT INTO mutes (user_id, razon, fecha_inicio, fecha_fin, agente_id, agente_nombre, activo) VALUES (?, ?, ?, ?, ?, ?, 1)", (miembro.id, razon, datetime.now().isoformat(), fecha_fin, ctx.author.id, str(ctx.author)))
        await self.registrar_log_moderacion(ctx, "MUTE", miembro, razon, "30 días")
        await ctx.send(embed=embed_success("✅ Mute aplicado", f"{miembro.mention} ha sido muteado.\nRazón: {razon}"))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, miembro: discord.Member = None):
        if not miembro:
            return await ctx.send(embed=embed_help("unmute", "Quita el mute a un usuario.", "-unmute @usuario", "-unmute @Juan", "Gestionar roles"))
        muted_role = await self.ensure_muted_role(ctx.guild)
        if muted_role not in miembro.roles:
            return await ctx.send(embed=embed_error("El usuario no está muteado."))
        await miembro.remove_roles(muted_role, reason=f"Unmute por {ctx.author}")
        await db.execute("UPDATE mutes SET activo = 0 WHERE user_id = ? AND activo = 1", (miembro.id,))
        await self.registrar_log_moderacion(ctx, "UNMUTE", miembro, "Levantado por moderador")
        await ctx.send(embed=embed_success("✅ Unmute aplicado", f"{miembro.mention} ya puede hablar."))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, miembro: discord.Member = None, *, razon: str = None):
        if not miembro or not razon:
            return await ctx.send(embed=embed_help("warn", "Añade una advertencia a un usuario.", "-warn @usuario <razón>", "-warn @Juan No respeta las normas", "Gestionar mensajes"))
        await db.execute("INSERT INTO warnings (user_id, razon, fecha, agente_id, agente_nombre) VALUES (?, ?, ?, ?, ?)", (miembro.id, razon, datetime.now().isoformat(), ctx.author.id, str(ctx.author)))
        warns = await db.fetchall("SELECT id FROM warnings WHERE user_id = ?", (miembro.id,))
        num_warns = len(warns)
        await self.registrar_log_moderacion(ctx, f"WARN #{num_warns}", miembro, razon)
        await ctx.send(embed=embed_success("⚠️ Advertencia registrada", f"{miembro.mention} ha recibido una advertencia.\nRazón: {razon}\nTotal: {num_warns} advertencias.", 0xFFA500))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='delwarn')
    @commands.has_permissions(administrator=True)
    async def delwarn(self, ctx, miembro: discord.Member = None, id_warn: int = None):
        if not miembro or not id_warn:
            return await ctx.send(embed=embed_help("delwarn", "Elimina una advertencia de un usuario por su ID.", "-delwarn @usuario <id_warn>", "-delwarn @Juan 3", "Administrador"))
        row = await db.fetchone("SELECT id FROM warnings WHERE id = ? AND user_id = ?", (id_warn, miembro.id))
        if not row:
            return await ctx.send(embed=embed_error("Advertencia no encontrada."))
        await db.execute("DELETE FROM warnings WHERE id = ?", (id_warn,))
        await self.registrar_log_moderacion(ctx, f"WARN #{id_warn} ELIMINADA", miembro, "Eliminada por administrador")
        await ctx.send(embed=embed_success("🗑️ Advertencia eliminada", f"Se eliminó la advertencia #{id_warn} de {miembro.mention}.", 0xFF6600))
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='history')
    @tiene_rol_usuario()
    async def history(self, ctx, miembro: discord.Member = None):
        if not miembro:
            return await ctx.send(embed=embed_help("history", "Muestra el historial de sanciones de un usuario.", "-history @usuario", "-history @Juan", ""))
        warns = await db.fetchall("SELECT id, razon, fecha, agente_nombre FROM warnings WHERE user_id = ? ORDER BY fecha DESC", (miembro.id,))
        mutes = await db.fetchall("SELECT id, razon, fecha_inicio, fecha_fin, agente_nombre FROM mutes WHERE user_id = ? ORDER BY fecha_inicio DESC", (miembro.id,))
        embed = discord.Embed(title=f"📜 Historial de sanciones de {miembro.display_name}", color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_thumbnail(url=miembro.display_avatar.url)
        if warns:
            warns_text = "\n".join([f"**#{w[0]}** - {w[1]} (por {w[4]}) - {datetime.fromisoformat(w[3]).strftime('%d/%m/%Y %H:%M')}" for w in warns])
            embed.add_field(name="⚠️ Advertencias", value=warns_text, inline=False)
        else:
            embed.add_field(name="⚠️ Advertencias", value="*Ninguna*", inline=False)
        if mutes:
            mutes_text = "\n".join([f"**#{m[0]}** - {m[1]} (por {m[5]}) - {datetime.fromisoformat(m[3]).strftime('%d/%m/%Y %H:%M')} → {datetime.fromisoformat(m[4]).strftime('%d/%m/%Y %H:%M') if m[4] else 'Activo'}" for m in mutes])
            embed.add_field(name="🔇 Mutes", value=mutes_text, inline=False)
        else:
            embed.add_field(name="🔇 Mutes", value="*Ninguna*", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='warnings')
    @tiene_rol_usuario()
    async def warnings(self, ctx, miembro: discord.Member = None):
        if not miembro:
            return await ctx.send(embed=embed_help("warnings", "Muestra las advertencias de un usuario.", "-warnings @usuario", "-warnings @Juan", ""))
        warns = await db.fetchall("SELECT id, razon, fecha, agente_nombre FROM warnings WHERE user_id = ? ORDER BY fecha DESC", (miembro.id,))
        if not warns:
            return await ctx.send(embed=embed_success("✅ Sin advertencias", f"{miembro.display_name} no tiene advertencias."))
        embed = discord.Embed(title=f"⚠️ Advertencias de {miembro.display_name}", color=discord.Color.orange())
        for w in warns:
            embed.add_field(name=f"#{w[0]}", value=f"Razón: {w[1]}\nPor: {w[4]}\nFecha: {datetime.fromisoformat(w[3]).strftime('%d/%m/%Y %H:%M')}", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Niveles ====================
class Niveles(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.tiempo_task.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        uid = message.author.id
        user_data = await db.fetchone("SELECT last_message_time, last_message_content FROM niveles WHERE user_id = ?", (uid,))
        now = datetime.now()
        if user_data and user_data[0]:
            last_time = datetime.fromisoformat(user_data[0])
            last_content = user_data[1] or ""
            if (now - last_time).total_seconds() < COOLDOWN_MENSAJE_XP:
                return
            if message.content.lower() == last_content.lower():
                return
        result = await db.fetchone("SELECT mensajes FROM niveles WHERE user_id = ?", (uid,))
        current_messages = result[0] if result else 0
        new_messages = current_messages + 1
        new_level = new_messages // MENSAJES_POR_NIVEL
        old_level = current_messages // MENSAJES_POR_NIVEL
        remainder = new_messages % MENSAJES_POR_NIVEL
        next_remaining = MENSAJES_POR_NIVEL - remainder if remainder else MENSAJES_POR_NIVEL
        if result is None:
            await db.execute("INSERT OR IGNORE INTO niveles (user_id, mensajes, last_message_time, last_message_content) VALUES (?, ?, ?, ?)", (uid, 0, None, None))
        await db.execute("UPDATE niveles SET mensajes = ?, last_message_time = ?, last_message_content = ? WHERE user_id = ?", (new_messages, now.isoformat(), message.content[:100], uid))
        if new_level > old_level and new_level > 0:
            nivel_data = await db.get_nivel(uid)
            last_level_up = nivel_data.get('last_level_up')
            puede_subir = True
            if last_level_up:
                ultima_subida = datetime.fromisoformat(last_level_up)
                if (datetime.now() - ultima_subida).days < DIAS_PARA_SUBIR_NIVEL:
                    puede_subir = False
            if puede_subir:
                await db.execute("UPDATE niveles SET nivel = ?, last_level_up = ? WHERE user_id = ?", (new_level, now.isoformat(), uid))
                await self.verificar_recompensa_nivel(message.author, new_level)
                await message.channel.send(f"🎉 {message.author.mention} ha subido al nivel **{new_level}** por actividad!\n💬 **{new_messages} mensajes** acumulados | Próximo nivel en **{next_remaining} mensajes**.")
            else:
                dias_restantes = DIAS_PARA_SUBIR_NIVEL - (datetime.now() - ultima_subida).days
                await message.channel.send(f"⚠️ {message.author.mention}, has alcanzado el nivel **{new_level}** pero debes esperar **{dias_restantes} días** para subir (cooldown de 14 días entre niveles). Sigue ganando XP mientras tanto.")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.author.bot:
            return
        uid = ctx.author.id
        now = datetime.now()
        user_data = await db.fetchone("SELECT last_command_time FROM niveles WHERE user_id = ?", (uid,))
        if user_data and user_data[0]:
            last_time = datetime.fromisoformat(user_data[0])
            if (now - last_time).total_seconds() < COOLDOWN_COMANDO_XP:
                return
        await db.execute("UPDATE niveles SET last_command_time = ? WHERE user_id = ?", (now.isoformat(), uid))

    @tasks.loop(minutes=30)
    async def tiempo_task(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue
                user_state = await db.fetchone("SELECT last_time_time FROM niveles WHERE user_id = ?", (member.id,))
                if user_state and user_state[0]:
                    last = datetime.fromisoformat(user_state[0])
                    if (datetime.now() - last).total_seconds() < 300:
                        continue
                xp = XP_POR_TIEMPO
                nuevo_nivel = await db.add_xp(member.id, xp, "time")
                if nuevo_nivel:
                    nivel_data = await db.get_nivel(member.id)
                    last_level_up = nivel_data.get('last_level_up')
                    puede_subir = True
                    if last_level_up:
                        ultima_subida = datetime.fromisoformat(last_level_up)
                        if (datetime.now() - ultima_subida).days < DIAS_PARA_SUBIR_NIVEL:
                            puede_subir = False
                    if puede_subir:
                        await self.verificar_recompensa_nivel(member, nuevo_nivel)
                        canal = member.guild.system_channel or member.guild.text_channels[0]
                        await canal.send(f"🎉 {member.mention} ha subido al nivel **{nuevo_nivel}**!")

    async def verificar_recompensa_nivel(self, member: discord.Member, nivel: int):
        for nivel_requerido, rol_id in ROLES_POR_NIVEL.items():
            if nivel >= nivel_requerido and rol_id:
                rol = member.guild.get_role(rol_id)
                if rol and rol not in member.roles:
                    await member.add_roles(rol, reason=f"Recompensa por nivel {nivel}")
                    await self.log("NIVEL", f"{member} alcanzó nivel {nivel} y obtuvo rol {rol.name}")

    @commands.command(name='nivel')
    @tiene_rol_usuario()
    async def ver_nivel(self, ctx, miembro: discord.Member = None):
        miembro = miembro or ctx.author
        data = await db.get_nivel(miembro.id)
        embed = discord.Embed(title=f"📊 Nivel de {miembro.display_name}", color=discord.Color.blue())
        embed.add_field(name="Nivel", value=data['nivel'], inline=True)
        embed.add_field(name="XP total", value=data['xp'], inline=True)
        xp_siguiente = ((data['nivel'] + 1) ** 2) * 100
        embed.add_field(name="XP para siguiente nivel", value=f"{xp_siguiente - data['xp']}", inline=True)
        if data['last_level_up']:
            ultima_subida = datetime.fromisoformat(data['last_level_up'])
            dias_restantes = DIAS_PARA_SUBIR_NIVEL - (datetime.now() - ultima_subida).days
            if dias_restantes > 0:
                embed.add_field(name="⏳ Cooldown", value=f"Puedes subir de nivel nuevamente en **{dias_restantes} días**.", inline=False)
            else:
                embed.add_field(name="✅ Cooldown", value="Ya puedes subir de nivel cuando alcances el XP necesario.", inline=False)
        else:
            embed.add_field(name="✅ Cooldown", value="Sin restricciones, sube de nivel cuando alcances el XP.", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='ranking')
    @tiene_rol_usuario()
    async def ranking_niveles(self, ctx):
        top = await db.get_ranking_niveles(10)
        embed = discord.Embed(title="🏆 Ranking de niveles", color=discord.Color.gold())
        desc = ""
        for i, (uid, xp, nivel) in enumerate(top, 1):
            user = self.bot.get_user(uid)
            nombre = user.display_name if user else f"Usuario {uid}"
            desc += f"**#{i}** {nombre} - Nivel {nivel} ({xp} XP)\n"
        embed.description = desc
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    def construir_server_embed(self, guild: discord.Guild) -> discord.Embed:
        owner_text = "\n".join([f"<@{oid}> (`{oid}`)" for oid in OWNER_IDS]) if OWNER_IDS else "No configurados"
        canales = len(guild.channels)
        roles = len(guild.roles)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        online_members = sum(1 for m in guild.members if not m.bot and m.status != discord.Status.offline)
        bots = sum(1 for m in guild.members if m.bot)
        boosts = guild.premium_subscription_count or 0
        boost_tier = guild.premium_tier
        embed = discord.Embed(title="✨ **** NOVA AGORA V2 SERVER ****", description="Bienvenido al informe premium del Servidor.\nEstilo exclusivo Nova Developers, con datos reales y toque cinematográfico.", color=0x00E5FF)
        embed.add_field(name="**** OWNER IDS ****", value=owner_text, inline=False)
        embed.add_field(name="**** CANALES ****", value=f"💬 Texto: {text_channels}\n🔊 Voz: {voice_channels}\n🗂️ Categorías: {categories}\n📌 Total canales: {canales}", inline=False)
        embed.add_field(name="**** ROLES ****", value=f"🎭 {roles} roles registrados", inline=True)
        embed.add_field(name="**** MIEMBROS ****", value=f"👥 Total: {guild.member_count}\n🟢 Online: {online_members}\n🤖 Bots: {bots}", inline=True)
        embed.add_field(name="**** NOVA DEVELOPERS ****", value="- Bot personalizado Nova Developers\n- Hosting 24/7 optimizado\n- Comandos exclusivos RP\n- PDA, Multas y DeepWeb integrados", inline=False)
        embed.add_field(name="**** ESTADO PREMIUM ****", value=f"Boost Tier: {boost_tier} · Boosts: {boosts}\nCreado: {guild.created_at.strftime('%d/%m/%Y')}", inline=False)
        embed.add_field(name="**** SERVER ID ****", value=f"-# `{guild.id}`", inline=False)
        embed.set_footer(text=f"ID OWNER: {', '.join(str(oid) for oid in OWNER_IDS)} • Nova Agora V2 • Bot: Nova Developers")
        return embed

    @commands.command(name='información', aliases=['info', 'server', 'serverinfo', 'informacion'])
    @tiene_rol_usuario()
    async def server_info(self, ctx):
        embed = self.construir_server_embed(ctx.guild)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @app_commands.command(name='info', description='Información premium del servidor Nova Agora V2')
    async def server_slash(self, interaction: discord.Interaction):
        embed = self.construir_server_embed(interaction.guild)
        await interaction.response.send_message(embed=embed)

    @tiempo_task.before_loop
    async def before_tiempo(self):
        await self.bot.wait_until_ready()

# ==================== COG: TicketSystem ====================
class TicketModal(discord.ui.Modal, title="Valorar ticket"):
    def __init__(self, bot, channel_id, user_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.user_id = user_id
    rating = discord.ui.TextInput(label="Puntuación (1-5)", placeholder="Ej: 5", max_length=1)
    comment = discord.ui.TextInput(label="Comentario (opcional)", style=discord.TextStyle.paragraph, required=False, max_length=500)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("No puedes valorar este ticket.", ephemeral=True)
        try:
            rating = int(self.rating.value)
            if rating < 1 or rating > 5:
                raise ValueError
        except:
            return await interaction.response.send_message("Puntuación debe ser 1-5.", ephemeral=True)
        await db.execute("UPDATE tickets SET rating = ?, rating_comment = ? WHERE channel_id = ?", (rating, self.comment.value, self.channel_id))
        await interaction.response.send_message("✅ Valoración registrada. ¡Gracias!", ephemeral=True)

class TicketSystem(BaseCog):
    CATEGORIAS = {
        "dudas": {"emoji": "❓", "nombre": "Dudas Generales o sobre el Rol", "desc": "Preguntas sobre normas, funcionamiento, etc."},
        "economico": {"emoji": "👁️", "nombre": "Soporte Económico", "desc": "Reclamo de dinero, trabajos, recompensas."},
        "ck": {"emoji": "🔍", "nombre": "Character Kill (CK)", "desc": "Muerte final del personaje."},
        "alianzas": {"emoji": "🦷", "nombre": "Alianzas", "desc": "Propuestas de alianza."},
        "oposiciones": {"emoji": "📚", "nombre": "Solicitar Oposiciones para Soporte", "desc": "Quieres entrar al equipo."},
        "reporte": {"emoji": "🎵", "nombre": "Reportar a un Jugador", "desc": "Denuncias."},
        "bug": {"emoji": "💬", "nombre": "Reporte de Bug", "desc": "Errores."},
        "apelacion": {"emoji": "⚖️", "nombre": "Apelación de Sanción", "desc": "Apelar sanción."}
    }

    async def ensure_ticket_category(self, guild):
        cat = discord.utils.get(guild.categories, name="🎫 Tickets")
        if not cat:
            overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
            cat = await guild.create_category("🎫 Tickets", overwrites=overwrites)
        return cat

    async def ensure_staff_role(self, guild):
        role = discord.utils.get(guild.roles, name="Staff")
        if not role:
            role = await guild.create_role(name="Staff", reason="Equipo de soporte")
        return role

    async def create_ticket_channel(self, ctx, category_key: str):
        guild = ctx.guild
        user = ctx.author
        cat = await self.ensure_ticket_category(guild)
        staff_role = await self.ensure_staff_role(guild)
        base_name = f"ticket-{user.name.lower().replace(' ', '-')}"
        channel_name = base_name
        counter = 1
        while discord.utils.get(guild.channels, name=channel_name):
            counter += 1
            channel_name = f"{base_name}-{counter}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        channel = await guild.create_text_channel(channel_name, category=cat, overwrites=overwrites)
        await db.execute("INSERT INTO tickets (user_id, channel_id, category, created_at, status) VALUES (?, ?, ?, ?, 'abierto')", (user.id, channel.id, category_key, datetime.now().isoformat()))
        embed = discord.Embed(title=f"{await get_emoji('ticket')} Ticket abierto — {self.CATEGORIAS[category_key]['nombre']}", description=f"**Usuario:** {user.mention}\n**Categoría:** {self.CATEGORIAS[category_key]['emoji']} {self.CATEGORIAS[category_key]['nombre']}\n\nEl equipo de soporte te atenderá en breve.", color=discord.Color.blue(), timestamp=datetime.now())
        embed.set_footer(text=f"Ticket #{await self.get_ticket_id(channel.id)}")
        await channel.send(embed=embed)
        view = TicketControlView(self.bot, channel.id, user.id)
        await channel.send("**Opciones del ticket:**", view=view)
        await staff_role.edit(mentionable=True)
        await channel.send(f"{staff_role.mention} Nuevo ticket creado por {user.mention}.", delete_after=10)
        await staff_role.edit(mentionable=False)
        await ctx.send(embed=embed_success("✅ Ticket creado", f"Tu ticket ha sido abierto en {channel.mention}."), ephemeral=True)

    async def get_ticket_id(self, channel_id):
        row = await db.fetchone("SELECT id FROM tickets WHERE channel_id = ?", (channel_id,))
        return row[0] if row else 0

    @commands.command(name='ticket_panel')
    @commands.has_permissions(administrator=True)
    async def crear_panel_tickets(self, ctx):
        embed = discord.Embed(title=f"{await get_emoji('ticket')} Sistema de Tickets - Nova Agora Roleplay", description="¡Bienvenido al centro de soporte!\nSelecciona la categoría que corresponda.\n\n" + "\n".join([f"{data['emoji']} → **{data['nombre']}**\n*{data['desc']}*\n" for data in self.CATEGORIAS.values()]) + "\n**📌 Importante:**\n- Tickets privados.\n- Abre solo uno a la vez.\n- Adjunta evidencia.\n\nGracias por ser parte de Nova Agora RP.", color=discord.Color.gold(), timestamp=datetime.now())
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzFwNGl2ajRzM3p4d2Zmd2Z5cGxvbjE2dHJlZnYxM2ZkMjZzNjZ5bCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/6T7IlHrbxl7MOye7Hn/giphy.gif")
        embed.set_footer(text="NOVA AGORA ROLEPLAY")
        view = TicketPanelView(self.bot, self.CATEGORIAS)
        await ctx.send(embed=embed, view=view)
        try:
            await ctx.message.delete()
        except:
            pass

class TicketPanelView(discord.ui.View):
    def __init__(self, bot, categorias):
        super().__init__(timeout=None)
        self.bot = bot
        self.categorias = categorias
        for key, data in categorias.items():
            button = discord.ui.Button(label=f"{data['emoji']} {data['nombre']}", style=discord.ButtonStyle.secondary, custom_id=f"ticket_{key}")
            button.callback = self.create_callback(key)
            self.add_item(button)

    def create_callback(self, key):
        async def callback(interaction: discord.Interaction):
            row = await db.fetchone("SELECT channel_id FROM tickets WHERE user_id = ? AND status = 'abierto'", (interaction.user.id,))
            if row:
                channel = interaction.guild.get_channel(row[0])
                await interaction.response.send_message(embed=embed_error(f"Ya tienes un ticket abierto en {channel.mention if channel else 'tu ticket anterior'}."), ephemeral=True)
                return
            cog = self.bot.get_cog("TicketSystem")
            if cog:
                await cog.create_ticket_channel(await interaction.client.get_context(interaction.message), key)
                await interaction.response.send_message("✅ Creando tu ticket...", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Error: módulo de tickets no cargado.", ephemeral=True)
        return callback

class TicketControlView(discord.ui.View):
    def __init__(self, bot, channel_id, user_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id
        self.user_id = user_id

    @discord.ui.button(label="🔒 Cerrar ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        staff_role = discord.utils.get(interaction.guild.roles, name="Staff")
        is_staff = (staff_role and staff_role in interaction.user.roles) or interaction.user.guild_permissions.administrator
        is_owner = interaction.user.id == self.user_id
        if not (is_owner or is_staff):
            await interaction.response.send_message("❌ No tienes permiso para cerrar este ticket.", ephemeral=True)
            return
        await db.execute("UPDATE tickets SET status = 'cerrado', closed_at = ? WHERE channel_id = ?", (datetime.now().isoformat(), self.channel_id))
        channel = interaction.channel
        user = channel.guild.get_member(self.user_id)
        embed = discord.Embed(title="🔒 Ticket cerrado", description=f"El ticket ha sido cerrado por {interaction.user.mention}.", color=discord.Color.red(), timestamp=datetime.now())
        await channel.send(embed=embed)
        if is_staff and user:
            modal = TicketModal(self.bot, self.channel_id, user.id)
            view = discord.ui.View(timeout=86400)
            button_modal = discord.ui.Button(label="Valorar ticket", style=discord.ButtonStyle.primary)
            async def modal_callback(interaction2):
                await interaction2.response.send_modal(modal)
            button_modal.callback = modal_callback
            view.add_item(button_modal)
            dm_embed = discord.Embed(title="📝 Valoración del ticket", description="¿Te atendieron correctamente? Tu opinión nos ayuda a mejorar.\n\n**¿Te respondieron en un tiempo razonable?**\n**¿Se resolvió tu problema como esperabas?**\n\nNo te tomará más de un minuto.\n\nNo te sientas obligado, puedes cancelar si lo deseas.", color=discord.Color.gold())
            try:
                await user.send(embed=dm_embed, view=view)
            except:
                pass
        await asyncio.sleep(5)
        await channel.delete()
        await self.bot.get_cog("TicketSystem").log("TICKET", f"Ticket #{await self.bot.get_cog('TicketSystem').get_ticket_id(self.channel_id)} cerrado por {interaction.user}")

# ==================== COG: AntiRaid ====================
class AntiRaid(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.thresholds = {"message_flood": 15}
        self.message_flood = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        user_id = message.author.id
        now = datetime.now()
        if user_id not in self.message_flood:
            self.message_flood[user_id] = []
        self.message_flood[user_id].append(now)
        self.message_flood[user_id] = [ts for ts in self.message_flood[user_id] if (now - ts).total_seconds() < 10]
        if len(self.message_flood[user_id]) > self.thresholds["message_flood"]:
            await self._punish_user(message.author, "flood_messages")
            self.message_flood[user_id] = []
        forbidden_words = ["n-word", "puto", "cabrón", "imbécil", "idiota"]
        content_lower = message.content.lower()
        for word in forbidden_words:
            if word in content_lower:
                await self._punish_user(message.author, "forbidden_word")
                break

    async def _punish_user(self, user, reason_type):
        rows = await db.fetchall("SELECT COUNT(*) FROM antiraid_actions WHERE user_id = ? AND timestamp > ?", (user.id, (datetime.now() - timedelta(hours=24)).isoformat()))
        infracciones = rows[0][0] if rows else 0
        if infracciones < 2:
            await db.execute("INSERT INTO warnings (user_id, razon, fecha, agente_id, agente_nombre) VALUES (?, ?, ?, ?, ?)", (user.id, f"Anti-Raid: {reason_type}", datetime.now().isoformat(), self.bot.user.id, "Sistema"))
            await self.log("ANTIRAID_WARN", f"{user} recibió advertencia por {reason_type}")
            try:
                await user.send(embed=embed_error(f"⚠️ Has sido advertido por el sistema anti-raid: {reason_type}. Comportamiento inapropiado."))
            except:
                pass
        elif infracciones < 3:
            guild = self.bot.guilds[0] if self.bot.guilds else None
            if guild:
                muted_role = discord.utils.get(guild.roles, name="Muted")
                if muted_role:
                    member = guild.get_member(user.id)
                    if member:
                        await member.add_roles(muted_role, reason="Anti-Raid: comportamiento sospechoso")
                        await self.log("ANTIRAID_MUTE", f"{user} muteado por 1 hora por {reason_type}")
                        try:
                            await user.send(embed=embed_error(f"🔇 Has sido muteado por 1 hora debido a actividad sospechosa: {reason_type}."))
                        except:
                            pass
        elif infracciones < 4:
            guild = self.bot.guilds[0] if self.bot.guilds else None
            if guild:
                member = guild.get_member(user.id)
                if member:
                    await member.kick(reason=f"Anti-Raid: actividad sospechosa ({reason_type})")
                    await self.log("ANTIRAID_KICK", f"{user} expulsado por {reason_type}")
                    try:
                        await user.send(embed=embed_error(f"👢 Has sido expulsado del servidor por actividad sospechosa: {reason_type}."))
                    except:
                        pass
        else:
            await db.add_to_blacklist(user.id, f"Anti-Raid: {reason_type}", self.bot.user.id)
            await db.update_user_state(user.id, banned=True, ban_reason=f"Anti-Raid: {reason_type}", banned_by=self.bot.user.id, ban_date=datetime.now().isoformat())
            await db.delete_dni(user.id)
            guild = self.bot.guilds[0] if self.bot.guilds else None
            if guild:
                member = guild.get_member(user.id)
                if member:
                    await member.ban(reason=f"Anti-Raid: actividad sospechosa ({reason_type})", delete_message_days=0)
                    await self.log("ANTIRAID_BAN", f"{user} baneado permanentemente por {reason_type}")
                    try:
                        await user.send(embed=embed_error(f"🔨 Has sido baneado permanentemente del servidor por actividad maliciosa: {reason_type}."))
                    except:
                        pass

# ==================== COG: CheckUsers ====================
class CheckUsers(BaseCog):
    @app_commands.command(name="checkusers", description="Muestra los usuarios del servidor que están en la blacklist global.")
    @app_commands.default_permissions(administrator=True)
    async def checkusers(self, interaction: discord.Interaction):
        blacklist = await db.get_blacklist()
        blacklisted_ids = [b["user_id"] for b in blacklist]
        members = interaction.guild.members
        suspicious = []
        for member in members:
            if member.id in blacklisted_ids:
                reason = next((b["reason"] for b in blacklist if b["user_id"] == member.id), "Desconocido")
                suspicious.append(f"{member.mention} - {reason}")
        if not suspicious:
            await interaction.response.send_message("✅ No se encontraron usuarios sospechosos en este servidor.", ephemeral=True)
        else:
            embed = discord.Embed(title="⚠️ Usuarios en blacklist", description="\n".join(suspicious), color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ==================== COG: TabletPolicial ====================
class TabletPolicial(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self._hidden = True

    async def cog_check(self, ctx):
        user_state = await db.get_user_state(ctx.author.id)
        if not user_state.get('placa'):
            await ctx.send(embed=embed_error("No tienes placa policial."))
            return False
        return True

    @commands.command(name='tablet', hidden=True)
    async def tablet(self, ctx):
        view = TabletView(ctx.author.id)
        embed = discord.Embed(title=f"{await get_emoji('pda')} Tablet Policial - Nova Agora", description="Selecciona una acción desde el menú.", color=0x3498DB)
        await ctx.send(embed=embed, view=view)
        try:
            await ctx.message.delete()
        except:
            pass

class TabletView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("No eres el propietario de esta tablet.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🚔 Detener", style=discord.ButtonStyle.primary, row=0)
    async def detener(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DetenerModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔒 Encarcelar", style=discord.ButtonStyle.danger, row=0)
    async def encarcelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = EncarcelarModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="💰 Multar", style=discord.ButtonStyle.secondary, row=0)
    async def multar(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = MultarModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🔫 Requisar", style=discord.ButtonStyle.secondary, row=1)
    async def requisar(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RequisarModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📜 Licencias", style=discord.ButtonStyle.secondary, row=1)
    async def licencias(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LicenciaModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="❌ Cerrar", style=discord.ButtonStyle.red, row=2)
    async def cerrar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Tablet cerrada.", view=None, embed=None)

class DetenerModal(discord.ui.Modal, title="Detener ciudadano"):
    usuario = discord.ui.TextInput(label="ID o mención del usuario", placeholder="@usuario o ID")
    motivo = discord.ui.TextInput(label="Motivo", placeholder="Razón de la detención", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.usuario.value.replace('<@', '').replace('>', ''))
            miembro = interaction.guild.get_member(user_id)
            if not miembro:
                await interaction.response.send_message("Usuario no encontrado.", ephemeral=True)
                return
            embed = discord.Embed(title="🚨 DETENCIÓN", description=f"{interaction.user.display_name} ha detenido a {miembro.mention}. Motivo: {self.motivo.value}", color=0xFF0000)
            await interaction.response.send_message(embed=embed)
            await interaction.followup.send("Detención registrada.", ephemeral=True)
            await db.log_antiraid_action(interaction.user.id, "detener", interaction.guild.id)
        except ValueError:
            await interaction.response.send_message("Formato de usuario inválido.", ephemeral=True)

class EncarcelarModal(discord.ui.Modal, title="Encarcelar ciudadano"):
    usuario = discord.ui.TextInput(label="ID o mención del usuario", placeholder="@usuario o ID")
    minutos = discord.ui.TextInput(label="Minutos", placeholder="Número de minutos")
    motivo = discord.ui.TextInput(label="Motivo", placeholder="Razón del encarcelamiento", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.usuario.value.replace('<@', '').replace('>', ''))
            miembro = interaction.guild.get_member(user_id)
            if not miembro:
                await interaction.response.send_message("Usuario no encontrado.", ephemeral=True)
                return
            minutos = int(self.minutos.value)
            if minutos <= 0:
                await interaction.response.send_message("Los minutos deben ser positivos.", ephemeral=True)
                return
            hasta = datetime.now() + timedelta(minutes=minutos)
            await db.update_user_state(miembro.id, encarcelado_hasta=hasta.isoformat())
            embed = discord.Embed(title="🔒 ENCARCELAMIENTO", description=f"{interaction.user.display_name} ha encarcelado a {miembro.mention} por {minutos} minutos.\nMotivo: {self.motivo.value}", color=0xFF0000)
            await interaction.response.send_message(embed=embed)
            await db.log_antiraid_action(interaction.user.id, "encarcelar", interaction.guild.id)
        except ValueError:
            await interaction.response.send_message("ID o minutos inválidos.", ephemeral=True)

class MultarModal(discord.ui.Modal, title="Multar ciudadano"):
    usuario = discord.ui.TextInput(label="ID o mención del usuario", placeholder="@usuario o ID")
    cantidad = discord.ui.TextInput(label="Cantidad", placeholder="Monto de la multa")
    motivo = discord.ui.TextInput(label="Motivo", placeholder="Razón de la multa", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.usuario.value.replace('<@', '').replace('>', ''))
            miembro = interaction.guild.get_member(user_id)
            if not miembro:
                await interaction.response.send_message("Usuario no encontrado.", ephemeral=True)
                return
            cantidad = int(self.cantidad.value)
            if cantidad <= 0:
                await interaction.response.send_message("La cantidad debe ser mayor a 0.", ephemeral=True)
                return
            await db.add_multa(miembro.id, cantidad, self.motivo.value, interaction.user.display_name, "Tablet")
            embed = discord.Embed(title="📄 MULTA", description=f"{interaction.user.display_name} ha multado a {miembro.mention} con **${cantidad:,}**.\nMotivo: {self.motivo.value}", color=0xFFA500)
            await interaction.response.send_message(embed=embed)
            await db.log_antiraid_action(interaction.user.id, "multar", interaction.guild.id)
        except ValueError:
            await interaction.response.send_message("ID o cantidad inválidos.", ephemeral=True)

class RequisarModal(discord.ui.Modal, title="Requisar arma"):
    usuario = discord.ui.TextInput(label="ID o mención del usuario", placeholder="@usuario o ID")
    arma = discord.ui.TextInput(label="Arma", placeholder="Nombre del arma (ej: Pistola)")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.usuario.value.replace('<@', '').replace('>', ''))
            miembro = interaction.guild.get_member(user_id)
            if not miembro:
                await interaction.response.send_message("Usuario no encontrado.", ephemeral=True)
                return
            armas = await db.get_armas_equipadas(miembro.id)
            arma_real = next((k for k in armas if k.lower() == self.arma.value.lower()), None)
            if not arma_real:
                await interaction.response.send_message(f"{miembro.display_name} no tiene {self.arma.value} equipada.", ephemeral=True)
                return
            await db.execute("DELETE FROM armas_equipadas WHERE user_id = ? AND arma = ?", (miembro.id, arma_real))
            embed = discord.Embed(title="🔫 ARMA REQUISADA", description=f"{interaction.user.display_name} requisó {arma_real} a {miembro.mention}.", color=0xFF0000)
            await interaction.response.send_message(embed=embed)
            await db.log_antiraid_action(interaction.user.id, "requisar", interaction.guild.id)
        except ValueError:
            await interaction.response.send_message("ID inválido.", ephemeral=True)

class LicenciaModal(discord.ui.Modal, title="Gestionar licencia"):
    usuario = discord.ui.TextInput(label="ID o mención del usuario", placeholder="@usuario o ID")
    tipo = discord.ui.TextInput(label="Tipo de licencia", placeholder="Ej: licencia_pistola")
    accion = discord.ui.TextInput(label="Acción", placeholder="dar / quitar", default="dar")
    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.usuario.value.replace('<@', '').replace('>', ''))
            miembro = interaction.guild.get_member(user_id)
            if not miembro:
                await interaction.response.send_message("Usuario no encontrado.", ephemeral=True)
                return
            licencia = self.tipo.value.lower()
            accion = self.accion.value.lower()
            if accion == "dar":
                await db.dar_licencia(miembro.id, licencia)
                desc = f"concedió {licencia} a {miembro.mention}"
            elif accion == "quitar":
                await db.quitar_licencia(miembro.id, licencia)
                desc = f"revocó {licencia} a {miembro.mention}"
            else:
                await interaction.response.send_message("Acción debe ser 'dar' o 'quitar'.", ephemeral=True)
                return
            embed = discord.Embed(title="📋 LICENCIA", description=f"{interaction.user.display_name} {desc}.", color=0x00FF00 if accion == "dar" else 0xFF0000)
            await interaction.response.send_message(embed=embed)
            await db.log_antiraid_action(interaction.user.id, f"licencia_{accion}", interaction.guild.id)
        except ValueError:
            await interaction.response.send_message("ID inválido.", ephemeral=True)

# ==================== COG: DNI ====================
class DNI(BaseCog):
    @app_commands.command(name='dni', description="Crea tu DNI de personaje en NOVA AGORA V2")
    async def dni(self, interaction: discord.Interaction, nombre: str, apellidos: str, edad: int, genero: str, nacionalidad: str, color_ojos: str, altura: str, profesion: str):
        uid = interaction.user.id
        existing = await db.get_dni(uid)
        if existing:
            return await interaction.response.send_message(embed=embed_error("Ya tienes un DNI registrado."))
        numero = f"{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHJKLMNPQRSTVWXYZ')}"
        data = {"nombre": nombre, "apellidos": apellidos, "edad": edad, "genero": genero, "nacionalidad": nacionalidad, "color_ojos": color_ojos, "altura": altura, "profesion": profesion, "numero": numero, "fecha_creacion": datetime.now().isoformat()}
        await db.set_dni(uid, data)
        await interaction.response.send_message("✨ **** CREA TÚ DNI EN NOVA AGORA V2 ****")
        embed = discord.Embed(title="✅ DNI CREADO", description=f"**Nombre:** {nombre}\n**Apellidos:** {apellidos}\n**Edad:** {edad}\n**Género:** {genero}\n**Nacionalidad:** {nacionalidad}\n**Color de ojos:** {color_ojos}\n**Altura:** {altura}\n**Profesión:** {profesion}\n**Número DNI:** `{numero}`", color=0x00FF00)
        await interaction.followup.send(embed=embed)

    @commands.command(name='ver')
    @tiene_rol_usuario()
    async def ver(self, ctx, subcomando: str = None, usuario: Optional[discord.Member] = None):
        if subcomando is None or subcomando.lower() != 'dni':
            return await ctx.send(embed=embed_info("📋 Comando ver", "Usa `-ver dni [usuario]` para ver el DNI de alguien."))
        uid = usuario.id if usuario else ctx.author.id
        dni = await db.get_dni(uid)
        if not dni:
            return await ctx.send(embed=embed_error("Ese usuario no tiene DNI."))
        target = usuario or ctx.author
        embed = discord.Embed(title="DOCUMENTO NACIONAL DE IDENTIDAD • NOVA AGORA V2", description="ESTADOS UNIDOS · LOS ANGELES", color=0x00D1FF, timestamp=datetime.now())
        embed.set_author(name=target.display_name, icon_url=target.display_avatar.url)
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="✨ ESTADO", value="LOS ANGELES", inline=False)
        embed.add_field(name="🌟 NOMBRE", value=f"**{dni['nombre']}**", inline=False)
        embed.add_field(name="💫 APELLIDOS", value=f"**{dni['apellidos']}**", inline=False)
        embed.add_field(name="🔥 SEXO", value=dni['genero'], inline=False)
        embed.add_field(name="📅 FECHA NACIMIENTO", value=str(dni['edad']), inline=False)
        embed.add_field(name="👁️ COLOR OJOS", value=dni['color_ojos'], inline=False)
        embed.add_field(name="📏 ALTURA", value=dni['altura'], inline=False)
        embed.add_field(name="🎖️ PROFESIÓN", value=f"**{dni['profesion']}**", inline=False)
        embed.add_field(name="🌍 NACIONALIDAD", value=dni['nacionalidad'], inline=False)
        embed.add_field(name="🔐 Nº DNI", value=f"**{dni['numero']}**", inline=False)
        embed.add_field(name="✅ ESTADO DEL DOCUMENTO", value="**VÁLIDO**", inline=False)
        embed.add_field(name="🗓️ EMITIDO", value=datetime.fromisoformat(dni['fecha_creacion']).strftime('%d/%m/%Y %H:%M'), inline=False)
        embed.set_footer(text=f"NOVA AGORA V2 • CARNET OFICIAL • {datetime.now():%d/%m/%Y}")
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @app_commands.command(name='borrardni', description="Elimina el DNI de un usuario (solo administradores) en NOVA AGORA V2")
    @app_commands.checks.has_permissions(administrator=True)
    async def borrardni(self, interaction: discord.Interaction, usuario: discord.Member):
        dni = await db.get_dni(usuario.id)
        if not dni:
            return await interaction.response.send_message(embed=embed_error("Ese usuario no tiene DNI."))
        await db.delete_dni(usuario.id)
        await interaction.response.send_message("✨ **** BORRA DNI EN NOVA AGORA V2 ****")
        await interaction.followup.send(embed=embed_success("🗑️ DNI eliminado", f"Se eliminó el DNI de {usuario.mention}.", 0xFF0000))

# ==================== COG: Trabajos ====================
class Trabajos(BaseCog):
    trabajos_activos = {}

    @commands.command(name='minar')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_minero()
    @tiene_rol_usuario()
    async def minar(self, ctx):
        uid = str(ctx.author.id)
        if uid in self.trabajos_activos:
            return await ctx.send(embed=embed_error("-# **Ya estás trabajando. Termina tu turno actual con `-terminar-trabajo`.**"))
        msg = await ctx.send("⛏️ **Comenzando a minar...**\n *Excavando en la mina...*")
        await asyncio.sleep(random.randint(3, 6))
        rand = random.random() * 100
        acum = 0
        mineral_encontrado = None
        for mineral, datos in MINERALES.items():
            acum += datos["probabilidad"]
            if rand <= acum:
                mineral_encontrado = mineral
                break
        if not mineral_encontrado:
            mineral_encontrado = "Carbón"
        cantidad = random.randint(1, 3)
        valor = MINERALES[mineral_encontrado]["valor"] * cantidad
        emoji = MINERALES[mineral_encontrado]["emoji"]
        await db.add_item(ctx.author.id, "personal", mineral_encontrado, cantidad)
        embed = discord.Embed(
            title="⛏️ **RESULTADO DE LA MINERÍA**",
            description=f"{emoji} Has extraído **{cantidad}x {mineral_encontrado}**.\n💎 Valor aproximado: **${valor}**",
            color=0xB87333
        )
        await msg.edit(content=None, embed=embed)
        await self.log("MINAR", f"{ctx.author.name} extrajo {cantidad}x {mineral_encontrado}")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='bus')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_autobusero()
    @tiene_rol_usuario()
    async def bus(self, ctx):
        uid = str(ctx.author.id)
        if uid in self.trabajos_activos:
            return await ctx.send(embed=embed_error("-# **Ya estás trabajando. Termina tu turno actual con `-terminar-trabajo`.**"))
        self.trabajos_activos[uid] = {"tipo": "bus", "inicio": datetime.now(), "fin": datetime.now() + timedelta(minutes=5)}
        embed = discord.Embed(
            title="🚌 **CONDUCIENDO EL AUTOBÚS**",
            description="Has comenzado tu ruta como conductor de autobús.\nRecoge pasajeros y completa la ruta.\n**Tiempo estimado: 5 minutos**\n\nPulsa `-terminar-trabajo` para cobrar.",
            color=0xFFD700
        )
        await ctx.send(embed=embed)
        await self.log("BUS", f"{ctx.author.name} comenzó ruta de autobús")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='chatarrero')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_chatarrero()
    @tiene_rol_usuario()
    async def chatarrero(self, ctx):
        uid = str(ctx.author.id)
        if uid in self.trabajos_activos:
            return await ctx.send(embed=embed_error("-# **Ya estás trabajando. Termina tu turno actual con `-terminar-trabajo`.**"))
        self.trabajos_activos[uid] = {"tipo": "chatarrero", "inicio": datetime.now(), "fin": datetime.now() + timedelta(minutes=8)}
        embed = discord.Embed(
            title="🔧 **RECOLECTANDO CHATARRA**",
            description="Has comenzado a recolectar metales y piezas viejas.\n**Tiempo estimado: 8 minutos**\n\nPulsa `-terminar-trabajo` para cobrar.",
            color=0x808080
        )
        await ctx.send(embed=embed)
        await self.log("CHATARRERO", f"{ctx.author.name} comenzó recolección de chatarra")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='terminar-trabajo')
    @check_ban()
    @tiene_rol_usuario()
    async def terminar_trabajo(self, ctx):
        uid = str(ctx.author.id)
        if uid not in self.trabajos_activos:
            return await ctx.send(embed=embed_error("-# **No tienes ningún trabajo activo.\nUsa `-minar`, `-bus` o `-chatarrero` para comenzar.**"))
        trabajo = self.trabajos_activos[uid]
        tipo = trabajo["tipo"]
        fin = trabajo["fin"]
        ahora = datetime.now()
        if ahora < fin:
            return await ctx.send(embed=embed_error(f"-# **Todavía no has terminado. Te quedan {(fin-ahora).seconds//60} minutos.**"))
        if tipo == "minar":
            embed = discord.Embed(title="⛏️ **MINERÍA COMPLETADA**", description="Has terminado tu jornada de minería. Los minerales ya están en tu inventario.", color=0xB87333)
            await ctx.send(embed=embed)
        elif tipo == "bus":
            pago = random.randint(500, 1200)
            await db.add_cash(ctx.author.id, pago)
            embed = discord.Embed(title="🚌 **RUTA COMPLETADA**", description=f"Has cobrado **${pago:,}** por tu servicio de autobús.", color=0xFFD700)
            await ctx.send(embed=embed)
        elif tipo == "chatarrero":
            chatarra = random.randint(5, 20)
            valor_total = chatarra * 15
            await db.add_cash(ctx.author.id, valor_total)
            await db.add_item(ctx.author.id, "personal", "Chatarra", chatarra)
            embed = discord.Embed(title="🔧 **RECOLECCIÓN COMPLETADA**", description=f"Has recogido **{chatarra} piezas de chatarra** y las has vendido por **${valor_total:,}**.", color=0x808080)
            await ctx.send(embed=embed)
        del self.trabajos_activos[uid]
        await self.log("TERMINAR_TRABAJO", f"{ctx.author.name} finalizó trabajo de {tipo}")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Kits ====================
class Kits(BaseCog):
    COOLDOWN_SEGUNDOS = 43200

    @commands.command(name='policial')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def kit_policial(self, ctx):
        await self._reclamar_kit(ctx, "LSPD", "Kit policial", [("Placa Policial", 1), ("Linterna", 1), ("Radio", 1), ("Esposas", 1), ("Guantes", 1)])
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='mecanico')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def kit_mecanico(self, ctx):
        await self._reclamar_kit(ctx, "Mecánico", "Kit mecánico", [("Llave Inglesa", 1), ("Herramientas", 1)])
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='ems')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def kit_ems(self, ctx):
        await self._reclamar_kit(ctx, "EMS", "Kit EMS", [("Botiquin", 1), ("Desfibrilador", 1), ("Kit Médico", 1)])
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.command(name='bomberos')
    @check_ban()
    @check_encarcelado()
    @tiene_rol_usuario()
    async def kit_bomberos(self, ctx):
        await self._reclamar_kit(ctx, "Bomberos", "Kit bomberos", [("Traje Ignifugo", 1), ("Hacha", 1), ("Manguera", 1), ("Botiquin", 1)])
        try:
            await ctx.message.delete()
        except:
            pass

    async def _reclamar_kit(self, ctx, rol_requerido, nombre_kit, items):
        user = ctx.author
        if not any(role.name == rol_requerido for role in user.roles):
            return await ctx.send(embed=embed_error(f"Necesitas el rol **{rol_requerido}** para reclamar el {nombre_kit}."))
        ok, rest = await db.check_cooldown(user.id, f"kit_{rol_requerido.lower()}", self.COOLDOWN_SEGUNDOS)
        if not ok:
            horas = rest // 3600
            minutos = (rest % 3600) // 60
            return await ctx.send(embed=embed_error(f"Ya has reclamado el {nombre_kit} recientemente. Puedes volver a reclamarlo en {horas}h {minutos}m."))
        for item, cantidad in items:
            await db.add_item(user.id, "personal", item, cantidad)
        desc = ", ".join([f"{cant}x {item}" for item, cant in items])
        await ctx.send(embed=embed_success(f"🎁 {nombre_kit} reclamado", f"Has recibido: {desc}"))
        await self.log("KIT", f"{user.name} reclamó {nombre_kit}")

# ==================== COG: OwnerMenu ====================
class OwnerMenu(BaseCog):
    @app_commands.command(name='actualizar-comandos', description="Fuerza la sincronización de todos los slash commands (solo Owners)")
    async def actualizar_comandos(self, interaction: discord.Interaction):
        if interaction.user.id not in OWNER_IDS:
            return await interaction.response.send_message(embed=embed_error("Solo los Owners pueden usar este comando."), ephemeral=True)
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await self.bot.tree.sync()
            for guild in self.bot.guilds:
                await self.bot.tree.sync(guild=discord.Object(id=guild.id))
            await interaction.followup.send(embed=embed_success("✅ Slash commands sincronizados", f"Se sincronizaron **{len(synced)}** comandos globales correctamente.", 0x00FF00), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=embed_error(f"Error al sincronizar: {str(e)[:200]}"), ephemeral=True)

    @commands.command(name='sync')
    @is_owner()
    async def sync(self, ctx):
        """Fuerza sincronización de slash commands en este servidor (instantáneo)"""
        msg = await ctx.send("⏳ Sincronizando slash commands...")
        try:
            # Sync guild first (instantáneo)
            guild_synced = await self.bot.tree.sync(guild=discord.Object(id=ctx.guild.id))
            # Sync global también
            global_synced = await self.bot.tree.sync()
            total_guild = len(guild_synced)
            total_global = len(global_synced)
            embed = discord.Embed(
                title="✅ Slash commands sincronizados",
                description=f"**{total_guild}** en servidor | **{total_global}** globales.\nEscribe `/anuncios` para usarlo.",
                color=0x00FF00
            )
            await msg.edit(content=None, embed=embed)
        except Exception as e:
            await msg.edit(content=None, embed=embed_error(f"Error: {str(e)[:200]}"))

    @commands.group(name='owner', invoke_without_command=True)
    @is_owner()
    async def owner(self, ctx):
        embed = discord.Embed(title="🔧 Panel de Owner", description="Comandos disponibles:", color=0x00FF00)
        embed.add_field(name="`-owner add-emoji <nombre> <emoji>`", value="Agrega un emoji animado al servidor (puedes usar el emoji de otro servidor si el bot tiene permisos).", inline=False)
        embed.add_field(name="`-owner list-emojis`", value="Lista los emojis personalizados añadidos.", inline=False)
        embed.add_field(name="`-owner menu`", value="Abre un menú interactivo para gestionar emojis.", inline=False)
        embed.add_field(name="🌐 Panel web", value=f"Accede a `/owner/emojis` en el navegador con el token `{ADMIN_TOKEN}` para gestionar emojis globales.", inline=False)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @owner.command(name='add-emoji')
    @is_owner()
    async def add_animated_emoji(self, ctx, nombre: str, emoji: str):
        guild = ctx.guild
        if not guild.me.guild_permissions.create_expression:
            return await ctx.send(embed=embed_error("El bot necesita el permiso 'Crear expresiones' (Crear emojis)."))
        emoji_id = None
        if emoji.startswith("<a:") or emoji.startswith("<:"):
            try:
                emoji_id = int(emoji.split(":")[-1][:-1])
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.gif" if emoji.startswith("<a:") else f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            except:
                return await ctx.send(embed=embed_error("Formato de emoji inválido. Usa un emoji animado tipo `<a:nombre:123456789>` o `:nombre:` de este servidor."))
        else:
            custom_emoji = discord.utils.get(guild.emojis, name=emoji.strip(":"))
            if custom_emoji:
                emoji_id = custom_emoji.id
                emoji_url = custom_emoji.url
            else:
                return await ctx.send(embed=embed_error("Emoji no encontrado en este servidor. Proporciónalo en formato `<a:nombre:ID>`."))
        try:
            new_emoji = await guild.create_custom_emoji(name=nombre, image=await self.bot.loop.run_in_executor(None, self._download_image, emoji_url))
            await db.add_animated_emoji(nombre, new_emoji.id, ctx.author.id)
            await ctx.send(embed=embed_success("✅ Emoji añadido", f"Se ha añadido el emoji `:{new_emoji.name}:` al servidor."))
            await self.log("ADD_EMOJI", f"{ctx.author.name} añadió emoji {nombre} (ID: {new_emoji.id})")
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al añadir emoji: {str(e)[:100]}"))
        try:
            await ctx.message.delete()
        except:
            pass

    def _download_image(self, url):
        import requests
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    @owner.command(name='list-emojis')
    @is_owner()
    async def list_emojis(self, ctx):
        emojis = await db.get_all_animated_emojis()
        if not emojis:
            return await ctx.send(embed=embed_info("📋 Emojis", "No hay emojis personalizados añadidos."))
        desc = "\n".join([f"`:{e['name']}:` (<:{e['name']}:{e['emoji_id']}>)" for e in emojis])
        embed = discord.Embed(title="📋 Emojis personalizados", description=desc, color=0x00FF00)
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass

    @owner.command(name='menu')
    @is_owner()
    async def owner_menu(self, ctx):
        view = OwnerMenuView()
        embed = discord.Embed(title="🔧 Menú de Owner", description="Selecciona una opción para gestionar el bot y los emojis animados.\n\nTambién puedes usar el panel web: `/owner/emojis`", color=0x00FF00)
        await ctx.send(embed=embed, view=view)
        try:
            await ctx.message.delete()
        except:
            pass

class OwnerMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="➕ Añadir Emoji", style=discord.ButtonStyle.success, emoji="➕")
    async def add_emoji_btn(self, interaction: discord.Interaction, button):
        modal = AddEmojiModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="📋 Listar Emojis", style=discord.ButtonStyle.primary, emoji="📋")
    async def list_emoji_btn(self, interaction: discord.Interaction, button):
        emojis = await db.get_all_animated_emojis()
        if not emojis:
            embed = embed_info("📋 Emojis", "No hay emojis personalizados.")
        else:
            desc = "\n".join([f"`:{e['name']}:` (<:{e['name']}:{e['emoji_id']}>)" for e in emojis])
            embed = discord.Embed(title="📋 Emojis personalizados", description=desc, color=0x00FF00)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚙️ Comandos Owner", style=discord.ButtonStyle.secondary, emoji="⚙️")
    async def cmd_help(self, interaction: discord.Interaction, button):
        embed = discord.Embed(title="⚙️ Comandos de Owner", description="`-bot [días]` - Activar bot\n`-bot-off` - Apagar bot\n`-owner add-emoji <nombre> <emoji>` - Añadir emoji animado\n`-owner list-emojis` - Ver emojis\n`-owner menu` - Este menú\n`-grant-pda @user` - Dar acceso PDA web\n`-revoke-pda @user` - Revocar acceso PDA", color=0x00FF00)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AddEmojiModal(discord.ui.Modal, title="Añadir Emoji Animado"):
    nombre = discord.ui.TextInput(label="Nombre del emoji", placeholder="Ej: NovaGif", max_length=32)
    emoji_input = discord.ui.TextInput(label="Emoji", placeholder="Ej: <a:NovaGif:123456789> o :nombre:", style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild.me.guild_permissions.create_expression:
            return await interaction.response.send_message(embed=embed_error("El bot necesita permiso 'Crear expresiones'."), ephemeral=True)
        emoji_str = self.emoji_input.value
        nombre = self.nombre.value
        emoji_id = None
        if emoji_str.startswith("<a:") or emoji_str.startswith("<:"):
            try:
                emoji_id = int(emoji_str.split(":")[-1][:-1])
                emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.gif" if emoji_str.startswith("<a:") else f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
            except:
                return await interaction.response.send_message(embed=embed_error("Formato de emoji inválido."), ephemeral=True)
        else:
            custom_emoji = discord.utils.get(guild.emojis, name=emoji_str.strip(":"))
            if custom_emoji:
                emoji_id = custom_emoji.id
                emoji_url = custom_emoji.url
            else:
                return await interaction.response.send_message(embed=embed_error("Emoji no encontrado en este servidor."), ephemeral=True)
        try:
            import requests
            response = requests.get(emoji_url)
            response.raise_for_status()
            new_emoji = await guild.create_custom_emoji(name=nombre, image=response.content)
            await db.add_animated_emoji(nombre, new_emoji.id, interaction.user.id)
            await interaction.response.send_message(embed=embed_success("✅ Emoji añadido", f"Se ha añadido `:{new_emoji.name}:` al servidor."), ephemeral=True)
            await db.log_antiraid_action(interaction.user.id, "add_emoji", guild.id)
        except Exception as e:
            await interaction.response.send_message(embed=embed_error(f"Error: {str(e)[:100]}"), ephemeral=True)

# ==================== COG: Dashboard ====================
class Dashboard(BaseCog):
    @app_commands.command(name='dashboard', description="Panel de control avanzado de Nova Agora")
    @app_commands.default_permissions(administrator=False)
    async def dashboard_slash(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(ROL_DASHBOARD_ID)
        if not role or role not in interaction.user.roles:
            if interaction.user.id not in OWNER_IDS:
                return await interaction.response.send_message(embed=embed_error("No tienes permiso para usar este comando."), ephemeral=True)
        total_users = (await db.fetchone("SELECT COUNT(*) FROM economy"))[0]
        total_cash = (await db.fetchone("SELECT SUM(cash) FROM economy"))[0] or 0
        total_bank = (await db.fetchone("SELECT SUM(bank) FROM economy"))[0] or 0
        total_black = (await db.fetchone("SELECT SUM(black_money) FROM economy"))[0] or 0
        total_money = total_cash + total_bank + total_black
        rol_lspd = interaction.guild.get_role(ROL_LSPD_ID)
        people_in_rol = len(rol_lspd.members) if rol_lspd else 0
        trabajos_activos = len(Trabajos.trabajos_activos)
        comandos_ejecutados = await db.get_estadistica('comandos_totales') or 0
        atracos_totales = await db.get_estadistica('robos_totales') or 0
        top_niveles = await db.get_ranking_niveles(5)
        embed = discord.Embed(
            title="📊 DASHBOARD NOVA AGORA",
            description="**Estadísticas en tiempo real del servidor**",
            color=0x00E5FF,
            timestamp=datetime.now()
        )
        embed.add_field(name="👥 Usuarios registrados", value=f"{total_users}", inline=True)
        embed.add_field(name="💰 Economía total", value=f"${total_money:,}", inline=True)
        embed.add_field(name="🚔 Personas en rol LSPD", value=f"{people_in_rol}", inline=True)
        embed.add_field(name="💼 Trabajos activos", value=f"{trabajos_activos}", inline=True)
        embed.add_field(name="📟 Comandos ejecutados", value=f"{comandos_ejecutados}", inline=True)
        embed.add_field(name="🏴 Atracos realizados", value=f"{atracos_totales}", inline=True)
        ranking_text = ""
        for i, (uid, xp, nivel) in enumerate(top_niveles, 1):
            user = interaction.guild.get_member(uid)
            nombre = user.display_name if user else f"Usuario {uid}"
            ranking_text += f"{i}. {nombre} - Nivel {nivel} ({xp} XP)\n"
        embed.add_field(name="🏆 Ranking de niveles", value=ranking_text or "Sin datos", inline=False)
        embed.set_footer(text="Actualizado en tiempo real")
        await interaction.response.send_message(embed=embed)

# ==================== COG: Alertas ====================
class Alertas(BaseCog):
    @commands.command(name='alerta-robo')
    @tiene_rol_lspd_operativo()
    async def alerta_robo(self, ctx):
        rol_lspd = ctx.guild.get_role(ROL_LSPD_OPERATIVO_ID)
        if not rol_lspd:
            return await ctx.send(embed=embed_error("Rol LSPD Operativo no encontrado."))
        emoji_animado = "<a:PirateAlert:1495516168121745449>"
        mensaje = (
            f"{emoji_animado} **🚨 DEFCON 4 🚨** {emoji_animado}\n\n"
            f"{rol_lspd.mention}\n"
            "**CORRE, ESTÁN ROBANDO EN LA OTRA COMISARÍA, VES DEPRISA**\n\n"
            "🚔 Refuerzos solicitados.\n"
            "⚠️ Posible enfrentamiento armado.\n"
            "📍 Acude a la ubicación marcada.\n\n"
            f"{emoji_animado} **CÓDIGO ROJO - ACCIÓN INMEDIATA** {emoji_animado}"
        )
        await ctx.send(content=mensaje)
        try:
            await ctx.message.delete()
        except:
            pass
        await self.log("ALERTA_ROBO", f"{ctx.author.name} activó la alerta de robo")

    @commands.command(name='alerta-defcon')
    @tiene_rol_lspd_operativo()
    async def alerta_defcon(self, ctx, nivel: int = None):
        if nivel is None or nivel not in range(1, 7):
            embed = discord.Embed(
                title="🛡️ SISTEMA DEFCON",
                description="**Uso:** `-alerta-defcon <nivel>`\n\n**Niveles disponibles:**\n🔵 DEFCON 6 — Paz total\n🟢 DEFCON 5 — Vigilancia normal\n🟡 DEFCON 4 — Alerta elevada\n🟠 DEFCON 3 — Alerta alta\n🔴 DEFCON 2 — Peligro inminente\n🚨 DEFCON 1 — MÁXIMA EMERGENCIA",
                color=0x3498DB
            )
            return await ctx.send(embed=embed)
        defcon_data = {
            6: {"color": 0x3498DB, "emoji": "🔵", "nombre": "PAZ TOTAL", "desc": "***Situación completamente tranquila. Sin amenazas activas. Patrullaje rutinario.***", "accion": "Patrullaje estándar. Sin alerta activa."},
            5: {"color": 0x2ECC71, "emoji": "🟢", "nombre": "VIGILANCIA NORMAL", "desc": "***Vigilancia estándar activa. Sin amenazas confirmadas. Estado operativo normal.***", "accion": "Mantener vigilancia. Reportar cualquier actividad sospechosa."},
            4: {"color": 0xF1C40F, "emoji": "🟡", "nombre": "ALERTA ELEVADA", "desc": "***Actividad sospechosa detectada. Se requiere presencia policial reforzada en zonas clave.***", "accion": "Reforzar patrullaje. Estar alerta ante posibles incidentes."},
            3: {"color": 0xE67E22, "emoji": "🟠", "nombre": "ALERTA ALTA", "desc": "***Amenaza confirmada en la ciudad. Todas las unidades deben estar en posición.***", "accion": "Todas las unidades en alerta. Coordinación con superiores obligatoria."},
            2: {"color": 0xE74C3C, "emoji": "🔴", "nombre": "PELIGRO INMINENTE", "desc": "***PELIGRO INMINENTE. Situación crítica activa. Se requiere respuesta inmediata de todas las unidades.***", "accion": "Respuesta inmediata requerida. Evacuar civiles de la zona si es necesario."},
            1: {"color": 0x8B0000, "emoji": "🚨", "nombre": "MÁXIMA EMERGENCIA", "desc": "***⚠️ DEFCON 1 — MÁXIMA EMERGENCIA. SITUACIÓN FUERA DE CONTROL. TODAS LAS UNIDADES DEBEN ACUDIR DE INMEDIATO. ⚠️***", "accion": "EMERGENCIA TOTAL. Todas las unidades disponibles a sus puestos. Sin excepción."},
        }
        d = defcon_data[nivel]
        embed = discord.Embed(
            title=f"{d['emoji']} DEFCON {nivel} — {d['nombre']} {d['emoji']}",
            description=d['desc'],
            color=d['color'],
            timestamp=datetime.now()
        )
        embed.add_field(name="📋 Acción requerida", value=d['accion'], inline=False)
        embed.set_footer(text=f"Activado por {ctx.author.display_name} • LSPD Nova Agora RP")
        await ctx.send(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
        await self.log("ALERTA_DEFCON", f"{ctx.author.name} activó DEFCON {nivel}")
        try:
            await ctx.message.delete()
        except:
            pass

# ==================== COG: Disponibilidad ====================
class Disponibilidad(BaseCog):
    @commands.command(name='dispo')
    @check_ban()
    @tiene_rol_usuario()
    async def dispo(self, ctx, servicio: str = None, cantidad: int = None):
        if not servicio or cantidad is None:
            embed = embed_help("dispo", "Muestra la disponibilidad de un servicio de emergencia.", "-dispo <lspd/lsmd/lssd> <cantidad>", "-dispo lspd 5", "")
            return await ctx.send(embed=embed)
        servicio = servicio.lower()
        if servicio not in ['lspd', 'lsmd', 'lssd']:
            return await ctx.send(embed=embed_error("Servicio no válido. Usa: lspd, lsmd, lssd"))
        if cantidad < 0:
            return await ctx.send(embed=embed_error("La cantidad no puede ser negativa."))
        unidad = "unidad" if cantidad == 1 else "unidades"
        if servicio == 'lspd':
            rol_lspd = ctx.guild.get_role(ROL_LSPD_ID)
            if rol_lspd:
                await ctx.send(rol_lspd.mention)
            if cantidad == 0:
                estado = "🔴 SATURADO"
                desc = "⚠️ Actualmente no hay unidades disponibles.\n🚨 Todas las patrullas se encuentran atendiendo incidencias."
            elif cantidad == 1:
                estado = "🟢 1 unidad disponible"
                desc = f"🚓 Actualmente hay **{cantidad} {unidad} disponible** patrullando la ciudad."
            else:
                estado = f"🟢 {cantidad} unidades disponibles"
                desc = f"🚓 Actualmente hay **{cantidad} {unidad} disponibles** patrullando la ciudad."
            footer = "⚡ Tiempo de respuesta sujeto a disponibilidad."
        elif servicio == 'lsmd':
            rol_lsmd = ctx.guild.get_role(ROL_LSMD_ID)
            if rol_lsmd:
                await ctx.send(rol_lsmd.mention)
            estado = "🟢 ACTIVO" if cantidad > 0 else "🔴 SATURADO"
            desc = f"🚑 **Unidades disponibles:** {cantidad}\n📞 **Pendientes de avisos del 911:** {random.randint(0,3)}\n❤️ **Personal médico operativo:** {cantidad} {'médico' if cantidad == 1 else 'médicos'}\n🟢 **Estado operativo:** {'Operativo' if cantidad > 0 else 'No disponible'}"
            footer = "Servicio de emergencias médicas de Los Santos."
        else:  # lssd
            rol_lssd = ctx.guild.get_role(ROL_SHERIFF_ID)
            if rol_lssd:
                await ctx.send(rol_lssd.mention)
            estado = "🟢 ACTIVO" if cantidad > 0 else "🔴 SATURADO"
            desc = f"🌵 **Patrullaje rural activo:** {cantidad} {'unidad' if cantidad == 1 else 'unidades'}\n🚓 **Supervisión de carreteras:** {'Activa' if cantidad > 0 else 'Inactiva'}\n⚠️ **Atención a emergencias fuera de ciudad:** {'Disponible' if cantidad > 0 else 'No disponible'}\n🟢 **Estado operativo:** {'Operativo' if cantidad > 0 else 'No disponible'}"
            footer = "Sheriff's Department - Condado de Blaine"
        embed = discord.Embed(
            title=f"🚨 DISPONIBILIDAD {servicio.upper()} 🚨",
            description=f"📡 Estado Operativo: **{estado}**\n\n{desc}\n\n━━━━━━━━━━━━━━━━━━\n{footer}",
            color=0x00A8FF
        )
        await ctx.send(embed=embed)
        try:
            await ctx.message.delete()
        except:
            pass
        await self.log("DISPO", f"{ctx.author.name} consultó disponibilidad {servicio.upper()}: {cantidad}")

# ==================== SERVIDOR WEB ====================
class WebPanel:
    def __init__(self, bot):
        self.bot = bot
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_hex(16)
        self.setup_routes()

    def run_async_db(self, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head><title>Nova Agora RP</title><style>body{background:#1a1a2e;color:#eee;font-family:sans-serif;text-align:center;padding:50px;} .btn{background:#ffd700;color:#1a1a2e;padding:15px 30px;border-radius:50px;text-decoration:none;margin:10px;display:inline-block;}</style></head>
            <body><h1>⚡ Nova Agora Roleplay ⚡</h1><p>Bot profesional con +30 comandos y 20 trabajos.</p><a href="/login" class="btn">🔐 Panel Usuario</a><a href="https://discord.gg/2RTVjmPwMJ" class="btn">💬 Discord</a><a href="/tienda" class="btn">🛒 Tienda</a></body></html>
            ''')
        @self.app.route('/tienda')
        def tienda():
            return "<h1>Tienda Nova Agora</h1><p>Usa -comprar en Discord.</p><a href='/'>Volver</a>"
        @self.app.route('/login', methods=['GET','POST'])
        def login():
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                user = self.run_async_db(db.get_web_user(username))
                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    return redirect('/perfil')
                flash('Credenciales inválidas')
            return render_template_string('<form method="post"><input name="username" placeholder="Usuario"><input name="password" type="password"><button>Entrar</button></form><a href="/register">Registrarse</a>')
        @self.app.route('/register', methods=['GET','POST'])
        def register():
            if request.method == 'POST':
                username = request.form['username']
                password = request.form['password']
                if self.run_async_db(db.get_web_user(username)):
                    flash('Usuario existe')
                    return redirect('/register')
                hash_pw = generate_password_hash(password)
                self.run_async_db(db.create_web_user(username, hash_pw))
                flash('Registro exitoso')
                return redirect('/login')
            return '<form method="post"><input name="username"><input name="password" type="password"><button>Registrar</button></form>'
        @self.app.route('/perfil')
        def perfil():
            if 'user_id' not in session:
                return redirect('/login')
            user_id = session['user_id']
            web_user = self.run_async_db(db.get_web_user_by_id(user_id))
            if not web_user:
                return redirect('/login')
            discord_id = web_user.get('discord_id')
            if discord_id:
                eco = self.run_async_db(db.get_economy(discord_id))
                inv = self.run_async_db(db.get_inventory(discord_id, "personal"))
                nivel = self.run_async_db(db.get_nivel(discord_id))
            else:
                eco = {"cash":0,"bank":0,"black_money":0}
                inv = {}
                nivel = {"nivel":0,"xp":0}
            return render_template_string(f'<h1>Perfil de {web_user["username"]}</h1><p>Efectivo: ${eco["cash"]}<br>Banco: ${eco["bank"]}<br>Dinero negro: ${eco["black_money"]}<br>Nivel: {nivel["nivel"]}<br>XP: {nivel["xp"]}</p><h2>Inventario</h2><ul>{"".join(f"<li>{i} x{c}</li>" for i,c in inv.items()) or "<li>Vacío</li>"}</ul><a href="/logout">Cerrar sesión</a>')
        @self.app.route('/logout')
        def logout():
            session.clear()
            return redirect('/')
        @self.app.route('/blacklist', methods=['GET','POST'])
        def blacklist():
            token = request.args.get('token')
            if token != ADMIN_TOKEN:
                return 'Acceso denegado'
            if request.method == 'POST':
                action = request.form['action']
                uid = int(request.form['user_id'])
                if action == 'add':
                    self.run_async_db(db.add_to_blacklist(uid, request.form.get('reason',''), 0))
                    self.run_async_db(db.update_user_state(uid, banned=True))
                elif action == 'remove':
                    self.run_async_db(db.remove_from_blacklist(uid))
                    self.run_async_db(db.update_user_state(uid, banned=False))
                return redirect(f'/blacklist?token={ADMIN_TOKEN}')
            blacklist = self.run_async_db(db.get_blacklist())
            return render_template_string(f'<h1>Blacklist</h1><form method="post"><input name="user_id" placeholder="ID"><input name="reason" placeholder="Razón"><button name="action" value="add">Añadir</button></form><ul>{"".join(f"<li>{b['user_id']} - {b['reason']} <form method='post' style='display:inline'><input type='hidden' name='user_id' value='{b['user_id']}'><button name='action' value='remove'>Quitar</button></form></li>" for b in blacklist)}</ul>')
        @self.app.route('/owner/emojis', methods=['GET','POST'])
        def owner_emojis():
            token = request.args.get('token')
            if token != ADMIN_TOKEN:
                return 'Acceso denegado'
            if request.method == 'POST':
                key = request.form['key']
                emoji = request.form['emoji']
                self.run_async_db(db.set_emoji(key, emoji))
                return redirect(f'/owner/emojis?token={ADMIN_TOKEN}')
            emojis = self.run_async_db(db.get_all_emojis())
            return render_template_string(f'<h1>Gestión de emojis</h1><form method="post"><select name="key">{"".join(f"<option value='{k}'>{k}</option>" for k in DEFAULT_EMOJIS.keys())}</select><input name="emoji" placeholder="Nuevo emoji"><button>Actualizar</button></form><ul>{"".join(f"<li>{k}: {v}</li>" for k,v in emojis.items())}</ul>')

    def run(self):
        threading.Thread(target=lambda: self.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()

# ==================== INTENTS Y BOT ====================
def get_pre(bot, msg):
    try:
        with open('prefixes.json', 'r') as f:
            prefijos = json.load(f)
            return prefijos.get(str(msg.guild.id), DEFAULT_PREFIX)
    except:
        return DEFAULT_PREFIX

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.guilds = True
intents.guild_messages = True
intents.webhooks = True
bot = commands.Bot(command_prefix=get_pre, intents=intents, help_command=None)

@bot.tree.command(name="anuncios", description="Publica un anuncio oficial del servidor (solo Administración/Equipo Especial)")
@app_commands.describe(mensaje="Mensaje del anuncio")
async def anuncios(interaction: discord.Interaction, mensaje: str):
    roles_permitidos = {ROL_ADMIN_ID, ROL_EQUIPO_ESPECIAL_ID}
    tiene_permiso = any(r.id in roles_permitidos for r in interaction.user.roles) or interaction.user.guild_permissions.administrator
    if not tiene_permiso:
        return await interaction.response.send_message(embed=embed_error("No tienes permiso para usar este comando."), ephemeral=True)
    embed = discord.Embed(color=0x2B2D31, timestamp=datetime.now())
    embed.set_author(name="NOVA DEVELOPERS", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
    embed.add_field(name="📢 ANUNCIO ADMINISTRATIVO", value=mensaje, inline=False)
    embed.add_field(name="\u200b", value="━━━━━━━━━━━━━━━━━━━━\n📣 Sistema oficial de comunicaciones\n⚡ Mantente atento a próximas novedades", inline=False)
    embed.set_footer(text="Nova Agora RP • Administración Oficial")
    await interaction.response.send_message(content="@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    if bot.guilds:
        guild = bot.guilds[0]
        for role_id in [ROL_INICIADOR_ID, ROL_EQUIPO_ESPECIAL_ID, ROL_DASHBOARD_ID, ROL_LSPD_OPERATIVO_ID, ROL_LSMD_ID, ROL_SHERIFF_ID, ROL_USUARIO_ID, ROL_MINERO_ID, ROL_AUTOBUSERO_ID, ROL_CHATARRERO_ID, ROL_MAFIA_ID, ROL_MAFIA_ADMIN_ID]:
            if role_id != 0 and not guild.get_role(role_id):
                print(f"⚠️ Advertencia: El rol con ID {role_id} no existe. Crea los roles necesarios.")
    try:
        for guild in bot.guilds:
            await bot.tree.sync(guild=discord.Object(id=guild.id))
            print(f"✅ Slash commands sincronizados en {guild.name}")
        await bot.tree.sync()
        print("✅ Slash commands globales sincronizados.")
    except Exception as e:
        print(f"❌ Error al sincronizar slash commands: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    await ctx.send(embed=embed_error(f"Error: {str(error)[:100]}"))

async def main():
    async with bot:
        await db.init()
        # Cargar todos los cogs
        await bot.add_cog(Principal(bot))
        await bot.add_cog(Drogas(bot))
        await bot.add_cog(Vehiculos(bot))
        await bot.add_cog(Armas(bot))
        await bot.add_cog(Mercado(bot))
        await bot.add_cog(Casino(bot))
        await bot.add_cog(Atracos(bot))
        await bot.add_cog(Preparatorias(bot))
        await bot.add_cog(Banco(bot))
        await bot.add_cog(Multas(bot))
        await bot.add_cog(PDA(bot))
        await bot.add_cog(Movil(bot))
        await bot.add_cog(Redes(bot))
        await bot.add_cog(WhatsApp(bot))
        await bot.add_cog(Periodico(bot))
        await bot.add_cog(Admin(bot))
        await bot.add_cog(Roleplay(bot))
        await bot.add_cog(Hosting(bot))
        await bot.add_cog(Soporte(bot))
        await bot.add_cog(Ayuda(bot))
        await bot.add_cog(Moderacion(bot))
        await bot.add_cog(Niveles(bot))
        await bot.add_cog(TicketSystem(bot))
        await bot.add_cog(AntiRaid(bot))
        await bot.add_cog(CheckUsers(bot))
        await bot.add_cog(TabletPolicial(bot))
        await bot.add_cog(DNI(bot))
        await bot.add_cog(Trabajos(bot))
        await bot.add_cog(Kits(bot))
        await bot.add_cog(OwnerMenu(bot))
        await bot.add_cog(Dashboard(bot))
        await bot.add_cog(Alertas(bot))
        await bot.add_cog(Disponibilidad(bot))

        hosting_cog = bot.get_cog("Hosting")
        if hosting_cog:
            hosting_cog.check_expiry.start()
        web = WebPanel(bot)
        web.run()
        print(f"🌐 Panel web: http://localhost:5000  |  Token admin: {ADMIN_TOKEN}")
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
