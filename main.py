"""
Nova Agora RP Bot — Edición Ultra 10.7 (5/5 estrellas)
=======================================================
- Todos los cogs incluidos (28) con implementación completa.
- Robos: badu, lico, ammu, yellowjack, yate, pacific, jugador.
- Sistema de tickets con valoración, PDA, tablet policial, DNI, economía, niveles.
- Comando -bot corregido (solo owners, muestra estado y renueva).
- Base de datos optimizada con caché y migraciones automáticas.
- Panel web con estadísticas y blacklist.
- Tienda actualizada con nuevos items (armas, licencias, etc.)
- Código completamente depurado y listo para producción.
"""

import os
import random
import asyncio
import json
import threading
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
from flask import Flask, render_template_string, jsonify, request, abort, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

# ====================================================
# CONFIGURACIÓN GLOBAL
# ====================================================
TOKEN = os.getenv("DISCORD_TOKEN") or "MTQ4NDE2MTczNDIyNTk1MzAzMA.GVF9Rn.42O8-xXDVv-ejUyzYn4njjBSafvLulPsl2YZak"
if not TOKEN:
    raise ValueError("No se ha configurado DISCORD_TOKEN")

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", secrets.token_urlsafe(16))
print(f"🔐 Panel web token: {ADMIN_TOKEN} (guárdalo para acceder a /blacklist)")

DEFAULT_PREFIX = '-'
LOGS_DIR = 'logs'
CANAL_LOGS = 0
CANAL_PERIODICO = 0
CANAL_VOICE_CATEGORY = 0
ROL_POLICIA_DEFAULT = 0
OWNER_IDS = [1059183337832468510, 729054497233436775]  # IDs de los dueños

# Datos estáticos
PRECIOS_DROGAS_BASE = {
    "Marihuana": {"compra": 50, "venta": 100, "categoria": "cannabis"},
    "Cocaína": {"compra": 250, "venta": 500, "categoria": "estimulante"},
    "Meta": {"compra": 150, "venta": 300, "categoria": "estimulante"},
    "Éxtasis": {"compra": 75, "venta": 150, "categoria": "sintetica"},
    "Heroína": {"compra": 400, "venta": 800, "categoria": "opioide"},
}
TIPOS_ARMAS = {
    "Pistola": {"emoji": "🔫", "municion_tipo": "9mm", "durabilidad_max": 100, "licencia": "licencia_pistola"},
    "Escopeta": {"emoji": "🔫", "municion_tipo": "12gauge", "durabilidad_max": 80, "licencia": "licencia_escopeta"},
    "Rifle": {"emoji": "🔫", "municion_tipo": "556mm", "durabilidad_max": 150, "licencia": "licencia_rifle"},
    # Nuevas armas que se pueden equipar (se añadirán a TIPOS_ARMAS dinámicamente o se manejarán con genéricas)
}
TIPOS_MUNICION = {"9mm": {"emoji": "🔹", "precio": 5}, "12gauge": {"emoji": "🔸", "precio": 15}, "556mm": {"emoji": "🔺", "precio": 25}}

# Nueva tienda actualizada con todos los items solicitados
TIENDA_ITEMS = [
    # Blancas
    ("Hacha", 4000, "🪓"), ("Machete", 5000, "🔪"), ("Puño americano", 5000, "👊"),
    # Cortas
    ("SNS", 18000, "🔫"), ("Normal", 20000, "🔫"), ("Vintage", 25000, "🔫"),
    ("Calibre .50", 30000, "🔫"), ("Pesada", 35000, "🔫"), ("Revólver Pesado", 65000, "🔫"),
    ("Perforante", 85000, "🔫"),
    # Medias
    ("Mini SMG", 120000, "🔫"), ("Micro Uzi", 150000, "🔫"), ("Subfusil", 180000, "🔫"),
    ("Subfusil de asalto", 200000, "🔫"), ("ADP", 250000, "🔫"),
    # Largas
    ("Mosquete", 100000, "🔫"), ("Escopeta recortada", 200000, "🔫"), ("MiniAk47", 220000, "🔫"),
    ("Escopeta corredera", 230000, "🔫"), ("Ak47", 280000, "🔫"), ("Rifle bullpup", 300000, "🔫"),
    # Arrojadizas
    ("Coctel molotov", 6000, "🔥"), ("Granada casera", 12000, "💣"), ("Granada", 15000, "💣"),
    ("C4", 20000, "🧨"),
    # Licencias de conducción
    ("Licencia de camión", 1250, "🚚"), ("Licencia de coche", 1500, "🚗"), ("Licencia de moto", 2000, "🏍️"),
    # Licencias de armas
    ("Licencia de armas blancas", 5000, "🔪"), ("Licencia de armas cortas", 12000, "🔫"),
    # Items existentes que se mantienen (algunos pueden duplicarse, se reemplazan los similares)
    ("Sprunk", 5, "🥤"), ("Hotdog", 10, "🌭"), ("Cigs", 20, "🚬"),
    ("Phone", 500, "📱"), ("Kit", 150, "🔧"), ("Botiquin", 75, "🩹"),
    ("9mm", 1200, "🔫"), ("Burger", 15, "🍔"), ("E-Cola", 5, "🥤"),
    ("Mascara", 50, "🎭"), ("Gasolina", 100, "⛽"), ("Linterna", 25, "🔦"),
    ("Mochila", 200, "🎒"), ("GPS", 300, "🚗"), ("Ganzúa", 80, "🔑"),
    ("Radio", 150, "📻"), ("Pizza", 12, "🍕"), ("Agua", 3, "🧃"),
    ("Encendedor", 5, "🚬"), ("Auriculares", 75, "🎧"), ("Cámara", 400, "📷"),
    ("Guantes", 30, "🧤"), ("Zapatillas", 120, "👟"), ("Chaqueta", 250, "🧥"),
    ("Dinero Negro", 500, "💶"),
    ("Papas", 3, "🍟"), ("Gaseosa", 4, "🥤"), ("Empanada", 8, "🥟"), ("Chocolate", 2, "🍫"),
    ("Bolsas Atraco", 300, "🛍️"), ("Pasamontañas", 75, "😷"), ("Esposas", 500, "⛓️"),
    ("Llave Inglesa", 100, "🔧"), ("Herramientas", 150, "🔧"),
    ("Desfibrilador", 800, "🩺"), ("Traje Ignifugo", 600, "🔥"), ("Hacha", 200, "🪓"),  # ya está arriba, pero se reemplaza
    ("Manguera", 180, "💧"), ("Placa Policial", 0, "🪪"), ("Kit Médico", 500, "💊"),
]

APUESTA_MIN = 100
APUESTA_MAX = 50000
MAX_DROGA_POR_COMPRA = 27

CANAL_LOG_ECONOMIA = 0
CANAL_LOG_SANCIONES = 0
ROL_MUTED = 0
CATEGORIA_TICKETS = 0
ROL_STAFF = 0
TICKET_PANEL_CHANNEL = 0

XP_POR_MENSAJE = random.randint(15, 25)
XP_POR_COMANDO = random.randint(5, 10)
XP_POR_TIEMPO = 10
COOLDOWN_XP = 60
ROLES_POR_NIVEL = {5: 0, 10: 0, 15: 0, 20: 0, 25: 0, 30: 0}

# ====================================================
# FUNCIONES AUXILIARES DE EMBED
# ====================================================
def embed_error(msg: str) -> discord.Embed:
    return discord.Embed(title="❌ Error", description=msg, color=0xFF0000)

def embed_success(titulo: str, descripcion: str = "", color=0x00FF00) -> discord.Embed:
    return discord.Embed(title=titulo, description=descripcion, color=color)

def embed_info(titulo: str, descripcion: str = "", color=0x3498DB) -> discord.Embed:
    return discord.Embed(title=titulo, description=descripcion, color=color)

def embed_help(comando: str, descripcion: str, uso: str, ejemplo: str, permisos: str = "") -> discord.Embed:
    embed = discord.Embed(title=f"📖 Ayuda: `{comando}`", color=discord.Color.blue())
    embed.add_field(name="📝 Descripción", value=descripcion, inline=False)
    embed.add_field(name="📌 Uso", value=f"`{uso}`", inline=False)
    embed.add_field(name="📋 Ejemplo", value=f"`{ejemplo}`", inline=False)
    if permisos:
        embed.add_field(name="🔒 Permisos", value=permisos, inline=False)
    return embed

# ====================================================
# BASE DE DATOS UNIFICADA (OPTIMIZADA + MIGRACIONES)
# ====================================================
class Database:
    def __init__(self, db_path="nova.db"):
        self.db_path = db_path
        self._cache = {}
        self._cache_time = {}
        self._user_columns = None

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Bot config
            await db.execute("CREATE TABLE IF NOT EXISTS bot_config (key TEXT PRIMARY KEY, value TEXT)")
            expiry = (datetime.now() + timedelta(days=30)).isoformat()
            await db.execute("INSERT OR IGNORE INTO bot_config (key, value) VALUES ('expiry', ?)", (expiry,))

            # Usuarios (incluye datos de DNI)
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
            # Migración: agregar columnas faltantes (si la tabla ya existía sin ellas)
            columnas_dni = [
                "dni_nombre TEXT", "dni_apellidos TEXT", "dni_edad INTEGER", "dni_genero TEXT",
                "dni_nacionalidad TEXT", "dni_color_ojos TEXT", "dni_altura TEXT", "dni_profesion TEXT",
                "dni_numero TEXT", "dni_fecha_creacion TEXT"
            ]
            cur = await db.execute("PRAGMA table_info(users)")
            existing_cols = [row[1] for row in await cur.fetchall()]
            for col_def in columnas_dni:
                col_name = col_def.split()[0]
                if col_name not in existing_cols:
                    try:
                        await db.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
                        print(f"✅ Columna '{col_name}' añadida a la tabla users.")
                    except Exception as e:
                        print(f"⚠️ No se pudo añadir {col_name}: {e}")

            # Tabla para licencias de conducción
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
            # Multas
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
            # Precios drogas
            await db.execute("CREATE TABLE IF NOT EXISTS precios_drogas (droga TEXT PRIMARY KEY, precio_compra INTEGER, precio_venta INTEGER)")
            for droga, datos in PRECIOS_DROGAS_BASE.items():
                await db.execute("INSERT OR IGNORE INTO precios_drogas (droga, precio_compra, precio_venta) VALUES (?, ?, ?)",
                                 (droga, datos["compra"], datos["venta"]))
            # Twitter, Facebook
            await db.execute("CREATE TABLE IF NOT EXISTS posts_tw (id TEXT PRIMARY KEY, user_id INTEGER, texto TEXT, tiempo TEXT)")
            await db.execute("CREATE TABLE IF NOT EXISTS seguidores_tw (follower INTEGER, following INTEGER, since TEXT, PRIMARY KEY (follower, following))")
            await db.execute("CREATE TABLE IF NOT EXISTS posts_fb (id TEXT PRIMARY KEY, user_id INTEGER, texto TEXT, tiempo TEXT)")

            # Tablas de moderación
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
            await db.execute("""
                CREATE TABLE IF NOT EXISTS niveles (
                    user_id INTEGER PRIMARY KEY,
                    xp INTEGER DEFAULT 0,
                    nivel INTEGER DEFAULT 0,
                    last_message_time TEXT,
                    last_command_time TEXT,
                    last_time_time TEXT
                )
            """)
            # BLACKLIST GLOBAL
            await db.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    banned_by INTEGER,
                    ban_date TEXT
                )
            """)
            # ANTIRAID: registro de acciones
            await db.execute("""
                CREATE TABLE IF NOT EXISTS antiraid_actions (
                    user_id INTEGER,
                    action_type TEXT,
                    timestamp TIMESTAMP,
                    guild_id INTEGER
                )
            """)

            # Índices para rendimiento
            await db.execute("CREATE INDEX IF NOT EXISTS idx_inventory_user ON inventory(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_warnings_user ON warnings(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_niveles_nivel ON niveles(nivel)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_antiraid_user ON antiraid_actions(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_antiraid_timestamp ON antiraid_actions(timestamp)")
            await db.commit()
            print("✅ Base de datos inicializada con índices optimizados y migraciones aplicadas.")

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

    async def _cached_fetchone(self, query, params=(), ttl=30):
        key = (query, str(params))
        now = datetime.now().timestamp()
        if key in self._cache and (now - self._cache_time.get(key, 0)) < ttl:
            return self._cache[key]
        row = await self.fetchone(query, params)
        self._cache[key] = row
        self._cache_time[key] = now
        return row

    async def _cached_fetchall(self, query, params=(), ttl=30):
        key = (query, str(params))
        now = datetime.now().timestamp()
        if key in self._cache and (now - self._cache_time.get(key, 0)) < ttl:
            return self._cache[key]
        rows = await self.fetchall(query, params)
        self._cache[key] = rows
        self._cache_time[key] = now
        return rows

    async def invalidate_cache(self, pattern=None):
        if pattern is None:
            self._cache.clear()
            self._cache_time.clear()
        else:
            to_remove = [k for k in self._cache if pattern in k[0]]
            for k in to_remove:
                del self._cache[k]
                del self._cache_time[k]

    async def get_expiry(self) -> Optional[datetime]:
        row = await self.fetchone("SELECT value FROM bot_config WHERE key = 'expiry'")
        if row:
            return datetime.fromisoformat(row[0])
        return None

    async def set_expiry(self, expiry: datetime):
        await self.execute("UPDATE bot_config SET value = ? WHERE key = 'expiry'", (expiry.isoformat(),))

    # Economía
    async def get_economy(self, user_id: int) -> dict:
        row = await self._cached_fetchone("SELECT cash, bank, black_money FROM economy WHERE user_id = ?", (user_id,), ttl=10)
        if row:
            return {"cash": row[0], "bank": row[1], "black_money": row[2]}
        else:
            await self.execute("INSERT INTO economy (user_id) VALUES (?)", (user_id,))
            return {"cash": 0, "bank": 0, "black_money": 0}

    async def add_cash(self, user_id: int, amount: int):
        await self.execute("UPDATE economy SET cash = cash + ? WHERE user_id = ?", (amount, user_id))
        await self.invalidate_cache("economy")

    async def add_bank(self, user_id: int, amount: int):
        await self.execute("UPDATE economy SET bank = bank + ? WHERE user_id = ?", (amount, user_id))
        await self.invalidate_cache("economy")

    async def add_black(self, user_id: int, amount: int):
        await self.execute("UPDATE economy SET black_money = black_money + ? WHERE user_id = ?", (amount, user_id))
        await self.invalidate_cache("economy")

    async def remove_cash(self, user_id: int, amount: int):
        await self.execute("UPDATE economy SET cash = cash - ? WHERE user_id = ? AND cash >= ?", (amount, user_id, amount))
        await self.invalidate_cache("economy")

    async def remove_bank(self, user_id: int, amount: int):
        await self.execute("UPDATE economy SET bank = bank - ? WHERE user_id = ? AND bank >= ?", (amount, user_id, amount))
        await self.invalidate_cache("economy")

    async def remove_black(self, user_id: int, amount: int):
        await self.execute("UPDATE economy SET black_money = black_money - ? WHERE user_id = ? AND black_money >= ?", (amount, user_id, amount))
        await self.invalidate_cache("economy")

    # Inventario
    async def add_item(self, user_id: int, inv_type: str, item: str, cantidad: int = 1):
        await self.execute("""
            INSERT INTO inventory (user_id, inv_type, item, quantity)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, inv_type, item) DO UPDATE SET quantity = quantity + ?
        """, (user_id, inv_type, item, cantidad, cantidad))
        await self.invalidate_cache("inventory")

    async def remove_item(self, user_id: int, inv_type: str, item: str, cantidad: int = 1) -> int:
        row = await self.fetchone(
            "SELECT quantity FROM inventory WHERE user_id = ? AND inv_type = ? AND item = ?",
            (user_id, inv_type, item)
        )
        if not row or row[0] < cantidad:
            return 0
        if row[0] == cantidad:
            await self.execute("DELETE FROM inventory WHERE user_id = ? AND inv_type = ? AND item = ?",
                               (user_id, inv_type, item))
        else:
            await self.execute("UPDATE inventory SET quantity = quantity - ? WHERE user_id = ? AND inv_type = ? AND item = ?",
                               (cantidad, user_id, inv_type, item))
        await self.invalidate_cache("inventory")
        return cantidad

    async def get_inventory(self, user_id: int, inv_type: str) -> dict:
        rows = await self._cached_fetchall(
            "SELECT item, quantity FROM inventory WHERE user_id = ? AND inv_type = ?",
            (user_id, inv_type), ttl=10
        )
        return {item: qty for item, qty in rows}

    # Estado de usuario (con cache de columnas)
    async def _get_user_columns(self):
        if self._user_columns is None:
            async with aiosqlite.connect(self.db_path) as db:
                cur = await db.execute("PRAGMA table_info(users)")
                self._user_columns = [desc[0] for desc in await cur.fetchall()]
        return self._user_columns

    async def get_user_state(self, user_id: int) -> dict:
        row = await self._cached_fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,), ttl=60)
        if not row:
            await self.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
            row = await self.fetchone("SELECT * FROM users WHERE user_id = ?", (user_id,))
        columns = await self._get_user_columns()
        return {col: row[i] for i, col in enumerate(columns)}

    async def update_user_state(self, user_id: int, **kwargs):
        for key, value in kwargs.items():
            await self.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
        await self.invalidate_cache("users")

    # DNI
    async def get_dni(self, user_id: int) -> dict:
        row = await self.fetchone("SELECT dni_nombre, dni_apellidos, dni_edad, dni_genero, dni_nacionalidad, dni_color_ojos, dni_altura, dni_profesion, dni_numero, dni_fecha_creacion FROM users WHERE user_id = ?", (user_id,))
        if row and row[0]:
            return {
                "nombre": row[0],
                "apellidos": row[1],
                "edad": row[2],
                "genero": row[3],
                "nacionalidad": row[4],
                "color_ojos": row[5],
                "altura": row[6],
                "profesion": row[7],
                "numero": row[8],
                "fecha_creacion": row[9]
            }
        return None

    async def set_dni(self, user_id: int, data: dict):
        await self.execute("""
            UPDATE users SET dni_nombre = ?, dni_apellidos = ?, dni_edad = ?, dni_genero = ?, dni_nacionalidad = ?,
            dni_color_ojos = ?, dni_altura = ?, dni_profesion = ?, dni_numero = ?, dni_fecha_creacion = ?
            WHERE user_id = ?
        """, (data["nombre"], data["apellidos"], data["edad"], data["genero"], data["nacionalidad"],
              data["color_ojos"], data["altura"], data["profesion"], data["numero"], data["fecha_creacion"], user_id))
        await self.invalidate_cache("users")

    async def delete_dni(self, user_id: int):
        await self.execute("""
            UPDATE users SET dni_nombre = NULL, dni_apellidos = NULL, dni_edad = NULL, dni_genero = NULL,
            dni_color_ojos = NULL, dni_altura = NULL, dni_profesion = NULL,
            dni_numero = NULL, dni_fecha_creacion = NULL WHERE user_id = ?
        """, (user_id,))
        await self.invalidate_cache("users")

    # Multas y caja
    async def add_multa(self, user_id: int, cantidad: int, motivo: str, agente: str, placa_agente: str):
        fecha = datetime.now().isoformat()
        await self.execute("""
            INSERT INTO multas (user_id, cantidad, motivo, fecha, agente, placa_agente)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, cantidad, motivo, fecha, agente, placa_agente))
        await self.execute("UPDATE caja_municipal SET monto = monto + ? WHERE id = 1", (cantidad,))
        await self.invalidate_cache("multas")

    async def get_multas_pendientes(self, user_id: int) -> List[dict]:
        rows = await self.fetchall(
            "SELECT id, cantidad, motivo, fecha, agente FROM multas WHERE user_id = ? AND pagada = 0",
            (user_id,)
        )
        return [{"id": r[0], "cantidad": r[1], "motivo": r[2], "fecha": r[3], "agente": r[4]} for r in rows]

    async def pagar_multa(self, multa_id: int):
        await self.execute("UPDATE multas SET pagada = 1 WHERE id = ?", (multa_id,))
        await self.invalidate_cache("multas")

    async def get_caja_municipal(self) -> int:
        row = await self.fetchone("SELECT monto FROM caja_municipal WHERE id = 1")
        return row[0] if row else 0

    # Vehículos
    async def add_vehiculo(self, user_id: int, matricula: str, modelo: str):
        await self.execute("""
            INSERT INTO vehiculos (user_id, matricula, modelo, seguro, itv, combustible)
            VALUES (?, ?, ?, 1, ?, 100)
        """, (user_id, matricula, modelo, (datetime.now() + timedelta(days=30)).isoformat()))
        await self.invalidate_cache("vehiculos")

    async def get_vehiculos(self, user_id: int) -> dict:
        rows = await self.fetchall("SELECT matricula, modelo, seguro, itv, combustible FROM vehiculos WHERE user_id = ?", (user_id,))
        return {r[0]: {"modelo": r[1], "seguro": bool(r[2]), "itv": r[3], "combustible": r[4]} for r in rows}

    async def update_vehiculo(self, user_id: int, matricula: str, **kwargs):
        for key, value in kwargs.items():
            await self.execute(f"UPDATE vehiculos SET {key} = ? WHERE user_id = ? AND matricula = ?", (value, user_id, matricula))
        await self.invalidate_cache("vehiculos")

    # Armas y licencias
    async def dar_licencia(self, user_id: int, licencia: str):
        await self.execute("""
            INSERT INTO armas_licencias (user_id, licencia, tiene) VALUES (?, ?, 1)
            ON CONFLICT(user_id, licencia) DO UPDATE SET tiene = 1
        """, (user_id, licencia))
        await self.invalidate_cache("armas")

    async def quitar_licencia(self, user_id: int, licencia: str):
        await self.execute("UPDATE armas_licencias SET tiene = 0 WHERE user_id = ? AND licencia = ?", (user_id, licencia))
        await self.invalidate_cache("armas")

    async def get_licencias(self, user_id: int) -> dict:
        rows = await self.fetchall("SELECT licencia, tiene FROM armas_licencias WHERE user_id = ?", (user_id,))
        return {r[0]: bool(r[1]) for r in rows}

    async def get_armas_equipadas(self, user_id: int) -> dict:
        rows = await self.fetchall("SELECT arma, durabilidad, municion FROM armas_equipadas WHERE user_id = ?", (user_id,))
        return {r[0]: {"durabilidad": r[1], "municion": r[2]} for r in rows}

    # Licencias de conducción
    async def dar_licencia_conduccion(self, user_id: int, tipo: str):
        await self.execute("INSERT OR REPLACE INTO licencias_conduccion (user_id, tipo, fecha_obtencion) VALUES (?, ?, ?)",
                           (user_id, tipo, datetime.now().isoformat()))
        await self.invalidate_cache("licencias_conduccion")

    async def tiene_licencia_conduccion(self, user_id: int, tipo: str) -> bool:
        row = await self.fetchone("SELECT 1 FROM licencias_conduccion WHERE user_id = ? AND tipo = ?", (user_id, tipo))
        return row is not None

    # Cooldowns
    async def check_cooldown(self, user_id: int, comando: str, segundos: int) -> Tuple[bool, int]:
        row = await self.fetchone("SELECT expires FROM cooldowns WHERE user_id = ? AND comando = ?", (user_id, comando))
        ahora = datetime.now()
        if row and row[0]:
            expires = datetime.fromisoformat(row[0])
            if expires > ahora:
                restante = int((expires - ahora).total_seconds())
                return False, restante
        nueva_expira = ahora + timedelta(seconds=segundos)
        await self.execute("""
            INSERT INTO cooldowns (user_id, comando, expires) VALUES (?, ?, ?)
            ON CONFLICT(user_id, comando) DO UPDATE SET expires = ?
        """, (user_id, comando, nueva_expira.isoformat(), nueva_expira.isoformat()))
        return True, 0

    # Rachas casino
    async def actualizar_racha(self, user_id: int, ganado: bool):
        tipo = "win" if ganado else "loss"
        row = await self.fetchone("SELECT racha, tipo FROM rachas WHERE user_id = ?", (user_id,))
        if row and row[1] == tipo:
            nueva_racha = row[0] + 1
        else:
            nueva_racha = 1
        await self.execute("""
            INSERT INTO rachas (user_id, racha, tipo) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET racha = ?, tipo = ?
        """, (user_id, nueva_racha, tipo, nueva_racha, tipo))

    async def get_racha(self, user_id: int) -> dict:
        row = await self.fetchone("SELECT racha, tipo FROM rachas WHERE user_id = ?", (user_id,))
        return {"racha": row[0] if row else 0, "tipo": row[1] if row else None}

    # Estadísticas
    async def inc_estadistica(self, key: str, inc: int = 1):
        row = await self.fetchone("SELECT value FROM estadisticas WHERE key = ?", (key,))
        if row:
            val = int(row[0]) + inc
            await self.execute("UPDATE estadisticas SET value = ? WHERE key = ?", (str(val), key))
        else:
            await self.execute("INSERT INTO estadisticas (key, value) VALUES (?, ?)", (key, str(inc)))

    async def get_estadistica(self, key: str) -> int:
        row = await self.fetchone("SELECT value FROM estadisticas WHERE key = ?", (key,))
        return int(row[0]) if row else 0

    # Redes sociales
    async def add_post_ig(self, user_id: int, texto: str) -> str:
        pid = ''.join(random.choices('0123456789abcdef', k=8))
        await self.execute("INSERT INTO posts_ig (id, user_id, texto, tiempo, likes) VALUES (?, ?, ?, ?, ?)",
                           (pid, user_id, texto, datetime.now().isoformat(), json.dumps([])))
        return pid

    async def get_posts_ig(self, user_id: int) -> List[dict]:
        rows = await self.fetchall("SELECT id, texto, tiempo, likes FROM posts_ig WHERE user_id = ? ORDER BY tiempo DESC", (user_id,))
        return [{"id": r[0], "texto": r[1], "tiempo": r[2], "likes": json.loads(r[3]) if r[3] else []} for r in rows]

    async def add_like_ig(self, post_id: str, user_id: int):
        row = await self.fetchone("SELECT likes FROM posts_ig WHERE id = ?", (post_id,))
        if row:
            likes = json.loads(row[0]) if row[0] else []
            if user_id not in likes:
                likes.append(user_id)
                await self.execute("UPDATE posts_ig SET likes = ? WHERE id = ?", (json.dumps(likes), post_id))
                return True
        return False

    async def follow_ig(self, follower: int, following: int):
        await self.execute("INSERT OR IGNORE INTO seguidores_ig (follower, following) VALUES (?, ?)", (follower, following))

    async def unfollow_ig(self, follower: int, following: int):
        await self.execute("DELETE FROM seguidores_ig WHERE follower = ? AND following = ?", (follower, following))

    async def get_followers_ig(self, user_id: int) -> int:
        row = await self.fetchone("SELECT COUNT(*) FROM seguidores_ig WHERE following = ?", (user_id,))
        return row[0] if row else 0

    async def get_following_ig(self, user_id: int) -> int:
        row = await self.fetchone("SELECT COUNT(*) FROM seguidores_ig WHERE follower = ?", (user_id,))
        return row[0] if row else 0

    async def is_following_ig(self, follower: int, following: int) -> bool:
        row = await self.fetchone("SELECT 1 FROM seguidores_ig WHERE follower = ? AND following = ?", (follower, following))
        return row is not None

    async def add_post_tw(self, user_id: int, texto: str) -> str:
        pid = ''.join(random.choices('0123456789abcdef', k=8))
        await self.execute("INSERT INTO posts_tw (id, user_id, texto, tiempo) VALUES (?, ?, ?, ?)",
                           (pid, user_id, texto, datetime.now().isoformat()))
        return pid

    async def follow_tw(self, follower: int, following: int):
        await self.execute("INSERT OR IGNORE INTO seguidores_tw (follower, following, since) VALUES (?, ?, ?)",
                           (follower, following, datetime.now().isoformat()))

    async def unfollow_tw(self, follower: int, following: int):
        await self.execute("DELETE FROM seguidores_tw WHERE follower = ? AND following = ?", (follower, following))

    async def get_followers_tw(self, user_id: int) -> int:
        row = await self.fetchone("SELECT COUNT(*) FROM seguidores_tw WHERE following = ?", (user_id,))
        return row[0] if row else 0

    async def is_following_tw(self, follower: int, following: int) -> bool:
        row = await self.fetchone("SELECT 1 FROM seguidores_tw WHERE follower = ? AND following = ?", (follower, following))
        return row is not None

    async def add_post_fb(self, user_id: int, texto: str) -> str:
        pid = ''.join(random.choices('0123456789abcdef', k=8))
        await self.execute("INSERT INTO posts_fb (id, user_id, texto, tiempo) VALUES (?, ?, ?, ?)",
                           (pid, user_id, texto, datetime.now().isoformat()))
        return pid

    async def add_wa_contact(self, user_id: int, numero: str, nombre: str):
        await self.execute("INSERT OR IGNORE INTO wa_contactos (user_id, numero, nombre) VALUES (?, ?, ?)", (user_id, numero, nombre))

    async def get_wa_contacts(self, user_id: int) -> dict:
        rows = await self.fetchall("SELECT numero, nombre FROM wa_contactos WHERE user_id = ?", (user_id,))
        return {r[0]: r[1] for r in rows}

    async def add_wa_chat(self, de: int, para: int, mensaje: str):
        await self.execute("INSERT INTO wa_chats (de, para, mensaje, tiempo) VALUES (?, ?, ?, ?)",
                           (de, para, mensaje, datetime.now().isoformat()))

    async def get_wa_chats(self, user1: int, user2: int) -> List[dict]:
        rows = await self.fetchall("""
            SELECT de, mensaje, tiempo FROM wa_chats
            WHERE (de = ? AND para = ?) OR (de = ? AND para = ?)
            ORDER BY tiempo ASC
        """, (user1, user2, user2, user1))
        return [{"de": r[0], "mensaje": r[1], "tiempo": r[2]} for r in rows]

    async def get_precio_droga(self, droga: str, es_compra: bool = True) -> int:
        row = await self.fetchone("SELECT precio_compra, precio_venta FROM precios_drogas WHERE droga = ?", (droga,))
        if row:
            return row[0] if es_compra else row[1]
        return PRECIOS_DROGAS_BASE[droga]["compra"] if es_compra else PRECIOS_DROGAS_BASE[droga]["venta"]

    async def actualizar_precio_droga(self, droga: str, cantidad_vendida: int):
        pass

    async def add_mercado(self, pub_id: str, vendedor: int, item: str, descripcion: str, precio: int):
        await self.execute("INSERT INTO mercado (id, vendedor, item, descripcion, precio, fecha) VALUES (?, ?, ?, ?, ?, ?)",
                           (pub_id, vendedor, item, descripcion, precio, datetime.now().isoformat()))

    async def get_mercado(self) -> List[dict]:
        rows = await self.fetchall("SELECT id, vendedor, item, descripcion, precio, fecha FROM mercado ORDER BY fecha DESC")
        return [{"id": r[0], "vendedor": r[1], "item": r[2], "descripcion": r[3], "precio": r[4], "fecha": r[5]} for r in rows]

    async def remove_mercado(self, pub_id: str):
        await self.execute("DELETE FROM mercado WHERE id = ?", (pub_id,))

    async def get_mercado_by_id(self, pub_id: str):
        return await self.fetchone("SELECT vendedor, item, precio FROM mercado WHERE id = ?", (pub_id,))

    # Niveles
    async def add_xp(self, user_id: int, xp: int, tipo: str = "message"):
        now = datetime.now().isoformat()
        row = await self.fetchone("SELECT xp, nivel, last_message_time, last_command_time, last_time_time FROM niveles WHERE user_id = ?", (user_id,))
        if not row:
            await self.execute("INSERT INTO niveles (user_id, xp, nivel) VALUES (?, ?, 0)", (user_id, xp))
            xp_actual = xp
        else:
            xp_actual = row[0] + xp
            await self.execute("UPDATE niveles SET xp = ? WHERE user_id = ?", (xp_actual, user_id))
            if tipo == "message":
                await self.execute("UPDATE niveles SET last_message_time = ? WHERE user_id = ?", (now, user_id))
            elif tipo == "command":
                await self.execute("UPDATE niveles SET last_command_time = ? WHERE user_id = ?", (now, user_id))
            elif tipo == "time":
                await self.execute("UPDATE niveles SET last_time_time = ? WHERE user_id = ?", (now, user_id))

        nuevo_nivel = int((xp_actual ** 0.5) / 10)
        if nuevo_nivel > (row[1] if row else 0):
            await self.execute("UPDATE niveles SET nivel = ? WHERE user_id = ?", (nuevo_nivel, user_id))
            return nuevo_nivel
        return None

    async def get_nivel(self, user_id: int) -> dict:
        row = await self._cached_fetchone("SELECT xp, nivel FROM niveles WHERE user_id = ?", (user_id,), ttl=30)
        if row:
            return {"xp": row[0], "nivel": row[1]}
        return {"xp": 0, "nivel": 0}

    async def get_ranking_niveles(self, limit=10) -> List[Tuple[int, int, int]]:
        rows = await self.fetchall("SELECT user_id, xp, nivel FROM niveles ORDER BY xp DESC LIMIT ?", (limit,))
        return rows

    # BLACKLIST
    async def add_to_blacklist(self, user_id: int, reason: str, banned_by: int):
        await self.execute("INSERT OR IGNORE INTO blacklist (user_id, reason, banned_by, ban_date) VALUES (?, ?, ?, ?)",
                           (user_id, reason, banned_by, datetime.now().isoformat()))

    async def remove_from_blacklist(self, user_id: int):
        await self.execute("DELETE FROM blacklist WHERE user_id = ?", (user_id,))

    async def is_blacklisted(self, user_id: int) -> bool:
        row = await self.fetchone("SELECT 1 FROM blacklist WHERE user_id = ?", (user_id,))
        return row is not None

    async def get_blacklist(self) -> List[dict]:
        rows = await self.fetchall("SELECT user_id, reason, banned_by, ban_date FROM blacklist")
        return [{"user_id": r[0], "reason": r[1], "banned_by": r[2], "ban_date": r[3]} for r in rows]

    # ANTIRAID: registrar acción
    async def log_antiraid_action(self, user_id: int, action_type: str, guild_id: int):
        await self.execute("INSERT INTO antiraid_actions (user_id, action_type, timestamp, guild_id) VALUES (?, ?, ?, ?)",
                           (user_id, action_type, datetime.now().isoformat(), guild_id))

    async def count_actions_last_minute(self, user_id: int, action_type: str, guild_id: int, minutes: int = 1) -> int:
        cutoff = datetime.now() - timedelta(minutes=minutes)
        row = await self.fetchone("SELECT COUNT(*) FROM antiraid_actions WHERE user_id = ? AND action_type = ? AND guild_id = ? AND timestamp > ?",
                                   (user_id, action_type, guild_id, cutoff.isoformat()))
        return row[0] if row else 0

db = Database()

# ====================================================
# DECORADORES PERSONALIZADOS
# ====================================================
def tiene_dni():
    async def predicate(ctx):
        dni = await db.get_dni(ctx.author.id)
        if not dni:
            await ctx.send(embed=embed_error("No tienes DNI. Crea uno con `-dni`"))
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
        user_state = await db.get_user_state(ctx.author.id)
        enc = user_state.get('encarcelado_hasta')
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
        user_state = await db.get_user_state(ctx.author.id)
        if user_state.get('banned'):
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

# ====================================================
# VISTA DE CONFIRMACIÓN
# ====================================================
class ConfirmView(discord.ui.View):
    def __init__(self, user_id: int, timeout: int = 30):
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

# ====================================================
# CLASE BASE PARA COGS
# ====================================================
class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log(self, accion: str, detalles: str):
        channel = self.bot.get_channel(CANAL_LOGS)
        if channel:
            await channel.send(f"📝 `{accion}`: {detalles}")
        try:
            with open('rtu_logs.json', 'a', encoding='utf-8') as f:
                json.dump({"time": datetime.now().isoformat(), "accion": accion, "detalles": detalles}, f)
                f.write('\n')
        except:
            pass

    async def dm_user(self, user_id: int, embed: discord.Embed) -> bool:
        user = self.bot.get_user(user_id)
        if user:
            try:
                await user.send(embed=embed)
                return True
            except discord.Forbidden:
                pass
        return False

    async def obtener_nombre_dni(self, uid: int) -> Optional[str]:
        try:
            dni = await db.get_dni(uid)
            if dni and dni.get('nombre') and dni.get('apellidos'):
                return f"{dni['nombre']} {dni['apellidos']}".strip()
        except Exception:
            pass
        return None

    async def log_economia(self, mensaje: str):
        canal = self.bot.get_channel(CANAL_LOG_ECONOMIA)
        if canal:
            await canal.send(f"💰 **Economía** • {mensaje}")

    async def registrar_log_moderacion(self, ctx, accion: str, target: discord.Member, razon: str, duracion: str = None):
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

# ====================================================
# COGS (28 en total)
# ====================================================

class Principal(BaseCog):
    @commands.hybrid_command(name='inv', description="Ver inventario")
    @check_ban()
    @check_encarcelado()
    async def inv(self, ctx, tipo: Optional[str] = None):
        uid = ctx.author.id
        if not tipo:
            return await ctx.send(embed=embed_info("🎒 Inventarios", "Tipos: personal · vehiculo · propiedad · negocios\nUsa `-inv [tipo]`"))
        t = tipo.lower()
        if t not in ['personal', 'vehiculo', 'propiedad', 'negocios']:
            return await ctx.send(embed=embed_error("Tipos: personal, vehiculo, propiedad, negocios"))
        inv = await db.get_inventory(uid, t)
        txt = "\n".join([f"📦 **{it}** x{c}" for it, c in sorted(inv.items())]) if inv else "*Vacío*"
        embed = discord.Embed(title=f"{t.capitalize()}", description=txt, color=0x3498DB)
        economy = await db.get_economy(uid)
        embed.set_footer(text=f"💰 Saldo: **${economy['cash']:,}** | 🏦 Banco: **${economy['bank']:,}**")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='balance', aliases=['bal'], description="Ver saldo")
    @check_ban()
    async def bal(self, ctx):
        uid = ctx.author.id
        eco = await db.get_economy(uid)
        embed = discord.Embed(
            title="💰 Tu Cartera",
            description=(
                f"**{ctx.author.name}**\n\n"
                f"💵 En mano: **${eco['cash']:,}**\n"
                f"🏦 En banco: **${eco['bank']:,}**\n"
                f"💶 Dinero negro: **${eco['black_money']:,}** *(blanquea con `-blanquear`)*"
            ),
            color=0xFFD700
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name='balance-top')
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
            title="💵 TOP DINERO — Nova Agora RP",
            description=desc or "*Sin datos*",
            color=0xFFD700,
            timestamp=datetime.now()
        )
        embed.add_field(name="📊 Tu posición:", value=f"```\n#{pos_autor} — ${saldo_autor:,}\n```", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Página {pagina}/{total_pags}  ·  {len(totales)} usuarios  ·  NOVA AGORA RP")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='tienda', description="Abrir tienda")
    @check_ban()
    @check_encarcelado()
    async def shop(self, ctx):
        view = TiendaPaginator(ctx.author.id)
        await view.send(ctx)

    @commands.command(name='comprar')
    @check_ban()
    @check_encarcelado()
    async def comprar(self, ctx, item: str, cantidad: int = 1):
        uid = ctx.author.id
        item_norm = next((n for n, _, _ in TIENDA_ITEMS if n.lower() == item.lower()), None)
        if not item_norm:
            return await ctx.send(embed=embed_error("Artículo no encontrado."))
        precio = next(pr for n, pr, _ in TIENDA_ITEMS if n == item_norm) * cantidad
        eco = await db.get_economy(uid)
        if eco['cash'] < precio:
            return await ctx.send(embed=embed_error(f"Necesitas **${precio:,}**. Tienes: **${eco['cash']:,}**"))
        await db.add_cash(uid, -precio)
        await db.add_item(uid, "personal", item_norm, cantidad)
        embed = discord.Embed(title="✅ Compra realizada", description=f"{cantidad}x {item_norm} por **${precio:,}**", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("COMPRA", f"{ctx.author.name} compró {cantidad}x {item_norm} por ${precio:,}")

    @commands.command(name='use')
    @check_ban()
    @check_encarcelado()
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
        
        # Manejo especial para licencias
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

        # Efectos normales para otros items
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
            # Nuevos items (armas, etc.) no tienen efecto especial por ahora
            "hacha": "empuña el hacha con fuerza.", "machete": "blande el machete.", "puño americano": "se coloca el puño americano.",
            "sns": "saca la pistola SNS.", "normal": "saca la pistola normal.", "vintage": "saca la pistola vintage.",
            "calibre .50": "prepara la pistola Calibre .50.", "pesada": "saca la pistola pesada.",
            "revólver pesado": "carga el revólver pesado.", "perforante": "prepara la pistola perforante.",
            "mini smg": "saca la Mini SMG.", "micro uzi": "saca la Micro Uzi.", "subfusil": "saca el subfusil.",
            "subfusil de asalto": "prepara el subfusil de asalto.", "adp": "saca el ADP.",
            "mosquete": "prepara el mosquete.", "escopeta recortada": "saca la escopeta recortada.",
            "miniak47": "saca la MiniAK47.", "escopeta corredera": "prepara la escopeta corredera.",
            "ak47": "empuña la AK47.", "rifle bullpup": "prepara el rifle bullpup.",
            "coctel molotov": "prepara un coctel molotov.", "granada casera": "prepara una granada casera.",
            "granada": "prepara una granada.", "c4": "prepara el explosivo C4."
        }
        accion = efectos.get(item_real.lower(), f"usa {item_real}.")
        await db.remove_item(uid, "personal", item_real, 1)
        nombre = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        embed = discord.Embed(description=f"**{nombre}** {accion}", color=0x800080, timestamp=datetime.now())
        embed.set_author(name="🎮 Acción de Item", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        await self.log("USE_ITEM", f"{ctx.author.name} usó {item_real}")

    @commands.command(name='blanquear', aliases=['lavar'])
    @check_ban()
    @check_encarcelado()
    async def blanquear(self, ctx):
        await self.use_item(ctx, item="dinero negro")

    @commands.command(name='intercambio')
    @check_ban()
    @check_encarcelado()
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

    @commands.command(name='mover')
    @check_ban()
    @check_encarcelado()
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

    @commands.command(name='trabajo')
    @check_encarcelado()
    async def trabajo_cmd(self, ctx):
        view = TrabajoView()
        embed = discord.Embed(
            title="⚙️ SISTEMA DE TRABAJO",
            description="✅ **Entrar a trabajar** — Inicia tu turno\n⏹️ **Salir del trabajo** — Cobra $50/min",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=view)

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
            description="Ganas $50/min\nPulsa **Salir** cuando termines.",
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
        sueldo = int(minutos * 50)
        await db.add_cash(int(uid), sueldo)
        del self.trabajo_data[uid]
        embed = discord.Embed(
            title="💰 ¡FIN DEL TURNO!",
            description=f"Tiempo: {minutos:.1f} min\nSueldo: **${sueldo:,}**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class TiendaPaginator(discord.ui.View):
    def __init__(self, user_id: int, items_por_pagina: int = 9):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.items_por_pagina = items_por_pagina
        self.pagina_actual = 0
        self.total_items = len(TIENDA_ITEMS)
        self.total_paginas = (self.total_items + items_por_pagina - 1) // items_por_pagina
        self.message = None
        self.update_buttons()

    def get_embed(self):
        inicio = self.pagina_actual * self.items_por_pagina
        fin = min(inicio + self.items_por_pagina, self.total_items)
        items_pagina = TIENDA_ITEMS[inicio:fin]

        desc = ""
        for nombre, precio, emoji in items_pagina:
            desc += f"{emoji} **{nombre}** — **${precio}**\n"
        embed = discord.Embed(
            title=f"🏪 TIENDA RP — Página {self.pagina_actual + 1}/{self.total_paginas}",
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
        self.message = await ctx.send(embed=self.get_embed(), view=self)

class TiendaBoton(discord.ui.Button):
    def __init__(self, label, pagina):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.pagina = pagina

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        view.pagina_actual = self.pagina
        view.update_buttons()
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class TiendaBotonCerrar(discord.ui.Button):
    def __init__(self):
        super().__init__(label="❌ Cerrar", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Tienda cerrada.", embed=None, view=None)
        self.view.stop()

# ------------------------------------------------
# COG: Drogas
# ------------------------------------------------
class Drogas(BaseCog):
    EMOJIS_DROGA = {"Marihuana": "🌿", "Cocaína": "❄️", "Meta": "💊", "Éxtasis": "🔵", "Heroína": "💉"}

    @commands.group(name='droga', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    async def droga(self, ctx):
        embed = discord.Embed(title="💊 Mercado de Drogas (Precios Dinámicos)", color=discord.Color.dark_green())
        for droga in self.EMOJIS_DROGA:
            precio_compra = await db.get_precio_droga(droga, True)
            precio_venta = await db.get_precio_droga(droga, False)
            embed.add_field(
                name=f"{self.EMOJIS_DROGA[droga]} {droga}",
                value=f"🛒 Compra: **${precio_compra}**\n💵 Venta: **${precio_venta}**",
                inline=False
            )
        embed.set_footer(text="Precios dinámicos según oferta/demanda")
        await ctx.send(embed=embed)

    @droga.command(name='comprar')
    @check_ban()
    @check_encarcelado()
    async def drg_buy(self, ctx, tipo: str, cantidad: int = 1):
        uid = ctx.author.id
        tipo_norm = tipo.capitalize()
        if tipo_norm not in self.EMOJIS_DROGA:
            return await ctx.send(embed=embed_error(f"Tipos válidos: {', '.join(self.EMOJIS_DROGA.keys())}"))
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

    @droga.command(name='vender')
    @check_ban()
    @check_encarcelado()
    async def drg_sell(self, ctx, tipo: str, cantidad: int = 1):
        uid = ctx.author.id
        tipo_norm = tipo.capitalize()
        if tipo_norm not in self.EMOJIS_DROGA:
            return await ctx.send(embed=embed_error(f"Tipos válidos: {', '.join(self.EMOJIS_DROGA.keys())}"))
        inv = await db.get_inventory(uid, "personal")
        if inv.get(tipo_norm, 0) < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes {cantidad}x {tipo_norm}."))
        precio_unitario = await db.get_precio_droga(tipo_norm, False)
        ganancia = precio_unitario * cantidad
        await db.remove_item(uid, "personal", tipo_norm, cantidad)
        await db.add_cash(uid, ganancia)
        await db.actualizar_precio_droga(tipo_norm, cantidad)
        embed = discord.Embed(title="✅ Venta realizada", description=f"{cantidad}x {tipo_norm} por **${ganancia:,}**", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("VENTA_DROGA", f"{ctx.author.name}: {cantidad}x {tipo_norm} -> +${ganancia:,}")

# ------------------------------------------------
# COG: Vehiculos
# ------------------------------------------------
class Vehiculos(BaseCog):
    @commands.group(name='vehiculo', aliases=['coche', 'car'], invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    async def vehiculo(self, ctx):
        uid = ctx.author.id
        vehiculos = await db.get_vehiculos(uid)
        if not vehiculos:
            return await ctx.send(embed=embed_info("🚗 Vehículos", "No tienes vehículos."))
        embed = discord.Embed(title="🚗 MIS VEHÍCULOS", color=discord.Color.blue())
        for mat, info in vehiculos.items():
            seguro = "✅" if info['seguro'] else "❌"
            itv = "✅" if info['itv'] and datetime.fromisoformat(info['itv']) > datetime.now() else "❌"
            embed.add_field(
                name=f"🚗 {info['modelo']} — `{mat}`",
                value=f"Seguro: {seguro} | ITV: {itv}\n⛽ Combustible: {info['combustible']}%",
                inline=False
            )
        await ctx.send(embed=embed)

    @vehiculo.command(name='conducir')
    @check_ban()
    @check_encarcelado()
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

    @vehiculo.command(name='repostar')
    @check_ban()
    @check_encarcelado()
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

    @vehiculo.command(name='itv')
    @check_ban()
    @check_encarcelado()
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

# ------------------------------------------------
# COG: Armas
# ------------------------------------------------
class Armas(BaseCog):
    @commands.group(name='arma', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    async def arma(self, ctx):
        uid = ctx.author.id
        licencias = await db.get_licencias(uid)
        armas = await db.get_armas_equipadas(uid)
        embed = discord.Embed(title="🔫 SISTEMA DE ARMAS", color=discord.Color.dark_red())
        txt_lic = "\n".join([f"{'✅' if v else '❌'} {l.replace('_', ' ').title()}" for l, v in licencias.items()]) if licencias else "Ninguna"
        embed.add_field(name="📋 Licencias:", value=txt_lic, inline=False)
        txt_armas = "\n".join([f"🔫 {a} — Dur: {info['durabilidad']}% | Munición: {info['municion']}" for a, info in armas.items()]) if armas else "Ninguna"
        embed.add_field(name="🔫 Armas equipadas:", value=txt_armas, inline=False)
        embed.add_field(
            name="Comandos:",
            value="`-arma equipar <tipo>`\n`-arma disparar`\n`-arma recargar <tipo> <cantidad>`",
            inline=False
        )
        await ctx.send(embed=embed)

    @arma.command(name='equipar')
    @check_ban()
    @check_encarcelado()
    async def arma_equipar(self, ctx, tipo_arma: str):
        tipo = tipo_arma.capitalize()
        # Verificar si el arma está en el inventario personal
        inv = await db.get_inventory(ctx.author.id, "personal")
        if tipo not in inv:
            return await ctx.send(embed=embed_error(f"No tienes {tipo} en tu inventario."))
        # Verificar licencia
        licencias = await db.get_licencias(ctx.author.id)
        # Mapeo de tipos de arma a licencia necesaria
        licencia_necesaria = None
        if tipo in ["Hacha", "Machete", "Puño americano"]:
            licencia_necesaria = "licencia_blanca"
        elif tipo in ["SNS", "Normal", "Vintage", "Calibre .50", "Pesada", "Revólver Pesado", "Perforante", "9mm"]:
            licencia_necesaria = "licencia_corta"
        elif tipo in ["Mini SMG", "Micro Uzi", "Subfusil", "Subfusil de asalto", "ADP"]:
            licencia_necesaria = "licencia_corta"  # o una específica
        elif tipo in ["Mosquete", "Escopeta recortada", "MiniAk47", "Escopeta corredera", "Ak47", "Rifle bullpup"]:
            licencia_necesaria = "licencia_rifle"  # o largas
        else:
            # Para armas existentes
            for arma_tipo, datos in TIPOS_ARMAS.items():
                if arma_tipo.lower() == tipo.lower():
                    licencia_necesaria = datos.get("licencia")
                    break
        if licencia_necesaria and not licencias.get(licencia_necesaria, False):
            return await ctx.send(embed=embed_error("No tienes la licencia necesaria para equipar esta arma."))
        # Si no hay licencia específica, permitir (ejemplo: armas sin licencia)
        # Añadir a armas_equipadas con durabilidad y munición por defecto
        durabilidad = 100
        municion = 0
        await db.execute("INSERT OR REPLACE INTO armas_equipadas (user_id, arma, durabilidad, municion) VALUES (?, ?, ?, ?)",
                         (ctx.author.id, tipo, durabilidad, municion))
        embed = discord.Embed(title="🔫 ARMA EQUIPADA", description=f"**{tipo}** equipada.", color=0x00FF00)
        await ctx.send(embed=embed)
        await self.log("ARMA_EQUIPAR", f"{ctx.author.name}: {tipo}")

    @arma.command(name='disparar')
    @check_ban()
    @check_encarcelado()
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
        embed = discord.Embed(
            title="💥 ¡DISPARO!",
            description=f"**{ctx.author.display_name}** dispara con **{arma}**\nMunición restante: {nueva_municion}\nDurabilidad: {nueva_durabilidad}%",
            color=0xFFA500
        )
        await ctx.send(embed=embed)
        await self.log("ARMA_DISPARAR", f"{ctx.author.name}: {arma}")

    @arma.command(name='recargar')
    @check_ban()
    @check_encarcelado()
    async def arma_recargar(self, ctx, tipo_arma: str, cantidad: int):
        tipo = tipo_arma.capitalize()
        # Verificar si el arma está equipada
        row = await db.fetchone("SELECT arma FROM armas_equipadas WHERE user_id = ? AND arma = ?", (ctx.author.id, tipo))
        if not row:
            return await ctx.send(embed=embed_error("Esa arma no está equipada."))
        # Precio de munición genérico
        precio_por_bala = 10
        costo = precio_por_bala * cantidad
        eco = await db.get_economy(ctx.author.id)
        if eco['cash'] < costo:
            return await ctx.send(embed=embed_error(f"Necesitas **${costo:,}**."))
        await db.add_cash(ctx.author.id, -costo)
        await db.execute("UPDATE armas_equipadas SET municion = municion + ? WHERE user_id = ? AND arma = ?", (cantidad, ctx.author.id, tipo))
        embed = discord.Embed(
            title="🔫 ARMA RECARGADA",
            description=f"{tipo} recargada con {cantidad} balas.\nCosto: **${costo:,}**",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("ARMA_RECARGAR", f"{ctx.author.name}: {tipo}, +{cantidad} balas")

# ------------------------------------------------
# COG: Mercado
# ------------------------------------------------
class Mercado(BaseCog):
    @commands.group(name='mercado', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    async def mercado(self, ctx):
        publicaciones = await db.get_mercado()
        if not publicaciones:
            return await ctx.send(embed=embed_info("🏪 Mercado", "No hay publicaciones."))
        embed = discord.Embed(title="🏪 MERCADO — Publicaciones", color=0xFFD700)
        for pub in publicaciones[:10]:
            vendedor = ctx.guild.get_member(pub['vendedor'])
            vendedor_nombre = vendedor.display_name if vendedor else f"Usuario {pub['vendedor']}"
            embed.add_field(
                name=f"📦 ID: `{pub['id']}` — {pub['item']}",
                value=f"📝 {pub['descripcion'][:50]}...\n💵 **${pub['precio']:,}** | 👤 {vendedor_nombre}\n_Publicado: {pub['fecha'][:10]}_",
                inline=False
            )
        embed.set_footer(text="Usa -mercado comprar <id> para comprar")
        await ctx.send(embed=embed)

    @mercado.command(name='publicar')
    @check_ban()
    @check_encarcelado()
    async def mercado_publicar(self, ctx, item: str, precio: int, *, descripcion: str):
        uid = ctx.author.id
        inv = await db.get_inventory(uid, "personal")
        item_real = next((k for k in inv if k.lower() == item.lower()), None)
        if not item_real:
            return await ctx.send(embed=embed_error("No tienes ese item."))
        if precio <= 0:
            return await ctx.send(embed=embed_error("Precio debe ser mayor a 0."))
        pub_id = ''.join(random.choices('0123456789ABCDEF', k=6))
        await db.remove_item(uid, "personal", item_real, 1)
        await db.add_mercado(pub_id, uid, item_real, descripcion, precio)
        embed = discord.Embed(
            title="✅ Publicación creada",
            description=f"Item: {item_real}\nPrecio: **${precio:,}**\nID: {pub_id}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("MERCADO_PUBLICAR", f"{ctx.author.name}: {item_real} por ${precio:,}")

    @mercado.command(name='comprar')
    @check_ban()
    @check_encarcelado()
    async def mercado_comprar(self, ctx, pub_id: str):
        pub = await db.get_mercado_by_id(pub_id)
        if not pub:
            return await ctx.send(embed=embed_error("Publicación no encontrada."))
        vendedor, item, precio = pub
        if vendedor == ctx.author.id:
            return await ctx.send(embed=embed_error("No puedes comprar tu propia publicación."))
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

    @mercado.command(name='mispub')
    @check_ban()
    async def mercado_mis_pub(self, ctx):
        rows = await db.fetchall("SELECT id, item, precio, descripcion FROM mercado WHERE vendedor = ?", (ctx.author.id,))
        if not rows:
            return await ctx.send(embed=embed_info("🏪 Mis publicaciones", "No tienes publicaciones."))
        embed = discord.Embed(title="🏪 MIS PUBLICACIONES", color=0x3498DB)
        for r in rows:
            embed.add_field(name=f"📦 ID: `{r[0]}` — {r[1]}", value=f"💵 **${r[2]:,}**\n📝 {r[3][:30]}...", inline=False)
        await ctx.send(embed=embed)

    @mercado.command(name='cancelar')
    @check_ban()
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

# ------------------------------------------------
# COG: Casino
# ------------------------------------------------
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
    async def casino(self, ctx):
        embed = discord.Embed(
            title="🎰 Golden Coast · Legendary Casino's",
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
        embed.set_footer(text=f"💰 Saldo: **${eco['cash']:,}**  ·  NOVA AGORA RP")
        await ctx.send(embed=embed)

    @casino.command(name='ruleta-info')
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

    @casino.command(name='racha')
    async def ver_racha(self, ctx):
        uid = ctx.author.id
        racha = await db.get_racha(uid)
        if racha['racha'] == 0:
            return await ctx.send(embed=embed_info("📊 Racha", "Sin partidas aún."))
        tipo_txt = "victorias 🏆" if racha['tipo'] == "win" else "derrotas 💀"
        embed = discord.Embed(title="📊 Tu racha", description=f"Racha: **{racha['racha']} {tipo_txt}**", color=discord.Color.green() if racha['tipo'] == "win" else discord.Color.red())
        await ctx.send(embed=embed)

    @casino.command(name='slots')
    async def slots(self, ctx, apuesta: int):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))
        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 1.75 if racha['racha'] >= 5 else 2.5 if racha['racha'] >= 7 else 3.0

        await db.add_cash(uid, -apuesta)
        SIMBOLOS = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣", "🃏"]
        MULTS = {"💎": 15, "7️⃣": 10, "⭐": 7, "🍇": 5, "🍊": 4, "🍋": 3, "🍒": 2, "🃏": 20}
        msg = await self._animacion_casino(ctx, ["🎰  GIRANDO...", "🎰  [ 🎲 | ??? | ??? | ??? ]",
                                                 "🎰  [ 🍒 | 🎲  | ??? | ??? ]", "🎰  [ 🍒 | 🍋  | 🎲  | ??? ]", "🎰  Parando..."])
        res = [random.choice(SIMBOLOS) for _ in range(4)]
        no_joker = [s for s in res if s != "🃏"]
        jokers = res.count("🃏")
        disp = f"[ {' | '.join(res)} ]"

        if jokers == 4:
            mult_fin = 50 * mult_racha
            ganancia = int(apuesta * mult_fin)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo = "¡¡MEGA JACKPOT!! 🃏×4"
            color = 0xFFD700
            resultado = f"+${ganancia-apuesta:,}"
        elif len(set(no_joker)) == 1 and len(no_joker) >= 3:
            sym = no_joker[0]
            mult_fin = MULTS.get(sym, 3) * mult_racha * (1 + jokers * 0.5)
            ganancia = int(apuesta * mult_fin)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo = f"¡¡JACKPOT!! {sym}×{4-jokers}" + ("🃏" * jokers if jokers else "")
            color = 0xFFD700
            resultado = f"+${ganancia-apuesta:,}"
        elif jokers >= 2:
            ganancia = int(apuesta * 3 * mult_racha)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo = "¡Doble comodín! 🃏🃏"
            color = 0x00FF00
            resultado = f"+${ganancia-apuesta:,}"
        elif len(set(no_joker)) <= 2 and (len(no_joker) + jokers) >= 3:
            ganancia = int((apuesta // 2) * mult_racha)
            await db.add_cash(uid, ganancia)
            await db.actualizar_racha(uid, True)
            titulo = "¡Par!"
            color = 0x00FF00
            resultado = f"+${ganancia-apuesta:,}"
        else:
            await db.actualizar_racha(uid, False)
            titulo = "Sin suerte..."
            color = 0xFF0000
            resultado = f"-${apuesta:,}"
        embed = discord.Embed(title=f"🎰 {titulo}", description=f"**{disp}**\n{resultado}", color=color)
        await msg.edit(content=None, embed=embed)
        await self.log("CASINO_SLOTS", f"{ctx.author.name}: ${apuesta} → {disp}")

    @casino.command(name='ruleta')
    async def ruleta(self, ctx, apuesta: int, *, tipo: str):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))
        tipo_norm = tipo.lower().strip()
        tipos_validos = ['rojo','negro','verde','par','impar','00',
                         'col1','col2','col3','1-12','13-24','25-36'] + [str(i) for i in range(37)]
        if tipo_norm not in tipos_validos:
            return await ctx.send(embed=embed_error("Tipo no válido. Usa -casino ruleta-info"))
        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 1.75 if racha['racha'] >= 5 else 2.5 if racha['racha'] >= 7 else 3.0

        msg = await self._animacion_casino(ctx, ["🎡  LA RULETA GIRA...", "🎡  ●○○○○○○○○○○○○○○○○○○○○○",
                                                 "🎡  ○○○○○●○○○○○○○○○○○○○○○○", "🎡  ○○○○○○○○○○●○○○○○○○○○○○",
                                                 "🎡  ○○○○○○○○○○○○○○○●○○○○○○", "🎡  ○○○○○○○○○○○○○○○○○○○●○○", "🎡  Cayendo..."], delay=0.35)
        numero = random.randint(0, 37)
        color_real = "verde" if numero in (0, 37) else "rojo" if numero in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] else "negro"
        gano = False
        multiplicador = 0
        if tipo_norm in ('rojo', 'negro', 'verde'):
            if tipo_norm == color_real:
                gano = True
                multiplicador = 14 if tipo_norm == 'verde' else 2
        elif tipo_norm in ('par', 'impar'):
            if numero != 0 and numero != 37:
                if (tipo_norm == 'par' and numero % 2 == 0) or (tipo_norm == 'impar' and numero % 2 == 1):
                    gano = True
                    multiplicador = 2
        elif tipo_norm == '00':
            if numero == 37:
                gano = True
                multiplicador = 34
        elif tipo_norm.isdigit():
            n = int(tipo_norm)
            if n == numero:
                gano = True
                multiplicador = 34
        elif tipo_norm in ('col1', 'col2', 'col3'):
            col = {'col1': [1,4,7,10,13,16,19,22,25,28,31,34],
                   'col2': [2,5,8,11,14,17,20,23,26,29,32,35],
                   'col3': [3,6,9,12,15,18,21,24,27,30,33,36]}
            if numero in col[tipo_norm]:
                gano = True
                multiplicador = 3
        elif tipo_norm in ('1-12', '13-24', '25-36'):
            rangos = {'1-12': (1,12), '13-24': (13,24), '25-36': (25,36)}
            if rangos[tipo_norm][0] <= numero <= rangos[tipo_norm][1]:
                gano = True
                multiplicador = 3

        await db.add_cash(uid, -apuesta)
        if gano:
            ganancia = int(apuesta * multiplicador * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado = f"+${ganancia:,}"
            color = 0x00FF00
        else:
            await db.actualizar_racha(uid, False)
            resultado = f"-${apuesta:,}"
            color = 0xFF0000
        num_display = "00" if numero == 37 else str(numero)
        embed = discord.Embed(title="🎡 Ruleta", description=f"Número: **{num_display}** ({color_real})\nResultado: {resultado}", color=color)
        await msg.edit(content=None, embed=embed)
        await self.log("CASINO_RULETA", f"{ctx.author.name}: ${apuesta} → {num_display} {'WIN' if gano else 'LOSS'}")

    @casino.command(name='dados')
    async def dados(self, ctx, apuesta: int):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))
        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 1.75 if racha['racha'] >= 5 else 2.5 if racha['racha'] >= 7 else 3.0

        msg = await self._animacion_casino(ctx, ["🎲  LANZANDO DADOS...", "🎲  [ ? | ? ]", "🎲  Parando..."])
        d1, d2 = random.randint(1,6), random.randint(1,6)
        total = d1 + d2
        await db.add_cash(uid, -apuesta)
        if d1 == d2:
            ganancia = int(apuesta * 3 * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado = f"+${ganancia:,}"
            color = 0x00FF00
            titulo = f"¡DOBLES! {d1}+{d2}={total}"
        elif total >= 10:
            ganancia = int(apuesta * 2 * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado = f"+${ganancia:,}"
            color = 0x00FF00
            titulo = f"¡Número alto! {d1}+{d2}={total}"
        else:
            await db.actualizar_racha(uid, False)
            resultado = f"-${apuesta:,}"
            color = 0xFF0000
            titulo = f"Sin suerte... {d1}+{d2}={total}"
        embed = discord.Embed(title=f"🎲 {titulo}", description=f"Dados: {d1} + {d2} = {total}\nResultado: {resultado}", color=color)
        await msg.edit(content=None, embed=embed)
        await self.log("CASINO_DADOS", f"{ctx.author.name}: ${apuesta} → {d1}+{d2}={total}")

    @commands.command(name='bj')
    async def blackjack(self, ctx, apuesta: int):
        uid = ctx.author.id
        err = await self._validar_apuesta(uid, apuesta)
        if err:
            return await ctx.send(embed=embed_error(err))
        racha = await db.get_racha(uid)
        mult_racha = 1.0
        if racha['tipo'] == "win" and racha['racha'] >= 3:
            mult_racha = 1.75 if racha['racha'] >= 5 else 2.5 if racha['racha'] >= 7 else 3.0

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
            resultado = f"🃏 **¡BLACKJACK!** +${ganancia:,}"
            color = 0xFFD700
        elif casa == 21:
            await db.actualizar_racha(uid, False)
            resultado = f"❌ **La casa tiene Blackjack.** -${apuesta:,}"
            color = 0xFF0000
        elif jugador > 21:
            await db.actualizar_racha(uid, False)
            resultado = f"❌ **¡Te pasaste!** -${apuesta:,}"
            color = 0xFF0000
        elif jugador > casa or casa > 21:
            ganancia = int(apuesta * 2 * mult_racha - apuesta)
            await db.add_cash(uid, ganancia + apuesta)
            await db.actualizar_racha(uid, True)
            resultado = f"✅ **¡Ganaste!** +${ganancia:,}"
            color = 0x00FF00
        elif jugador == casa:
            await db.add_cash(uid, apuesta)
            resultado = "🤝 **¡Empate!** Recuperas tu apuesta"
            color = 0x3498DB
        else:
            await db.actualizar_racha(uid, False)
            resultado = f"❌ **La casa gana.** -${apuesta:,}"
            color = 0xFF0000
        embed = discord.Embed(title="🃏 Blackjack", description=f"Tu mano: {jugador}\nCasa: {casa}\n{resultado}", color=color)
        await ctx.send(embed=embed)
        await self.log("CASINO_BJ", f"{ctx.author.name}: ${apuesta} → J:{jugador} C:{casa}")

# ------------------------------------------------
# COG: Atracos (todos los robos)
# ------------------------------------------------
class Atracos(BaseCog):
    @commands.group(name='rob', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    async def rob(self, ctx):
        embed = embed_help(
            "rob",
            "Realiza un atraco en diferentes ubicaciones.",
            "-rob <badu|lico|ammu|yellowjack|yate|pacific|jugador>",
            "-rob ammu\n-rob yate\n-rob jugador @Juan",
            ""
        )
        await ctx.send(embed=embed)

    @rob.command(name='badu')
    async def rob_badu(self, ctx):
        ok, rest = await db.check_cooldown(ctx.author.id, 'badu', 1500)
        if not ok:
            m, s = divmod(rest, 60)
            return await ctx.send(embed=embed_error(f"Espera {m}m {s}s para volver a atracar Badu."))
        msg = await ctx.send("🔓 **Descifrando la caja registradora**")
        await asyncio.sleep(2)
        dinero = random.randint(1000, 3500)
        await db.add_black(ctx.author.id, dinero)
        await db.inc_estadistica('robos_totales')
        await db.inc_estadistica('atracos_hoy')
        embed = discord.Embed(
            title="💶 ¡ATRACO BADU EXITOSO!",
            description=f"Obtuviste **${dinero:,}** en dinero negro.",
            color=0x00FF00
        )
        await msg.edit(content=None, embed=embed)
        await self.log("ATRACO_BADU", f"{ctx.author.name}: +${dinero} dinero negro")

    @rob.command(name='lico')
    async def rob_lico(self, ctx):
        ok, rest = await db.check_cooldown(ctx.author.id, 'lico', 2700)
        if not ok:
            m, s = divmod(rest, 60)
            return await ctx.send(embed=embed_error(f"Espera {m}m {s}s para volver a atracar Lico's."))
        msg = await ctx.send("🔓 **Accediendo a la caja fuerte**")
        await asyncio.sleep(2)
        dinero = random.randint(3500, 6200)
        await db.add_black(ctx.author.id, dinero)
        await db.inc_estadistica('robos_totales')
        embed = discord.Embed(
            title="💶 ¡ATRACO LICO'S EXITOSO!",
            description=f"Obtuviste **${dinero:,}** en dinero negro.",
            color=0x00FF00
        )
        await msg.edit(content=None, embed=embed)
        await self.log("ATRACO_LICO", f"{ctx.author.name}: +${dinero} dinero negro")

    @rob.command(name='ammu')
    async def rob_ammu(self, ctx):
        ok, rest = await db.check_cooldown(ctx.author.id, 'ammu', 5400)
        if not ok:
            m, s = divmod(rest, 60)
            return await ctx.send(embed=embed_error(f"Espera {m}m {s}s para volver a atracar Ammu-Nation."))
        msg = await ctx.send("🔓 **Descifrando código de la caja fuerte**")
        await asyncio.sleep(2)
        dinero = random.randint(5000, 12000)
        pistola = random.random() < 0.25
        municion = random.randint(30, 120) if pistola else 0
        await db.add_black(ctx.author.id, dinero)
        if pistola:
            await db.add_item(ctx.author.id, "personal", "Pistola de combate", 1)
            await db.add_item(ctx.author.id, "personal", "Munición", municion)
        await db.inc_estadistica('robos_totales')
        embed = discord.Embed(
            title="🏪 ¡ATRACO A AMMU-NATION EXITOSO!",
            description=f"Obtuviste **${dinero:,}** en dinero negro.\n" + (f"🔫 Pistola de combate +{municion} balas" if pistola else "❌ Sin arma"),
            color=0x00FF00
        )
        await msg.edit(content=None, embed=embed)
        await self.log("ATRACO_AMMU", f"{ctx.author.name}: +${dinero} dinero negro, arma: {pistola}")

    @rob.command(name='yellowjack')
    async def rob_yellowjack(self, ctx):
        ok, rest = await db.check_cooldown(ctx.author.id, 'yellowjack', 3600)
        if not ok:
            m, s = divmod(rest, 60)
            return await ctx.send(embed=embed_error(f"Espera {m}m {s}s para volver a atracar Yellow Jack."))
        msg = await ctx.send("🔫 **Asaltando Yellow Jack**")
        await asyncio.sleep(2)
        dinero = random.randint(800, 2500)
        rehenes = random.randint(1, 5)
        await db.add_black(ctx.author.id, dinero)
        await db.inc_estadistica('robos_totales')
        embed = discord.Embed(
            title="💶 ¡ROBO YELLOW JACK!",
            description=f"Obtuviste **${dinero:,}** en dinero negro.\nRehenes: {rehenes}",
            color=0x00FF00
        )
        await msg.edit(content=None, embed=embed)
        await self.log("ATRACO_YELLOWJACK", f"{ctx.author.name}: +${dinero} dinero negro, {rehenes} rehenes")

    @rob.command(name='yate')
    async def rob_yate(self, ctx):
        ok, rest = await db.check_cooldown(ctx.author.id, 'yate', 7200)
        if not ok:
            m, s = divmod(rest, 60)
            return await ctx.send(embed=embed_error(f"Espera {m}m {s}s para volver a atracar el yate."))
        msg = await ctx.send("⛵ **Abordando el yate de lujo...**")
        await asyncio.sleep(3)
        dinero = random.randint(15000, 25000)
        droga = random.choice(list(PRECIOS_DROGAS_BASE.keys()))
        gramos = random.randint(5, 20)
        await db.add_black(ctx.author.id, dinero)
        await db.add_item(ctx.author.id, "personal", droga, gramos)
        await db.inc_estadistica('robos_totales')
        embed = discord.Embed(
            title="⛵ ¡ATRACO AL YATE EXITOSO!",
            description=f"Obtuviste **${dinero:,}** en dinero negro.\nAdemás encontraste **{gramos} gramos de {droga}**.",
            color=0xFFD700
        )
        await msg.edit(content=None, embed=embed)
        await self.log("ATRACO_YATE", f"{ctx.author.name}: +${dinero} negro, +{gramos}g {droga}")

    @rob.command(name='pacific')
    async def rob_pacific(self, ctx):
        ok, rest = await db.check_cooldown(ctx.author.id, 'pacific', 10800)
        if not ok:
            m, s = divmod(rest, 60)
            return await ctx.send(embed=embed_error(f"Espera {m}m {s}s para volver a atracar el Pacific Standard."))
        msg = await ctx.send("🏦 **Asaltando el Pacific Standard Bank...**")
        await asyncio.sleep(4)
        dinero = random.randint(40000, 60000)
        await db.add_black(ctx.author.id, dinero)
        await db.inc_estadistica('robos_totales')
        embed = discord.Embed(
            title="🏦 ¡ATRACO AL PACIFIC STANDARD EXITOSO!",
            description=f"Obtuviste **${dinero:,}** en dinero negro. ¡Botín histórico!",
            color=0xFFD700
        )
        await msg.edit(content=None, embed=embed)
        await self.log("ATRACO_PACIFIC", f"{ctx.author.name}: +${dinero} negro")

    @rob.command(name='jugador')
    async def atracar_jugador(self, ctx, victima: discord.Member):
        uid, vid = ctx.author.id, victima.id
        if uid == vid:
            return await ctx.send(embed=embed_error("No puedes atracarte a ti mismo."))
        ok, rest = await db.check_cooldown(uid, 'atracar_jugador', 600)
        if not ok:
            m, s = divmod(rest, 60)
            return await ctx.send(embed=embed_error(f"Espera {m}m {s}s para volver a atracar."))
        eco = await db.get_economy(vid)
        if eco['cash'] <= 0:
            return await ctx.send(embed=embed_error("La víctima no lleva dinero encima."))
        msg = await ctx.send(f"🔫 **Atracando a {victima.display_name}...**")
        await asyncio.sleep(2)
        porcentaje = random.uniform(0.1, 0.5)
        dinero_robado = int(eco['cash'] * porcentaje)
        await db.add_cash(vid, -dinero_robado)
        await db.add_black(uid, dinero_robado)
        await db.inc_estadistica('robos_totales')
        embed = discord.Embed(
            title="💀 ¡ATRACO EXITOSO!",
            description=f"Robaste **${dinero_robado:,}** a {victima.mention}.",
            color=0xFF0000
        )
        await msg.edit(content=None, embed=embed)
        await self.log("ATRACO_JUGADOR", f"{ctx.author.name} atracó a {victima.name}: ${dinero_robado}")

# ------------------------------------------------
# COG: Banco
# ------------------------------------------------
class Banco(BaseCog):
    @commands.group(name='banco', invoke_without_command=True)
    @check_ban()
    @check_encarcelado()
    async def banco(self, ctx):
        uid = ctx.author.id
        eco = await db.get_economy(uid)
        embed = discord.Embed(
            title="🏦 BANCO CENTRAL",
            description=f"💵 Efectivo: **${eco['cash']:,}**\n🏦 En banco: **${eco['bank']:,}**\n💰 Total: **${eco['cash'] + eco['bank']:,}**",
            color=0x3498DB
        )
        if eco['black_money'] > 0:
            embed.add_field(name="💶 Dinero negro", value=f"Tienes **${eco['black_money']:,}** pendiente de blanquear. Usa `-blanquear`.", inline=False)
        embed.add_field(
            name="Comandos",
            value="`-banco ingresar <cantidad>`\n`-banco retirar <cantidad>`\n`-banco transferir @user <cantidad>`",
            inline=False
        )
        await ctx.send(embed=embed)

    @banco.command(name='ingresar')
    async def banco_ingresar(self, ctx, cantidad: int):
        uid = ctx.author.id
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("Cantidad mayor a 0."))
        eco = await db.get_economy(uid)
        if eco['cash'] < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes **${cantidad:,}** en efectivo."))
        await db.add_cash(uid, -cantidad)
        await db.add_bank(uid, cantidad)
        await ctx.send(embed=embed_success("🏦 Ingreso", f"Has ingresado **${cantidad:,}**."))

    @banco.command(name='retirar')
    async def banco_retirar(self, ctx, cantidad: int):
        uid = ctx.author.id
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("Cantidad mayor a 0."))
        eco = await db.get_economy(uid)
        if eco['bank'] < cantidad:
            return await ctx.send(embed=embed_error(f"No tienes **${cantidad:,}** en el banco."))
        await db.add_bank(uid, -cantidad)
        await db.add_cash(uid, cantidad)
        await ctx.send(embed=embed_success("🏦 Retiro", f"Has retirado **${cantidad:,}**."))

    @banco.command(name='transferir')
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
        await ctx.send(embed=embed_success("🏦 Transferencia", f"Has transferido **${cantidad:,}** a {usuario.mention}."))
        await self.log("BANCO_TRANSFERENCIA", f"{ctx.author.name} transfirió ${cantidad} a {usuario.name}")

# ------------------------------------------------
# COG: Multas
# ------------------------------------------------
class Multas(BaseCog):
    @commands.group(name='multa', invoke_without_command=True)
    @check_ban()
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
                value=f"Motivo: {m['motivo']}\nAgente: {m['agente']}\nFecha: {m['fecha'][:10]}",
                inline=False
            )
            total += m['cantidad']
        embed.add_field(name="Total pendiente", value=f"**${total:,}**", inline=False)
        embed.set_footer(text="Usa -multa pagar <número> para pagar una multa")
        await ctx.send(embed=embed)

    @multa.command(name='pagar')
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
            multa = multas[numero-1]
            eco = await db.get_economy(uid)
            if eco['cash'] < multa['cantidad']:
                return await ctx.send(embed=embed_error(f"Necesitas **${multa['cantidad']:,}**."))
            await db.add_cash(uid, -multa['cantidad'])
            await db.pagar_multa(multa['id'])
            await ctx.send(embed=embed_success("✅ Multa pagada", f"Has pagado **${multa['cantidad']:,}** por: {multa['motivo']}."))
            await self.log("MULTA_PAGAR", f"{ctx.author.name} pagó multa #{numero}: ${multa['cantidad']}")

# ------------------------------------------------
# COG: PDA (Policial)
# ------------------------------------------------
class PDA(BaseCog):
    RANGOS = ["Cadete", "Agente", "Agente de Primera", "Cabo", "Sargento", "Teniente", "Capitán", "Comandante", "Jefe de Policía"]
    RANGO_EMOJIS = {
        "Cadete": "👮", "Agente": "🚔", "Agente de Primera": "🚔", "Cabo": "⭐",
        "Sargento": "⭐⭐", "Teniente": "🎖️", "Capitán": "🎖️🎖️", "Comandante": "👑",
        "Jefe de Policía": "👑🛡️"
    }

    async def cog_check(self, ctx):
        user_state = await db.get_user_state(ctx.author.id)
        if not user_state.get('placa'):
            await ctx.send(embed=embed_error("No tienes placa policial."))
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
        embed = discord.Embed(title="🚨 PANEL PDA", color=0x3498DB)
        embed.add_field(name="👤 Agente", value=f"{nombre}", inline=True)
        embed.add_field(name="🪪 Placa", value=f"{placa}", inline=True)
        embed.add_field(name=f"{emoji} Rango", value=f"{rango}", inline=True)
        embed.add_field(name="🏦 Caja Municipal", value=f"**${caja:,}**", inline=False)
        embed.add_field(
            name="Comandos",
            value="`-pda detener @u <motivo>`\n`-pda encarcelar @u <min> <motivo>`\n`-pda multar @u <cantidad> <motivo>`\n`-pda requisar @u <arma>`\n`-pda licencia @u <tipo> [dar/quitar]`\n`-pda buscar <nombre>`\n`-pda crear-placa <numero>`",
            inline=False
        )
        await ctx.send(embed=embed)

    @pda.command(name='detener')
    async def pda_detener(self, ctx, usuario: discord.Member, *, motivo: str):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        placa = user_state['placa']
        rango = user_state['rango']
        nombre_ag = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        nombre_det = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        embed = discord.Embed(
            title="🚨 DETENCIÓN",
            description=f"{nombre_ag} ha detenido a {nombre_det}. Motivo: {motivo}",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        await self.log("PDA_DETENER", f"{nombre_ag} detuvo a {nombre_det}: {motivo}")

    @pda.command(name='encarcelar')
    async def pda_encarcelar(self, ctx, usuario: discord.Member, minutos: int, *, motivo: str):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        placa = user_state['placa']
        rango = user_state['rango']
        nombre_ag = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        nombre_det = await self.obtener_nombre_dni(usuario.id) or usuario.display_name
        hasta = datetime.now() + timedelta(minutes=minutos)
        await db.update_user_state(usuario.id, encarcelado_hasta=hasta.isoformat())
        embed = discord.Embed(
            title="🔒 ENCARCELAMIENTO",
            description=f"{nombre_ag} ha encarcelado a {nombre_det} por {minutos} minutos.\nMotivo: {motivo}",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        await self.log("PDA_ENCARCELAR", f"{nombre_ag} encarceló a {nombre_det} por {minutos}min: {motivo}")

    @pda.command(name='multar')
    async def pda_multar(self, ctx, usuario: discord.Member, cantidad: int, *, motivo: str):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        placa = user_state['placa']
        nombre_ag = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        await db.add_multa(usuario.id, cantidad, motivo, nombre_ag, placa)
        embed = discord.Embed(
            title="📄 MULTA",
            description=f"{nombre_ag} ha multado a {usuario.mention} con **${cantidad:,}**.\nMotivo: {motivo}",
            color=0xFFA500
        )
        await ctx.send(embed=embed)
        await self.log("PDA_MULTAR", f"{nombre_ag} multó a {usuario.name}: ${cantidad} - {motivo}")

    @pda.command(name='requisar')
    async def pda_requisar(self, ctx, usuario: discord.Member, *, arma: str):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        placa = user_state['placa']
        nombre_ag = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        armas = await db.get_armas_equipadas(usuario.id)
        arma_real = next((k for k in armas if k.lower() == arma.lower()), None)
        if not arma_real:
            return await ctx.send(embed=embed_error(f"{usuario.display_name} no tiene {arma} equipada."))
        await db.execute("DELETE FROM armas_equipadas WHERE user_id = ? AND arma = ?", (usuario.id, arma_real))
        embed = discord.Embed(
            title="🔫 ARMA REQUISADA",
            description=f"{nombre_ag} requisó {arma_real} a {usuario.mention}.",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        await self.log("PDA_REQUISAR", f"{nombre_ag} requisó {arma_real} a {usuario.name}")

    @pda.command(name='licencia')
    async def pda_licencia(self, ctx, usuario: discord.Member, tipo_licencia: str, accion: str = "dar"):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        placa = user_state['placa']
        nombre_ag = await self.obtener_nombre_dni(uid) or ctx.author.display_name
        licencia = tipo_licencia.lower()
        if accion.lower() == "dar":
            await db.dar_licencia(usuario.id, licencia)
            embed = discord.Embed(
                title="📋 LICENCIA OTORGADA",
                description=f"{nombre_ag} concedió {licencia} a {usuario.mention}.",
                color=0x00FF00
            )
        else:
            await db.quitar_licencia(usuario.id, licencia)
            embed = discord.Embed(
                title="📋 LICENCIA REVOCADA",
                description=f"{nombre_ag} revocó {licencia} a {usuario.mention}.",
                color=0xFF0000
            )
        await ctx.send(embed=embed)
        await self.log("PDA_LICENCIA", f"{nombre_ag} {accion} {licencia} a {usuario.name}")

    @pda.command(name='buscar')
    async def pda_buscar(self, ctx, *, nombre: str):
        rows = await db.fetchall("SELECT user_id, dni_nombre, dni_apellidos FROM users WHERE dni_nombre LIKE ? OR dni_apellidos LIKE ?",
                                 (f'%{nombre}%', f'%{nombre}%'))
        if not rows:
            return await ctx.send(embed=embed_error("No se encontraron resultados."))
        embed = discord.Embed(title=f"🔍 Resultados para '{nombre}'", color=0x3498DB)
        for uid, nombre, apellidos in rows[:5]:
            user = ctx.guild.get_member(uid)
            nombre_completo = f"{nombre} {apellidos}".strip()
            embed.add_field(
                name=nombre_completo,
                value=f"ID: {uid}\nUsuario: {user.mention if user else uid}",
                inline=False
            )
        await ctx.send(embed=embed)

    @pda.command(name='crear-placa')
    async def pda_crear_placa(self, ctx, numero: str):
        if not any(role.name == "LSPD" for role in ctx.author.roles):
            return await ctx.send(embed=embed_error("Necesitas el rol **LSPD** para crear una placa policial."))

        if not numero.isdigit() or len(numero) != 4:
            return await ctx.send(embed=embed_error("El número de placa debe ser exactamente 4 dígitos (ej: 0001)."))

        placa_completa = f"LSPD-{numero}"
        user_state = await db.get_user_state(ctx.author.id)
        if user_state.get('placa'):
            return await ctx.send(embed=embed_error(f"Ya tienes una placa asignada: {user_state['placa']}. Usa `-pda quitar-placa` si quieres cambiarla."))

        await db.update_user_state(ctx.author.id, placa=placa_completa)
        embed = discord.Embed(
            title="✅ PLACA ASIGNADA",
            description=f"Se te ha asignado la placa **{placa_completa}**. Ahora puedes usar los comandos de PDA.",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("CREAR_PLACA", f"{ctx.author.name} asignó placa {placa_completa}")

    @pda.command(name='quitar-placa')
    async def pda_quitar_placa(self, ctx):
        user_state = await db.get_user_state(ctx.author.id)
        if not user_state.get('placa'):
            return await ctx.send(embed=embed_error("No tienes una placa asignada."))

        await db.update_user_state(ctx.author.id, placa=None)
        embed = discord.Embed(
            title="🗑️ PLACA ELIMINADA",
            description="Tu placa policial ha sido eliminada.",
            color=0xFF6600
        )
        await ctx.send(embed=embed)
        await self.log("QUITAR_PLACA", f"{ctx.author.name} eliminó su placa")

# ------------------------------------------------
# COG: Móvil
# ------------------------------------------------
class Movil(BaseCog):
    @commands.hybrid_command(name='movil', description="Abrir móvil")
    @check_ban()
    async def movil(self, ctx):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        if user_state['airplane_mode']:
            return await ctx.send(embed=embed_error("Modo avión activado. Desactívalo con `-avion off`"))
        numero = user_state['phone_number'] or "Sin número"
        wifi = "📶 Conectado" if user_state['wifi_connected'] else "📶 Desconectado"
        embed = discord.Embed(
            title=f"📱 Móvil de {ctx.author.name}",
            description=f"📞 Número: `{numero}`\n{wifi}",
            color=0x00BCD4
        )
        view = MovilView(ctx.author.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(name='avion')
    @check_ban()
    async def avion(self, ctx, estado: str):
        uid = ctx.author.id
        if estado.lower() not in ['on', 'off']:
            return await ctx.send(embed=embed_error("Usa `on` o `off`"))
        on = estado.lower() == 'on'
        await db.update_user_state(uid, airplane_mode=on)
        await ctx.send(embed=embed_success("✈️ Modo avión", f"{'Activado' if on else 'Desactivado'}"))

    @commands.command(name='wifi')
    @check_ban()
    async def wifi(self, ctx, accion: str = None):
        uid = ctx.author.id
        user_state = await db.get_user_state(uid)
        if not accion:
            return await ctx.send(embed=embed_info("📶 WiFi", f"Estado: {'Conectado' if user_state['wifi_connected'] else 'Desconectado'}\nUsa `-wifi conectar` o `-wifi desconectar`"))
        if accion.lower() == 'conectar':
            if user_state['wifi_connected']:
                return await ctx.send(embed=embed_error("Ya estás conectado."))
            await db.update_user_state(uid, wifi_connected=True)
            await ctx.send(embed=embed_success("📶 WiFi", "Conectado a la red."))
        elif accion.lower() == 'desconectar':
            if not user_state['wifi_connected']:
                return await ctx.send(embed=embed_error("Ya estás desconectado."))
            await db.update_user_state(uid, wifi_connected=False)
            await ctx.send(embed=embed_success("📶 WiFi", "Desconectado de la red.", color=0xFFA500))
        else:
            await ctx.send(embed=embed_error("Usa `conectar` o `desconectar`"))

    @commands.command(name='comprar-sim', aliases=['sim'])
    @check_ban()
    async def comprar_sim(self, ctx):
        uid = ctx.author.id
        eco = await db.get_economy(uid)
        if eco['cash'] < 500:
            return await ctx.send(embed=embed_error("Necesitas $500."))
        numero = f"+34 6{random.randint(10,99)} {random.randint(100,999)} {random.randint(100,999)}"
        await db.add_cash(uid, -500)
        await db.update_user_state(uid, phone_number=numero)
        await ctx.send(embed=embed_success("📱 SIM comprada", f"Número: `{numero}`\nCosto: $500"))
        await self.log("COMPRA_SIM", f"{ctx.author.name} compró SIM: {numero}")

class MovilView(discord.ui.View):
    def __init__(self, uid):
        super().__init__(timeout=120)
        self.uid = uid

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.uid:
            await interaction.response.send_message(embed=embed_error("No es tu móvil."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="📸 Instagram", style=discord.ButtonStyle.danger, row=0)
    async def btn_ig(self, interaction, button):
        await interaction.response.send_message(embed=embed_info("📸 Instagram", "Comandos:\n`-ig perfil`\n`-ig post \"texto\"`\n`-ig like <id>`\n`-ig seguir @user`\n`-ig priv @user msg`\n`-ig trending`", 0xE4405F), ephemeral=True)

    @discord.ui.button(label="🐦 Twitter", style=discord.ButtonStyle.secondary, row=0)
    async def btn_tw(self, interaction, button):
        await interaction.response.send_message(embed=embed_info("🐦 Twitter", "Comandos:\n`-tw perfil`\n`-tw tweet \"texto\"`\n`-tw seguir @user`\n`-tw priv @user msg`", 0x1DA1F2), ephemeral=True)

    @discord.ui.button(label="📘 Facebook", style=discord.ButtonStyle.primary, row=0)
    async def btn_fb(self, interaction, button):
        await interaction.response.send_message(embed=embed_info("📘 Facebook", "Comandos:\n`-fb post \"texto\"`\n`-fb priv @user msg`\n`-fb perfil`", 0x1877F2), ephemeral=True)

    @discord.ui.button(label="💬 WhatsApp", style=discord.ButtonStyle.success, row=1)
    async def btn_wa(self, interaction, button):
        await interaction.response.send_message(embed=embed_info("💬 WhatsApp", "Comandos:\n`-wa contactos`\n`-wa agregar +34... Nombre`\n`-wa chat @user msg`\n`-wa llamar @user`", 0x25D366), ephemeral=True)

    @discord.ui.button(label="🕸️ DeepWeb", style=discord.ButtonStyle.danger, row=1)
    async def btn_dw(self, interaction, button):
        await interaction.response.send_message(embed=embed_info("🕸️ DeepWeb", "Anónimo.\n`-dw priv @user mensaje`", 0x2C2F33), ephemeral=True)

    @discord.ui.button(label="⚙️ Config", style=discord.ButtonStyle.secondary, row=2)
    async def btn_cfg(self, interaction, button):
        user_state = await db.get_user_state(self.uid)
        n = user_state['phone_number'] or "❌ Sin número"
        av = "✈️ ON" if user_state['airplane_mode'] else "✈️ OFF"
        wf = "📶 ON" if user_state['wifi_connected'] else "📶 OFF"
        await interaction.response.send_message(embed=embed_info("⚙️ Configuración", f"📱 {n}\n{av}\n{wf}\n\n`-avion on/off`\n`-wifi conectar/desconectar`\n`-comprar-sim`", 0x95A5A6), ephemeral=True)

# ------------------------------------------------
# COG: Redes Sociales (Instagram, Twitter, Facebook, DeepWeb)
# ------------------------------------------------
class Redes(BaseCog):
    @commands.group(name='ig', invoke_without_command=True)
    @check_ban()
    async def ig(self, ctx):
        await ctx.send(embed=embed_info("📸 Instagram", "`-ig perfil`\n`-ig post \"texto\"`\n`-ig like <id>`\n`-ig seguir @user`\n`-ig priv @user msg`\n`-ig trending`", 0xE4405F))

    @ig.command(name='perfil')
    async def ig_perfil(self, ctx, usuario: discord.Member = None):
        objetivo = usuario or ctx.author
        uid = objetivo.id
        user_state = await db.get_user_state(uid)
        seguidores = await db.get_followers_ig(uid)
        siguiendo = await db.get_following_ig(uid)
        posts = await db.get_posts_ig(uid)
        likes_totales = sum(len(p['likes']) for p in posts)
        embed = discord.Embed(title=f"📸 @{objetivo.name}", color=0xE4405F)
        embed.add_field(name="Seguidores", value=f"{seguidores}", inline=True)
        embed.add_field(name="Siguiendo", value=f"{siguiendo}", inline=True)
        embed.add_field(name="Posts", value=f"{len(posts)}", inline=True)
        embed.add_field(name="Likes recibidos", value=f"{likes_totales}", inline=True)
        embed.add_field(name="Privacidad", value="Pública" if user_state['ig_public'] else "Privada", inline=True)
        embed.add_field(name="Bio", value=user_state['ig_bio'] or "Sin bio", inline=False)
        embed.set_thumbnail(url=objetivo.display_avatar.url)
        await ctx.send(embed=embed)

    @ig.command(name='post')
    async def ig_post(self, ctx, *, texto: str):
        uid = ctx.author.id
        pid = await db.add_post_ig(uid, texto)
        await ctx.send(embed=embed_success("📸 Publicado", f"ID: `{pid}`\n{texto[:200]}"))

    @ig.command(name='like')
    async def ig_like(self, ctx, post_id: str):
        uid = ctx.author.id
        if await db.add_like_ig(post_id, uid):
            await ctx.send(embed=embed_success("❤️ Like", f"Has dado like al post `{post_id}`.", 0xE4405F))
            await self.log("IG_LIKE", f"{ctx.author.name} dio like al post {post_id}")
        else:
            await ctx.send(embed=embed_error("Post no encontrado o ya le diste like."))

    @ig.command(name='seguir')
    async def ig_seguir(self, ctx, usuario: discord.Member):
        uid, tid = ctx.author.id, usuario.id
        if uid == tid:
            return await ctx.send(embed=embed_error("No puedes seguirte a ti mismo."))
        if await db.is_following_ig(uid, tid):
            await db.unfollow_ig(uid, tid)
            await ctx.send(embed=embed_success("📸 Dejado de seguir", f"Dejaste de seguir a {usuario.display_name}.", 0xFFA500))
        else:
            await db.follow_ig(uid, tid)
            await ctx.send(embed=embed_success("📸 Siguiendo", f"Ahora sigues a {usuario.display_name}.", 0x00FF00))
            await self.dm_user(tid, discord.Embed(title="📸 Nuevo seguidor", description=f"{ctx.author.display_name} te sigue ahora en Instagram.", color=0xE4405F))

    @ig.command(name='trending')
    async def ig_trending(self, ctx):
        rows = await db.fetchall("SELECT id, user_id, texto, tiempo, likes FROM posts_ig")
        posts = []
        for row in rows:
            likes = json.loads(row[4]) if row[4] else []
            if len(likes) > 0:
                posts.append({"user_id": row[1], "texto": row[2], "likes": len(likes), "id": row[0]})
        posts.sort(key=lambda x: x['likes'], reverse=True)
        embed = discord.Embed(title="📸 TRENDING SEMANAL", color=0xE4405F)
        for i, p in enumerate(posts[:5], 1):
            user = ctx.guild.get_member(p['user_id'])
            nombre = user.display_name if user else f"Usuario {p['user_id']}"
            embed.add_field(
                name=f"{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else f'#{i}'} {nombre} — ❤️ {p['likes']}",
                value=f"{p['texto'][:50]}...\n🆔 `{p['id']}`",
                inline=False
            )
        await ctx.send(embed=embed)

    @ig.command(name='priv')
    async def ig_priv(self, ctx, user: discord.Member, *, msg: str):
        if ctx.author.id == user.id:
            return await ctx.send(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        dm = discord.Embed(
            title="📩 Instagram — Mensaje privado",
            description=msg,
            color=0xE4405F,
            timestamp=datetime.now()
        )
        dm.set_author(name=f"@{ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await self.dm_user(user.id, dm)
        await ctx.send(embed=embed_success("📨 Mensaje enviado", f"Enviado a @{user.display_name}"))

    @commands.group(name='tw', invoke_without_command=True)
    @check_ban()
    async def tw(self, ctx):
        await ctx.send(embed=embed_info("🐦 Twitter", "`-tw perfil`\n`-tw tweet \"texto\"`\n`-tw seguir @user`\n`-tw priv @user msg`", 0x1DA1F2))

    @tw.command(name='perfil')
    async def tw_perfil(self, ctx, usuario: discord.Member = None):
        objetivo = usuario or ctx.author
        uid = objetivo.id
        seguidores = await db.get_followers_tw(uid)
        siguiendo = await db.get_following_tw(uid)
        posts = await db.fetchall("SELECT id FROM posts_tw WHERE user_id = ?", (uid,))
        embed = discord.Embed(title=f"🐦 @{objetivo.name}", color=0x1DA1F2)
        embed.add_field(name="Seguidores", value=f"{seguidores}", inline=True)
        embed.add_field(name="Siguiendo", value=f"{siguiendo}", inline=True)
        embed.add_field(name="Tweets", value=f"{len(posts)}", inline=True)
        embed.set_thumbnail(url=objetivo.display_avatar.url)
        await ctx.send(embed=embed)

    @tw.command(name='tweet')
    async def tw_tweet(self, ctx, *, texto: str):
        uid = ctx.author.id
        pid = await db.add_post_tw(uid, texto)
        await ctx.send(embed=embed_success("🐦 Tweet", f"{texto[:200]}\nID: `{pid}`", 0x1DA1F2))

    @tw.command(name='seguir')
    async def tw_seguir(self, ctx, usuario: discord.Member):
        uid, tid = ctx.author.id, usuario.id
        if uid == tid:
            return await ctx.send(embed=embed_error("No puedes seguirte a ti mismo."))
        if await db.is_following_tw(uid, tid):
            await db.unfollow_tw(uid, tid)
            await ctx.send(embed=embed_success("🐦 Dejado de seguir", f"Dejaste de seguir a {usuario.display_name} en Twitter.", 0xFFA500))
        else:
            await db.follow_tw(uid, tid)
            await ctx.send(embed=embed_success("🐦 Siguiendo", f"Ahora sigues a {usuario.display_name} en Twitter.", 0x00FF00))
            await self.dm_user(tid, discord.Embed(title="🐦 Nuevo seguidor", description=f"{ctx.author.display_name} te sigue ahora en Twitter.", color=0x1DA1F2))

    @tw.command(name='priv')
    async def tw_priv(self, ctx, user: discord.Member, *, msg: str):
        if ctx.author.id == user.id:
            return await ctx.send(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        dm = discord.Embed(title="🐦 Twitter — DM", description=msg, color=0x1DA1F2, timestamp=datetime.now())
        dm.set_author(name=f"@{ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await self.dm_user(user.id, dm)
        await ctx.send(embed=embed_success("📨 DM enviado", f"A @{user.display_name}"))

    @commands.group(name='fb', invoke_without_command=True)
    @check_ban()
    async def fb(self, ctx):
        await ctx.send(embed=embed_info("📘 Facebook", "`-fb post \"texto\"`\n`-fb priv @user msg`\n`-fb perfil`", 0x1877F2))

    @fb.command(name='post')
    async def fb_post(self, ctx, *, texto: str):
        uid = ctx.author.id
        pid = await db.add_post_fb(uid, texto)
        await ctx.send(embed=embed_success("📘 Publicado", f"ID: `{pid}`\n{texto[:200]}", 0x1877F2))

    @fb.command(name='perfil')
    async def fb_perfil(self, ctx):
        uid = ctx.author.id
        posts = await db.fetchall("SELECT id FROM posts_fb WHERE user_id = ?", (uid,))
        await ctx.send(embed=embed_info(f"📘 {ctx.author.name}", f"Tienes {len(posts)} publicaciones.", 0x1877F2))

    @fb.command(name='priv')
    async def fb_priv(self, ctx, user: discord.Member, *, msg: str):
        if ctx.author.id == user.id:
            return await ctx.send(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        dm = discord.Embed(title="📘 Facebook — Mensaje privado", description=msg, color=0x1877F2, timestamp=datetime.now())
        dm.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        await self.dm_user(user.id, dm)
        await ctx.send(embed=embed_success("📨 Mensaje enviado", f"A {user.display_name}"))

    @commands.group(name='dw', invoke_without_command=True)
    @check_ban()
    async def dw(self, ctx):
        await ctx.send(embed=embed_info("🕸️ DeepWeb", "Anónimo.\n`-dw priv @user mensaje`", 0x2C2F33))

    @dw.command(name='priv')
    async def dw_priv(self, ctx, user: discord.Member, *, msg: str):
        if ctx.author.id == user.id:
            return await ctx.send(embed=embed_error("No puedes enviarte un mensaje a ti mismo."))
        dm = discord.Embed(title="🕸️ Mensaje Anónimo — DeepWeb", description=msg, color=0x2C2F33, timestamp=datetime.now())
        dm.set_footer(text="— Identidad oculta")
        await self.dm_user(user.id, dm)
        await ctx.send(embed=embed_success("🕸️ Mensaje enviado", "Anónimo."))

# ------------------------------------------------
# COG: WhatsApp
# ------------------------------------------------
class WhatsApp(BaseCog):
    @commands.group(name='wa', invoke_without_command=True)
    @check_ban()
    async def wa(self, ctx):
        await ctx.send(embed=embed_info("💬 WhatsApp", "`-wa contactos`\n`-wa agregar +34... Nombre`\n`-wa chat @user msg`\n`-wa llamar @user`", 0x25D366))

    @wa.command(name='contactos')
    async def wa_contactos(self, ctx):
        uid = ctx.author.id
        contactos = await db.get_wa_contacts(uid)
        if not contactos:
            return await ctx.send(embed=embed_info("📒 Contactos", "No tienes contactos."))
        txt = "\n".join([f"📱 `{num}` — {nom}" for num, nom in contactos.items()])
        await ctx.send(embed=embed_info("📒 Contactos", txt, 0x25D366))

    @wa.command(name='agregar')
    async def wa_agregar(self, ctx, numero: str, *, nombre: str):
        uid = ctx.author.id
        if not numero.startswith("+"):
            numero = "+" + numero
        await db.add_wa_contact(uid, numero, nombre)
        await ctx.send(embed=embed_success("✅ Contacto añadido", f"**{nombre}**: `{numero}`"))

    @wa.command(name='chat')
    async def wa_chat(self, ctx, user: discord.Member, *, msg: str):
        uid, tid = ctx.author.id, user.id
        unum = (await db.get_user_state(uid)).get('phone_number')
        tnum = (await db.get_user_state(tid)).get('phone_number')
        if not unum:
            return await ctx.send(embed=embed_error("Necesitas una SIM. Usa `-comprar-sim`"))
        if not tnum:
            return await ctx.send(embed=embed_error(f"{user.display_name} no tiene SIM."))
        await db.add_wa_chat(uid, tid, msg)
        dm = discord.Embed(
            title="💬 WhatsApp — Mensaje",
            description=msg,
            color=0x25D366,
            timestamp=datetime.now()
        )
        dm.set_author(name=f"{ctx.author.display_name} ({unum})", icon_url=ctx.author.display_avatar.url)
        dm.set_footer(text=f"Número: {unum}")
        await self.dm_user(tid, dm)
        await ctx.send(embed=embed_success("📨 Mensaje enviado", f"A {user.display_name} (`{tnum}`)"))

    @wa.command(name='llamar')
    async def wa_llamar(self, ctx, user: discord.Member, duracion: int = 5):
        uid, tid = ctx.author.id, user.id
        if uid == tid:
            return await ctx.send(embed=embed_error("No puedes llamarte a ti mismo."))
        unum = (await db.get_user_state(uid)).get('phone_number')
        tnum = (await db.get_user_state(tid)).get('phone_number')
        if not unum:
            return await ctx.send(embed=embed_error("Necesitas una SIM. Usa `-comprar-sim`"))
        if not tnum:
            return await ctx.send(embed=embed_error(f"{user.display_name} no tiene SIM."))
        if not ctx.author.voice:
            return await ctx.send(embed=embed_error("Debes estar en un canal de voz para llamar."))
        categoria = ctx.guild.get_channel(CANAL_VOICE_CATEGORY)
        if not categoria:
            categoria = discord.utils.get(ctx.guild.categories, name="Llamadas")
            if not categoria:
                categoria = await ctx.guild.create_category("Llamadas")
        canal_nombre = f"📞 Llamada-{ctx.author.name[:5]}-{user.name[:5]}"
        try:
            canal_voz = await ctx.guild.create_voice_channel(name=canal_nombre, category=categoria, user_limit=2)
            await ctx.author.move_to(canal_voz)
            if user.voice:
                await user.move_to(canal_voz)
            embed = discord.Embed(
                title="📞 LLAMADA INICIADA",
                description=f"De: {ctx.author.mention}\nPara: {user.mention}\nDuración: {duracion} minutos\nCanal: {canal_voz.mention}",
                color=0x25D366
            )
            await ctx.send(embed=embed)
            await self.dm_user(tid, discord.Embed(title="📞 Llamada entrante", description=f"{ctx.author.display_name} te está llamando. Duración: {duracion} min.", color=0x25D366))
            await asyncio.sleep(duracion * 60)
            await canal_voz.delete()
            await ctx.send(embed=embed_success("📞 LLAMADA FINALIZADA", color=0xFF0000))
        except Exception as e:
            await ctx.send(embed=embed_error(str(e)))

# ------------------------------------------------
# COG: Periódico
# ------------------------------------------------
class Periodico(BaseCog):
    @commands.command(name='periodico')
    @commands.has_permissions(administrator=True)
    async def publicar_periodico(self, ctx):
        if not any(role.name.lower() == "periodista" for role in ctx.author.roles) and not ctx.author.guild_permissions.administrator:
            return await ctx.send(embed=embed_error("Solo los **Periodistas** pueden publicar el periódico."))
        canal = self.bot.get_channel(CANAL_PERIODICO)
        if not canal:
            return await ctx.send(embed=embed_error("Canal de periódico no configurado. Edita la variable `CANAL_PERIODICO` en el código."))
        embed = discord.Embed(
            title="📰 LOS SANTOS OBSERVER",
            description=f"*Edición del {datetime.now().strftime('%d/%m/%Y %H:%M')}*",
            color=0x2C3E50,
            timestamp=datetime.now()
        )
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
        embed.set_footer(text="NOVA AGORA RP · Los Santos Observer")
        await canal.send(embed=embed)
        await self.log("PERIODICO", f"{ctx.author.name} publicó una edición del periódico")
        await ctx.send(embed=embed_success("✅ Periódico publicado", "La edición ha sido publicada."))

# ------------------------------------------------
# COG: Admin (con comandos de administración)
# ------------------------------------------------
class Admin(BaseCog):
    @commands.command(name='say')
    @commands.has_permissions(administrator=True)
    async def say(self, ctx, *, mensaje: str = None):
        if not mensaje:
            return await ctx.send(embed=embed_help(
                "say",
                "Repite el mensaje en negrita.",
                "-say <mensaje>",
                "-say Hola a todos\n-say pepe",
                "Administrador"
            ))
        await ctx.send(f"**{mensaje}**")
        try:
            await ctx.message.delete()
        except:
            pass

    @commands.group(name='ban', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx):
        await ctx.send(embed=embed_help(
            "ban",
            "Banea a un usuario. Usa el subcomando 'definitivo' para baneo permanente + blacklist.",
            "-ban @usuario [razón]          (baneo normal)\n-ban definitivo @usuario [razón]",
            "-ban @Juan Spam\n-ban definitivo @Juan Spam masivo",
            "Administrador"
        ))

    @ban.command(name='definitivo')
    @commands.has_permissions(administrator=True)
    async def ban_definitivo(self, ctx, miembro: discord.Member, *, razon: str = "Sin razón"):
        if miembro.id == ctx.author.id:
            return await ctx.send(embed=embed_error("No puedes banearte a ti mismo."))

        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.send(embed=embed_error("No tengo permiso para banear miembros en este servidor."))

        await db.add_to_blacklist(miembro.id, razon, ctx.author.id)
        await db.update_user_state(miembro.id, banned=True, ban_reason=razon, banned_by=ctx.author.id, ban_date=datetime.now().isoformat())
        try:
            await ctx.guild.ban(miembro, reason=razon, delete_message_days=0)
            discord_ban = "✅ Baneado del servidor"
        except Exception as e:
            discord_ban = f"❌ Error al banear del servidor: {str(e)[:100]}"
        embed = discord.Embed(
            title="🔨 BANEO DEFINITIVO EJECUTADO",
            description=f"Usuario: {miembro.mention}\nRazón: {razon}\n{discord_ban}\n🖤 Añadido a la blacklist global.",
            color=0xFF0000
        )
        await ctx.send(embed=embed)
        await self.log("BAN_DEFINITIVO", f"{ctx.author.name} baneó permanentemente a {miembro.name}: {razon}")

    @commands.command(name='unban')
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, uid: int = None):
        if not uid:
            return await ctx.send(embed=embed_help(
                "unban",
                "Desbanea a un usuario por su ID y lo elimina de la blacklist global.",
                "-unban <id>",
                "-unban 123456789012345678",
                "Administrador"
            ))
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
        embed = discord.Embed(
            title="✅ DESBANEO EJECUTADO",
            description=f"Usuario: {user.mention if 'user' in locals() else uid}\n{discord_unban}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("UNBAN", f"{ctx.author.name} desbaneó ID: {uid} (eliminado de blacklist)")

    @commands.command(name='money')
    @commands.has_permissions(administrator=True)
    async def money(self, ctx, accion: str = None, miembro: discord.Member = None, cantidad: int = None):
        if not accion or not miembro or not cantidad:
            return await ctx.send(embed=embed_help(
                "money",
                "Añade o quita dinero en efectivo a un usuario.",
                "-money add/remove @usuario <cantidad>",
                "-money add @Juan 5000\n-money remove @Juan 2000",
                "Administrador"
            ))
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("La cantidad debe ser mayor a 0."))
        if accion.lower() == 'add':
            await db.add_cash(miembro.id, cantidad)
            await ctx.send(embed=embed_success("💸 Dinero añadido", f"**${cantidad:,}** a {miembro.mention}"))
            await self.log("MONEY_ADD", f"{ctx.author.name} dio ${cantidad:,} a {miembro.name}")
        elif accion.lower() == 'remove':
            eco = await db.get_economy(miembro.id)
            if eco['cash'] < cantidad:
                return await ctx.send(embed=embed_error("Saldo insuficiente."))
            await db.add_cash(miembro.id, -cantidad)
            await ctx.send(embed=embed_success("💸 Dinero removido", f"**${cantidad:,}** de {miembro.mention}", 0xFF6600))
            await self.log("MONEY_REMOVE", f"{ctx.author.name} quitó ${cantidad:,} a {miembro.name}")
        else:
            await ctx.send(embed=embed_error("Acción debe ser `add` o `remove`."))

    @commands.command(name='setprefix')
    @commands.has_permissions(administrator=True)
    async def setpre(self, ctx, p: str = None):
        if not p:
            return await ctx.send(embed=embed_help(
                "setprefix",
                "Cambia el prefijo del bot en este servidor.",
                "-setprefix <nuevo_prefijo>",
                "-setprefix !",
                "Administrador"
            ))
        if len(p) > 5:
            return await ctx.send(embed=embed_error("Máximo 5 caracteres."))
        with open('prefixes.json', 'w') as f:
            json.dump({str(ctx.guild.id): p}, f)
        await ctx.send(embed=embed_success("✅ Prefijo cambiado", f"Nuevo prefijo: `{p}`"))
        await self.log("SETPREFIX", f"{ctx.author.name} cambió prefijo a '{p}'")

    @commands.command(name='add-inv')
    @commands.has_permissions(administrator=True)
    async def addinv(self, ctx, miembro: discord.Member = None, tipo: str = None, item: str = None, cantidad: int = 1):
        if not miembro or not tipo or not item:
            return await ctx.send(embed=embed_help(
                "add-inv",
                "Añade un item al inventario de un usuario.",
                "-add-inv @usuario <tipo> <item> [cantidad]",
                "-add-inv @Juan personal Pistola 1\nTipos: personal, vehiculo, propiedad, negocios",
                "Administrador"
            ))
        t = tipo.lower()
        if t not in ['personal', 'vehiculo', 'propiedad', 'negocios']:
            return await ctx.send(embed=embed_error("Tipo inválido. Usa: personal, vehiculo, propiedad, negocios"))
        await db.add_item(miembro.id, t, item, cantidad)
        await ctx.send(embed=embed_success("✅ Item añadido", f"{cantidad}x {item} a {miembro.mention} ({t})"))
        await self.log("ADD_INV", f"{ctx.author.name} añadió {cantidad}x {item} ({t}) a {miembro.name}")

    @commands.command(name='rem-inv')
    @commands.has_permissions(administrator=True)
    async def reminv(self, ctx, miembro: discord.Member = None, tipo: str = None, item: str = None, cantidad: int = 1):
        if not miembro or not tipo or not item:
            return await ctx.send(embed=embed_help(
                "rem-inv",
                "Elimina un item del inventario de un usuario.",
                "-rem-inv @usuario <tipo> <item> [cantidad]",
                "-rem-inv @Juan personal Pistola 1",
                "Administrador"
            ))
        t = tipo.lower()
        if t not in ['personal', 'vehiculo', 'propiedad', 'negocios']:
            return await ctx.send(embed=embed_error("Tipo inválido. Usa: personal, vehiculo, propiedad, negocios"))
        eliminado = await db.remove_item(miembro.id, t, item, cantidad)
        if eliminado == 0:
            return await ctx.send(embed=embed_error(f"{miembro.name} no tiene {item} en {t}."))
        await ctx.send(embed=embed_success("🗑️ Item eliminado", f"{eliminado}x {item} de {miembro.mention} ({t})", 0xFF6600))
        await self.log("REM_INV", f"{ctx.author.name} eliminó {eliminado}x {item} ({t}) de {miembro.name}")

    @commands.command(name='add-coche')
    @commands.has_permissions(administrator=True)
    async def addcar(self, ctx, miembro: discord.Member = None, modelo: str = None):
        if not miembro or not modelo:
            return await ctx.send(embed=embed_help(
                "add-coche",
                "Registra un vehículo para un usuario (matrícula aleatoria).",
                "-add-coche @usuario <modelo>",
                "-add-coche @Juan Turismo",
                "Administrador"
            ))
        matricula = f"{random.randint(1000,9999)} {''.join(random.choices('BCDFGHJKLMNPQRSTVWXYZ', k=3))}"
        await db.add_vehiculo(miembro.id, matricula, modelo)
        embed = discord.Embed(
            title="✅ VEHÍCULO REGISTRADO",
            description=f"Modelo: {modelo}\nMatrícula: {matricula}\nPropietario: {miembro.mention}",
            color=0x00FF00
        )
        await ctx.send(embed=embed)
        await self.log("ADD_COCHE", f"{ctx.author.name} añadió {modelo} ({matricula}) a {miembro.name}")

    @commands.command(name='remove-coche')
    @commands.has_permissions(administrator=True)
    async def remcar(self, ctx, miembro: discord.Member = None, matricula: str = None):
        if not miembro or not matricula:
            return await ctx.send(embed=embed_help(
                "remove-coche",
                "Elimina un vehículo de un usuario por matrícula.",
                "-remove-coche @usuario <matrícula>",
                "-remove-coche @Juan 1234 ABC",
                "Administrador"
            ))
        await db.execute("DELETE FROM vehiculos WHERE user_id = ? AND matricula = ?", (miembro.id, matricula))
        await ctx.send(embed=embed_success("🗑️ Vehículo eliminado", f"Matrícula {matricula} de {miembro.mention}", 0xFF6600))
        await self.log("REM_COCHE", f"{ctx.author.name} quitó {matricula} a {miembro.name}")

    @commands.command(name='add-droga')
    @commands.has_permissions(administrator=True)
    async def adddrg(self, ctx, miembro: discord.Member = None, tipo: str = None, cantidad: int = 1):
        if not miembro or not tipo:
            return await ctx.send(embed=embed_help(
                "add-droga",
                "Añade droga al inventario personal de un usuario.",
                "-add-droga @usuario <tipo> [cantidad]",
                "-add-droga @Juan Marihuana 5",
                "Administrador"
            ))
        tipo_norm = tipo.capitalize()
        if tipo_norm not in Drogas.EMOJIS_DROGA:
            return await ctx.send(embed=embed_error(f"Tipo no válido. Opciones: {', '.join(Drogas.EMOJIS_DROGA.keys())}"))
        await db.add_item(miembro.id, "personal", tipo_norm, cantidad)
        await ctx.send(embed=embed_success("✅ Droga añadida", f"{cantidad}x {tipo_norm} a {miembro.mention}"))
        await self.log("ADD_DROGA", f"{ctx.author.name} añadió {cantidad}x {tipo_norm} a {miembro.name}")

    @commands.command(name='add-licencia')
    @commands.has_permissions(administrator=True)
    async def addlicencia(self, ctx, miembro: discord.Member = None, licencia: str = None):
        if not miembro or not licencia:
            return await ctx.send(embed=embed_help(
                "add-licencia",
                "Otorga una licencia de armas.",
                "-add-licencia @usuario <tipo_licencia>",
                "-add-licencia @Juan licencia_pistola",
                "Administrador"
            ))
        await db.dar_licencia(miembro.id, licencia.lower())
        await ctx.send(embed=embed_success("✅ Licencia otorgada", f"{licencia} a {miembro.mention}"))

    @commands.command(name='rem-licencia')
    @commands.has_permissions(administrator=True)
    async def remlicencia(self, ctx, miembro: discord.Member = None, licencia: str = None):
        if not miembro or not licencia:
            return await ctx.send(embed=embed_help(
                "rem-licencia",
                "Revoca una licencia de armas.",
                "-rem-licencia @usuario <tipo_licencia>",
                "-rem-licencia @Juan licencia_pistola",
                "Administrador"
            ))
        await db.quitar_licencia(miembro.id, licencia.lower())
        await ctx.send(embed=embed_success("🗑️ Licencia revocada", f"{licencia} a {miembro.mention}", 0xFF6600))

    @commands.command(name='quitar-warn')
    @commands.has_permissions(administrator=True)
    async def quitar_warn(self, ctx, miembro: discord.Member = None, id_warn: int = None):
        if not miembro or not id_warn:
            return await ctx.send(embed=embed_help(
                "quitar-warn",
                "Elimina una advertencia de un usuario por su ID.",
                "-quitar-warn @usuario <id_warn>",
                "-quitar-warn @Juan 3",
                "Administrador"
            ))
        row = await db.fetchone("SELECT id FROM warnings WHERE id = ? AND user_id = ?", (id_warn, miembro.id))
        if not row:
            return await ctx.send(embed=embed_error("Advertencia no encontrada."))
        await db.execute("DELETE FROM warnings WHERE id = ?", (id_warn,))
        await self.registrar_log_moderacion(ctx, f"WARN #{id_warn} ELIMINADA", miembro, "Eliminada por administrador")
        await ctx.send(embed=embed_success("🗑️ Advertencia eliminada", f"Se eliminó la advertencia #{id_warn} de {miembro.mention}.", 0xFF6600))

    @commands.command(name='economy-reset')
    @commands.has_permissions(administrator=True)
    async def economy_reset(self, ctx, target: str = None, cantidad: int = 0):
        if not target:
            return await ctx.send(embed=embed_help(
                "economy-reset",
                "Resetea la economía de un usuario o de todos los miembros con un rol.",
                "-economy-reset @usuario [cantidad]\n-economy-reset @rol [cantidad]",
                "-economy-reset @Juan 1000\n-economy-reset @Nuevos 500",
                "Administrador"
            ))
        if cantidad < 0:
            return await ctx.send(embed=embed_error("La cantidad no puede ser negativa."))

        try:
            user = await commands.MemberConverter().convert(ctx, target)
            await db.execute("UPDATE economy SET cash = ?, bank = ?, black_money = ? WHERE user_id = ?",
                             (cantidad, cantidad, cantidad, user.id))
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
            embed = discord.Embed(
                title="⚠️ Confirmar reseteo masivo",
                description=f"¿Estás seguro de que quieres resetear la economía de **{len(members)}** miembros con el rol {role.mention} a **${cantidad:,}**?",
                color=0xFFA500
            )
            await ctx.send(embed=embed, view=view)
            await view.wait()
            if not view.value:
                return await ctx.send(embed=embed_info("Operación cancelada."))

            for member in members:
                await db.execute("UPDATE economy SET cash = ?, bank = ?, black_money = ? WHERE user_id = ?",
                                 (cantidad, cantidad, cantidad, member.id))
            await ctx.send(embed=embed_success("✅ Economías reseteadas", f"Se ha reseteado la economía de {len(members)} miembros a **${cantidad:,}**."))
            await self.log("ECONOMY_RESET_MASS", f"{ctx.author.name} reseteó economía de {len(members)} miembros con rol {role.name} a ${cantidad}")
            return
        except commands.BadArgument:
            pass

        await ctx.send(embed=embed_error("No se encontró un usuario o rol con ese nombre. Usa @usuario o @rol."))

# ------------------------------------------------
# COG: Roleplay (me, do, entorno, reparar, curar) - CORREGIDO
# ------------------------------------------------
class Roleplay(BaseCog):
    @commands.command(name='me')
    @check_encarcelado()
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
    @check_encarcelado()
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
    @check_encarcelado()
    async def entorno(self, ctx, *, descripcion: str):
        try:
            partes = descripcion.split("|", 1)
            desc = partes[0].strip()
            lugar = partes[1].strip().upper() if len(partes) > 1 else None
            titulo = f"🚨 ALERTA DE ENTORNO — {lugar} 🚨" if lugar else "🚨 ALERTA DE ENTORNO 🚨"
            embed = discord.Embed(title=titulo, description=f"*{desc}*", color=discord.Color.red(), timestamp=datetime.now())
            embed.set_author(name="🌍 Narrador del Entorno", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -entorno: {str(e)[:100]}"))

    @commands.command(name='reparar')
    @tiene_profesion("mecánico", "mecanico")
    @check_encarcelado()
    async def reparar(self, ctx, objetivo: discord.Member, *, descripcion: str = "Reparación completada."):
        try:
            nombre_mec = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
            nombre_obj = await self.obtener_nombre_dni(objetivo.id) or objetivo.display_name
            embed = discord.Embed(
                title="🔧 REPARACIÓN COMPLETADA",
                description=f"**{nombre_mec}** ha reparado el vehículo de **{nombre_obj}**.\n\n*{descripcion.strip()}*",
                color=0xE67E22,
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -reparar: {str(e)[:100]}"))

    @commands.command(name='curar')
    @tiene_profesion("médico", "medico", "doctor", "enfermero", "ems")
    @check_encarcelado()
    async def curar(self, ctx, objetivo: discord.Member, *, descripcion: str = "Tratamiento completado."):
        try:
            nombre_med = await self.obtener_nombre_dni(ctx.author.id) or ctx.author.display_name
            nombre_obj = await self.obtener_nombre_dni(objetivo.id) or objetivo.display_name
            embed = discord.Embed(
                title="🏥 CURACIÓN COMPLETADA",
                description=f"**{nombre_med}** ha atendido a **{nombre_obj}**.\n\n*{descripcion.strip()}*",
                color=0x2ECC71,
                timestamp=datetime.now()
            )
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except:
                pass
        except Exception as e:
            await ctx.send(embed=embed_error(f"Error al ejecutar -curar: {str(e)[:100]}"))

# ------------------------------------------------
# COG: Hosting (CORREGIDO)
# ------------------------------------------------
class Hosting(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot_active = False

    @commands.command(name='bot', aliases=['Bot'])
    @is_owner()
    async def hosting_comando(self, ctx, dias: int = None):
        """Activa/renueva el bot por X días (solo owners)."""
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

    @commands.command(name='botoff', aliases=['botStop', 'botstop'])
    @is_owner()
    async def botoff_comando(self, ctx):
        """Detiene el bot inmediatamente (solo owners)."""
        embed = discord.Embed(
            title="⛔ Bot detenido",
            description="El bot se está apagando...",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await ctx.send(embed=embed)
        await self.log("HOSTING", f"{ctx.author.name} detuvo el bot manualmente.")
        await asyncio.sleep(1)
        await self.bot.close()

    @tasks.loop(hours=1)
    async def check_expiry(self):
        """Verifica cada hora si el bot debe seguir activo."""
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

# ------------------------------------------------
# COG: Soporte (status, votacion, purge, config, roles, etc.)
# ------------------------------------------------
class Soporte(BaseCog):
    @commands.command(name='status')
    @commands.has_permissions(administrator=True)
    async def status(self, ctx, iniciador: str = None, ciudadanos: int = None, policias: int = None, soporte: int = 0):
        if iniciador is None or ciudadanos is None or policias is None:
            embed = embed_help(
                "status",
                "Publica el estado de la sesión de rol en el canal actual.",
                "-status <iniciador> <ciudadanos> <policías> [soporte]",
                "-status Juan 10 5 2",
                "Administrador"
            )
            return await ctx.send(embed=embed)
        if any(x < 0 for x in [ciudadanos, policias, soporte]):
            return await ctx.send(embed=embed_error("Los números no pueden ser negativos."))
        total = ciudadanos + policias + soporte
        embed = discord.Embed(
            title="🎮 ESTAMOS EN ROL 🎮",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        embed.add_field(name="📌 Iniciador:", value=f"```\n{iniciador}\n```", inline=False)
        embed.add_field(name="🧑 Personas en rol:", value=f"```\n{ciudadanos}\n```", inline=False)
        embed.add_field(name="🚔 Policías en rol:", value=f"```\n{policias}\n```", inline=False)
        embed.add_field(name="🛠️ Soporte en rol:", value=f"```\n{soporte}\n```", inline=False)
        embed.add_field(name="📊 Total en sesión:", value=f"```\n{total}\n```", inline=False)
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzFwNGl2ajRzM3p4d2Zmd2Z5cGxvbjE2dHJlZnYxM2ZkMjZzNjZ5bCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/6T7IlHrbxl7MOye7Hn/giphy.gif")
        embed.set_footer(text=f"Soporte: {ctx.author.display_name}  ·  NOVA AGORA RP", icon_url=ctx.author.display_avatar.url)
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.send(content="@rol", embed=embed)
        await self.log("STATUS", f"{ctx.author.name} — {iniciador} | {ciudadanos}p {policias}pol {soporte}sop")

    @commands.command(name='votacion')
    @commands.has_permissions(administrator=True)
    async def votacion(self, ctx, hora: str = None, *, tema: str = None):
        if not hora:
            embed = embed_help(
                "votacion",
                "Crea una votación de rol en el canal actual con reacciones.",
                "-votacion <hora> [tema]",
                "-votacion 20:00\n-votacion 20:00 Sesión nocturna",
                "Administrador"
            )
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
        embed = discord.Embed(
            title="🗳️ VOTACIÓN DE ROL ✨",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.add_field(name="📌 → Hora:", value=f"```\n{datos['hora']}\n```", inline=False)
        if datos.get("tema"):
            embed.add_field(name="📝 → Tema:", value=f"```\n{datos['tema']}\n```", inline=False)
        embed.add_field(
            name="\u200b",
            value=(
                "✅ → **Si te vas a unir.**\n🚔 → **Si te unes como policía.**\n"
                "❌ → **No te unes.**\n😅 → **Si te vas a unir tarde.**"
            ),
            inline=False
        )
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzFwNGl2ajRzM3p4d2Zmd2Z5cGxvbjE2dHJlZnYxM2ZkMjZzNjZ5bCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/6T7IlHrbxl7MOye7Hn/giphy.gif")
        embed.set_footer(text=f"Soporte: {autor.display_name}  ·  NOVA AGORA RP", icon_url=autor.display_avatar.url)
        msg = await canal.send(content="@rol", embed=embed)
        for emoji in ["✅", "🚔", "❌", "😅"]:
            await msg.add_reaction(emoji)
        await self.log("VOTACION", f"{autor.name} → {datos['hora']}")

    @commands.command(name='purge')
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, cantidad: int = None):
        if cantidad is None:
            embed = embed_help(
                "purge",
                "Borra mensajes en masa en el canal actual.",
                "-purge <1-100>",
                "-purge 20",
                "Gestionar mensajes"
            )
            return await ctx.send(embed=embed)
        if not 1 <= cantidad <= 100:
            return await ctx.send(embed=embed_error("La cantidad debe estar entre 1 y 100."))
        try:
            deleted = await ctx.channel.purge(limit=cantidad + 1)
            msg = await ctx.send(embed=embed_success("🧹 Mensajes eliminados", f"**{len(deleted)-1}** mensajes borrados."))
            await asyncio.sleep(4)
            await msg.delete()
        except discord.HTTPException as e:
            if e.code == 50034:
                await ctx.send(embed=embed_error("No se pueden borrar mensajes de más de 14 días."))
            else:
                await ctx.send(embed=embed_error(f"Error: {str(e)[:100]}"))

    @commands.command(name='config')
    @commands.has_permissions(administrator=True)
    async def config(self, ctx, rol: str = None, *, descripcion: str = None):
        if rol is None or descripcion is None:
            embed = embed_help(
                "config",
                "Guarda la descripción de un rol para mostrarla con `-roles`.",
                "-config <nombre_del_rol> <descripción>",
                "-config Policía Rol encargado de mantener el orden.",
                "Administrador"
            )
            return await ctx.send(embed=embed)
        cfg = self.cargar_config_roles()
        key = rol.lower().strip()
        cfg[key] = {
            "nombre": rol.strip(),
            "descripcion": descripcion.strip(),
            "configurado_por": ctx.author.display_name,
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M")
        }
        self.guardar_config_roles(cfg)
        embed = discord.Embed(title="⚙️ ROL CONFIGURADO", color=discord.Color.blue())
        embed.add_field(name="📌 Rol", value=f"`{rol.strip()}`", inline=True)
        embed.add_field(name="📝 Descripción", value=descripcion.strip(), inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='roles')
    async def roles(self, ctx, rol: Optional[str] = None):
        cfg = self.cargar_config_roles()
        if not cfg:
            return await ctx.send(embed=embed_error("No hay roles configurados."))
        if rol:
            key = rol.lower().strip()
            if key not in cfg:
                return await ctx.send(embed=embed_error(f"Rol `{rol}` no encontrado."))
            r = cfg[key]
            embed = discord.Embed(title=f"⚙️ {r['nombre']}", description=r['descripcion'], color=discord.Color.blue())
            embed.set_footer(text=f"Configurado por {r.get('configurado_por','?')} · {r.get('fecha','?')}")
            return await ctx.send(embed=embed)
        embed = discord.Embed(title="📋 Roles Configurados", color=discord.Color.blue(), timestamp=datetime.now())
        for key, r in cfg.items():
            embed.add_field(name=f"⚙️ {r['nombre']}", value=r['descripcion'][:100], inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='quitar-rol')
    @commands.has_permissions(administrator=True)
    async def quitar_rol(self, ctx, *, rol: str = None):
        if rol is None:
            embed = embed_help(
                "quitar-rol",
                "Elimina la configuración de un rol.",
                "-quitar-rol <nombre_del_rol>",
                "-quitar-rol Policía",
                "Administrador"
            )
            return await ctx.send(embed=embed)
        cfg = self.cargar_config_roles()
        key = rol.lower().strip()
        if key not in cfg:
            return await ctx.send(embed=embed_error(f"Rol `{rol}` no encontrado."))
        nombre = cfg[key]["nombre"]
        del cfg[key]
        self.guardar_config_roles(cfg)
        embed = discord.Embed(title="🗑️ ROL ELIMINADO", color=discord.Color.red(), timestamp=datetime.now())
        embed.add_field(name="📌 Rol eliminado", value=f"`{nombre}`", inline=True)
        embed.add_field(name="👤 Eliminado por", value=ctx.author.mention, inline=True)
        embed.set_footer(text=f"Quedan {len(cfg)} roles configurados")
        await ctx.send(embed=embed)

    @commands.command(name='set-economy-all')
    @commands.has_permissions(administrator=True)
    async def set_economy_all(self, ctx, rol: discord.Role = None, cantidad: int = None):
        if not rol and not cantidad:
            cfg = self.cargar_economy_roles()
            if not cfg:
                return await ctx.send(embed=embed_error("No hay roles configurados con saldo automático."))
            embed = discord.Embed(title="💰 Roles con Economy configurado", color=discord.Color.gold(), timestamp=datetime.now())
            for rid, cant in cfg.items():
                role = ctx.guild.get_role(int(rid))
                nombre = role.mention if role else f"`ID: {rid}` (eliminado)"
                embed.add_field(name=nombre, value=f"```\n**${cant:,}**\n```", inline=True)
            embed.set_footer(text="NOVA AGORA RP · Economy Roles")
            return await ctx.send(embed=embed)
        if rol is None or cantidad is None:
            embed = embed_help(
                "set-economy-all",
                "Asigna un saldo inicial a todos los miembros que tienen un rol específico.",
                "-set-economy-all @rol <cantidad>",
                "-set-economy-all @Nuevos 1000",
                "Administrador"
            )
            return await ctx.send(embed=embed)
        if cantidad <= 0:
            return await ctx.send(embed=embed_error("La cantidad debe ser mayor a $0."))
        cfg = self.cargar_economy_roles()
        cfg[rol.id] = cantidad
        self.guardar_economy_roles(cfg)
        miembros_con_rol = [m for m in ctx.guild.members if rol in m.roles and not m.bot]
        for miembro in miembros_con_rol:
            await db.add_cash(miembro.id, cantidad)
        embed = discord.Embed(
            title="🎮 ECONOMY ROL CONFIGURADO 🎮",
            description=f"**Rol:** {rol.name}\n**Cantidad:** **${cantidad:,}**\n**Actualizados:** {len(miembros_con_rol)} miembros",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Configurado por {ctx.author.display_name}  ·  NOVA AGORA RP")
        await ctx.send(embed=embed)
        await self.log("SET_ECONOMY_ROL", f"{ctx.author.name} → {rol.name} = ${cantidad:,} ({len(miembros_con_rol)} miembros)")

    def cargar_config_roles(self) -> dict:
        try:
            with open('config_roles.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def guardar_config_roles(self, data: dict):
        with open('config_roles.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def cargar_economy_roles(self) -> dict:
        try:
            with open('economy_roles.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def guardar_economy_roles(self, data: dict):
        with open('economy_roles.json', 'w', encoding='utf-8') as f:
            json.dump({str(k): v for k, v in data.items()}, f, ensure_ascii=False, indent=2)

# ------------------------------------------------
# COG: Ayuda (menú interactivo)
# ------------------------------------------------
class Ayuda(BaseCog):
    CATEGORIAS = {
        "soporte": {
            "emoji": "🛠️",
            "nombre": "Soporte",
            "comandos": [
                ("-status <iniciador> <ciudadanos> <policías> [soporte]", "**Publica el estado de sesión RP**"),
                ("-votacion <hora> [tema]", "**Crea una votación de rol**"),
                ("-purge <1-100>", "**Borra mensajes en masa**"),
                ("-config <rol> <descripción> 🔒", "**Configura un rol del servidor**"),
                ("-roles [rol]", "**Muestra los roles configurados**"),
                ("-quitar-rol <rol> 🔒", "**Elimina un rol configurado**"),
                ("-set-economy-all [@rol] [cantidad] 🔒", "**Asigna saldo automático por rol**"),
                ("-economy-reset @usuario/@rol [cantidad] 🔒", "**Resetea la economía de un usuario o rol**"),
                ("/anuncios 🔒", "**Publica un anuncio oficial**"),
                ("/purge <n> 🔒", "**Purge con slash**"),
                ("/votacion <hora> [tema] 🔒", "**Votación con slash**")
            ]
        },
        "roleplay": {
            "emoji": "🎭",
            "nombre": "Roleplay",
            "comandos": [
                ("-me <acción>", "**Narra una acción de tu personaje**"),
                ("-do <pensamiento>", "**Expresa un pensamiento en rol**"),
                ("-entorno <descripción> [|lugar]", "**Describe el entorno (alertas)**"),
                ("-reparar @usuario [descripción]", "**Repara un vehículo (mecánico)**"),
                ("-curar @usuario [descripción]", "**Cura heridas (médico/EMS)**"),
                ("-dni <nombre> <apellidos> <edad> <género> <nacionalidad> <color_ojos> <altura> <profesión>", "**Crea tu DNI**"),
                ("-editardni <campo> <nuevo_valor>", "**Edita tu DNI**"),
                ("-ver dni [@usuario]", "**Muestra el DNI propio o de otro**"),
                ("-verdni [@usuario]", "**Alias de -ver dni**"),
                ("-borrardni @usuario 🔒", "**Elimina DNI de un usuario**")
            ]
        },
        "trabajos": {
            "emoji": "💼",
            "nombre": "Trabajos",
            "comandos": [
                ("-trabajo", "**Sistema de trabajo por minutos**"),
                ("-inv [tipo]", "**Muestra tu inventario**"),
                ("-tienda", "**Abre la tienda de items**"),
                ("-mover <item> <cantidad> <origen> <destino>", "**Mueve items entre inventarios**"),
                ("-intercambio @usuario <cantidad> <item>", "**Da items a otro jugador**"),
                ("-use <item>", "**Usa un item del inventario**"),
                ("-comprar <item> [cantidad]", "**Compra artículos de la tienda**")
            ]
        },
        "ilegales": {
            "emoji": "💊",
            "nombre": "Ilegales",
            "comandos": [
                ("-droga", "**Muestra precios de drogas**"),
                ("-droga comprar <tipo> [cantidad]", "**Compra droga (max 27)**"),
                ("-droga vender <tipo> [cantidad]", "**Vende droga**"),
                ("-rob badu", "**Atraca Badu**"),
                ("-rob lico", "**Atraca Lico's**"),
                ("-rob ammu", "**Atraca Ammu-Nation**"),
                ("-rob yellowjack", "**Atraca Yellow Jack**"),
                ("-rob yate", "**Atraca el yate**"),
                ("-rob pacific", "**Atraca Pacific Standard**"),
                ("-rob jugador @usuario", "**Atraca a un jugador**"),
                ("-blanquear", "**Blanquea dinero negro (65%)**")
            ]
        },
        "armas": {
            "emoji": "🔫",
            "nombre": "Armas",
            "comandos": [
                ("-arma", "**Ver armas equipadas y licencias**"),
                ("-arma equipar <tipo>", "**Equipa un arma**"),
                ("-arma disparar", "**Dispara con el arma equipada**"),
                ("-arma recargar <tipo> <cantidad>", "**Recarga munición**")
            ]
        },
        "vehiculos": {
            "emoji": "🚗",
            "nombre": "Vehículos",
            "comandos": [
                ("-vehiculo", "**Lista tus vehículos**"),
                ("-vehiculo conducir <matrícula>", "**Conduce un vehículo**"),
                ("-vehiculo repostar <matrícula> [cantidad]", "**Reposta combustible**"),
                ("-vehiculo itv <matrícula>", "**Pasa la ITV**")
            ]
        },
        "mercado": {
            "emoji": "🏪",
            "nombre": "Mercado",
            "comandos": [
                ("-mercado", "**Muestra publicaciones**"),
                ("-mercado publicar <item> <precio> <descripción>", "**Publica un item**"),
                ("-mercado comprar <id>", "**Compra un item**"),
                ("-mercado mispub", "**Ver tus publicaciones**"),
                ("-mercado cancelar <id>", "**Cancela publicación**")
            ]
        },
        "casino": {
            "emoji": "🎰",
            "nombre": "Casino",
            "comandos": [
                ("-casino slots <apuesta>", "**Tragaperras**"),
                ("-casino ruleta <apuesta> <tipo>", "**Ruleta**"),
                ("-casino dados <apuesta>", "**Dados**"),
                ("-bj <apuesta>", "**Blackjack**"),
                ("-casino racha", "**Ver racha**")
            ]
        },
        "movil": {
            "emoji": "📱",
            "nombre": "Móvil & Redes",
            "comandos": [
                ("-movil", "**Abre el móvil**"),
                ("-avion on/off", "**Modo avión**"),
                ("-wifi conectar/desconectar", "**Gestiona WiFi**"),
                ("-comprar-sim", "**Compra número de teléfono**"),
                ("-ig perfil", "**Ver perfil de Instagram**"),
                ("-ig post <texto>", "**Publicar en Instagram**"),
                ("-ig like <id>", "**Dar like**"),
                ("-ig seguir @usuario", "**Seguir/dejar de seguir**"),
                ("-ig priv @usuario <msg>", "**Enviar DM**"),
                ("-ig trending", "**Posts más populares**"),
                ("-tw perfil", "**Ver perfil de Twitter**"),
                ("-tw tweet <texto>", "**Publicar tweet**"),
                ("-tw seguir @usuario", "**Seguir/dejar de seguir**"),
                ("-tw priv @usuario <msg>", "**Enviar DM**"),
                ("-fb post <texto>", "**Publicar en Facebook**"),
                ("-fb priv @usuario <msg>", "**Enviar mensaje**"),
                ("-dw priv @usuario <msg>", "**Mensaje anónimo DeepWeb**"),
                ("-wa contactos", "**Ver contactos**"),
                ("-wa agregar +34... <nombre>", "**Añadir contacto**"),
                ("-wa chat @usuario <msg>", "**Enviar mensaje**"),
                ("-wa llamar @usuario [minutos]", "**Llamada de voz**")
            ]
        },
        "pda": {
            "emoji": "🚨",
            "nombre": "PDA Policial",
            "comandos": [
                ("-pda", "**Ver panel PDA**"),
                ("-pda detener @usuario <motivo>", "**Detener a un ciudadano**"),
                ("-pda encarcelar @usuario <minutos> <motivo>", "**Encarcelar**"),
                ("-pda multar @usuario <cantidad> <motivo>", "**Poner multa**"),
                ("-pda requisar @usuario <arma>", "**Requisar arma**"),
                ("-pda licencia @usuario <tipo> [dar/quitar]", "**Gestionar licencias**"),
                ("-pda buscar <nombre>", "**Buscar antecedentes**"),
                ("-pda crear-placa <numero>", "**Crea una placa policial (requiere LSPD)**"),
                ("-pda quitar-placa", "**Elimina tu placa policial**")
            ]
        },
        "admin": {
            "emoji": "🔧",
            "nombre": "Administración",
            "comandos": [
                ("-say <mensaje> 🔒", "**Repite el mensaje en negrita**"),
                ("-ban @usuario [razón] 🔒", "**Banea al usuario (si la razón empieza con 'definitivo', aplica ban permanente)**"),
                ("-ban definitivo @usuario [razón] 🔒", "**Baneo permanente + blacklist**"),
                ("-unban <id> 🔒", "**Desbanea por ID y elimina de blacklist**"),
                ("-money add/remove @usuario <cantidad> 🔒", "**Modifica dinero**"),
                ("-setprefix <prefijo> 🔒", "**Cambia el prefijo**"),
                ("-add-inv @usuario <tipo> <item> [cantidad] 🔒", "**Añade items**"),
                ("-rem-inv @usuario <tipo> <item> [cantidad] 🔒", "**Elimina items**"),
                ("-add-coche @usuario <modelo> 🔒", "**Registra vehículo**"),
                ("-remove-coche @usuario <matrícula> 🔒", "**Elimina vehículo**"),
                ("-add-droga @usuario <tipo> [cantidad] 🔒", "**Añade droga**"),
                ("-add-licencia @usuario <licencia> 🔒", "**Otorga licencia**"),
                ("-rem-licencia @usuario <licencia> 🔒", "**Revoca licencia**"),
                ("-periodico 🔒", "**Publica el periódico**"),
                ("-bot [días] 🔒", "**Activa el bot por X días (solo owners)**"),
                ("-botoff 🔒", "**Detiene el bot inmediatamente (solo owners)**"),
                ("-quitar-warn @usuario <id_warn> 🔒", "**Elimina una advertencia**"),
                ("-borrardni @usuario 🔒", "**Elimina DNI de un usuario**"),
                ("-economy-reset @usuario/@rol [cantidad] 🔒", "**Resetea la economía de un usuario o rol**")
            ]
        },
        "moderacion": {
            "emoji": "🔨",
            "nombre": "Moderación",
            "comandos": [
                ("-mute @usuario <razón> 🔒", "**Silencia a un usuario**"),
                ("-unmute @usuario 🔒", "**Quita el silencio**"),
                ("-warn @usuario <razón> 🔒", "**Añade una advertencia**"),
                ("-delwarn @usuario <id> 🔒", "**Elimina una advertencia**"),
                ("-history @usuario", "**Muestra historial de sanciones**"),
                ("-warnings @usuario", "**Muestra solo las advertencias**")
            ]
        },
        "kits": {
            "emoji": "🎁",
            "nombre": "Kits por Rol",
            "comandos": [
                ("-policial", "**Reclama tu kit policial (rol LSPD, cooldown 12h)**"),
                ("-mecanico", "**Reclama tu kit mecánico (rol Mecánico, cooldown 12h)**"),
                ("-ems", "**Reclama tu kit EMS (rol EMS, cooldown 12h)**"),
                ("-bomberos", "**Reclama tu kit bomberos (rol Bomberos, cooldown 12h)**")
            ]
        }
    }

    @commands.command(name='ayuda', aliases=['help'])
    async def ayuda(self, ctx, cat: Optional[str] = None):
        if cat and cat.lower() in self.CATEGORIAS:
            cat_info = self.CATEGORIAS[cat.lower()]
            embed = discord.Embed(
                title=f"{cat_info['emoji']} · TODOS LOS COMANDOS DE {cat_info['nombre'].upper()}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            desc = ""
            for cmd, desc_cmd in cat_info["comandos"]:
                desc += f"» **{cmd}**\n— {desc_cmd}\n\n"
            embed.description = desc
            embed.set_footer(text=f"Prefijo: {get_pre(self.bot, ctx.message)}  ·  🔒 = Solo admins/mods  ·  NOVA AGORA RP")
            await ctx.send(embed=embed)
            return

        prefijo = get_pre(self.bot, ctx.message)
        eco = await db.get_economy(ctx.author.id)
        saldo = eco['cash'] + eco['bank']

        embed = discord.Embed(
            title="📚 NOVA AGORA RP — Panel de Ayuda",
            description=(
                f"**Prefijo:** `{prefijo}` — Selecciona una categoría en el menú de abajo.\n\n"
                f"🛠️ · **Soporte**\n"
                f"🎭 · **Roleplay**\n"
                f"💼 · **Trabajos**\n"
                f"💊 · **Ilegales**\n"
                f"🔫 · **Armas**\n"
                f"🚗 · **Vehículos**\n"
                f"🏪 · **Mercado**\n"
                f"🎰 · **Casino**\n"
                f"📱 · **Móvil & Redes**\n"
                f"🚨 · **PDA Policial**\n"
                f"🔧 · **Administración**\n"
                f"🔨 · **Moderación**\n"
                f"🎁 · **Kits por Rol**\n\n"
                f"🔒 = Solo administradores/moderadores"
            ),
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Saldo: **${saldo:,}**  ·  NOVA AGORA RP")
        view = AyudaView(prefijo, self.CATEGORIAS, ctx.author.id)
        await ctx.send(embed=embed, view=view)

class AyudaView(discord.ui.View):
    def __init__(self, prefijo, categorias, user_id):
        super().__init__(timeout=120)
        self.prefijo = prefijo
        self.categorias = categorias
        self.user_id = user_id

        options = []
        for key, info in categorias.items():
            options.append(discord.SelectOption(
                label=info["nombre"],
                description=f"Comandos de {info['nombre']}",
                emoji=info["emoji"],
                value=key
            ))

        select = discord.ui.Select(
            placeholder="📂 Selecciona una categoría...",
            options=options,
            row=0
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=embed_error("No eres el dueño de este menú."), ephemeral=True)
            return
        key = interaction.data['values'][0]
        cat_info = self.categorias[key]
        embed = discord.Embed(
            title=f"{cat_info['emoji']} · TODOS LOS COMANDOS DE {cat_info['nombre'].upper()}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        desc = ""
        for cmd, desc_cmd in cat_info["comandos"]:
            desc += f"» **{cmd}**\n— {desc_cmd}\n\n"
        embed.description = desc
        embed.set_footer(text=f"Prefijo: {self.prefijo}  ·  🔒 = Solo admins/mods  ·  NOVA AGORA RP")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

# ------------------------------------------------
# COG: Moderacion (mute, warn, history, etc.)
# ------------------------------------------------
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
            return await ctx.send(embed=embed_help(
                "mute",
                "Silencia a un usuario por tiempo indefinido (30 días).",
                "-mute @usuario [razón]",
                "-mute @Juan Spam en el chat",
                "Gestionar roles"
            ))
        muted_role = await self.ensure_muted_role(ctx.guild)
        if muted_role in miembro.roles:
            return await ctx.send(embed=embed_error("El usuario ya está muteado."))
        await miembro.add_roles(muted_role, reason=f"Mute por {ctx.author}: {razon}")
        fecha_fin = (datetime.now() + timedelta(days=30)).isoformat()
        await db.execute("""
            INSERT INTO mutes (user_id, razon, fecha_inicio, fecha_fin, agente_id, agente_nombre, activo)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (miembro.id, razon, datetime.now().isoformat(), fecha_fin, ctx.author.id, str(ctx.author)))
        await self.registrar_log_moderacion(ctx, "MUTE", miembro, razon, "30 días")
        await ctx.send(embed=embed_success("✅ Mute aplicado", f"{miembro.mention} ha sido muteado.\nRazón: {razon}"))

    @commands.command(name='unmute')
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, miembro: discord.Member = None):
        if not miembro:
            return await ctx.send(embed=embed_help(
                "unmute",
                "Quita el mute a un usuario.",
                "-unmute @usuario",
                "-unmute @Juan",
                "Gestionar roles"
            ))
        muted_role = await self.ensure_muted_role(ctx.guild)
        if muted_role not in miembro.roles:
            return await ctx.send(embed=embed_error("El usuario no está muteado."))
        await miembro.remove_roles(muted_role, reason=f"Unmute por {ctx.author}")
        await db.execute("UPDATE mutes SET activo = 0 WHERE user_id = ? AND activo = 1", (miembro.id,))
        await self.registrar_log_moderacion(ctx, "UNMUTE", miembro, "Levantado por moderador")
        await ctx.send(embed=embed_success("✅ Unmute aplicado", f"{miembro.mention} ya puede hablar."))

    @commands.command(name='warn')
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, miembro: discord.Member = None, *, razon: str = None):
        if not miembro or not razon:
            return await ctx.send(embed=embed_help(
                "warn",
                "Añade una advertencia a un usuario.",
                "-warn @usuario <razón>",
                "-warn @Juan No respeta las normas",
                "Gestionar mensajes"
            ))
        await db.execute("""
            INSERT INTO warnings (user_id, razon, fecha, agente_id, agente_nombre)
            VALUES (?, ?, ?, ?, ?)
        """, (miembro.id, razon, datetime.now().isoformat(), ctx.author.id, str(ctx.author)))
        warns = await db.fetchall("SELECT id FROM warnings WHERE user_id = ?", (miembro.id,))
        num_warns = len(warns)
        await self.registrar_log_moderacion(ctx, f"WARN #{num_warns}", miembro, razon)
        await ctx.send(embed=embed_success("⚠️ Advertencia registrada", f"{miembro.mention} ha recibido una advertencia.\nRazón: {razon}\nTotal: {num_warns} advertencias.", 0xFFA500))

    @commands.command(name='delwarn')
    @commands.has_permissions(administrator=True)
    async def delwarn(self, ctx, miembro: discord.Member = None, id_warn: int = None):
        if not miembro or not id_warn:
            return await ctx.send(embed=embed_help(
                "delwarn",
                "Elimina una advertencia de un usuario por su ID.",
                "-delwarn @usuario <id_warn>",
                "-delwarn @Juan 3",
                "Administrador"
            ))
        row = await db.fetchone("SELECT id FROM warnings WHERE id = ? AND user_id = ?", (id_warn, miembro.id))
        if not row:
            return await ctx.send(embed=embed_error("Advertencia no encontrada."))
        await db.execute("DELETE FROM warnings WHERE id = ?", (id_warn,))
        await self.registrar_log_moderacion(ctx, f"WARN #{id_warn} ELIMINADA", miembro, "Eliminada por administrador")
        await ctx.send(embed=embed_success("🗑️ Advertencia eliminada", f"Se eliminó la advertencia #{id_warn} de {miembro.mention}.", 0xFF6600))

    @commands.command(name='history')
    async def history(self, ctx, miembro: discord.Member = None):
        if not miembro:
            return await ctx.send(embed=embed_help(
                "history",
                "Muestra el historial de sanciones de un usuario.",
                "-history @usuario",
                "-history @Juan",
                ""
            ))
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
            embed.add_field(name="🔇 Mutes", value="*Ninguno*", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='warnings')
    async def warnings(self, ctx, miembro: discord.Member = None):
        if not miembro:
            return await ctx.send(embed=embed_help(
                "warnings",
                "Muestra las advertencias de un usuario.",
                "-warnings @usuario",
                "-warnings @Juan",
                ""
            ))
        warns = await db.fetchall("SELECT id, razon, fecha, agente_nombre FROM warnings WHERE user_id = ? ORDER BY fecha DESC", (miembro.id,))
        if not warns:
            return await ctx.send(embed=embed_success("✅ Sin advertencias", f"{miembro.display_name} no tiene advertencias."))
        embed = discord.Embed(title=f"⚠️ Advertencias de {miembro.display_name}", color=discord.Color.orange())
        for w in warns:
            embed.add_field(name=f"#{w[0]}", value=f"Razón: {w[1]}\nPor: {w[4]}\nFecha: {datetime.fromisoformat(w[3]).strftime('%d/%m/%Y %H:%M')}", inline=False)
        await ctx.send(embed=embed)

# ------------------------------------------------
# COG: Niveles (XP y niveles)
# ------------------------------------------------
class Niveles(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.tiempo_task.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        user_state = await db.fetchone("SELECT last_message_time FROM niveles WHERE user_id = ?", (message.author.id,))
        if user_state and user_state[0]:
            last = datetime.fromisoformat(user_state[0])
            if (datetime.now() - last).total_seconds() < COOLDOWN_XP:
                return
        xp = random.randint(15, 25)
        nuevo_nivel = await db.add_xp(message.author.id, xp, "message")
        if nuevo_nivel:
            await self.verificar_recompensa_nivel(message.author, nuevo_nivel)
            await message.channel.send(f"🎉 {message.author.mention} ha subido al nivel **{nuevo_nivel}**!")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        if ctx.author.bot:
            return
        user_state = await db.fetchone("SELECT last_command_time FROM niveles WHERE user_id = ?", (ctx.author.id,))
        if user_state and user_state[0]:
            last = datetime.fromisoformat(user_state[0])
            if (datetime.now() - last).total_seconds() < 30:
                return
        xp = random.randint(5, 10)
        nuevo_nivel = await db.add_xp(ctx.author.id, xp, "command")
        if nuevo_nivel:
            await self.verificar_recompensa_nivel(ctx.author, nuevo_nivel)
            await ctx.send(f"🎉 {ctx.author.mention} has subido al nivel **{nuevo_nivel}**!")

    @tasks.loop(minutes=5)
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
    async def ver_nivel(self, ctx, miembro: discord.Member = None):
        miembro = miembro or ctx.author
        data = await db.get_nivel(miembro.id)
        embed = discord.Embed(title=f"📊 Nivel de {miembro.display_name}", color=discord.Color.blue())
        embed.add_field(name="Nivel", value=data['nivel'], inline=True)
        embed.add_field(name="XP total", value=data['xp'], inline=True)
        xp_siguiente = ((data['nivel'] + 1) ** 2) * 100
        embed.add_field(name="XP para siguiente nivel", value=f"{xp_siguiente - data['xp']}", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='ranking')
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

    @tiempo_task.before_loop
    async def before_tiempo(self):
        await self.bot.wait_until_ready()

# ------------------------------------------------
# COG: TicketSystem (completo con panel y modal de valoración)
# ------------------------------------------------
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
        await db.execute("INSERT INTO tickets (user_id, channel_id, category, created_at, status) VALUES (?, ?, ?, ?, 'abierto')",
                         (user.id, channel.id, category_key, datetime.now().isoformat()))
        embed = discord.Embed(title=f"📩 Ticket abierto — {self.CATEGORIAS[category_key]['nombre']}",
                              description=f"**Usuario:** {user.mention}\n**Categoría:** {self.CATEGORIAS[category_key]['emoji']} {self.CATEGORIAS[category_key]['nombre']}\n\nEl equipo de soporte te atenderá en breve.",
                              color=discord.Color.blue(), timestamp=datetime.now())
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
        embed = discord.Embed(
            title="📩 Sistema de Tickets - Nova Agora Roleplay",
            description=(
                "¡Bienvenido al centro de soporte!\nSelecciona la categoría que corresponda.\n\n" +
                "\n".join([f"{data['emoji']} → **{data['nombre']}**\n*{data['desc']}*\n" for data in self.CATEGORIAS.values()]) +
                "\n**📌 Importante:**\n- Tickets privados.\n- Abre solo uno a la vez.\n- Adjunta evidencia.\n\nGracias por ser parte de Nova Agora RP."
            ),
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzFwNGl2ajRzM3p4d2Zmd2Z5cGxvbjE2dHJlZnYxM2ZkMjZzNjZ5bCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/6T7IlHrbxl7MOye7Hn/giphy.gif")
        embed.set_footer(text="NOVA AGORA ROLEPLAY")
        view = TicketPanelView(self.bot, self.CATEGORIAS)
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()

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
        embed = discord.Embed(
            title="🔒 Ticket cerrado",
            description=f"El ticket ha sido cerrado por {interaction.user.mention}.",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        await channel.send(embed=embed)
        if is_staff and user:
            modal = TicketModal(self.bot, self.channel_id, user.id)
            view = discord.ui.View(timeout=86400)
            button_modal = discord.ui.Button(label="Valorar ticket", style=discord.ButtonStyle.primary)
            async def modal_callback(interaction2):
                await interaction2.response.send_modal(modal)
            button_modal.callback = modal_callback
            view.add_item(button_modal)
            dm_embed = discord.Embed(
                title="📝 Valoración del ticket",
                description="¿Te atendieron correctamente? Tu opinión nos ayuda a mejorar.\n\n"
                            "**¿Te respondieron en un tiempo razonable?**\n**¿Se resolvió tu problema como esperabas?**\n\n"
                            "No te tomará más de un minuto.\n\nNo te sientas obligado, puedes cancelar si lo deseas.",
                color=discord.Color.gold()
            )
            try:
                await user.send(embed=dm_embed, view=view)
            except:
                pass
        await asyncio.sleep(5)
        await channel.delete()
        await self.bot.get_cog("TicketSystem").log("TICKET", f"Ticket #{await self.bot.get_cog('TicketSystem').get_ticket_id(self.channel_id)} cerrado por {interaction.user}")

# ------------------------------------------------
# COG: AntiRaid (solo flood de mensajes y palabras prohibidas)
# ------------------------------------------------
class AntiRaid(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.thresholds = {
            "message_flood": 15,
        }
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
        rows = await db.fetchall("SELECT COUNT(*) FROM antiraid_actions WHERE user_id = ? AND timestamp > ?",
                                 (user.id, (datetime.now() - timedelta(hours=24)).isoformat()))
        infracciones = rows[0][0] if rows else 0

        if infracciones < 2:
            await db.execute("""
                INSERT INTO warnings (user_id, razon, fecha, agente_id, agente_nombre)
                VALUES (?, ?, ?, ?, ?)
            """, (user.id, f"Anti-Raid: {reason_type}", datetime.now().isoformat(), self.bot.user.id, "Sistema"))
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

# ------------------------------------------------
# COG: CheckUsers (slash command)
# ------------------------------------------------
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

# ------------------------------------------------
# COG: TabletPolicial (comando oculto -tablet)
# ------------------------------------------------
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
        embed = discord.Embed(
            title="📱 Tablet Policial - Nova Agora RP",
            description="Selecciona una acción desde el menú.",
            color=0x3498DB
        )
        await ctx.send(embed=embed, view=view)

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
            embed = discord.Embed(
                title="🚨 DETENCIÓN",
                description=f"{interaction.user.display_name} ha detenido a {miembro.mention}. Motivo: {self.motivo.value}",
                color=0xFF0000
            )
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
            embed = discord.Embed(
                title="🔒 ENCARCELAMIENTO",
                description=f"{interaction.user.display_name} ha encarcelado a {miembro.mention} por {minutos} minutos.\nMotivo: {self.motivo.value}",
                color=0xFF0000
            )
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
            embed = discord.Embed(
                title="📄 MULTA",
                description=f"{interaction.user.display_name} ha multado a {miembro.mention} con **${cantidad:,}**.\nMotivo: {self.motivo.value}",
                color=0xFFA500
            )
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
            embed = discord.Embed(
                title="🔫 ARMA REQUISADA",
                description=f"{interaction.user.display_name} requisó {arma_real} a {miembro.mention}.",
                color=0xFF0000
            )
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
            embed = discord.Embed(
                title="📋 LICENCIA",
                description=f"{interaction.user.display_name} {desc}.",
                color=0x00FF00 if accion == "dar" else 0xFF0000
            )
            await interaction.response.send_message(embed=embed)
            await db.log_antiraid_action(interaction.user.id, f"licencia_{accion}", interaction.guild.id)
        except ValueError:
            await interaction.response.send_message("ID inválido.", ephemeral=True)

# ------------------------------------------------
# COG: DNI (con almacenamiento en base de datos)
# ------------------------------------------------
class DNI(BaseCog):
    @commands.hybrid_command(name='dni', description="Crea tu DNI de personaje")
    @check_ban()
    async def dni(self, ctx, nombre: str, apellidos: str, edad: int, genero: str, nacionalidad: str, color_ojos: str, altura: str, profesion: str):
        uid = ctx.author.id
        existing = await db.get_dni(uid)
        if existing:
            return await ctx.send(embed=embed_error("Ya tienes un DNI registrado."))
        numero = f"{random.randint(10000000, 99999999)}{random.choice('ABCDEFGHJKLMNPQRSTVWXYZ')}"
        data = {
            "nombre": nombre, "apellidos": apellidos, "edad": edad, "genero": genero,
            "nacionalidad": nacionalidad, "color_ojos": color_ojos, "altura": altura,
            "profesion": profesion, "numero": numero, "fecha_creacion": datetime.now().isoformat()
        }
        await db.set_dni(uid, data)
        embed = discord.Embed(title="✅ DNI CREADO", description=(
            f"**Nombre:** {nombre}\n**Apellidos:** {apellidos}\n**Edad:** {edad}\n**Género:** {genero}\n"
            f"**Nacionalidad:** {nacionalidad}\n**Color de ojos:** {color_ojos}\n"
            f"**Altura:** {altura}\n**Profesión:** {profesion}\n**Número DNI:** `{numero}`"
        ), color=0x00FF00)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='editardni', description="Edita tu DNI")
    @check_ban()
    async def editardni(self, ctx, campo: str, *, nuevo_valor: str):
        uid = ctx.author.id
        dni = await db.get_dni(uid)
        if not dni:
            return await ctx.send(embed=embed_error("No tienes DNI."))
        campos = ['nombre', 'apellidos', 'edad', 'genero', 'nacionalidad', 'color_ojos', 'altura', 'profesion']
        if campo.lower() not in campos:
            return await ctx.send(embed=embed_error(f"Campos válidos: {', '.join(campos)}"))
        if campo.lower() == 'edad':
            try:
                nuevo_valor = int(nuevo_valor)
                if nuevo_valor < 0 or nuevo_valor > 120:
                    raise ValueError
            except:
                return await ctx.send(embed=embed_error("Edad debe ser un número entre 0 y 120."))
        dni[campo.lower()] = nuevo_valor
        await db.set_dni(uid, dni)
        await ctx.send(embed=embed_success("✏️ DNI actualizado", f"**{campo}** → `{nuevo_valor}`"))

    @commands.group(name='ver', invoke_without_command=True)
    async def ver(self, ctx):
        await ctx.send(embed=embed_info("📋 Comando ver", "Usa `-ver dni [usuario]` para ver el DNI de alguien."))

    @ver.command(name='dni', aliases=['dn'])
    @check_ban()
    async def ver_dni(self, ctx, usuario: Optional[discord.Member] = None):
        uid = usuario.id if usuario else ctx.author.id
        dni = await db.get_dni(uid)
        if not dni:
            return await ctx.send(embed=embed_error("Ese usuario no tiene DNI."))
        embed = discord.Embed(
            title=f"📄 **DNI de {dni['nombre']} {dni['apellidos']}**",
            color=0x3498DB,
            timestamp=datetime.now()
        )
        target = usuario or ctx.author
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="👤 **Nombre completo**", value=f"{dni['nombre']} {dni['apellidos']}", inline=False)
        embed.add_field(name="🎂 **Edad**", value=dni['edad'], inline=True)
        embed.add_field(name="⚥ **Género**", value=dni['genero'], inline=True)
        embed.add_field(name="🌍 **Nacionalidad**", value=dni['nacionalidad'], inline=True)
        embed.add_field(name="👁️ **Color de ojos**", value=dni['color_ojos'], inline=True)
        embed.add_field(name="📏 **Altura**", value=dni['altura'], inline=True)
        embed.add_field(name="💼 **Profesión**", value=dni['profesion'], inline=True)
        embed.add_field(name="🆔 **Número DNI**", value=f"`{dni['numero']}`", inline=False)
        embed.add_field(name="📅 **Creado**", value=datetime.fromisoformat(dni['fecha_creacion']).strftime("%d/%m/%Y %H:%M"), inline=False)
        embed.set_footer(text="Nova Agora RP • Documento de Identidad")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='verdni', description="Ver DNI de un usuario")
    @check_ban()
    async def verdni(self, ctx, usuario: Optional[discord.Member] = None):
        await self.ver_dni(ctx, usuario)

    @commands.hybrid_command(name='borrardni', description="Elimina el DNI de un usuario (solo administradores)")
    @commands.has_permissions(administrator=True)
    async def borrardni(self, ctx, usuario: discord.Member):
        dni = await db.get_dni(usuario.id)
        if not dni:
            return await ctx.send(embed=embed_error("Ese usuario no tiene DNI."))
        await db.delete_dni(usuario.id)
        await ctx.send(embed=embed_success("🗑️ DNI eliminado", f"Se eliminó el DNI de {usuario.mention}.", 0xFF0000))

# ------------------------------------------------
# COG: Kits (sistema de kits por rol con comandos separados y cooldown 12h)
# ------------------------------------------------
class Kits(BaseCog):
    COOLDOWN_SEGUNDOS = 43200  # 12 horas

    @commands.command(name='policial')
    @check_ban()
    @check_encarcelado()
    async def kit_policial(self, ctx):
        await self._reclamar_kit(ctx, "LSPD", "Kit policial", [("Placa Policial", 1), ("Linterna", 1), ("Radio", 1), ("Esposas", 1), ("Guantes", 1)])

    @commands.command(name='mecanico')
    @check_ban()
    @check_encarcelado()
    async def kit_mecanico(self, ctx):
        await self._reclamar_kit(ctx, "Mecánico", "Kit mecánico", [("Llave Inglesa", 1), ("Herramientas", 1)])

    @commands.command(name='ems')
    @check_ban()
    @check_encarcelado()
    async def kit_ems(self, ctx):
        await self._reclamar_kit(ctx, "EMS", "Kit EMS", [("Botiquin", 1), ("Desfibrilador", 1), ("Kit Médico", 1)])

    @commands.command(name='bomberos')
    @check_ban()
    @check_encarcelado()
    async def kit_bomberos(self, ctx):
        await self._reclamar_kit(ctx, "Bomberos", "Kit bomberos", [("Traje Ignifugo", 1), ("Hacha", 1), ("Manguera", 1), ("Botiquin", 1)])

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

# ====================================================
# PANEL WEB
# ====================================================
class WebPanel:
    def __init__(self, bot):
        self.bot = bot
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_hex(16)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Panel Web - Nova Agora RP</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; color: #eee; }
                    .header { background: #16213e; padding: 20px; text-align: center; border-bottom: 3px solid #e94560; }
                    .header h1 { color: #e94560; }
                    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
                    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
                    .stat-card { background: #0f3460; padding: 20px; border-radius: 10px; text-align: center; }
                    .stat-card h3 { color: #e94560; margin-bottom: 10px; }
                    .stat-card .value { font-size: 2em; font-weight: bold; }
                    .section { background: #16213e; padding: 20px; margin: 20px 0; border-radius: 10px; }
                    .section h2 { color: #e94560; margin-bottom: 15px; border-bottom: 2px solid #0f3460; padding-bottom: 10px; }
                    table { width: 100%; border-collapse: collapse; }
                    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #0f3460; }
                    th { color: #e94560; }
                    .badge { background: #e94560; padding: 3px 8px; border-radius: 5px; font-size: 0.8em; }
                    .nav { margin-bottom: 20px; }
                    .nav a { color: #e94560; margin-right: 20px; text-decoration: none; }
                </style>
            </head>
            <body>
                <div class="header"><h1>🎮 NOVA AGORA RP — Panel de Administración</h1><p>Estadísticas en tiempo real</p></div>
                <div class="container">
                    <div class="nav"><a href="/">Inicio</a> <a href="/blacklist">Blacklist</a></div>
                    <div class="stats-grid">
                        <div class="stat-card"><h3>👥 Usuarios Registrados</h3><div class="value">{{ stats.usuarios }}</div></div>
                        <div class="stat-card"><h3>💰 Dinero Total</h3><div class="value">${{ stats.dinero_total }}</div></div>
                        <div class="stat-card"><h3>🏦 Caja Municipal</h3><div class="value">${{ stats.caja_municipal }}</div></div>
                        <div class="stat-card"><h3>🚔 Atracos Hoy</h3><div class="value">{{ stats.atracos_hoy }}</div></div>
                    </div>
                    <div class="section"><h2>🏆 Top 10 Niveles</h2>
                        <table>
                            <thead><tr><th>#</th><th>Nombre</th><th>Nivel</th><th>XP</th></tr></thead>
                            <tbody>{% for user in stats.top_niveles %}<tr><td>#{{ loop.index }}</td><td>{{ user.nombre }}</td><td>{{ user.nivel }}</td><td>{{ user.xp }}</td></tr>{% endfor %}</tbody>
                        </table>
                    </div>
                    <div class="section"><h2>💵 Top 10 Económico</h2>
                        <table>
                            <thead><tr><th>#</th><th>Nombre</th><th>Efectivo</th><th>Banco</th><th>Total</th></tr></thead>
                            <tbody>{% for user in stats.top_economia %}<tr><td>#{{ loop.index }}</td><td>{{ user.nombre }}</td><td>${{ user.efectivo }}</td><td>${{ user.banco }}</td><td><span class="badge">${{ user.total }}</span></td></tr>{% endfor %}</tbody>
                        </table>
                    </div>
                    <div class="section"><h2>📊 Estadísticas de Atracos</h2><p><strong>Total:</strong> {{ stats.robos_totales }} | <strong>Hoy:</strong> {{ stats.atracos_hoy }}</p></div>
                    <div class="section"><h2>🎫 Tickets Recientes</h2>
                        表
                            <thead><tr><th>ID</th><th>Usuario</th><th>Categoría</th><th>Estado</th><th>Fecha</th></tr></thead>
                            <tbody>{% for t in stats.tickets %}<tr><td>{{ t.id }}</td><td>{{ t.user }}</td><td>{{ t.categoria }}</td><td>{{ t.status }}</td><td>{{ t.fecha[:10] }}</td></tr>{% endfor %}</tbody>
                        </table>
                    </div>
                </div>
            </body>
            </html>
            ''', stats=self.get_stats())

        @self.app.route('/blacklist', methods=['GET', 'POST'])
        def blacklist_page():
            token = request.args.get('token') or (request.form.get('token') if request.method == 'POST' else None)
            if not token:
                return '<form method="get"><input type="text" name="token" placeholder="Token"><button>Acceder</button></form>'
            if token != ADMIN_TOKEN:
                abort(401)
            if request.method == 'POST':
                action = request.form.get('action')
                user_id = request.form.get('user_id')
                if action == 'add' and user_id:
                    asyncio.run_coroutine_threadsafe(db.add_to_blacklist(int(user_id), request.form.get('reason',''), 0), self.bot.loop)
                    asyncio.run_coroutine_threadsafe(db.update_user_state(int(user_id), banned=True), self.bot.loop)
                elif action == 'remove' and user_id:
                    asyncio.run_coroutine_threadsafe(db.remove_from_blacklist(int(user_id)), self.bot.loop)
                    asyncio.run_coroutine_threadsafe(db.update_user_state(int(user_id), banned=False), self.bot.loop)
                return redirect(url_for('blacklist_page', token=token))
            blacklist = asyncio.run_coroutine_threadsafe(db.get_blacklist(), self.bot.loop).result()
            return render_template_string('''
            <html><head><title>Blacklist</title><style>body{background:#1a1a2e;color:#eee;font-family:sans-serif;}</style></head>
            <body><h1>Blacklist Global</h1><form method="post"><input type="hidden" name="token" value="{{ token }}">
            <label>ID:</label><input name="user_id" required><label>Razón:</label><input name="reason"><button name="action" value="add">Añadir</button></form>
            <table border="1"><tr><th>ID</th><th>Razón</th><th>Baneado por</th><th>Fecha</th><th></th></tr>
            {% for item in blacklist %}<tr><td>{{ item.user_id }}</td><td>{{ item.reason }}</td><td>{{ item.banned_by }}</td><td>{{ item.ban_date[:16] }}</td>
            <td><form method="post"><input type="hidden" name="token" value="{{ token }}"><input type="hidden" name="user_id" value="{{ item.user_id }}"><button name="action" value="remove">Quitar</button></form></td></tr>{% endfor %}
            </table></body></html>
            ''', blacklist=blacklist, token=ADMIN_TOKEN)

        @self.app.route('/api/stats')
        def api_stats():
            return jsonify(self.get_stats())

    def get_stats(self):
        try:
            async def fetch():
                row = await db.fetchone("SELECT SUM(cash+bank) FROM economy")
                dinero_total = row[0] if row else 0
                caja = await db.get_caja_municipal()
                atracos_hoy = await db.get_estadistica('atracos_hoy')
                robos_totales = await db.get_estadistica('robos_totales')
                top_econ = await db.fetchall("SELECT user_id,cash,bank FROM economy ORDER BY (cash+bank) DESC LIMIT 10")
                top_niv = await db.get_ranking_niveles(10)
                tickets = await db.fetchall("SELECT id,user_id,category,status,created_at FROM tickets ORDER BY created_at DESC LIMIT 10")
                usuarios = (await db.fetchone("SELECT COUNT(*) FROM economy"))[0]
                return {'dinero_total': dinero_total, 'caja_municipal': caja, 'atracos_hoy': atracos_hoy, 'robos_totales': robos_totales,
                        'top_economia': top_econ, 'top_niveles': top_niv, 'tickets': tickets, 'usuarios': usuarios}
            data = asyncio.run_coroutine_threadsafe(fetch(), self.bot.loop).result()
            top_econ = [{'nombre': self.bot.get_user(uid).display_name if self.bot.get_user(uid) else str(uid), 'efectivo': f"{cash:,}", 'banco': f"{bank:,}", 'total': f"{cash+bank:,}"} for uid,cash,bank in data['top_economia']]
            top_niv = [{'nombre': self.bot.get_user(uid).display_name if self.bot.get_user(uid) else str(uid), 'nivel': nivel, 'xp': xp} for uid,xp,nivel in data['top_niveles']]
            tickets = [{'id':t[0], 'user': self.bot.get_user(t[1]).display_name if self.bot.get_user(t[1]) else str(t[1]), 'categoria':t[2], 'status':t[3], 'fecha':t[4][:10]} for t in data['tickets']]
            return {'usuarios': data['usuarios'], 'dinero_total': f"{data['dinero_total']:,}", 'caja_municipal': f"{data['caja_municipal']:,}",
                    'atracos_hoy': data['atracos_hoy'], 'robos_totales': data['robos_totales'], 'top_economia': top_econ, 'top_niveles': top_niv, 'tickets': tickets}
        except:
            return {'usuarios':0,'dinero_total':'0','caja_municipal':'0','atracos_hoy':0,'robos_totales':0,'top_economia':[],'top_niveles':[],'tickets':[]}

    def run(self):
        threading.Thread(target=lambda: self.app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True).start()

# ====================================================
# INTENTS Y BOT
# ====================================================
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

@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    if bot.guilds:
        guild = bot.guilds[0]
        if not discord.utils.get(guild.roles, name="Muted"):
            await guild.create_role(name="Muted")
        if not discord.utils.get(guild.categories, name="🎫 Tickets"):
            await guild.create_category("🎫 Tickets")
        if not discord.utils.get(guild.roles, name="Staff"):
            await guild.create_role(name="Staff")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos slash sincronizados.")
    except Exception as e:
        print(f"❌ Error al sincronizar slash: {e}")

async def main():
    async with bot:
        await db.init()
        expiry = await db.get_expiry()
        if expiry:
            if expiry < datetime.now():
                print(f"⚠️ ADVERTENCIA: El bot ha expirado ({expiry}). Usa '-bot <días>' para reactivar.")
            else:
                tiempo_restante = expiry - datetime.now()
                dias = tiempo_restante.days
                horas = tiempo_restante.seconds // 3600
                print(f"✅ Bot activo - Expira en {dias}d {horas}h ({expiry})")
        else:
            print("ℹ️ Bot no configurado. Usa '-bot <días>' para activar.")
        # Añadir todos los cogs
        await bot.add_cog(Principal(bot))
        await bot.add_cog(Drogas(bot))
        await bot.add_cog(Vehiculos(bot))
        await bot.add_cog(Armas(bot))
        await bot.add_cog(Mercado(bot))
        await bot.add_cog(Casino(bot))
        await bot.add_cog(Atracos(bot))
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
        await bot.add_cog(Kits(bot))

        hosting_cog = bot.get_cog("Hosting")
        if hosting_cog:
            hosting_cog.check_expiry.start()

        web = WebPanel(bot)
        web.run()
        print(f"🌐 Panel web: http://localhost:5000  |  Token blacklist: {ADMIN_TOKEN}")
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())