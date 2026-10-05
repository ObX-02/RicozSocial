
# =========================================================
# RICOZSOCIAL
# ENTERPRISE SOCIAL MEDIA MANAGEMENT PLATFORM
# =========================================================

import os
import time
import re

from functools import wraps
from datetime import datetime, date, timedelta


# =========================================================
# ENVIRONMENT CONFIGURATION
# =========================================================

from dotenv import load_dotenv

load_dotenv()


# =========================================================
# GOOGLE GEMINI AI
# =========================================================

from google import genai


# =========================================================
# DATABASE
# =========================================================

import psycopg
from psycopg.rows import dict_row


# =========================================================
# FLASK
# =========================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    abort,
    jsonify,
)


# =========================================================
# SECURITY
# =========================================================

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


# =========================================================
# CONFIGURATION
# =========================================================

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)


# =========================================================
# GEMINI AI CONFIGURATION
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    GEMINI_API_KEY = GEMINI_API_KEY.strip()

gemini_client = (
    genai.Client()
    if GEMINI_API_KEY
    else None
)



# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_URL = (
    os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
    or os.getenv("POSTGRES_URL_NON_POOLING")
    or os.getenv("DATABASE_URL")
)


if not DATABASE_URL:

    DATABASE_URL = (
        "postgresql://postgres@localhost:5432/ricoz_social"
    )


def get_db_connection():

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=10
    )


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_URL = (
    os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
    or os.getenv("POSTGRES_URL_NON_POOLING")
    or os.getenv("DATABASE_URL")
)

if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres@localhost:5432/ricoz_social"


def get_db_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=10
    )

# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:
            

            # =================================================
            # USERS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'user',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
                       
            # =================================================
            # BRANDS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS brands (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    description TEXT,
                    logo_url TEXT,
                    website_url TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # BRAND MEMBERS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS brand_members (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL DEFAULT 'member',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(brand_id, user_id)
                )
            """)
            # =========================================================
            # CONTENT CATEGORIES
            # =========================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS content_categories (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    color VARCHAR(20) DEFAULT '#e31e24',
                    created_by INTEGER
                        REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(brand_id, name)
                )
            """)

            # =========================================================
            # CONTENT TAGS
            # =========================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS content_tags (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    name VARCHAR(100) NOT NULL,
                    created_by INTEGER
                        REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(brand_id, name)
                )
            """)

            # =========================================================
            # POST TAGS
            # =========================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS post_tags (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL
                        REFERENCES posts(id) ON DELETE CASCADE,
                    tag_id INTEGER NOT NULL
                        REFERENCES content_tags(id) ON DELETE CASCADE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, tag_id)
                )
            """)

            # =========================================================
            # POST CATEGORY
            # =========================================================

            cur.execute("""
                ALTER TABLE posts
                ADD COLUMN IF NOT EXISTS category_id INTEGER
                REFERENCES content_categories(id) ON DELETE SET NULL
            """)

            # =========================================================
            # INDEXES
            # =========================================================

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_categories_brand
                ON content_categories(brand_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_tags_brand
                ON content_tags(brand_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_post_tags_post
                ON post_tags(post_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_post_tags_tag
                ON post_tags(tag_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_category
                ON posts(category_id)
            """)

            # =================================================
            # SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_accounts (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    platform VARCHAR(50) NOT NULL,
                    account_name VARCHAR(150) NOT NULL,
                    username VARCHAR(150),
                    account_id VARCHAR(255),
                    profile_url TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP,
                    is_connected BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # POSTS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    created_by INTEGER
                        REFERENCES users(id) ON DELETE SET NULL,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    media_url TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'draft',
                    scheduled_at TIMESTAMP,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # POST PLATFORMS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS post_platforms (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL
                        REFERENCES posts(id) ON DELETE CASCADE,
                    social_account_id INTEGER NOT NULL
                        REFERENCES social_accounts(id) ON DELETE CASCADE,
                    platform_status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    external_post_id VARCHAR(255),
                    published_at TIMESTAMP,
                    error_message TEXT,
                    UNIQUE(post_id, social_account_id)
                )
            """)

            # =================================================
            # CONTENT APPROVALS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS content_approvals (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL
                        REFERENCES posts(id) ON DELETE CASCADE,
                    submitted_by INTEGER
                        REFERENCES users(id) ON DELETE SET NULL,
                    reviewer_id INTEGER
                        REFERENCES users(id) ON DELETE SET NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    comments TEXT,
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # COMMUNITY COMMENTS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS community_comments (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    social_account_id INTEGER
                        REFERENCES social_accounts(id) ON DELETE SET NULL,
                    external_comment_id VARCHAR(255),
                    author_name VARCHAR(150),
                    author_username VARCHAR(150),
                    content TEXT NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    reply TEXT,
                    replied_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # LISTENING KEYWORDS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS listening_keywords (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    keyword VARCHAR(150) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # SOCIAL MENTIONS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_mentions (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    keyword_id INTEGER
                        REFERENCES listening_keywords(id)
                        ON DELETE SET NULL,
                    platform VARCHAR(50),
                    author_name VARCHAR(150),
                    author_username VARCHAR(150),
                    content TEXT NOT NULL,
                    mention_url TEXT,
                    sentiment VARCHAR(50) DEFAULT 'neutral',
                    status VARCHAR(50) DEFAULT 'new',
                    mentioned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # ANALYTICS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    social_account_id INTEGER
                        REFERENCES social_accounts(id)
                        ON DELETE SET NULL,
                    post_id INTEGER
                        REFERENCES posts(id)
                        ON DELETE SET NULL,
                    metric_date DATE NOT NULL,
                    impressions INTEGER DEFAULT 0,
                    reach INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    followers INTEGER DEFAULT 0
                )
            """)

            # =================================================
            # REPORTS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id) ON DELETE CASCADE,
                    created_by INTEGER
                        REFERENCES users(id) ON DELETE SET NULL,
                    name VARCHAR(255) NOT NULL,
                    period_start DATE NOT NULL,
                    period_end DATE NOT NULL,
                    report_type VARCHAR(100) NOT NULL DEFAULT 'performance',
                    file_url TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # NOTIFICATIONS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    notification_type VARCHAR(50) NOT NULL DEFAULT 'general',
                    is_read BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # ACTIVITY LOGS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER
                        REFERENCES users(id) ON DELETE SET NULL,
                    brand_id INTEGER
                        REFERENCES brands(id) ON DELETE SET NULL,
                    action VARCHAR(100) NOT NULL,
                    entity_type VARCHAR(100),
                    entity_id INTEGER,
                    description TEXT,
                    ip_address VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # SAFE MIGRATIONS
            # =================================================

            cur.execute("""
                ALTER TABLE content_approvals
                ADD COLUMN IF NOT EXISTS created_at
                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_brand_status
                ON posts(brand_id, status)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_posts_scheduled
                ON posts(scheduled_at)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_social_accounts_brand
                ON social_accounts(brand_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_social_accounts_platform
                ON social_accounts(platform)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_social_accounts_connected
                ON social_accounts(is_connected)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user
                ON notifications(user_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_activity_logs_user
                ON activity_logs(user_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_approvals_status
                ON content_approvals(status)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_approvals_post
                ON content_approvals(post_id)
            """)
                       # =========================================================
            # CAMPAIGNS
            # =========================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id SERIAL PRIMARY KEY,

                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id)
                        ON DELETE CASCADE,

                    created_by INTEGER
                        REFERENCES users(id)
                        ON DELETE SET NULL,

                    name VARCHAR(200) NOT NULL,

                    description TEXT,

                    goal_type VARCHAR(50),

                    target_value NUMERIC(14, 2),

                    start_date DATE,

                    end_date DATE,

                    status VARCHAR(30) DEFAULT 'Draft',

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)


            # =========================================================
            # CAMPAIGN POSTS
            # =========================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS campaign_posts (
                    id SERIAL PRIMARY KEY,

                    campaign_id INTEGER NOT NULL
                        REFERENCES campaigns(id)
                        ON DELETE CASCADE,

                    post_id INTEGER NOT NULL
                        REFERENCES posts(id)
                        ON DELETE CASCADE,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(campaign_id, post_id)
                )
            """)


            # =========================================================
            # CAMPAIGN INDEXES
            # =========================================================

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaigns_brand_id
                ON campaigns(brand_id)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaigns_status
                ON campaigns(status)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaigns_dates
                ON campaigns(start_date, end_date)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaign_posts_campaign_id
                ON campaign_posts(campaign_id)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaign_posts_post_id
                ON campaign_posts(post_id)
            """)


        conn.commit()

    finally:
        conn.close()

# =========================================================
# CONSTANTS
# =========================================================

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)

SOCIAL_PLATFORMS = [
    "Facebook",
    "Instagram",
    "LinkedIn",
    "X",
    "YouTube",
    "TikTok",
    "Pinterest",
]

POST_STATUSES = [
    "draft",
    "pending_approval",
    "approved",
    "scheduled",
    "published",
    "rejected",
    "failed",
]

# =========================================================
# TEAM & ROLE-BASED ACCESS CONTROL
# =========================================================

SYSTEM_ROLES = {
    "admin": "Administrator",
    "manager": "Manager",
    "publisher": "Publisher",
    "analyst": "Analyst",
    "member": "Member",
}

BRAND_ROLES = {
    "owner": "Brand Owner",
    "manager": "Brand Manager",
    "publisher": "Publisher",
    "analyst": "Analyst",
    "member": "Member",
}

ROLE_PERMISSIONS = {
    "admin": {
        "*"
    },

    "manager": {
        "dashboard.view",
        "brands.view",
        "brands.create",
        "brands.edit",
        "brands.manage",
        "team.view",
        "team.create",
        "team.edit",
        "team.manage",
        "content.view",
        "content.create",
        "content.edit",
        "content.delete",
        "content.publish",
        "content.schedule",
        "content.approve",
        "calendar.view",
        "community.view",
        "community.reply",
        "listening.view",
        "listening.manage",
        "analytics.view",
        "reports.view",
        "reports.create",
        "notifications.view",
    },

    "publisher": {
        "dashboard.view",
        "brands.view",
        "content.view",
        "content.create",
        "content.edit",
        "content.schedule",
        "content.publish",
        "calendar.view",
        "community.view",
        "community.reply",
        "listening.view",
        "analytics.view",
        "notifications.view",
    },

    "analyst": {
        "dashboard.view",
        "brands.view",
        "content.view",
        "calendar.view",
        "analytics.view",
        "reports.view",
        "reports.create",
        "listening.view",
        "notifications.view",
    },

    "member": {
        "dashboard.view",
        "brands.view",
        "content.view",
        "content.create",
        "content.edit",
        "calendar.view",
        "community.view",
        "notifications.view",
    },
}


BRAND_ROLE_PERMISSIONS = {
    "owner": {
        "brand.view",
        "brand.manage",
        "brand.members",
        "content.view",
        "content.create",
        "content.edit",
        "content.delete",
        "content.publish",
        "content.schedule",
        "content.approve",
        "calendar.view",
        "community.view",
        "community.reply",
        "listening.view",
        "listening.manage",
        "analytics.view",
        "reports.view",
        "reports.create",
    },

    "manager": {
        "brand.view",
        "brand.manage",
        "brand.members",
        "content.view",
        "content.create",
        "content.edit",
        "content.delete",
        "content.publish",
        "content.schedule",
        "content.approve",
        "calendar.view",
        "community.view",
        "community.reply",
        "listening.view",
        "listening.manage",
        "analytics.view",
        "reports.view",
        "reports.create",
    },

    "publisher": {
        "brand.view",
        "content.view",
        "content.create",
        "content.edit",
        "content.schedule",
        "content.publish",
        "calendar.view",
        "community.view",
        "community.reply",
        "analytics.view",
    },

    "analyst": {
        "brand.view",
        "content.view",
        "calendar.view",
        "analytics.view",
        "reports.view",
        "reports.create",
        "listening.view",
    },

    "member": {
        "brand.view",
        "content.view",
        "content.create",
        "content.edit",
        "calendar.view",
        "community.view",
    },
}

# =========================================================
# AUTH HELPERS
# =========================================================

def get_current_user():

    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active,
                    created_at
                FROM users
                WHERE id = %s
            """, (user_id,))

            user = cur.fetchone()

            if not user or not user["is_active"]:
                session.clear()
                return None

            return user

    finally:
        conn.close()


def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if not get_current_user():

            flash(
                "Please login to continue.",
                "warning"
            )

            return redirect(
                url_for(
                    "login",
                    next=request.path
                )
            )

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        user = get_current_user()

        if not user:

            flash(
                "Please login to continue.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        if user["role"] != "admin":

            flash(
                "Administrator access is required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return view(*args, **kwargs)

    return wrapped_view


# =========================================================
# ACTIVITY LOGGING
# =========================================================

def log_activity(
    action,
    entity_type=None,
    entity_id=None,
    description=None,
    brand_id=None
):

    user = get_current_user()

    if not user:
        return

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO activity_logs (
                    user_id,
                    brand_id,
                    action,
                    entity_type,
                    entity_id,
                    description,
                    ip_address
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user["id"],
                brand_id,
                action,
                entity_type,
                entity_id,
                description,
                request.remote_addr
            ))

        conn.commit()

    finally:
        conn.close()


# =========================================================
# GET HELPERS
# =========================================================

def get_brand_or_404(brand_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE id = %s
            """, (brand_id,))

            brand = cur.fetchone()
            # =========================================================
            # CAMPAIGNS
            # =========================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    id SERIAL PRIMARY KEY,

                    brand_id INTEGER NOT NULL
                        REFERENCES brands(id)
                        ON DELETE CASCADE,

                    created_by INTEGER
                        REFERENCES users(id)
                        ON DELETE SET NULL,

                    name VARCHAR(200) NOT NULL,

                    description TEXT,

                    goal_type VARCHAR(50),

                    target_value NUMERIC(14, 2),

                    start_date DATE,

                    end_date DATE,

                    status VARCHAR(30) DEFAULT 'Draft',

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)


            # =========================================================
            # CAMPAIGN POSTS
            # =========================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS campaign_posts (
                    id SERIAL PRIMARY KEY,

                    campaign_id INTEGER NOT NULL
                        REFERENCES campaigns(id)
                        ON DELETE CASCADE,

                    post_id INTEGER NOT NULL
                        REFERENCES posts(id)
                        ON DELETE CASCADE,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    UNIQUE(campaign_id, post_id)
                )
            """)


            # =========================================================
            # CAMPAIGN INDEXES
            # =========================================================

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaigns_brand_id
                ON campaigns(brand_id)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaigns_status
                ON campaigns(status)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaigns_dates
                ON campaigns(start_date, end_date)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaign_posts_campaign_id
                ON campaign_posts(campaign_id)
            """)


            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_campaign_posts_post_id
                ON campaign_posts(post_id)
            """)

            if not brand:
                abort(404)

            return brand

    finally:
        conn.close()


def get_social_account_or_404(account_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM social_accounts
                WHERE id = %s
            """, (account_id,))

            account = cur.fetchone()

            if not account:
                abort(404)

            return account

    finally:
        conn.close()


def get_post_or_404(post_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM posts
                WHERE id = %s
            """, (post_id,))

            post = cur.fetchone()

            if not post:
                abort(404)

            return post

    finally:
        conn.close()


# =========================================================
# GLOBAL TEMPLATE CONTEXT
# =========================================================

@app.context_processor
def inject_global_context():

    user = get_current_user()

    pending_approvals = 0
    unread_notifications = 0

    if user:

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT COUNT(*) AS count
                    FROM content_approvals
                    WHERE status = 'pending'
                """)

                row = cur.fetchone()

                pending_approvals = (
                    row["count"] if row else 0
                )

                cur.execute("""
                    SELECT COUNT(*) AS count
                    FROM notifications
                    WHERE user_id = %s
                    AND is_read = FALSE
                """, (user["id"],))

                row = cur.fetchone()

                unread_notifications = (
                    row["count"] if row else 0
                )

        finally:
            conn.close()

    return {
        "current_user": user,
        "pending_approvals": pending_approvals,
        "unread_notifications": unread_notifications,
        "current_year": datetime.now().year,
    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    user = get_current_user()

    if user:
        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if get_current_user():

        current_user = get_current_user()

        if current_user.get("role") == "admin":
            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name:

            flash(
                "Name is required.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if not EMAIL_PATTERN.match(email):

            flash(
                "Please enter a valid email address.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                """, (email,))

                if cur.fetchone():

                    flash(
                        "An account with this email already exists.",
                        "danger"
                    )

                    return render_template(
                        "register.html"
                    )

                # -------------------------------------------------
                # IMPORTANT:
                # New registrations are normal client accounts.
                # Nobody can create an admin account through
                # the public registration page.
                # -------------------------------------------------

                cur.execute("""
                    INSERT INTO users (
                        name,
                        email,
                        password_hash,
                        role,
                        is_active
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    name,
                    email,
                    generate_password_hash(password),
                    "member",
                    True
                ))

                user = cur.fetchone()

                conn.commit()

                session.clear()
                session["user_id"] = user["id"]

                flash(
                    "Account created successfully.",
                    "success"
                )

                return redirect(
                    url_for("dashboard")
                )

        except Exception:

            conn.rollback()

            app.logger.exception(
                "Registration failed."
            )

            flash(
                "Unable to create your account right now.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        finally:

            conn.close()

    return render_template(
        "register.html"
    )


# =========================================================
# CLIENT LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if get_current_user():

        current_user = get_current_user()

        if current_user.get("role") == "admin":
            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Email and password are required.",
                "danger"
            )

            return render_template(
                "login.html",
                login_type="client"
            )

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT *
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                """, (email,))

                user = cur.fetchone()

                # -------------------------------------------------
                # CREDENTIAL CHECK
                # -------------------------------------------------

                if not user or not user.get("password_hash"):

                    flash(
                        "Invalid email or password.",
                        "danger"
                    )

                    return render_template(
                        "login.html",
                        login_type="client"
                    )

                if not check_password_hash(
                    user["password_hash"],
                    password
                ):

                    flash(
                        "Invalid email or password.",
                        "danger"
                    )

                    return render_template(
                        "login.html",
                        login_type="client"
                    )

                # -------------------------------------------------
                # ACCOUNT STATUS
                # -------------------------------------------------

                if not user["is_active"]:

                    flash(
                        "Your account is inactive.",
                        "danger"
                    )

                    return render_template(
                        "login.html",
                        login_type="client"
                    )

                # -------------------------------------------------
                # ADMIN ACCOUNT CANNOT USE CLIENT LOGIN
                # -------------------------------------------------

                if user.get("role") == "admin":

                    flash(
                        "Please use the Admin Login page for this account.",
                        "warning"
                    )

                    return render_template(
                        "login.html",
                        login_type="client"
                    )

                # -------------------------------------------------
                # CLIENT LOGIN
                # -------------------------------------------------

                session.clear()

                session["user_id"] = user["id"]
                session["login_type"] = "client"

                log_activity(
                    "login",
                    "user",
                    user["id"],
                    "User logged into the client panel."
                )

                flash(
                    "Welcome back.",
                    "success"
                )

                next_url = request.args.get("next")

                if (
                    next_url
                    and next_url.startswith("/")
                    and not next_url.startswith("//")
                ):

                    return redirect(next_url)

                return redirect(
                    url_for("dashboard")
                )

        except Exception:

            app.logger.exception(
                "Client login failed."
            )

            flash(
                "Unable to complete login right now.",
                "danger"
            )

            return render_template(
                "login.html",
                login_type="client"
            )

        finally:

            conn.close()

    return render_template(
        "login.html",
        login_type="client"
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if get_current_user():

        current_user = get_current_user()

        if current_user.get("role") == "admin":

            return redirect(
                url_for("admin_dashboard")
            )

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Email and password are required.",
                "danger"
            )

            return render_template(
                "login.html",
                login_type="admin"
            )

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT *
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                """, (email,))

                user = cur.fetchone()

                # -------------------------------------------------
                # CREDENTIAL CHECK
                # -------------------------------------------------

                if not user or not user.get("password_hash"):

                    flash(
                        "Invalid administrator credentials.",
                        "danger"
                    )

                    return render_template(
                        "login.html",
                        login_type="admin"
                    )

                if not check_password_hash(
                    user["password_hash"],
                    password
                ):

                    flash(
                        "Invalid administrator credentials.",
                        "danger"
                    )

                    return render_template(
                        "login.html",
                        login_type="admin"
                    )

                # -------------------------------------------------
                # ACCOUNT STATUS
                # -------------------------------------------------

                if not user["is_active"]:

                    flash(
                        "This administrator account is inactive.",
                        "danger"
                    )

                    return render_template(
                        "login.html",
                        login_type="admin"
                    )

                # -------------------------------------------------
                # ADMIN ROLE CHECK
                # -------------------------------------------------

                if user.get("role") != "admin":

                    flash(
                        "This account does not have administrator access.",
                        "danger"
                    )

                    return render_template(
                        "login.html",
                        login_type="admin"
                    )

                # -------------------------------------------------
                # ADMIN LOGIN
                # -------------------------------------------------

                session.clear()

                session["user_id"] = user["id"]
                session["login_type"] = "admin"

                log_activity(
                    "admin_login",
                    "user",
                    user["id"],
                    "Administrator logged into the admin panel."
                )

                flash(
                    "Welcome to the Admin Panel.",
                    "success"
                )

                next_url = request.args.get("next")

                if (
                    next_url
                    and next_url.startswith("/")
                    and not next_url.startswith("//")
                ):

                    return redirect(next_url)

                return redirect(
                    url_for("admin_dashboard")
                )

        except Exception:

            app.logger.exception(
                "Admin login failed."
            )

            flash(
                "Unable to complete administrator login right now.",
                "danger"
            )

            return render_template(
                "login.html",
                login_type="admin"
            )

        finally:

            conn.close()

    return render_template(
        "login.html",
        login_type="admin"
    )
# =========================================================
# ONE-TIME ADMIN SETUP
# =========================================================

@app.route("/setup-admin", methods=["GET", "POST"])
def setup_admin():

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:

            # Check whether an admin already exists
            cur.execute("""
                SELECT id
                FROM users
                WHERE role = 'admin'
                LIMIT 1
            """)

            existing_admin = cur.fetchone()

            if existing_admin:
                return """
                    <h2>Admin account already exists.</h2>
                    <p>Please use the Admin Login page.</p>
                """

            if request.method == "POST":

                name = request.form.get("name", "").strip()
                email = request.form.get("email", "").strip().lower()
                password = request.form.get("password", "")

                if not name or not email or not password:
                    return """
                        <h2>All fields are required.</h2>
                        <a href="/setup-admin">Go Back</a>
                    """

                if len(password) < 8:
                    return """
                        <h2>Password must be at least 8 characters.</h2>
                        <a href="/setup-admin">Go Back</a>
                    """

                password_hash = generate_password_hash(password)

                cur.execute("""
                    INSERT INTO users (
                        name,
                        email,
                        password_hash,
                        role,
                        is_active
                    )
                    VALUES (%s, %s, %s, 'admin', TRUE)
                    RETURNING id
                """, (
                    name,
                    email,
                    password_hash
                ))

                admin_user = cur.fetchone()

                conn.commit()

                log_activity(
                    user_id=admin_user["id"],
                    action="admin_account_created",
                    entity_type="user",
                    entity_id=admin_user["id"],
                    description="Initial administrator account created."
                )

                return """
                    <h2>Admin account created successfully.</h2>
                    <p>You can now login as administrator.</p>
                    <a href="/login?login_type=admin">
                        Go to Admin Login
                    </a>
                """

        return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Admin Setup — RicozSocial</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background: #f5f5f5;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                    }

                    .setup-box {
                        width: 400px;
                        background: white;
                        padding: 30px;
                        border-radius: 14px;
                        box-shadow: 0 10px 30px rgba(0,0,0,.12);
                    }

                    h2 {
                        margin-top: 0;
                    }

                    input {
                        width: 100%;
                        box-sizing: border-box;
                        padding: 12px;
                        margin: 8px 0 14px;
                        border: 1px solid #ddd;
                        border-radius: 8px;
                    }

                    button {
                        width: 100%;
                        padding: 12px;
                        border: 0;
                        border-radius: 8px;
                        background: #d71920;
                        color: white;
                        font-weight: 600;
                        cursor: pointer;
                    }

                    small {
                        color: #666;
                    }
                </style>
            </head>

            <body>

                <div class="setup-box">

                    <h2>RicozSocial Admin Setup</h2>

                    <p>
                        Create the first administrator account.
                    </p>

                    <form method="POST">

                        <label>Admin Name</label>
                        <input
                            type="text"
                            name="name"
                            placeholder="Administrator"
                            required
                        >

                        <label>Admin Email</label>
                        <input
                            type="email"
                            name="email"
                            placeholder="admin@example.com"
                            required
                        >

                        <label>Admin Password</label>
                        <input
                            type="password"
                            name="password"
                            minlength="8"
                            placeholder="Minimum 8 characters"
                            required
                        >

                        <button type="submit">
                            Create Admin Account
                        </button>

                    </form>

                    <br>

                    <small>
                        This page works only while no admin account exists.
                    </small>

                </div>

            </body>
            </html>
        """

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():

    current_user = get_current_user()

    if current_user:

        try:

            if current_user.get("role") == "admin":

                log_activity(
                    "admin_logout",
                    "user",
                    current_user["id"],
                    "Administrator logged out of the admin panel."
                )

            else:

                log_activity(
                    "logout",
                    "user",
                    current_user["id"],
                    "User logged out of the client panel."
                )

        except Exception:

            app.logger.exception(
                "Failed to log logout activity."
            )

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )
# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # =================================================
            # BASIC COUNTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = TRUE
            """)

            total_brands = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE is_connected = TRUE
            """)

            connected_accounts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
            """)

            total_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE status = 'scheduled'
            """)

            scheduled_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE status = 'published'
            """)

            published_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM content_approvals
                WHERE status = 'pending'
            """)

            pending_approval_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE status IN ('pending', 'unread')
            """)

            community_items = cur.fetchone()["count"]

            # =================================================
            # ANALYTICS SUMMARY
            # =================================================

            cur.execute("""
                SELECT
                    COALESCE(SUM(impressions), 0) AS total_impressions,
                    COALESCE(SUM(reach), 0) AS total_reach,
                    COALESCE(
                        SUM(likes)
                        + SUM(comments)
                        + SUM(shares)
                        + SUM(clicks),
                        0
                    ) AS total_engagement
                FROM analytics
            """)

            analytics_row = cur.fetchone()

            analytics = {
                "total_impressions": analytics_row["total_impressions"] or 0,
                "total_reach": analytics_row["total_reach"] or 0,
                "total_engagement": analytics_row["total_engagement"] or 0,
            }

            # =================================================
            # ANALYTICS CHART DATA
            # =================================================

            cur.execute("""
                SELECT
                    metric_date,
                    COALESCE(SUM(impressions), 0) AS impressions,
                    COALESCE(SUM(reach), 0) AS reach,
                    COALESCE(
                        SUM(likes)
                        + SUM(comments)
                        + SUM(shares)
                        + SUM(clicks),
                        0
                    ) AS engagement
                FROM analytics
                GROUP BY metric_date
                ORDER BY metric_date ASC
                LIMIT 30
            """)

            analytics_rows = cur.fetchall()

            analytics_chart_data = []

            for row in analytics_rows:

                metric_date = row["metric_date"]

                if hasattr(metric_date, "strftime"):
                    label = metric_date.strftime("%b %d")
                else:
                    label = str(metric_date)

                analytics_chart_data.append({
                    "label": label,
                    "impressions": row["impressions"] or 0,
                    "reach": row["reach"] or 0,
                    "engagement": row["engagement"] or 0,
                })

            # =================================================
            # SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                SELECT
                    id,
                    brand_id,
                    platform,
                    account_name,
                    username,
                    profile_url,
                    is_connected
                FROM social_accounts
                WHERE is_connected = TRUE
                ORDER BY created_at DESC
                LIMIT 10
            """)

            social_accounts = cur.fetchall()

            # =================================================
            # RECENT POSTS
            # =================================================

            cur.execute("""
                SELECT
                    p.*,
                    b.name AS brand_name
                FROM posts p
                LEFT JOIN brands b
                    ON b.id = p.brand_id
                ORDER BY p.created_at DESC
                LIMIT 8
            """)

            recent_posts = cur.fetchall()

            # =================================================
            # UPCOMING POSTS
            # =================================================

            cur.execute("""
                SELECT
                    p.*,
                    b.name AS brand_name
                FROM posts p
                LEFT JOIN brands b
                    ON b.id = p.brand_id
                WHERE p.status = 'scheduled'
                  AND p.scheduled_at IS NOT NULL
                ORDER BY p.scheduled_at ASC
                LIMIT 8
            """)

            upcoming_posts = cur.fetchall()

            # =================================================
            # PENDING APPROVALS
            # =================================================

            cur.execute("""
                SELECT
                    ca.id,
                    ca.status,
                    ca.created_at,
                    p.title AS post_title,
                    b.name AS brand_name,
                    u.name AS creator_name
                FROM content_approvals ca
                LEFT JOIN posts p
                    ON p.id = ca.post_id
                LEFT JOIN brands b
                    ON b.id = p.brand_id
                LEFT JOIN users u
                    ON u.id = p.created_by
                WHERE ca.status = 'pending'
                ORDER BY ca.created_at DESC
                LIMIT 8
            """)

            pending_approvals = cur.fetchall()

            # =================================================
            # BRANDS
            # =================================================

            cur.execute("""
                SELECT
                    id,
                    name,
                    logo_url,
                    website_url,
                    is_active
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
                LIMIT 8
            """)

            brands = cur.fetchall()

            # =================================================
            # NOTIFICATIONS
            # =================================================

            cur.execute("""
                SELECT *
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 5
            """, (
                current_user["id"],
            ))

            notifications = cur.fetchall()

        # =====================================================
        # DASHBOARD STATS OBJECT
        # =====================================================

        stats = {
            "total_brands": total_brands,
            "connected_accounts": connected_accounts,
            "total_posts": total_posts,
            "scheduled_posts": scheduled_posts,
            "published_posts": published_posts,
            "pending_approvals": pending_approval_count,
            "community_items": community_items,
        }

        # =====================================================
        # RENDER DASHBOARD
        # =====================================================

        return render_template(
            "dashboard.html",

            # Current user
            current_user=current_user,

            # Main statistics
            stats=stats,

            # Analytics
            analytics=analytics,
            analytics_chart_data=analytics_chart_data,

            # Social accounts
            social_accounts=social_accounts,

            # Content
            recent_posts=recent_posts,
            upcoming_posts=upcoming_posts,

            # Approvals
            pending_approvals=pending_approvals,

            # Brands
            brands=brands,

            # Notifications
            notifications=notifications,

            # Compatibility variables
            total_brands=total_brands,
            connected_accounts=connected_accounts,
            total_posts=total_posts,
            scheduled_posts=scheduled_posts,
            published_posts=published_posts,
            scheduled_posts_count=scheduled_posts,
            pending_approval_count=pending_approval_count,
            community_items=community_items,
        )

    except Exception as exc:

        app.logger.exception(
            "Failed to load dashboard."
        )

        return (
            f"""
            <div style="
                font-family: Arial, sans-serif;
                padding: 40px;
                max-width: 900px;
                margin: auto;
            ">
                <h2>Dashboard Error</h2>

                <p>
                    The dashboard could not be loaded.
                </p>

                <pre style="
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 8px;
                    overflow-x: auto;
                    white-space: pre-wrap;
                ">{str(exc)}</pre>

                <p>
                    Please check the Flask terminal/log for the
                    complete traceback.
                </p>
            </div>
            """,
            500
        )

    finally:

        conn.close()
# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@login_required
def admin_dashboard():

    current_user = get_current_user()

    # ---------------------------------------------------------
    # ADMIN ACCESS CHECK
    # ---------------------------------------------------------

    if not current_user:
        return redirect(
            url_for("login")
        )

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # =================================================
            # TOTAL CLIENTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM users
                WHERE role <> 'admin'
            """)

            total_clients = cur.fetchone()["count"]

            # =================================================
            # ACTIVE CLIENTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM users
                WHERE role <> 'admin'
                AND is_active = TRUE
            """)

            active_clients = cur.fetchone()["count"]

            # =================================================
            # INACTIVE CLIENTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM users
                WHERE role <> 'admin'
                AND is_active = FALSE
            """)

            inactive_clients = cur.fetchone()["count"]

            # =================================================
            # TOTAL BRANDS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = TRUE
            """)

            total_brands = cur.fetchone()["count"]

            # =================================================
            # TOTAL SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
            """)

            total_social_accounts = cur.fetchone()["count"]

            # =================================================
            # CONNECTED SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE is_connected = TRUE
            """)

            connected_accounts = cur.fetchone()["count"]

            # =================================================
            # TOTAL POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
            """)

            total_posts = cur.fetchone()["count"]

            # =================================================
            # PUBLISHED POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE status = 'published'
            """)

            published_posts = cur.fetchone()["count"]

            # =================================================
            # SCHEDULED POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE status = 'scheduled'
            """)

            scheduled_posts = cur.fetchone()["count"]

            # =================================================
            # DRAFT POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE status = 'draft'
            """)

            draft_posts = cur.fetchone()["count"]

            # =================================================
            # PENDING APPROVALS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM content_approvals
                WHERE status = 'pending'
            """)

            pending_approvals = cur.fetchone()["count"]

            # =================================================
            # COMMUNITY ITEMS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE status IN ('pending', 'unread')
            """)

            community_items = cur.fetchone()["count"]

            # =================================================
            # TOTAL USERS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM users
            """)

            total_users = cur.fetchone()["count"]

            # =================================================
            # RECENT CLIENTS
            # =================================================

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active,
                    created_at
                FROM users
                WHERE role <> 'admin'
                ORDER BY created_at DESC
                LIMIT 8
            """)

            recent_clients = cur.fetchall()

            # =================================================
            # RECENT POSTS
            # =================================================

            cur.execute("""
                SELECT
                    p.id,
                    p.title,
                    p.status,
                    p.created_at,
                    p.scheduled_at,
                    p.published_at,
                    p.brand_id,
                    b.name AS brand_name,
                    u.name AS creator_name
                FROM posts p
                LEFT JOIN brands b
                    ON b.id = p.brand_id
                LEFT JOIN users u
                    ON u.id = p.created_by
                ORDER BY p.created_at DESC
                LIMIT 8
            """)

            recent_posts = cur.fetchall()

            # =================================================
            # RECENT CLIENT ACTIVITY
            # =================================================

            cur.execute("""
                SELECT
                    al.id,
                    al.user_id,
                    al.brand_id,
                    al.action,
                    al.entity_type,
                    al.entity_id,
                    al.description,
                    al.ip_address,
                    al.created_at,
                    u.name AS user_name,
                    u.email AS user_email,
                    b.name AS brand_name
                FROM activity_logs al
                LEFT JOIN users u
                    ON u.id = al.user_id
                LEFT JOIN brands b
                    ON b.id = al.brand_id
                WHERE al.user_id IS NOT NULL
                AND (
                    u.role IS NULL
                    OR u.role <> 'admin'
                )
                ORDER BY al.created_at DESC
                LIMIT 15
            """)

            recent_activity = cur.fetchall()

            # =================================================
            # RECENT APPROVALS
            # =================================================

            cur.execute("""
                SELECT
                    ca.id,
                    ca.post_id,
                    ca.status,
                    ca.created_at,
                    ca.reviewed_at,
                    p.title AS post_title,
                    u.name AS submitted_by_name
                FROM content_approvals ca
                LEFT JOIN posts p
                    ON p.id = ca.post_id
                LEFT JOIN users u
                    ON u.id = ca.submitted_by
                ORDER BY ca.created_at DESC
                LIMIT 8
            """)

            recent_approvals = cur.fetchall()

            # =================================================
            # SYSTEM NOTIFICATIONS
            # =================================================

            cur.execute("""
                SELECT
                    id,
                    title,
                    message,
                    notification_type,
                    is_read,
                    created_at
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 8
            """, (
                current_user["id"],
            ))

            admin_notifications = cur.fetchall()

        return render_template(
            "admin_dashboard.html",

            # Current admin
            current_user=current_user,

            # Main statistics
            total_users=total_users,
            total_clients=total_clients,
            active_clients=active_clients,
            inactive_clients=inactive_clients,

            # Brands / accounts
            total_brands=total_brands,
            total_social_accounts=total_social_accounts,
            connected_accounts=connected_accounts,

            # Content
            total_posts=total_posts,
            published_posts=published_posts,
            scheduled_posts=scheduled_posts,
            draft_posts=draft_posts,

            # Workflow
            pending_approvals=pending_approvals,
            community_items=community_items,

            # Recent data
            recent_clients=recent_clients,
            recent_posts=recent_posts,
            recent_activity=recent_activity,
            recent_approvals=recent_approvals,
            admin_notifications=admin_notifications,
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin dashboard."
        )

        flash(
            "Unable to load the admin dashboard right now.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        conn.close()
# =========================================================
# ADMIN — CLIENT REPORTS
# =========================================================

@app.route("/admin/client-reports")
@login_required
def admin_client_reports():

    current_user = get_current_user()

    # ---------------------------------------------------------
    # ADMIN ACCESS CHECK
    # ---------------------------------------------------------

    if not current_user:
        return redirect(
            url_for("login")
        )

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # =================================================
            # TOTAL REPORTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM reports
            """)

            total_reports = cur.fetchone()["count"]

            # =================================================
            # TOTAL CLIENTS WITH REPORTS
            # =================================================

            cur.execute("""
                SELECT COUNT(DISTINCT b.id) AS count
                FROM reports r
                INNER JOIN brands b
                    ON b.id = r.brand_id
            """)

            clients_with_reports = cur.fetchone()["count"]

            # =================================================
            # REPORTS THIS MONTH
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM reports
                WHERE created_at >= DATE_TRUNC(
                    'month',
                    CURRENT_DATE
                )
            """)

            reports_this_month = cur.fetchone()["count"]

            # =================================================
            # REPORT LIST
            # =================================================

            cur.execute("""
                SELECT
                    r.id,
                    r.brand_id,
                    r.created_by,
                    r.name,
                    r.period_start,
                    r.period_end,
                    r.report_type,
                    r.file_url,
                    r.created_at,

                    b.name AS brand_name,

                    u.name AS created_by_name,
                    u.email AS created_by_email

                FROM reports r

                LEFT JOIN brands b
                    ON b.id = r.brand_id

                LEFT JOIN users u
                    ON u.id = r.created_by

                ORDER BY r.created_at DESC

                LIMIT 100
            """)

            reports = cur.fetchall()

            # =================================================
            # CLIENT / BRAND LIST
            # =================================================

            cur.execute("""
                SELECT
                    b.id,
                    b.name,
                    b.is_active,
                    COUNT(r.id) AS report_count

                FROM brands b

                LEFT JOIN reports r
                    ON r.brand_id = b.id

                GROUP BY
                    b.id,
                    b.name,
                    b.is_active

                ORDER BY
                    b.name ASC
            """)

            report_clients = cur.fetchall()

        return render_template(
            "admin_client_reports.html",

            current_user=current_user,

            total_reports=total_reports,
            clients_with_reports=clients_with_reports,
            reports_this_month=reports_this_month,

            reports=reports,
            report_clients=report_clients,
        )

    except Exception:

        app.logger.exception(
            "Failed to load client reports."
        )

        flash(
            "Unable to load client reports right now.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        conn.close()
# =========================================================
# AI CONTENT ASSISTANT
# DIRECT GEMINI GENERATION WITH RETRY + FALLBACK
# =========================================================

@app.route(
    "/ai-assistant",
    methods=["GET", "POST"]
)
@login_required
def ai_assistant():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    # =====================================================
    # GET
    # =====================================================

    if request.method == "GET":

        return render_template(
            "ai_assistant.html",
            current_user=current_user,
            generated_content=None,
            error_message=None
        )

    # =====================================================
    # POST
    # =====================================================

    topic = request.form.get(
        "topic",
        ""
    ).strip()

    platform = request.form.get(
        "platform",
        "Instagram"
    ).strip()

    tone = request.form.get(
        "tone",
        "Professional"
    ).strip()

    length = request.form.get(
        "length",
        "Medium"
    ).strip()

    # =====================================================
    # VALIDATION
    # =====================================================

    if not topic:

        return jsonify({
            "success": False,
            "error": "Please enter a topic or idea."
        }), 400

    if len(topic) > 5000:

        return jsonify({
            "success": False,
            "error": (
                "Please keep the topic under "
                "5000 characters."
            )
        }), 400

    if not gemini_client:

        return jsonify({
            "success": False,
            "error": (
                "AI service is not configured. "
                "Please check your GEMINI_API_KEY."
            )
        }), 500

    # =====================================================
    # AI PROMPT
    # =====================================================

    prompt = f"""
You are an expert social media content strategist
working inside RicozSocial.

Create a high-quality social media post based on
the following information.

Topic:
{topic}

Platform:
{platform}

Tone:
{tone}

Length:
{length}

Requirements:

1. Write engaging and professional content.
2. Match the selected platform.
3. Do not mention AI, Gemini, automation, or this prompt.
4. Do not use unnecessary quotation marks.
5. Include a clear call-to-action when appropriate.
6. Provide exactly 5 relevant hashtags.
7. Keep the content natural and ready to publish.
8. Do not explain your process.
9. Do not add extra sections.

Return the response exactly in this format:

POST:
[post content]

HASHTAGS:
#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5
"""

    # =====================================================
    # GEMINI MODEL CONFIGURATION
    # =====================================================

    models_to_try = [
        "gemini-3.7-flash",
        "gemini-3.8-flash",
    ]

    last_error = None
    response = None

    # =====================================================
    # GEMINI GENERATION WITH RETRY + FALLBACK
    # =====================================================

    for model_index, model_name in enumerate(models_to_try):

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):

            try:

                app.logger.info(
                    "Gemini generation attempt %s/%s using %s",
                    attempt,
                    max_attempts,
                    model_name
                )

                response = gemini_client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                app.logger.info(
                    "Gemini response received successfully "
                    "using model %s.",
                    model_name
                )

                last_error = None

                break

            except Exception as e:

                last_error = e

                error_text = str(e).strip()
                error_lower = error_text.lower()

                app.logger.exception(
                    "Gemini generation failed | "
                    "model=%s | attempt=%s/%s",
                    model_name,
                    attempt,
                    max_attempts
                )

                # =================================================
                # RETRY ONLY TEMPORARY / OVERLOAD ERRORS
                # =================================================

                is_temporary_error = (
                    "503" in error_text
                    or "unavailable" in error_lower
                    or "high demand" in error_lower
                    or "temporarily" in error_lower
                    or "overloaded" in error_lower
                    or "resource exhausted" in error_lower
                    or "429" in error_text
                    or "rate limit" in error_lower
                )

                if not is_temporary_error:

                    break

                # -------------------------------------------------
                # WAIT BEFORE RETRY
                # -------------------------------------------------

                if attempt < max_attempts:

                    retry_delay = 2 ** attempt

                    app.logger.warning(
                        "Temporary Gemini error. "
                        "Retrying in %s seconds...",
                        retry_delay
                    )

                    time.sleep(retry_delay)

        # =====================================================
        # SUCCESSFUL MODEL RESPONSE
        # =====================================================

        if response is not None:

            break

        # =====================================================
        # MOVE TO FALLBACK MODEL
        # =====================================================

        if model_index < len(models_to_try) - 1:

            app.logger.warning(
                "Model %s failed. Trying fallback model %s.",
                model_name,
                models_to_try[model_index + 1]
            )

    # =====================================================
    # ALL MODELS FAILED
    # =====================================================

    if response is None:

        error_text = (
            str(last_error).strip()
            if last_error
            else ""
        )

        if not error_text:

            error_text = (
                "The Gemini service could not generate "
                "content at this time."
            )

        return jsonify({
            "success": False,
            "error": (
                "Gemini API error: "
                + error_text
            )
        }), 503

    # =====================================================
    # EXTRACT GENERATED TEXT
    # =====================================================

    generated_content = ""

    # -----------------------------------------------------
    # METHOD 1: STANDARD SDK TEXT
    # -----------------------------------------------------

    try:

        response_text = getattr(
            response,
            "text",
            None
        )

        if response_text:

            generated_content = str(
                response_text
            ).strip()

    except Exception:

        app.logger.exception(
            "Failed to read response.text."
        )

    # -----------------------------------------------------
    # METHOD 2: CANDIDATES -> CONTENT -> PARTS
    # -----------------------------------------------------

    if not generated_content:

        try:

            candidates = getattr(
                response,
                "candidates",
                None
            )

            if candidates:

                for candidate in candidates:

                    content = getattr(
                        candidate,
                        "content",
                        None
                    )

                    if not content:
                        continue

                    parts = getattr(
                        content,
                        "parts",
                        None
                    )

                    if not parts:
                        continue

                    for part in parts:

                        part_text = getattr(
                            part,
                            "text",
                            None
                        )

                        if part_text:

                            generated_content += (
                                str(part_text)
                                + "\n"
                            )

                    if generated_content.strip():

                        break

            generated_content = (
                generated_content
                .strip()
            )

        except Exception:

            app.logger.exception(
                "Failed to extract Gemini candidate text."
            )

    # =====================================================
    # RESPONSE DIAGNOSTICS
    # =====================================================

    if not generated_content:

        try:

            candidates = getattr(
                response,
                "candidates",
                None
            )

            if candidates:

                for index, candidate in enumerate(
                    candidates
                ):

                    finish_reason = getattr(
                        candidate,
                        "finish_reason",
                        None
                    )

                    safety_ratings = getattr(
                        candidate,
                        "safety_ratings",
                        None
                    )

                    app.logger.warning(
                        "Gemini candidate %s | "
                        "finish_reason=%s | "
                        "safety_ratings=%s",
                        index,
                        finish_reason,
                        safety_ratings
                    )

            else:

                app.logger.warning(
                    "Gemini returned no candidates."
                )

        except Exception:

            app.logger.exception(
                "Failed to inspect Gemini response."
            )

    # =====================================================
    # EMPTY RESPONSE
    # =====================================================

    if not generated_content:

        return jsonify({
            "success": False,
            "error": (
                "Gemini completed the request but "
                "returned no text. Please try again."
            )
        }), 500

    # =====================================================
    # ACTIVITY LOG
    # =====================================================

    try:

        log_activity(
            action="ai_content_generated",
            entity_type="ai_assistant",
            description=(
                f"Generated AI content for "
                f"{platform}."
            )
        )

    except Exception:

        app.logger.exception(
            "Failed to log AI content generation."
        )

    # =====================================================
    # SUCCESS
    # =====================================================

    return jsonify({
        "success": True,
        "generated_content": generated_content
    })
# =========================================================
# ADMIN CLIENT MANAGEMENT
# =========================================================

@app.route("/admin/clients")
@login_required
def admin_clients():

    current_user = get_current_user()

    # -----------------------------------------------------
    # AUTHENTICATION
    # -----------------------------------------------------

    if not current_user:

        return redirect(
            url_for("login")
        )


    # -----------------------------------------------------
    # ADMIN ACCESS
    # -----------------------------------------------------

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip().lower()


    conn = get_db_connection()


    try:

        with conn.cursor() as cur:

            # =================================================
            # CLIENT LIST
            # =================================================

            query = """
                SELECT
                    u.id,
                    u.name,
                    u.email,
                    u.role,
                    u.is_active,
                    u.created_at,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM brands b
                            WHERE b.created_by = u.id
                        ),
                        0
                    ) AS brands_count,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM posts p
                            WHERE p.created_by = u.id
                        ),
                        0
                    ) AS posts_count,

                    (
                        SELECT MAX(al.created_at)
                        FROM activity_logs al
                        WHERE al.user_id = u.id
                    ) AS last_activity

                FROM users u

                WHERE u.role <> 'admin'
            """


            params = []


            # =================================================
            # SEARCH FILTER
            # =================================================

            if search:

                query += """
                    AND (
                        u.name ILIKE %s
                        OR u.email ILIKE %s
                    )
                """

                search_value = f"%{search}%"

                params.extend([
                    search_value,
                    search_value
                ])


            # =================================================
            # STATUS FILTER
            # =================================================

            if status == "active":

                query += """
                    AND u.is_active = TRUE
                """


            elif status == "inactive":

                query += """
                    AND u.is_active = FALSE
                """


            # =================================================
            # ORDER CLIENTS
            # =================================================

            query += """
                ORDER BY u.created_at DESC
            """


            # =================================================
            # EXECUTE CLIENT QUERY
            # =================================================

            cur.execute(
                query,
                tuple(params)
            )

            clients = cur.fetchall()


            # =================================================
            # TOTAL CLIENTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM users
                WHERE role <> 'admin'
            """)

            total_clients = cur.fetchone()["count"]


            # =================================================
            # ACTIVE CLIENTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM users
                WHERE role <> 'admin'
                AND is_active = TRUE
            """)

            active_clients = cur.fetchone()["count"]


            # =================================================
            # INACTIVE CLIENTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM users
                WHERE role <> 'admin'
                AND is_active = FALSE
            """)

            inactive_clients = cur.fetchone()["count"]


        # =====================================================
        # CLIENT MANAGEMENT PAGE
        # =====================================================

        return render_template(
            "admin_clients.html",

            current_user=current_user,

            clients=clients,

            total_clients=total_clients,

            active_clients=active_clients,

            inactive_clients=inactive_clients,

            search=search,

            status=status
        )


    # =====================================================
    # ERROR HANDLING
    # =====================================================

    except Exception as e:

        app.logger.exception(
            "Failed to load admin client management."
        )


        # -------------------------------------------------
        # SHOW ACTUAL ERROR
        # -------------------------------------------------

        return f"""
        <!DOCTYPE html>

        <html lang="en">

        <head>

            <meta charset="UTF-8">

            <meta name="viewport"
                  content="width=device-width, initial-scale=1.0">

            <title>
                Client Management Error — RicozSocial
            </title>

            <style>

                * {{
                    box-sizing: border-box;
                }}

                body {{
                    margin: 0;
                    min-height: 100vh;

                    display: flex;
                    align-items: center;
                    justify-content: center;

                    padding: 30px;

                    font-family:
                        Arial,
                        Helvetica,
                        sans-serif;

                    background: #f8f8f8;

                    color: #222222;
                }}

                .error-card {{
                    width: 100%;
                    max-width: 760px;

                    padding: 35px;

                    background: #ffffff;

                    border: 1px solid #eeeeee;

                    border-top: 5px solid #e31e24;

                    border-radius: 16px;

                    box-shadow:
                        0 15px 45px
                        rgba(0, 0, 0, 0.08);
                }}

                .error-icon {{
                    width: 52px;
                    height: 52px;

                    display: flex;
                    align-items: center;
                    justify-content: center;

                    margin-bottom: 20px;

                    border-radius: 12px;

                    background: #fff0f1;

                    color: #e31e24;

                    font-size: 25px;
                    font-weight: 800;
                }}

                h1 {{
                    margin: 0 0 10px;

                    color: #171717;

                    font-size: 25px;
                    font-weight: 800;
                }}

                .description {{
                    margin: 0 0 22px;

                    color: #777777;

                    font-size: 14px;

                    line-height: 1.6;
                }}

                .error-box {{
                    padding: 18px;

                    background: #fff7f7;

                    border: 1px solid #ffd6d8;

                    border-radius: 10px;

                    color: #b31318;

                    font-family:
                        monospace;

                    font-size: 13px;

                    line-height: 1.6;

                    overflow-wrap: anywhere;
                }}

                .back-button {{
                    display: inline-flex;

                    align-items: center;
                    justify-content: center;

                    margin-top: 22px;

                    min-height: 42px;

                    padding: 0 18px;

                    background: #e31e24;

                    color: #ffffff;

                    border-radius: 9px;

                    text-decoration: none;

                    font-size: 13px;

                    font-weight: 700;
                }}

                .back-button:hover {{
                    background: #c8171d;
                }}

            </style>

        </head>


        <body>

            <div class="error-card">

                <div class="error-icon">
                    !
                </div>


                <h1>
                    Client Management Error
                </h1>


                <p class="description">
                    RicozSocial could not load the Client Management
                    page. The exact technical error is shown below.
                </p>


                <div class="error-box">
                    {str(e)}
                </div>


                <a
                    href="{url_for('admin_dashboard')}"
                    class="back-button"
                >
                    ← Back to Admin Dashboard
                </a>

            </div>

        </body>

        </html>
        """, 500


    finally:

        conn.close()
# =========================================================
# ADMIN CLIENT DETAILS
# =========================================================

@app.route("/admin/clients/<int:user_id>")
@login_required
def admin_client_details(user_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":
        flash("Administrator access is required.", "danger")
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # =================================================
            # CLIENT PROFILE
            # =================================================

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active,
                    created_at,
                    updated_at
                FROM users
                WHERE id = %s
                AND role <> 'admin'
            """, (user_id,))

            client = cur.fetchone()

            if not client:
                flash("Client account was not found.", "danger")
                return redirect(url_for("admin_clients"))


            # =================================================
            # BRAND COUNT
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE created_by = %s
            """, (user_id,))

            brands_count = cur.fetchone()["count"]


            # =================================================
            # SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts sa
                INNER JOIN brands b
                    ON b.id = sa.brand_id
                WHERE b.created_by = %s
            """, (user_id,))

            social_accounts_count = cur.fetchone()["count"]


            # =================================================
            # CONNECTED SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts sa
                INNER JOIN brands b
                    ON b.id = sa.brand_id
                WHERE b.created_by = %s
                AND sa.is_connected = TRUE
            """, (user_id,))

            connected_accounts_count = cur.fetchone()["count"]


            # =================================================
            # TOTAL POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE created_by = %s
            """, (user_id,))

            total_posts = cur.fetchone()["count"]


            # =================================================
            # PUBLISHED POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE created_by = %s
                AND status = 'published'
            """, (user_id,))

            published_posts = cur.fetchone()["count"]


            # =================================================
            # SCHEDULED POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE created_by = %s
                AND status = 'scheduled'
            """, (user_id,))

            scheduled_posts = cur.fetchone()["count"]


            # =================================================
            # DRAFT POSTS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE created_by = %s
                AND status = 'draft'
            """, (user_id,))

            draft_posts = cur.fetchone()["count"]


            # =================================================
            # PENDING APPROVALS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM content_approvals ca
                INNER JOIN posts p
                    ON p.id = ca.post_id
                WHERE p.created_by = %s
                AND ca.status = 'pending'
            """, (user_id,))

            pending_approvals = cur.fetchone()["count"]


            # =================================================
            # COMMUNITY ITEMS
            # =================================================

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments cc
                INNER JOIN brands b
                    ON b.id = cc.brand_id
                WHERE b.created_by = %s
                AND cc.status IN ('pending', 'unread')
            """, (user_id,))

            community_items = cur.fetchone()["count"]


            # =================================================
            # CLIENT BRANDS
            # =================================================

            cur.execute("""
                SELECT
                    b.id,
                    b.name,
                    b.description,
                    b.website_url,
                    b.logo_url,
                    b.is_active,
                    b.created_at,

                    (
                        SELECT COUNT(*)
                        FROM social_accounts sa
                        WHERE sa.brand_id = b.id
                    ) AS social_accounts_count,

                    (
                        SELECT COUNT(*)
                        FROM posts p
                        WHERE p.brand_id = b.id
                    ) AS posts_count

                FROM brands b
                WHERE b.created_by = %s
                ORDER BY b.created_at DESC
            """, (user_id,))

            client_brands = cur.fetchall()


            # =================================================
            # CLIENT SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                SELECT
                    sa.id,
                    sa.platform,
                    sa.account_name,
                    sa.username,
                    sa.profile_url,
                    sa.is_connected,
                    sa.created_at,
                    b.name AS brand_name
                FROM social_accounts sa
                INNER JOIN brands b
                    ON b.id = sa.brand_id
                WHERE b.created_by = %s
                ORDER BY sa.created_at DESC
                LIMIT 20
            """, (user_id,))

            client_social_accounts = cur.fetchall()


            # =================================================
            # RECENT POSTS
            # =================================================

            cur.execute("""
                SELECT
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,
                    b.name AS brand_name
                FROM posts p
                LEFT JOIN brands b
                    ON b.id = p.brand_id
                WHERE p.created_by = %s
                ORDER BY p.created_at DESC
                LIMIT 10
            """, (user_id,))

            client_posts = cur.fetchall()


            # =================================================
            # RECENT APPROVALS
            # =================================================

            cur.execute("""
                SELECT
                    ca.id,
                    ca.post_id,
                    ca.status,
                    ca.comments,
                    ca.created_at,
                    ca.reviewed_at,
                    p.title AS post_title
                FROM content_approvals ca
                INNER JOIN posts p
                    ON p.id = ca.post_id
                WHERE p.created_by = %s
                ORDER BY ca.created_at DESC
                LIMIT 10
            """, (user_id,))

            client_approvals = cur.fetchall()


            # =================================================
            # RECENT ACTIVITY
            # =================================================

            cur.execute("""
                SELECT
                    al.id,
                    al.action,
                    al.entity_type,
                    al.entity_id,
                    al.description,
                    al.ip_address,
                    al.created_at,
                    b.name AS brand_name
                FROM activity_logs al
                LEFT JOIN brands b
                    ON b.id = al.brand_id
                WHERE al.user_id = %s
                ORDER BY al.created_at DESC
                LIMIT 20
            """, (user_id,))

            client_activity = cur.fetchall()


            # =================================================
            # LAST ACTIVITY
            # =================================================

            cur.execute("""
                SELECT MAX(created_at) AS last_activity
                FROM activity_logs
                WHERE user_id = %s
            """, (user_id,))

            last_activity = cur.fetchone()["last_activity"]


            # =================================================
            # CLIENT NOTIFICATIONS
            # =================================================

            cur.execute("""
                SELECT
                    id,
                    title,
                    message,
                    notification_type,
                    is_read,
                    created_at
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (user_id,))

            client_notifications = cur.fetchall()


        return render_template(
    "admin_client_details.html",
    current_user=current_user,
    client=client,
    brands_count=brands_count,
    social_accounts_count=social_accounts_count,
    connected_accounts_count=connected_accounts_count,
    total_posts=total_posts,
    published_posts=published_posts,
    scheduled_posts=scheduled_posts,
    draft_posts=draft_posts,
    pending_approvals=pending_approvals,
    community_items=community_items,
    last_activity=last_activity,
    client_brands=client_brands,
    client_social_accounts=client_social_accounts,
    client_posts=client_posts,
    client_approvals=client_approvals,
    client_activity=client_activity,
    client_notifications=client_notifications,

    show_admin_back_button=True
)
    except Exception:

        app.logger.exception(
            "Failed to load admin client details."
        )

        flash(
            "Unable to load client details right now.",
            "danger"
        )

        return redirect(url_for("admin_clients"))

    finally:

        conn.close()
# =========================================================
# ADMIN CLIENT MANAGEMENT ACTIONS
# =========================================================

@app.route(
    "/admin/clients/<int:user_id>/toggle-status",
    methods=["POST"]
)
@login_required
def admin_toggle_client_status(user_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":
        flash(
            "Administrator access is required.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    # ---------------------------------------------------------
    # Prevent admin accounts from being modified here
    # ---------------------------------------------------------

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active
                FROM users
                WHERE id = %s
            """, (
                user_id,
            ))

            client = cur.fetchone()

            if not client:

                flash(
                    "Client account was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_clients")
                )

            if client["role"] == "admin":

                flash(
                    "Administrator accounts cannot be managed from Client Management.",
                    "danger"
                )

                return redirect(
                    url_for("admin_clients")
                )

            # -------------------------------------------------
            # Toggle status
            # -------------------------------------------------

            new_status = not client["is_active"]

            cur.execute("""
                UPDATE users
                SET
                    is_active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                new_status,
                user_id
            ))

            # -------------------------------------------------
            # Notification
            # -------------------------------------------------

            if new_status:

                notification_title = "Account Activated"

                notification_message = (
                    "Your RicozSocial account has been activated "
                    "by an administrator."
                )

                activity_action = "client_activated"

                activity_description = (
                    f"Activated client account: "
                    f"{client['name']} ({client['email']})."
                )

                flash_message = (
                    f"{client['name']}'s account has been activated."
                )

            else:

                notification_title = "Account Deactivated"

                notification_message = (
                    "Your RicozSocial account has been deactivated "
                    "by an administrator. Please contact support "
                    "if you believe this was done in error."
                )

                activity_action = "client_deactivated"

                activity_description = (
                    f"Deactivated client account: "
                    f"{client['name']} ({client['email']})."
                )

                flash_message = (
                    f"{client['name']}'s account has been deactivated."
                )

            cur.execute("""
                INSERT INTO notifications (
                    user_id,
                    title,
                    message,
                    notification_type,
                    is_read,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE,
                    CURRENT_TIMESTAMP
                )
            """, (
                user_id,
                notification_title,
                notification_message,
                "account"
            ))

        conn.commit()

        log_activity(
            activity_action,
            "user",
            user_id,
            activity_description
        )

        flash(
            flash_message,
            "success"
        )

        return redirect(
            request.referrer
            or url_for(
                "admin_client_details",
                user_id=user_id
            )
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to toggle client status."
        )

        flash(
            "Unable to update client account status.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_client_details",
                user_id=user_id
            )
        )

    finally:

        conn.close()


# =========================================================
# ADMIN EDIT CLIENT
# =========================================================

@app.route(
    "/admin/clients/<int:user_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def admin_edit_client(user_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active,
                    created_at,
                    updated_at
                FROM users
                WHERE id = %s
                AND role <> 'admin'
            """, (
                user_id,
            ))

            client = cur.fetchone()

            if not client:

                flash(
                    "Client account was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_clients")
                )

            if request.method == "POST":

                name = request.form.get(
                    "name",
                    ""
                ).strip()

                email = request.form.get(
                    "email",
                    ""
                ).strip().lower()

                if not name:

                    flash(
                        "Client name is required.",
                        "danger"
                    )

                    return render_template(
                        "admin_edit_client.html",
                        current_user=current_user,
                        client=client
                    )

                if not email:

                    flash(
                        "Client email is required.",
                        "danger"
                    )

                    return render_template(
                        "admin_edit_client.html",
                        current_user=current_user,
                        client=client
                    )

                # -------------------------------------------------
                # Check duplicate email
                # -------------------------------------------------

                cur.execute("""
                    SELECT id
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                    AND id <> %s
                """, (
                    email,
                    user_id
                ))

                existing_user = cur.fetchone()

                if existing_user:

                    flash(
                        "Another account is already using this email address.",
                        "danger"
                    )

                    return render_template(
                        "admin_edit_client.html",
                        current_user=current_user,
                        client=client
                    )

                # -------------------------------------------------
                # Update client
                # -------------------------------------------------

                cur.execute("""
                    UPDATE users
                    SET
                        name = %s,
                        email = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    name,
                    email,
                    user_id
                ))

                # -------------------------------------------------
                # Notification
                # -------------------------------------------------

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type,
                        is_read,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        FALSE,
                        CURRENT_TIMESTAMP
                    )
                """, (
                    user_id,
                    "Account Profile Updated",
                    "Your RicozSocial profile was updated by an administrator.",
                    "account"
                ))

            conn.commit()

            if request.method == "POST":

                log_activity(
                    "client_updated",
                    "user",
                    user_id,
                    f"Updated client profile: {name} ({email})."
                )

                flash(
                    "Client profile updated successfully.",
                    "success"
                )

                return redirect(
                    url_for(
                        "admin_client_details",
                        user_id=user_id
                    )
                )

        return render_template(
            "admin_edit_client.html",
            current_user=current_user,
            client=client
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to edit client account."
        )

        flash(
            "Unable to update client account.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_client_details",
                user_id=user_id
            )
        )

    finally:

        conn.close()


# =========================================================
# ADMIN RESET CLIENT PASSWORD
# =========================================================

@app.route(
    "/admin/clients/<int:user_id>/reset-password",
    methods=["POST"]
)
@login_required
def admin_reset_client_password(user_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    if len(new_password) < 8:

        flash(
            "Password must contain at least 8 characters.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_client_details",
                user_id=user_id
            )
        )

    if new_password != confirm_password:

        flash(
            "Passwords do not match.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_client_details",
                user_id=user_id
            )
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role
                FROM users
                WHERE id = %s
            """, (
                user_id,
            ))

            client = cur.fetchone()

            if not client:

                flash(
                    "Client account was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_clients")
                )

            if client["role"] == "admin":

                flash(
                    "Administrator passwords cannot be reset from Client Management.",
                    "danger"
                )

                return redirect(
                    url_for("admin_clients")
                )

            password_hash = generate_password_hash(
                new_password
            )

            cur.execute("""
                UPDATE users
                SET
                    password_hash = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                password_hash,
                user_id
            ))

            cur.execute("""
                INSERT INTO notifications (
                    user_id,
                    title,
                    message,
                    notification_type,
                    is_read,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE,
                    CURRENT_TIMESTAMP
                )
            """, (
                user_id,
                "Password Reset",
                "Your RicozSocial password was reset by an administrator.",
                "security"
            ))

        conn.commit()

        log_activity(
            "password_reset",
            "user",
            user_id,
            f"Administrator reset password for client: "
            f"{client['name']} ({client['email']})."
        )

        flash(
            "Client password has been reset successfully.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to reset client password."
        )

        flash(
            "Unable to reset client password.",
            "danger"
        )

    finally:

        conn.close()

    return redirect(
        url_for(
            "admin_client_details",
            user_id=user_id
        )
    )
# =========================================================
# ADMIN BRANDS MANAGEMENT
# =========================================================

@app.route("/admin/brands")
@login_required
def admin_brands():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":
        flash(
            "Administrator access is required.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip().lower()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            query = """
                SELECT
                    b.id,
                    b.name,
                    b.description,
                    b.logo_url,
                    b.website_url,
                    b.is_active,
                    b.created_at,
                    b.updated_at,

                    u.id AS owner_id,
                    u.name AS owner_name,
                    u.email AS owner_email,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM social_accounts sa
                            WHERE sa.brand_id = b.id
                        ),
                        0
                    ) AS social_accounts_count,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM social_accounts sa
                            WHERE sa.brand_id = b.id
                            AND sa.is_connected = TRUE
                        ),
                        0
                    ) AS connected_accounts_count,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM posts p
                            WHERE p.brand_id = b.id
                        ),
                        0
                    ) AS posts_count,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM brand_members bm
                            WHERE bm.brand_id = b.id
                        ),
                        0
                    ) AS members_count

                FROM brands b

                LEFT JOIN users u
                    ON u.id = b.created_by

                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        b.name ILIKE %s
                        OR b.description ILIKE %s
                        OR u.name ILIKE %s
                        OR u.email ILIKE %s
                    )
                """

                search_value = f"%{search}%"

                params.extend([
                    search_value,
                    search_value,
                    search_value,
                    search_value
                ])

            if status == "active":

                query += """
                    AND b.is_active = TRUE
                """

            elif status == "inactive":

                query += """
                    AND b.is_active = FALSE
                """

            query += """
                ORDER BY b.created_at DESC
            """

            cur.execute(
                query,
                tuple(params)
            )

            brands_list = cur.fetchall()

            # -------------------------------------------------
            # TOTAL BRANDS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
            """)

            total_brands = cur.fetchone()["count"]

            # -------------------------------------------------
            # ACTIVE BRANDS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = TRUE
            """)

            active_brands = cur.fetchone()["count"]

            # -------------------------------------------------
            # INACTIVE BRANDS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = FALSE
            """)

            inactive_brands = cur.fetchone()["count"]

            # -------------------------------------------------
            # TOTAL SOCIAL ACCOUNTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
            """)

            total_social_accounts = cur.fetchone()["count"]

            # -------------------------------------------------
            # CONNECTED SOCIAL ACCOUNTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE is_connected = TRUE
            """)

            connected_social_accounts = cur.fetchone()["count"]

            # -------------------------------------------------
            # TOTAL POSTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
            """)

            total_posts = cur.fetchone()["count"]

        return render_template(
            "admin_brands.html",
            current_user=current_user,
            brands_list=brands_list,
            total_brands=total_brands,
            active_brands=active_brands,
            inactive_brands=inactive_brands,
            total_social_accounts=total_social_accounts,
            connected_social_accounts=connected_social_accounts,
            total_posts=total_posts,
            search=search,
            status=status
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin brands management."
        )

        flash(
            "Unable to load brand management right now.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        conn.close()


# =========================================================
# ADMIN BRAND DETAILS
# =========================================================

@app.route("/admin/brands/<int:brand_id>")
@login_required
def admin_brand_details(brand_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # BRAND
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    b.id,
                    b.name,
                    b.description,
                    b.logo_url,
                    b.website_url,
                    b.is_active,
                    b.created_at,
                    b.updated_at,

                    u.id AS owner_id,
                    u.name AS owner_name,
                    u.email AS owner_email

                FROM brands b

                LEFT JOIN users u
                    ON u.id = b.created_by

                WHERE b.id = %s
            """, (
                brand_id,
            ))

            brand = cur.fetchone()

            if not brand:

                flash(
                    "Brand was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_brands")
                )

            # -------------------------------------------------
            # SOCIAL ACCOUNTS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    platform,
                    account_name,
                    username,
                    account_id,
                    profile_url,
                    is_connected,
                    created_at,
                    updated_at
                FROM social_accounts
                WHERE brand_id = %s
                ORDER BY created_at DESC
            """, (
                brand_id,
            ))

            brand_social_accounts = cur.fetchall()

            # -------------------------------------------------
            # MEMBERS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    bm.id,
                    bm.user_id,
                    bm.role,
                    bm.created_at,
                    u.name,
                    u.email,
                    u.is_active
                FROM brand_members bm

                INNER JOIN users u
                    ON u.id = bm.user_id

                WHERE bm.brand_id = %s
                ORDER BY bm.created_at ASC
            """, (
                brand_id,
            ))

            brand_members_list = cur.fetchall()

            # -------------------------------------------------
            # POSTS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,
                    u.name AS creator_name
                FROM posts p

                LEFT JOIN users u
                    ON u.id = p.created_by

                WHERE p.brand_id = %s
                ORDER BY p.created_at DESC
                LIMIT 20
            """, (
                brand_id,
            ))

            brand_posts = cur.fetchall()

            # -------------------------------------------------
            # POST COUNTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
            """, (
                brand_id,
            ))

            total_brand_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
                AND status = 'published'
            """, (
                brand_id,
            ))

            published_brand_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
                AND status = 'scheduled'
            """, (
                brand_id,
            ))

            scheduled_brand_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
                AND status = 'draft'
            """, (
                brand_id,
            ))

            draft_brand_posts = cur.fetchone()["count"]

            # -------------------------------------------------
            # COMMUNITY
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE brand_id = %s
                AND status IN ('pending', 'unread')
            """, (
                brand_id,
            ))

            pending_community = cur.fetchone()["count"]

            # -------------------------------------------------
            # ACTIVITY
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    al.id,
                    al.action,
                    al.entity_type,
                    al.entity_id,
                    al.description,
                    al.ip_address,
                    al.created_at,
                    u.name AS user_name,
                    u.email AS user_email
                FROM activity_logs al

                LEFT JOIN users u
                    ON u.id = al.user_id

                WHERE al.brand_id = %s
                ORDER BY al.created_at DESC
                LIMIT 20
            """, (
                brand_id,
            ))

            brand_activity = cur.fetchall()

        return render_template(
            "admin_brand_details.html",
            current_user=current_user,
            brand=brand,
            brand_social_accounts=brand_social_accounts,
            brand_members_list=brand_members_list,
            brand_posts=brand_posts,
            total_brand_posts=total_brand_posts,
            published_brand_posts=published_brand_posts,
            scheduled_brand_posts=scheduled_brand_posts,
            draft_brand_posts=draft_brand_posts,
            pending_community=pending_community,
            brand_activity=brand_activity
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin brand details."
        )

        flash(
            "Unable to load brand details right now.",
            "danger"
        )

        return redirect(
            url_for("admin_brands")
        )

    finally:

        conn.close()


# =========================================================
# ADMIN BRAND STATUS
# =========================================================

@app.route(
    "/admin/brands/<int:brand_id>/toggle-status",
    methods=["POST"]
)
@login_required
def admin_toggle_brand_status(brand_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    is_active,
                    created_by
                FROM brands
                WHERE id = %s
            """, (
                brand_id,
            ))

            brand = cur.fetchone()

            if not brand:

                flash(
                    "Brand was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_brands")
                )

            new_status = not brand["is_active"]

            cur.execute("""
                UPDATE brands
                SET
                    is_active = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                new_status,
                brand_id
            ))

            # -------------------------------------------------
            # Notify brand owner
            # -------------------------------------------------

            if brand["created_by"]:

                if new_status:

                    notification_title = "Brand Activated"

                    notification_message = (
                        f'Your brand "{brand["name"]}" '
                        "has been activated by an administrator."
                    )

                else:

                    notification_title = "Brand Deactivated"

                    notification_message = (
                        f'Your brand "{brand["name"]}" '
                        "has been deactivated by an administrator."
                    )

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type,
                        is_read,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        FALSE,
                        CURRENT_TIMESTAMP
                    )
                """, (
                    brand["created_by"],
                    notification_title,
                    notification_message,
                    "brand"
                ))

        conn.commit()

        if new_status:

            activity_action = "brand_activated"

            activity_description = (
                f'Activated brand: "{brand["name"]}".'
            )

            flash_message = (
                f'Brand "{brand["name"]}" has been activated.'
            )

        else:

            activity_action = "brand_deactivated"

            activity_description = (
                f'Deactivated brand: "{brand["name"]}".'
            )

            flash_message = (
                f'Brand "{brand["name"]}" has been deactivated.'
            )

        log_activity(
            activity_action,
            "brand",
            brand_id,
            activity_description,
            brand_id
        )

        flash(
            flash_message,
            "success"
        )

        return redirect(
            request.referrer
            or url_for(
                "admin_brand_details",
                brand_id=brand_id
            )
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to toggle brand status."
        )

        flash(
            "Unable to update brand status.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_brand_details",
                brand_id=brand_id
            )
        )

    finally:

        conn.close()
# =========================================================
# ADMIN SOCIAL ACCOUNTS MANAGEMENT
# =========================================================

@app.route("/admin/social-accounts")
@login_required
def admin_social_accounts():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":
        flash(
            "Administrator access is required.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    search = request.args.get(
        "search",
        ""
    ).strip()

    platform = request.args.get(
        "platform",
        ""
    ).strip().lower()

    status = request.args.get(
        "status",
        ""
    ).strip().lower()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            query = """
                SELECT
                    sa.id,
                    sa.brand_id,
                    sa.platform,
                    sa.account_name,
                    sa.username,
                    sa.account_id,
                    sa.profile_url,
                    sa.is_connected,
                    sa.token_expires_at,
                    sa.created_at,
                    sa.updated_at,

                    b.name AS brand_name,
                    b.is_active AS brand_is_active,

                    u.id AS owner_id,
                    u.name AS owner_name,
                    u.email AS owner_email

                FROM social_accounts sa

                LEFT JOIN brands b
                    ON b.id = sa.brand_id

                LEFT JOIN users u
                    ON u.id = b.created_by

                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        sa.account_name ILIKE %s
                        OR sa.username ILIKE %s
                        OR sa.account_id ILIKE %s
                        OR sa.platform ILIKE %s
                        OR b.name ILIKE %s
                        OR u.name ILIKE %s
                        OR u.email ILIKE %s
                    )
                """

                search_value = f"%{search}%"

                params.extend([
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                ])

            if platform:

                query += """
                    AND LOWER(sa.platform) = %s
                """

                params.append(platform)

            if status == "connected":

                query += """
                    AND sa.is_connected = TRUE
                """

            elif status == "disconnected":

                query += """
                    AND sa.is_connected = FALSE
                """

            query += """
                ORDER BY sa.created_at DESC
            """

            cur.execute(
                query,
                tuple(params)
            )

            accounts = cur.fetchall()

            # -------------------------------------------------
            # TOTAL ACCOUNTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
            """)

            total_accounts = cur.fetchone()["count"]

            # -------------------------------------------------
            # CONNECTED
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE is_connected = TRUE
            """)

            connected_accounts = cur.fetchone()["count"]

            # -------------------------------------------------
            # DISCONNECTED
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE is_connected = FALSE
            """)

            disconnected_accounts = cur.fetchone()["count"]

            # -------------------------------------------------
            # TOTAL BRANDS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = TRUE
            """)

            active_brands = cur.fetchone()["count"]

            # -------------------------------------------------
            # PLATFORM SUMMARY
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    LOWER(platform) AS platform,
                    COUNT(*) AS count
                FROM social_accounts
                GROUP BY LOWER(platform)
                ORDER BY count DESC
            """)

            platform_summary = cur.fetchall()

        return render_template(
            "admin_social_accounts.html",
            current_user=current_user,
            accounts=accounts,
            total_accounts=total_accounts,
            connected_accounts=connected_accounts,
            disconnected_accounts=disconnected_accounts,
            active_brands=active_brands,
            platform_summary=platform_summary,
            search=search,
            platform=platform,
            status=status
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin social accounts."
        )

        flash(
            "Unable to load social account management right now.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        conn.close()


# =========================================================
# ADMIN SOCIAL ACCOUNT DETAILS
# =========================================================

@app.route("/admin/social-accounts/<int:account_id>")
@login_required
def admin_social_account_details(account_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # ACCOUNT
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    sa.id,
                    sa.brand_id,
                    sa.platform,
                    sa.account_name,
                    sa.username,
                    sa.account_id,
                    sa.profile_url,
                    sa.access_token,
                    sa.refresh_token,
                    sa.token_expires_at,
                    sa.is_connected,
                    sa.created_at,
                    sa.updated_at,

                    b.name AS brand_name,
                    b.description AS brand_description,
                    b.website_url AS brand_website,
                    b.is_active AS brand_is_active,

                    u.id AS owner_id,
                    u.name AS owner_name,
                    u.email AS owner_email

                FROM social_accounts sa

                LEFT JOIN brands b
                    ON b.id = sa.brand_id

                LEFT JOIN users u
                    ON u.id = b.created_by

                WHERE sa.id = %s
            """, (
                account_id,
            ))

            account = cur.fetchone()

            if not account:

                flash(
                    "Social account was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_social_accounts")
                )

            # -------------------------------------------------
            # BRAND ACCOUNT SUMMARY
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE brand_id = %s
            """, (
                account["brand_id"],
            ))

            brand_account_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE brand_id = %s
                AND is_connected = TRUE
            """, (
                account["brand_id"],
            ))

            brand_connected_count = cur.fetchone()["count"]

            # -------------------------------------------------
            # BRAND POSTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
            """, (
                account["brand_id"],
            ))

            brand_posts_count = cur.fetchone()["count"]

            # -------------------------------------------------
            # RECENT ACTIVITY
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    al.id,
                    al.action,
                    al.entity_type,
                    al.entity_id,
                    al.description,
                    al.created_at,
                    u.name AS user_name,
                    u.email AS user_email
                FROM activity_logs al

                LEFT JOIN users u
                    ON u.id = al.user_id

                WHERE
                    al.entity_type = 'social_account'
                    AND al.entity_id = %s

                ORDER BY al.created_at DESC
                LIMIT 20
            """, (
                account_id,
            ))

            account_activity = cur.fetchall()

        return render_template(
            "admin_social_account_details.html",
            current_user=current_user,
            account=account,
            brand_account_count=brand_account_count,
            brand_connected_count=brand_connected_count,
            brand_posts_count=brand_posts_count,
            account_activity=account_activity
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin social account details."
        )

        flash(
            "Unable to load social account details.",
            "danger"
        )

        return redirect(
            url_for("admin_social_accounts")
        )

    finally:

        conn.close()


# =========================================================
# ADMIN SOCIAL ACCOUNT STATUS
# =========================================================

@app.route(
    "/admin/social-accounts/<int:account_id>/toggle-status",
    methods=["POST"]
)
@login_required
def admin_toggle_social_account_status(account_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    sa.id,
                    sa.brand_id,
                    sa.platform,
                    sa.account_name,
                    sa.username,
                    sa.is_connected,

                    b.name AS brand_name,
                    b.created_by AS owner_id

                FROM social_accounts sa

                LEFT JOIN brands b
                    ON b.id = sa.brand_id

                WHERE sa.id = %s
            """, (
                account_id,
            ))

            account = cur.fetchone()

            if not account:

                flash(
                    "Social account was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_social_accounts")
                )

            new_status = not account["is_connected"]

            cur.execute("""
                UPDATE social_accounts
                SET
                    is_connected = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                new_status,
                account_id
            ))

            # -------------------------------------------------
            # NOTIFICATION
            # -------------------------------------------------

            if account["owner_id"]:

                if new_status:

                    notification_title = (
                        "Social Account Activated"
                    )

                    notification_message = (
                        f'The {account["platform"]} account '
                        f'"{account["account_name"] or account["username"] or "Social Account"}" '
                        f'for brand "{account["brand_name"]}" '
                        "has been marked as connected by an administrator."
                    )

                else:

                    notification_title = (
                        "Social Account Disconnected"
                    )

                    notification_message = (
                        f'The {account["platform"]} account '
                        f'"{account["account_name"] or account["username"] or "Social Account"}" '
                        f'for brand "{account["brand_name"]}" '
                        "has been marked as disconnected by an administrator."
                    )

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type,
                        is_read,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        FALSE,
                        CURRENT_TIMESTAMP
                    )
                """, (
                    account["owner_id"],
                    notification_title,
                    notification_message,
                    "social_account"
                ))

        conn.commit()

        if new_status:

            activity_action = (
                "social_account_activated"
            )

            activity_description = (
                f'Activated {account["platform"]} account '
                f'"{account["account_name"] or account["username"] or "Social Account"}" '
                f'for brand "{account["brand_name"]}".'
            )

            flash_message = (
                "Social account marked as connected."
            )

        else:

            activity_action = (
                "social_account_deactivated"
            )

            activity_description = (
                f'Disconnected {account["platform"]} account '
                f'"{account["account_name"] or account["username"] or "Social Account"}" '
                f'for brand "{account["brand_name"]}".'
            )

            flash_message = (
                "Social account marked as disconnected."
            )

        log_activity(
            activity_action,
            "social_account",
            account_id,
            activity_description,
            account["brand_id"]
        )

        flash(
            flash_message,
            "success"
        )

        return redirect(
            request.referrer
            or url_for(
                "admin_social_account_details",
                account_id=account_id
            )
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to toggle social account status."
        )

        flash(
            "Unable to update social account status.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_social_account_details",
                account_id=account_id
            )
        )

    finally:

        conn.close()
# =========================================================
# ADMIN CONTENT / POST MANAGEMENT
# =========================================================

@app.route("/admin/posts")
@login_required
def admin_posts():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":
        flash(
            "Administrator access is required.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    search = request.args.get(
        "search",
        ""
    ).strip()

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip().lower()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # POSTS
            # -------------------------------------------------

            query = """
                SELECT
                    p.id,
                    p.brand_id,
                    p.created_by,
                    p.category_id,
                    p.title,
                    p.content,
                    p.media_url,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,
                    p.updated_at,

                    b.name AS brand_name,
                    b.is_active AS brand_is_active,

                    u.name AS creator_name,
                    u.email AS creator_email,

                    cc.name AS category_name,
                    cc.color AS category_color

                FROM posts p

                LEFT JOIN brands b
                    ON b.id = p.brand_id

                LEFT JOIN users u
                    ON u.id = p.created_by

                LEFT JOIN content_categories cc
                    ON cc.id = p.category_id

                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        p.title ILIKE %s
                        OR p.content ILIKE %s
                        OR b.name ILIKE %s
                        OR u.name ILIKE %s
                        OR u.email ILIKE %s
                    )
                """

                search_value = f"%{search}%"

                params.extend([
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                ])

            if brand_id:

                try:

                    brand_id_value = int(brand_id)

                    query += """
                        AND p.brand_id = %s
                    """

                    params.append(
                        brand_id_value
                    )

                except ValueError:

                    brand_id = ""

            if status:

                query += """
                    AND LOWER(p.status) = %s
                """

                params.append(
                    status
                )

            query += """
                ORDER BY p.created_at DESC
            """

            cur.execute(
                query,
                tuple(params)
            )

            posts_list = cur.fetchall()

            # -------------------------------------------------
            # BRANDS FOR FILTER
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name,
                    is_active
                FROM brands
                ORDER BY name ASC
            """)

            brands_for_filter = cur.fetchall()

            # -------------------------------------------------
            # TOTAL POSTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
            """)

            total_posts = cur.fetchone()["count"]

            # -------------------------------------------------
            # DRAFTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE LOWER(status) = 'draft'
            """)

            draft_posts = cur.fetchone()["count"]

            # -------------------------------------------------
            # SCHEDULED
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE LOWER(status) = 'scheduled'
            """)

            scheduled_posts = cur.fetchone()["count"]

            # -------------------------------------------------
            # PUBLISHED
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
                WHERE LOWER(status) = 'published'
            """)

            published_posts = cur.fetchone()["count"]

            # -------------------------------------------------
            # PENDING APPROVALS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM content_approvals
                WHERE LOWER(status) = 'pending'
            """)

            pending_approvals = cur.fetchone()["count"]

        return render_template(
            "admin_posts.html",
            current_user=current_user,
            posts_list=posts_list,
            brands_for_filter=brands_for_filter,
            total_posts=total_posts,
            draft_posts=draft_posts,
            scheduled_posts=scheduled_posts,
            published_posts=published_posts,
            pending_approvals=pending_approvals,
            search=search,
            brand_id=brand_id,
            status=status
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin post management."
        )

        flash(
            "Unable to load content management right now.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        conn.close()


# =========================================================
# ADMIN POST DETAILS
# =========================================================

@app.route("/admin/posts/<int:post_id>")
@login_required
def admin_post_details(post_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # POST
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    p.id,
                    p.brand_id,
                    p.created_by,
                    p.category_id,
                    p.title,
                    p.content,
                    p.media_url,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,
                    p.updated_at,

                    b.name AS brand_name,
                    b.description AS brand_description,
                    b.website_url AS brand_website,
                    b.is_active AS brand_is_active,

                    u.name AS creator_name,
                    u.email AS creator_email,

                    cc.name AS category_name,
                    cc.color AS category_color

                FROM posts p

                LEFT JOIN brands b
                    ON b.id = p.brand_id

                LEFT JOIN users u
                    ON u.id = p.created_by

                LEFT JOIN content_categories cc
                    ON cc.id = p.category_id

                WHERE p.id = %s
            """, (
                post_id,
            ))

            post = cur.fetchone()

            if not post:

                flash(
                    "Post was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_posts")
                )

            # -------------------------------------------------
            # POST PLATFORMS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    pp.id,
                    pp.social_account_id,
                    pp.platform_status,
                    pp.external_post_id,
                    pp.published_at,
                    pp.error_message,

                    sa.platform,
                    sa.account_name,
                    sa.username,
                    sa.is_connected

                FROM post_platforms pp

                LEFT JOIN social_accounts sa
                    ON sa.id = pp.social_account_id

                WHERE pp.post_id = %s

                ORDER BY pp.id ASC
            """, (
                post_id,
            ))

            post_platforms = cur.fetchall()

            # -------------------------------------------------
            # APPROVALS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    ca.id,
                    ca.submitted_by,
                    ca.reviewer_id,
                    ca.status,
                    ca.comments,
                    ca.reviewed_at,
                    ca.created_at,

                    submitter.name AS submitter_name,
                    submitter.email AS submitter_email,

                    reviewer.name AS reviewer_name,
                    reviewer.email AS reviewer_email

                FROM content_approvals ca

                LEFT JOIN users submitter
                    ON submitter.id = ca.submitted_by

                LEFT JOIN users reviewer
                    ON reviewer.id = ca.reviewer_id

                WHERE ca.post_id = %s

                ORDER BY ca.created_at DESC
            """, (
                post_id,
            ))

            post_approvals = cur.fetchall()

            # -------------------------------------------------
            # TAGS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    ct.id,
                    ct.name
                FROM post_tags pt

                INNER JOIN content_tags ct
                    ON ct.id = pt.tag_id

                WHERE pt.post_id = %s

                ORDER BY ct.name ASC
            """, (
                post_id,
            ))

            post_tags = cur.fetchall()

            # -------------------------------------------------
            # ACTIVITY
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    al.id,
                    al.action,
                    al.entity_type,
                    al.entity_id,
                    al.description,
                    al.ip_address,
                    al.created_at,

                    u.name AS user_name,
                    u.email AS user_email

                FROM activity_logs al

                LEFT JOIN users u
                    ON u.id = al.user_id

                WHERE
                    al.entity_type = 'post'
                    AND al.entity_id = %s

                ORDER BY al.created_at DESC

                LIMIT 30
            """, (
                post_id,
            ))

            post_activity = cur.fetchall()

        return render_template(
            "admin_post_details.html",
            current_user=current_user,
            post=post,
            post_platforms=post_platforms,
            post_approvals=post_approvals,
            post_tags=post_tags,
            post_activity=post_activity
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin post details."
        )

        flash(
            "Unable to load post details.",
            "danger"
        )

        return redirect(
            url_for("admin_posts")
        )

    finally:

        conn.close()
# =========================================================
# ADMIN CAMPAIGN MANAGEMENT
# =========================================================


@app.route("/admin/campaigns")
@login_required
def admin_campaigns():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip().lower()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # CAMPAIGNS
            # -------------------------------------------------

            query = """
                SELECT
                    c.id,
                    c.brand_id,
                    c.created_by,
                    c.name,
                    c.description,
                    c.goal_type,
                    c.target_value,
                    c.start_date,
                    c.end_date,
                    c.status,
                    c.created_at,
                    c.updated_at,

                    b.name AS brand_name,
                    b.is_active AS brand_is_active,

                    u.name AS creator_name,
                    u.email AS creator_email,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM campaign_posts cp
                            WHERE cp.campaign_id = c.id
                        ),
                        0
                    ) AS posts_count,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM campaign_posts cp
                            INNER JOIN posts p
                                ON p.id = cp.post_id
                            WHERE cp.campaign_id = c.id
                            AND LOWER(p.status) = 'published'
                        ),
                        0
                    ) AS published_posts_count,

                    COALESCE(
                        (
                            SELECT COUNT(*)
                            FROM campaign_posts cp
                            INNER JOIN posts p
                                ON p.id = cp.post_id
                            WHERE cp.campaign_id = c.id
                            AND LOWER(p.status) = 'scheduled'
                        ),
                        0
                    ) AS scheduled_posts_count

                FROM campaigns c

                LEFT JOIN brands b
                    ON b.id = c.brand_id

                LEFT JOIN users u
                    ON u.id = c.created_by

                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        c.name ILIKE %s
                        OR c.description ILIKE %s
                        OR b.name ILIKE %s
                        OR u.name ILIKE %s
                        OR u.email ILIKE %s
                    )
                """

                search_value = f"%{search}%"

                params.extend([
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                ])

            if brand_id:

                try:

                    brand_id_value = int(
                        brand_id
                    )

                    query += """
                        AND c.brand_id = %s
                    """

                    params.append(
                        brand_id_value
                    )

                except ValueError:

                    brand_id = ""

            if status:

                query += """
                    AND LOWER(c.status) = %s
                """

                params.append(
                    status
                )

            query += """
                ORDER BY c.created_at DESC
            """

            cur.execute(
                query,
                tuple(params)
            )

            campaigns = cur.fetchall()

            # -------------------------------------------------
            # BRANDS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name,
                    is_active
                FROM brands
                ORDER BY name ASC
            """)

            brands_for_filter = cur.fetchall()

            # -------------------------------------------------
            # TOTAL CAMPAIGNS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaigns
            """)

            total_campaigns = cur.fetchone()["count"]

            # -------------------------------------------------
            # ACTIVE CAMPAIGNS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaigns
                WHERE LOWER(status) = 'active'
            """)

            active_campaigns = cur.fetchone()["count"]

            # -------------------------------------------------
            # DRAFT CAMPAIGNS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaigns
                WHERE LOWER(status) = 'draft'
            """)

            draft_campaigns = cur.fetchone()["count"]

            # -------------------------------------------------
            # COMPLETED CAMPAIGNS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaigns
                WHERE LOWER(status) = 'completed'
            """)

            completed_campaigns = cur.fetchone()["count"]

            # -------------------------------------------------
            # TOTAL CAMPAIGN POSTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaign_posts
            """)

            total_campaign_posts = cur.fetchone()["count"]

        return render_template(
            "admin_campaigns.html",
            current_user=current_user,
            campaigns=campaigns,
            brands_for_filter=brands_for_filter,
            total_campaigns=total_campaigns,
            active_campaigns=active_campaigns,
            draft_campaigns=draft_campaigns,
            completed_campaigns=completed_campaigns,
            total_campaign_posts=total_campaign_posts,
            search=search,
            brand_id=brand_id,
            status=status
        )

    except Exception:

        app.logger.exception(
            "Failed to load admin campaigns."
        )

        flash(
            "Unable to load campaign management right now.",
            "danger"
        )

        return redirect(
            url_for("admin_dashboard")
        )

    finally:

        conn.close()


# =========================================================
# CREATE CAMPAIGN
# =========================================================

@app.route("/admin/campaigns/create", methods=["GET", "POST"])
@login_required
def admin_create_campaign():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":
        flash(
            "Administrator access is required.",
            "danger"
        )
        return redirect(url_for("dashboard"))

    conn = get_db_connection()

    try:

        # =====================================================
        # LOAD BRANDS
        # =====================================================

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    created_by,
                    is_active
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
            """)

            brands = cur.fetchall()


        # =====================================================
        # CREATE CAMPAIGN
        # =====================================================

        if request.method == "POST":

            brand_id = request.form.get(
                "brand_id",
                ""
            ).strip()

            name = request.form.get(
                "name",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            goal_type = request.form.get(
                "goal_type",
                ""
            ).strip()

            target_value = request.form.get(
                "target_value",
                ""
            ).strip()

            start_date = request.form.get(
                "start_date",
                ""
            ).strip()

            end_date = request.form.get(
                "end_date",
                ""
            ).strip()

            campaign_status = request.form.get(
                "status",
                "Draft"
            ).strip()


            # =================================================
            # VALIDATE BRAND
            # =================================================

            try:

                brand_id = int(brand_id)

            except (TypeError, ValueError):

                flash(
                    "Please select a valid brand.",
                    "danger"
                )

                return render_template(
                    "admin_create_campaign.html",
                    brands=brands
                )


            # =================================================
            # VALIDATE NAME
            # =================================================

            if not name:

                flash(
                    "Campaign name is required.",
                    "danger"
                )

                return render_template(
                    "admin_create_campaign.html",
                    brands=brands
                )


            # =================================================
            # VALIDATE STATUS
            # =================================================

            allowed_statuses = [
                "Draft",
                "Active",
                "Paused",
                "Completed",
                "Archived"
            ]

            if campaign_status not in allowed_statuses:

                campaign_status = "Draft"


            # =================================================
            # VALIDATE TARGET VALUE
            # =================================================

            if target_value:

                try:

                    target_value = float(
                        target_value
                    )

                    if target_value < 0:

                        flash(
                            "Target value cannot be negative.",
                            "danger"
                        )

                        return render_template(
                            "admin_create_campaign.html",
                            brands=brands
                        )

                except ValueError:

                    flash(
                        "Target value must be a valid number.",
                        "danger"
                    )

                    return render_template(
                        "admin_create_campaign.html",
                        brands=brands
                    )

            else:

                target_value = None


            # =================================================
            # VALIDATE DATES
            # =================================================

            if start_date and end_date:

                if end_date < start_date:

                    flash(
                        "End date cannot be before start date.",
                        "danger"
                    )

                    return render_template(
                        "admin_create_campaign.html",
                        brands=brands
                    )


            # =================================================
            # VERIFY BRAND
            # =================================================

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT
                        id,
                        name,
                        created_by
                    FROM brands
                    WHERE id = %s
                    AND is_active = TRUE
                """, (brand_id,))

                selected_brand = cur.fetchone()


                if not selected_brand:

                    flash(
                        "Selected brand was not found.",
                        "danger"
                    )

                    return render_template(
                        "admin_create_campaign.html",
                        brands=brands
                    )


                # =================================================
                # INSERT CAMPAIGN
                # =================================================

                cur.execute("""
                    INSERT INTO campaigns (
                        brand_id,
                        created_by,
                        name,
                        description,
                        goal_type,
                        target_value,
                        start_date,
                        end_date,
                        status
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                """, (
                    brand_id,
                    current_user["id"],
                    name,
                    description or None,
                    goal_type or None,
                    target_value,
                    start_date or None,
                    end_date or None,
                    campaign_status
                ))

                campaign_id = cur.fetchone()["id"]


                # =================================================
                # NOTIFY BRAND OWNER
                # =================================================

                if selected_brand.get("created_by"):

                    cur.execute("""
                        INSERT INTO notifications (
                            user_id,
                            title,
                            message,
                            notification_type
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s
                        )
                    """, (
                        selected_brand["created_by"],
                        "New Campaign Created",
                        (
                            f'Campaign "{name}" was created '
                            f'for your brand.'
                        ),
                        "campaign"
                    ))


            conn.commit()


            # =================================================
            # ACTIVITY LOG
            # =================================================

            log_activity(
                "created",
                "campaign",
                campaign_id,
                (
                    f'Created campaign "{name}" '
                    f'for brand "{selected_brand["name"]}".'
                ),
                brand_id
            )


            flash(
                "Campaign created successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "admin_campaign_details",
                    campaign_id=campaign_id
                )
            )


        # =====================================================
        # GET REQUEST
        # =====================================================

        return render_template(
            "admin_create_campaign.html",
            brands=brands
        )


    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to create campaign."
        )

        flash(
            "Unable to create campaign right now.",
            "danger"
        )

        return redirect(
            url_for("admin_campaigns")
        )


    finally:

        conn.close()
# =========================================================
# ADMIN CAMPAIGN DETAILS
# =========================================================

@app.route(
    "/admin/campaigns/<int:campaign_id>"
)
@login_required
def admin_campaign_details(campaign_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # CAMPAIGN
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    c.id,
                    c.brand_id,
                    c.created_by,
                    c.name,
                    c.description,
                    c.goal_type,
                    c.target_value,
                    c.start_date,
                    c.end_date,
                    c.status,
                    c.created_at,
                    c.updated_at,

                    b.name AS brand_name,
                    b.description AS brand_description,
                    b.website_url AS brand_website,
                    b.is_active AS brand_is_active,

                    u.name AS creator_name,
                    u.email AS creator_email

                FROM campaigns c

                LEFT JOIN brands b
                    ON b.id = c.brand_id

                LEFT JOIN users u
                    ON u.id = c.created_by

                WHERE c.id = %s
            """, (
                campaign_id,
            ))

            campaign = cur.fetchone()

            if not campaign:

                flash(
                    "Campaign was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_campaigns")
                )

            # -------------------------------------------------
            # CAMPAIGN POSTS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,

                    u.name AS creator_name

                FROM campaign_posts cp

                INNER JOIN posts p
                    ON p.id = cp.post_id

                LEFT JOIN users u
                    ON u.id = p.created_by

                WHERE cp.campaign_id = %s

                ORDER BY p.created_at DESC
            """, (
                campaign_id,
            ))

            campaign_posts = cur.fetchall()

            # -------------------------------------------------
            # POST COUNTS
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaign_posts
                WHERE campaign_id = %s
            """, (
                campaign_id,
            ))

            total_campaign_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaign_posts cp

                INNER JOIN posts p
                    ON p.id = cp.post_id

                WHERE cp.campaign_id = %s
                AND LOWER(p.status) = 'published'
            """, (
                campaign_id,
            ))

            published_campaign_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaign_posts cp

                INNER JOIN posts p
                    ON p.id = cp.post_id

                WHERE cp.campaign_id = %s
                AND LOWER(p.status) = 'scheduled'
            """, (
                campaign_id,
            ))

            scheduled_campaign_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM campaign_posts cp

                INNER JOIN posts p
                    ON p.id = cp.post_id

                WHERE cp.campaign_id = %s
                AND LOWER(p.status) = 'draft'
            """, (
                campaign_id,
            ))

            draft_campaign_posts = cur.fetchone()["count"]

            # -------------------------------------------------
            # ANALYTICS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    COALESCE(SUM(a.impressions), 0) AS impressions,
                    COALESCE(SUM(a.reach), 0) AS reach,
                    COALESCE(SUM(a.likes), 0) AS likes,
                    COALESCE(SUM(a.comments), 0) AS comments,
                    COALESCE(SUM(a.shares), 0) AS shares,
                    COALESCE(SUM(a.clicks), 0) AS clicks

                FROM analytics a

                INNER JOIN campaign_posts cp
                    ON cp.post_id = a.post_id

                WHERE cp.campaign_id = %s
            """, (
                campaign_id,
            ))

            campaign_analytics = cur.fetchone()
            # -------------------------------------------------
            # CAMPAIGN GOAL PROGRESS
            # -------------------------------------------------

            campaign_goal_progress = 0
            campaign_goal_current = 0
            campaign_goal_remaining = 0

            goal_type = (
                campaign.get("goal_type")
                or ""
            ).strip().lower()

            target_value = (
                campaign.get("target_value")
                or 0
            )

            if goal_type:

                if goal_type in (
                    "impressions",
                    "impression",
                    "views",
                ):

                    campaign_goal_current = (
                        campaign_analytics["impressions"]
                        or 0
                    )

                elif goal_type in (
                    "reach",
                    "audience_reach",
                ):

                    campaign_goal_current = (
                        campaign_analytics["reach"]
                        or 0
                    )

                elif goal_type in (
                    "likes",
                    "engagement",
                ):

                    campaign_goal_current = (
                        campaign_analytics["likes"]
                        or 0
                    )

                elif goal_type in (
                    "comments",
                    "comment",
                ):

                    campaign_goal_current = (
                        campaign_analytics["comments"]
                        or 0
                    )

                elif goal_type in (
                    "shares",
                    "share",
                ):

                    campaign_goal_current = (
                        campaign_analytics["shares"]
                        or 0
                    )

                elif goal_type in (
                    "clicks",
                    "traffic",
                ):

                    campaign_goal_current = (
                        campaign_analytics["clicks"]
                        or 0
                    )

                else:

                    campaign_goal_current = 0


                if target_value and float(target_value) > 0:

                    campaign_goal_progress = (
                        float(campaign_goal_current)
                        / float(target_value)
                    ) * 100

                    campaign_goal_progress = min(
                        campaign_goal_progress,
                        100
                    )

                    campaign_goal_remaining = max(
                        float(target_value)
                        - float(campaign_goal_current),
                        0
                    )

            # -------------------------------------------------
            # ACTIVITY
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    al.id,
                    al.action,
                    al.entity_type,
                    al.entity_id,
                    al.description,
                    al.created_at,

                    u.name AS user_name,
                    u.email AS user_email

                FROM activity_logs al

                LEFT JOIN users u
                    ON u.id = al.user_id

                WHERE
                    al.entity_type = 'campaign'
                    AND al.entity_id = %s

                ORDER BY al.created_at DESC

                LIMIT 30
            """, (
                campaign_id,
            ))

            campaign_activity = cur.fetchall()

        return render_template(
            "admin_campaign_details.html",
            current_user=current_user,
            campaign=campaign,
            campaign_posts=campaign_posts,
            total_campaign_posts=total_campaign_posts,
            published_campaign_posts=published_campaign_posts,
            scheduled_campaign_posts=scheduled_campaign_posts,
            draft_campaign_posts=draft_campaign_posts,
            campaign_analytics=campaign_analytics,
            campaign_activity=campaign_activity
        )

    except Exception:

        app.logger.exception(
            "Failed to load campaign details."
        )

        flash(
            "Unable to load campaign details.",
            "danger"
        )

        return redirect(
            url_for("admin_campaigns")
        )

    finally:

        conn.close()


# =========================================================
# ADMIN CAMPAIGN STATUS
# =========================================================

@app.route(
    "/admin/campaigns/<int:campaign_id>/status",
    methods=["POST"]
)
@login_required
def admin_update_campaign_status(campaign_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    new_status = request.form.get(
        "status",
        ""
    ).strip()

    valid_statuses = {
        "Draft",
        "Active",
        "Paused",
        "Completed"
    }

    if new_status not in valid_statuses:

        flash(
            "Invalid campaign status.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_campaign_details",
                campaign_id=campaign_id
            )
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    brand_id,
                    name,
                    status
                FROM campaigns
                WHERE id = %s
            """, (
                campaign_id,
            ))

            campaign = cur.fetchone()

            if not campaign:

                flash(
                    "Campaign was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_campaigns")
                )

            cur.execute("""
                UPDATE campaigns
                SET
                    status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                new_status,
                campaign_id
            ))

        conn.commit()

        log_activity(
            "campaign_status_changed",
            "campaign",
            campaign_id,
            f'Changed campaign "{campaign["name"]}" status from "{campaign["status"]}" to "{new_status}".',
            campaign["brand_id"]
        )

        flash(
            "Campaign status updated successfully.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to update campaign status."
        )

        flash(
            "Unable to update campaign status.",
            "danger"
        )

    finally:

        conn.close()

    return redirect(
        url_for(
            "admin_campaign_details",
            campaign_id=campaign_id
        )
    )


# =========================================================
# ADMIN ADD POST TO CAMPAIGN
# =========================================================

@app.route(
    "/admin/campaigns/<int:campaign_id>/add-post",
    methods=["POST"]
)
@login_required
def admin_add_post_to_campaign(campaign_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    post_id = request.form.get(
        "post_id",
        ""
    ).strip()

    try:

        post_id = int(
            post_id
        )

    except ValueError:

        flash(
            "Invalid post selected.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_campaign_details",
                campaign_id=campaign_id
            )
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # CAMPAIGN
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    brand_id,
                    name
                FROM campaigns
                WHERE id = %s
            """, (
                campaign_id,
            ))

            campaign = cur.fetchone()

            if not campaign:

                flash(
                    "Campaign was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_campaigns")
                )

            # -------------------------------------------------
            # POST
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    brand_id,
                    title
                FROM posts
                WHERE id = %s
            """, (
                post_id,
            ))

            post = cur.fetchone()

            if not post:

                flash(
                    "Post was not found.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_campaign_details",
                        campaign_id=campaign_id
                    )
                )

            if post["brand_id"] != campaign["brand_id"]:

                flash(
                    "A post can only be added to a campaign belonging to the same brand.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_campaign_details",
                        campaign_id=campaign_id
                    )
                )

            # -------------------------------------------------
            # ADD
            # -------------------------------------------------

            cur.execute("""
                INSERT INTO campaign_posts (
                    campaign_id,
                    post_id,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    CURRENT_TIMESTAMP
                )
                ON CONFLICT (
                    campaign_id,
                    post_id
                )
                DO NOTHING
            """, (
                campaign_id,
                post_id
            ))

        conn.commit()

        log_activity(
            "campaign_post_added",
            "campaign",
            campaign_id,
            f'Added post "{post["title"] or "Untitled Post"}" to campaign "{campaign["name"]}".',
            campaign["brand_id"]
        )

        flash(
            "Post added to campaign successfully.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to add post to campaign."
        )

        flash(
            "Unable to add post to campaign.",
            "danger"
        )

    finally:

        conn.close()

    return redirect(
        url_for(
            "admin_campaign_details",
            campaign_id=campaign_id
        )
    )


# =========================================================
# ADMIN REMOVE POST FROM CAMPAIGN
# =========================================================

@app.route(
    "/admin/campaigns/<int:campaign_id>/remove-post/<int:post_id>",
    methods=["POST"]
)
@login_required
def admin_remove_post_from_campaign(
    campaign_id,
    post_id
):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    if current_user.get("role") != "admin":

        flash(
            "Administrator access is required.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    c.id,
                    c.brand_id,
                    c.name
                FROM campaigns c
                WHERE c.id = %s
            """, (
                campaign_id,
            ))

            campaign = cur.fetchone()

            if not campaign:

                flash(
                    "Campaign was not found.",
                    "danger"
                )

                return redirect(
                    url_for("admin_campaigns")
                )

            cur.execute("""
                DELETE FROM campaign_posts
                WHERE campaign_id = %s
                AND post_id = %s
            """, (
                campaign_id,
                post_id
            ))

        conn.commit()

        log_activity(
            "campaign_post_removed",
            "campaign",
            campaign_id,
            f"Removed post #{post_id} from campaign \"{campaign['name']}\".",
            campaign["brand_id"]
        )

        flash(
            "Post removed from campaign.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to remove post from campaign."
        )

        flash(
            "Unable to remove post from campaign.",
            "danger"
        )

    finally:

        conn.close()

    return redirect(
        url_for(
            "admin_campaign_details",
            campaign_id=campaign_id
        )
    )
# =========================================================
# BRANDS
# =========================================================

@app.route("/brands")
@login_required
def brands():

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            query = """
                SELECT
                    b.*,
                    u.name AS creator_name,
                    (
                        SELECT COUNT(*)
                        FROM social_accounts sa
                        WHERE sa.brand_id = b.id
                    ) AS social_accounts_count,
                    (
                        SELECT COUNT(*)
                        FROM posts p
                        WHERE p.brand_id = b.id
                    ) AS posts_count
                FROM brands b
                LEFT JOIN users u
                    ON u.id = b.created_by
                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        b.name ILIKE %s
                        OR b.description ILIKE %s
                    )
                """

                like = f"%{search}%"

                params.extend([
                    like,
                    like
                ])

            if status == "active":

                query += """
                    AND b.is_active = TRUE
                """

            elif status == "inactive":

                query += """
                    AND b.is_active = FALSE
                """

            query += """
                ORDER BY b.created_at DESC
            """

            cur.execute(
                query,
                params
            )

            brand_rows = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
            """)

            total = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = TRUE
            """)

            active = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = FALSE
            """)

            inactive = cur.fetchone()["count"]

        return render_template(
            "brands.html",
            brands=brand_rows,
            total=total,
            active=active,
            inactive=inactive,
            search=search,
            status=status,
        )

    finally:
        conn.close()


@app.route("/brands/create", methods=["GET", "POST"])
@login_required
def create_brand():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        logo_url = request.form.get(
            "logo_url",
            ""
        ).strip()

        website_url = request.form.get(
            "website_url",
            ""
        ).strip()

        if not name:

            flash(
                "Brand name is required.",
                "danger"
            )

            return render_template(
                "brands.html"
            )

        user = get_current_user()

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO brands (
                        name,
                        description,
                        logo_url,
                        website_url,
                        created_by
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    name,
                    description,
                    logo_url or None,
                    website_url or None,
                    user["id"]
                ))

                brand = cur.fetchone()

                cur.execute("""
                    INSERT INTO brand_members (
                        brand_id,
                        user_id,
                        role
                    )
                    VALUES (%s, %s, 'owner')
                    ON CONFLICT DO NOTHING
                """, (
                    brand["id"],
                    user["id"]
                ))

            conn.commit()

            log_activity(
                "created",
                "brand",
                brand["id"],
                f"Created brand: {name}",
                brand["id"]
            )

            flash(
                "Brand created successfully.",
                "success"
            )

            return redirect(
                url_for("brands")
            )

        finally:
            conn.close()

    return render_template(
        "brands.html"
    )


@app.route("/brands/<int:brand_id>")
@login_required
def brand_detail(brand_id):

    brand = get_brand_or_404(
        brand_id
    )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM social_accounts
                WHERE brand_id = %s
                ORDER BY created_at DESC
            """, (brand_id,))

            social_accounts = cur.fetchall()

            cur.execute("""
                SELECT *
                FROM posts
                WHERE brand_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (brand_id,))

            posts = cur.fetchall()

            cur.execute("""
                SELECT *
                FROM brand_members bm
                JOIN users u
                    ON u.id = bm.user_id
                WHERE bm.brand_id = %s
                ORDER BY bm.created_at
            """, (brand_id,))

            members = cur.fetchall()

        return render_template(
            "brand_detail.html",
            brand=brand,
            social_accounts=social_accounts,
            posts=posts,
            members=members,
        )

    finally:
        conn.close()


@app.route(
    "/brands/<int:brand_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_brand(brand_id):

    brand = get_brand_or_404(
        brand_id
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        logo_url = request.form.get(
            "logo_url",
            ""
        ).strip()

        website_url = request.form.get(
            "website_url",
            ""
        ).strip()

        if not name:

            flash(
                "Brand name is required.",
                "danger"
            )

            return render_template(
                "brand_detail.html",
                brand=brand
            )

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    UPDATE brands
                    SET
                        name = %s,
                        description = %s,
                        logo_url = %s,
                        website_url = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    name,
                    description,
                    logo_url or None,
                    website_url or None,
                    brand_id
                ))

            conn.commit()

            log_activity(
                "updated",
                "brand",
                brand_id,
                f"Updated brand: {name}",
                brand_id
            )

            flash(
                "Brand updated successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "brand_detail",
                    brand_id=brand_id
                )
            )

        finally:
            conn.close()

    return render_template(
        "brand_detail.html",
        brand=brand
    )


@app.route(
    "/brands/<int:brand_id>/toggle",
    methods=["POST"]
)
@login_required
def toggle_brand(brand_id):

    brand = get_brand_or_404(
        brand_id
    )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE brands
                SET
                    is_active = NOT is_active,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING is_active
            """, (brand_id,))

            result = cur.fetchone()

        conn.commit()

        state = (
            "activated"
            if result["is_active"]
            else "deactivated"
        )

        log_activity(
            "status_changed",
            "brand",
            brand_id,
            f"Brand {state}",
            brand_id
        )

        flash(
            f"Brand {state} successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("brands")
    )


# =========================================================
# SOCIAL ACCOUNTS
# =========================================================

@app.route("/social-accounts")
@login_required
def social_accounts():

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    platform = request.args.get(
        "platform",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            query = """
                SELECT
                    sa.*,
                    b.name AS brand_name
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                WHERE 1 = 1
            """

            params = []

            if brand_id:

                query += """
                    AND sa.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            if status == "connected":

                query += """
                    AND sa.is_connected = TRUE
                """

            elif status == "disconnected":

                query += """
                    AND sa.is_connected = FALSE
                """

            query += """
                ORDER BY sa.created_at DESC
            """

            cur.execute(
                query,
                params
            )

            accounts = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
            """)

            total = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE is_connected = TRUE
            """)

            connected = cur.fetchone()["count"]

        return render_template(
            "social_accounts.html",
            accounts=accounts,
            brands=brands_list,
            total=total,
            connected=connected,
            brand_id=brand_id,
            platform=platform,
            status=status,
            platforms=SOCIAL_PLATFORMS,
        )

    finally:
        conn.close()


@app.route(
    "/social-accounts/create",
    methods=["GET", "POST"]
)
@login_required
def create_social_account():

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

        if request.method == "POST":

            brand_id = request.form.get(
                "brand_id",
                ""
            ).strip()

            platform = request.form.get(
                "platform",
                ""
            ).strip()

            account_name = request.form.get(
                "account_name",
                ""
            ).strip()

            username = request.form.get(
                "username",
                ""
            ).strip()

            account_id = request.form.get(
                "account_id",
                ""
            ).strip()

            profile_url = request.form.get(
                "profile_url",
                ""
            ).strip()

            if not brand_id or not platform or not account_name:

                flash(
                    "Brand, platform and account name are required.",
                    "danger"
                )

                return render_template(
                    "social_accounts.html",
                    brands=brands_list,
                    platforms=SOCIAL_PLATFORMS,
                    accounts=[],
                    total=0,
                    connected=0,
                )

            if platform not in SOCIAL_PLATFORMS:

                flash(
                    "Invalid social platform.",
                    "danger"
                )

                return redirect(
                    url_for("social_accounts")
                )

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id
                    FROM social_accounts
                    WHERE brand_id = %s
                    AND platform = %s
                    AND (
                        (
                            account_id IS NOT NULL
                            AND account_id <> ''
                            AND account_id = %s
                        )
                        OR
                        (
                            username IS NOT NULL
                            AND username <> ''
                            AND username = %s
                        )
                    )
                """, (
                    brand_id,
                    platform,
                    account_id,
                    username
                ))

                if cur.fetchone():

                    flash(
                        "This social account already exists.",
                        "danger"
                    )

                    return redirect(
                        url_for("social_accounts")
                    )

                cur.execute("""
                    INSERT INTO social_accounts (
                        brand_id,
                        platform,
                        account_name,
                        username,
                        account_id,
                        profile_url
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    brand_id,
                    platform,
                    account_name,
                    username or None,
                    account_id or None,
                    profile_url or None
                ))

                account = cur.fetchone()

            conn.commit()

            log_activity(
                "created",
                "social_account",
                account["id"],
                f"Connected {platform} account: {account_name}",
                int(brand_id)
            )

            flash(
                "Social account added successfully.",
                "success"
            )

            return redirect(
                url_for("social_accounts")
            )

    finally:
        conn.close()

    return render_template(
        "social_accounts.html",
        brands=brands_list,
        platforms=SOCIAL_PLATFORMS,
        accounts=[],
        total=0,
        connected=0,
    )


@app.route(
    "/social-accounts/<int:account_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_social_account(account_id):

    account = get_social_account_or_404(
        account_id
    )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            if request.method == "POST":

                brand_id = request.form.get(
                    "brand_id",
                    ""
                ).strip()

                platform = request.form.get(
                    "platform",
                    ""
                ).strip()

                account_name = request.form.get(
                    "account_name",
                    ""
                ).strip()

                username = request.form.get(
                    "username",
                    ""
                ).strip()

                new_account_id = request.form.get(
                    "account_id",
                    ""
                ).strip()

                profile_url = request.form.get(
                    "profile_url",
                    ""
                ).strip()

                if (
                    not brand_id
                    or not platform
                    or not account_name
                ):

                    flash(
                        "Brand, platform and account name are required.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "edit_social_account",
                            account_id=account_id
                        )
                    )

                cur.execute("""
                    SELECT id
                    FROM social_accounts
                    WHERE brand_id = %s
                    AND platform = %s
                    AND id <> %s
                    AND (
                        (
                            account_id IS NOT NULL
                            AND account_id <> ''
                            AND account_id = %s
                        )
                        OR
                        (
                            username IS NOT NULL
                            AND username <> ''
                            AND username = %s
                        )
                    )
                """, (
                    brand_id,
                    platform,
                    account_id,
                    new_account_id,
                    username
                ))

                if cur.fetchone():

                    flash(
                        "Another account with these details already exists.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "edit_social_account",
                            account_id=account_id
                        )
                    )

                cur.execute("""
                    UPDATE social_accounts
                    SET
                        brand_id = %s,
                        platform = %s,
                        account_name = %s,
                        username = %s,
                        account_id = %s,
                        profile_url = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    brand_id,
                    platform,
                    account_name,
                    username or None,
                    new_account_id or None,
                    profile_url or None,
                    account_id
                ))

            else:

                return render_template(
                    "social_accounts.html",
                    account=account,
                    brands=brands_list,
                    platforms=SOCIAL_PLATFORMS,
                    edit_mode=True
                )

        conn.commit()

        log_activity(
            "updated",
            "social_account",
            account_id,
            f"Updated social account: {account_name}",
            int(brand_id)
        )

        flash(
            "Social account updated successfully.",
            "success"
        )

        return redirect(
            url_for("social_accounts")
        )

    finally:
        conn.close()


@app.route(
    "/social-accounts/<int:account_id>/toggle",
    methods=["POST"]
)
@login_required
def toggle_social_account(account_id):

    account = get_social_account_or_404(
        account_id
    )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE social_accounts
                SET
                    is_connected = NOT is_connected,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING is_connected, brand_id
            """, (account_id,))

            result = cur.fetchone()

        conn.commit()

        state = (
            "connected"
            if result["is_connected"]
            else "disconnected"
        )

        log_activity(
            "status_changed",
            "social_account",
            account_id,
            f"Social account {state}",
            result["brand_id"]
        )

        flash(
            f"Social account {state} successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("social_accounts")
    )


@app.route(
    "/social-accounts/<int:account_id>/delete",
    methods=["POST"]
)
@login_required
def delete_social_account(account_id):

    account = get_social_account_or_404(
        account_id
    )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM social_accounts
                WHERE id = %s
            """, (account_id,))

        conn.commit()

        log_activity(
            "deleted",
            "social_account",
            account_id,
            f"Deleted social account: {account['account_name']}",
            account["brand_id"]
        )

        flash(
            "Social account deleted successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("social_accounts")
    )


# =========================================================
# PUBLISHER
# =========================================================

@app.route("/publisher")
@login_required
def publisher():

    search = request.args.get(
        "search",
        ""
    ).strip()

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    platform = request.args.get(
        "platform",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            query = """
                SELECT
                    p.*,
                    b.name AS brand_name,
                    u.name AS creator_name,
                    COALESCE(
                        STRING_AGG(
                            DISTINCT sa.platform,
                            ', '
                        ),
                        ''
                    ) AS platforms
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                LEFT JOIN users u
                    ON u.id = p.created_by
                LEFT JOIN post_platforms pp
                    ON pp.post_id = p.id
                LEFT JOIN social_accounts sa
                    ON sa.id = pp.social_account_id
                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        p.title ILIKE %s
                        OR p.content ILIKE %s
                    )
                """

                like = f"%{search}%"

                params.extend([
                    like,
                    like
                ])

            if brand_id:

                query += """
                    AND p.brand_id = %s
                """

                params.append(brand_id)

            if status:

                query += """
                    AND p.status = %s
                """

                params.append(status)

            if platform:

                query += """
                    AND EXISTS (
                        SELECT 1
                        FROM post_platforms pp2
                        JOIN social_accounts sa2
                            ON sa2.id = pp2.social_account_id
                        WHERE pp2.post_id = p.id
                        AND sa2.platform = %s
                    )
                """

                params.append(platform)

            query += """
                GROUP BY
                    p.id,
                    b.name,
                    u.name
                ORDER BY
                    COALESCE(
                        p.scheduled_at,
                        p.created_at
                    ) DESC
            """

            cur.execute(
                query,
                params
            )

            posts = cur.fetchall()

            stats = {}

            for item in POST_STATUSES:

                cur.execute("""
                    SELECT COUNT(*) AS count
                    FROM posts
                    WHERE status = %s
                """, (item,))

                stats[item] = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM posts
            """)

            stats["total"] = cur.fetchone()["count"]

        return render_template(
            "publisher.html",
            posts=posts,
            brands=brands_list,
            stats=stats,
            search=search,
            brand_id=brand_id,
            status=status,
            platform=platform,
            platforms=SOCIAL_PLATFORMS,
            post_statuses=POST_STATUSES,
        )

    finally:
        conn.close()


# =========================================================
# CREATE POST
# =========================================================

@app.route(
    "/publisher/create",
    methods=["GET", "POST"]
)
@login_required
def create_post():

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            cur.execute("""
                SELECT
                    sa.*,
                    b.name AS brand_name
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                WHERE sa.is_connected = TRUE
                ORDER BY b.name, sa.platform
            """)

            accounts = cur.fetchall()

            if request.method == "POST":

                brand_id = request.form.get(
                    "brand_id",
                    ""
                ).strip()

                title = request.form.get(
                    "title",
                    ""
                ).strip()

                content = request.form.get(
                    "content",
                    ""
                ).strip()

                media_url = request.form.get(
                    "media_url",
                    ""
                ).strip()

                status = request.form.get(
                    "status",
                    "draft"
                ).strip()

                scheduled_at = request.form.get(
                    "scheduled_at",
                    ""
                ).strip()

                selected_accounts = request.form.getlist(
                    "social_accounts"
                )

                if (
                    not brand_id
                    or not title
                    or not content
                ):

                    flash(
                        "Brand, title and content are required.",
                        "danger"
                    )

                    return render_template(
                        "publisher.html",
                        brands=brands_list,
                        accounts=accounts,
                        platforms=SOCIAL_PLATFORMS,
                        post_statuses=POST_STATUSES,
                        posts=[],
                        stats={"total": 0},
                    )

                if status not in POST_STATUSES:

                    status = "draft"

                parsed_schedule = None

                if scheduled_at:

                    try:

                        parsed_schedule = datetime.fromisoformat(
                            scheduled_at
                        )

                    except ValueError:

                        flash(
                            "Invalid scheduled date/time.",
                            "danger"
                        )

                        return redirect(
                            url_for("create_post")
                        )

                    if parsed_schedule <= datetime.now():

                        flash(
                            "Scheduled time must be in the future.",
                            "danger"
                        )

                        return redirect(
                            url_for("create_post")
                        )

                user = get_current_user()

                cur.execute("""
                    INSERT INTO posts (
                        brand_id,
                        created_by,
                        title,
                        content,
                        media_url,
                        status,
                        scheduled_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    brand_id,
                    user["id"],
                    title,
                    content,
                    media_url or None,
                    status,
                    parsed_schedule
                ))

                post = cur.fetchone()

                for account_id in selected_accounts:

                    cur.execute("""
                        INSERT INTO post_platforms (
                            post_id,
                            social_account_id
                        )
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        post["id"],
                        account_id
                    ))

        conn.commit()

        log_activity(
            "created",
            "post",
            post["id"],
            f"Created post: {title}",
            int(brand_id)
        )

        flash(
            "Post created successfully.",
            "success"
        )

        return redirect(
            url_for("publisher")
        )

    finally:
        conn.close()


# =========================================================
# EDIT POST
# =========================================================

@app.route(
    "/publisher/<int:post_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_post(post_id):

    post = get_post_or_404(
        post_id
    )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            cur.execute("""
                SELECT
                    sa.*,
                    b.name AS brand_name
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                WHERE sa.is_connected = TRUE
                ORDER BY b.name, sa.platform
            """)

            accounts = cur.fetchall()

            cur.execute("""
                SELECT social_account_id
                FROM post_platforms
                WHERE post_id = %s
            """, (post_id,))

            selected_accounts = [
                row["social_account_id"]
                for row in cur.fetchall()
            ]

            if request.method == "POST":

                brand_id = request.form.get(
                    "brand_id",
                    ""
                ).strip()

                title = request.form.get(
                    "title",
                    ""
                ).strip()

                content = request.form.get(
                    "content",
                    ""
                ).strip()

                media_url = request.form.get(
                    "media_url",
                    ""
                ).strip()

                status = request.form.get(
                    "status",
                    post["status"]
                ).strip()

                scheduled_at = request.form.get(
                    "scheduled_at",
                    ""
                ).strip()

                selected_accounts = request.form.getlist(
                    "social_accounts"
                )

                if not title or not content or not brand_id:

                    flash(
                        "Brand, title and content are required.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "edit_post",
                            post_id=post_id
                        )
                    )

                if status not in POST_STATUSES:
                    status = "draft"

                parsed_schedule = None

                if scheduled_at:

                    try:

                        parsed_schedule = datetime.fromisoformat(
                            scheduled_at
                        )

                    except ValueError:

                        flash(
                            "Invalid scheduled date/time.",
                            "danger"
                        )

                        return redirect(
                            url_for(
                                "edit_post",
                                post_id=post_id
                            )
                        )

                cur.execute("""
                    UPDATE posts
                    SET
                        brand_id = %s,
                        title = %s,
                        content = %s,
                        media_url = %s,
                        status = %s,
                        scheduled_at = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    brand_id,
                    title,
                    content,
                    media_url or None,
                    status,
                    parsed_schedule,
                    post_id
                ))

                cur.execute("""
                    DELETE FROM post_platforms
                    WHERE post_id = %s
                """, (post_id,))

                for account_id in selected_accounts:

                    cur.execute("""
                        INSERT INTO post_platforms (
                            post_id,
                            social_account_id
                        )
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        post_id,
                        account_id
                    ))

            else:

                return render_template(
                    "publisher.html",
                    post=post,
                    brands=brands_list,
                    accounts=accounts,
                    selected_accounts=selected_accounts,
                    edit_mode=True,
                    platforms=SOCIAL_PLATFORMS,
                    post_statuses=POST_STATUSES,
                )

        conn.commit()

        log_activity(
            "updated",
            "post",
            post_id,
            f"Updated post: {title}",
            int(brand_id)
        )

        flash(
            "Post updated successfully.",
            "success"
        )

        return redirect(
            url_for("publisher")
        )

    finally:
        conn.close()


# =========================================================
# DELETE POST
# =========================================================

@app.route(
    "/publisher/<int:post_id>/delete",
    methods=["POST"]
)
@login_required
def delete_post(post_id):

    post = get_post_or_404(
        post_id
    )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM posts
                WHERE id = %s
            """, (post_id,))

        conn.commit()

        log_activity(
            "deleted",
            "post",
            post_id,
            f"Deleted post: {post['title']}",
            post["brand_id"]
        )

        flash(
            "Post deleted successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("publisher")
    )


# =========================================================
# UPDATE POST STATUS
# =========================================================

@app.route(
    "/publisher/<int:post_id>/status",
    methods=["POST"]
)
@login_required
def update_post_status(post_id):

    post = get_post_or_404(
        post_id
    )

    new_status = request.form.get(
        "status",
        ""
    ).strip()

    if new_status not in POST_STATUSES:

        flash(
            "Invalid post status.",
            "danger"
        )

        return redirect(
            request.referrer
            or url_for("publisher")
        )

    scheduled_at = post["scheduled_at"]
    published_at = post["published_at"]

    if new_status == "scheduled":

        if not scheduled_at:

            flash(
                "A scheduled date and time is required.",
                "danger"
            )

            return redirect(
                request.referrer
                or url_for("publisher")
            )

    if new_status == "published":

        published_at = datetime.now()

    elif new_status != "published":

        published_at = None

    if new_status not in (
        "scheduled",
        "published"
    ):

        scheduled_at = None

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE posts
                SET
                    status = %s,
                    scheduled_at = %s,
                    published_at = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                new_status,
                scheduled_at,
                published_at,
                post_id
            ))

        conn.commit()

        log_activity(
            "status_changed",
            "post",
            post_id,
            f"Post status changed to {new_status}",
            post["brand_id"]
        )

        flash(
            "Post status updated successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("publisher")
    )


# =========================================================
# PUBLISHER POST DETAILS
# =========================================================

@app.route(
    "/publisher/<int:post_id>/details"
)
@login_required
def publisher_post_details(post_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    p.*,
                    b.name AS brand_name,
                    u.name AS creator_name
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                LEFT JOIN users u
                    ON u.id = p.created_by
                WHERE p.id = %s
            """, (post_id,))

            post = cur.fetchone()

            if not post:
                return jsonify({
                    "error": "Post not found"
                }), 404

            cur.execute("""
                SELECT
                    pp.*,
                    sa.platform,
                    sa.account_name,
                    sa.username
                FROM post_platforms pp
                JOIN social_accounts sa
                    ON sa.id = pp.social_account_id
                WHERE pp.post_id = %s
                ORDER BY sa.platform
            """, (post_id,))

            platforms = cur.fetchall()

        return jsonify({
            "post": post,
            "platforms": platforms,
        })

    finally:
        conn.close()


# =========================================================
# SUBMIT POST FOR APPROVAL
# =========================================================

@app.route(
    "/publisher/<int:post_id>/submit-approval",
    methods=["POST"]
)
@login_required
def submit_post_for_approval(post_id):

    post = get_post_or_404(
        post_id
    )

    user = get_current_user()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id
                FROM content_approvals
                WHERE post_id = %s
                AND status = 'pending'
                LIMIT 1
            """, (post_id,))

            existing = cur.fetchone()

            if existing:

                flash(
                    "This post is already waiting for approval.",
                    "warning"
                )

                return redirect(
                    url_for("publisher")
                )

            cur.execute("""
                INSERT INTO content_approvals (
                    post_id,
                    submitted_by,
                    status,
                    created_at
                )
                VALUES (%s, %s, 'pending', CURRENT_TIMESTAMP)
            """, (
                post_id,
                user["id"]
            ))

            cur.execute("""
                UPDATE posts
                SET
                    status = 'pending_approval',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (post_id,))

            cur.execute("""
                SELECT id
                FROM users
                WHERE role = 'admin'
                AND is_active = TRUE
            """)

            admins = cur.fetchall()

            for admin in admins:

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        'approval'
                    )
                """, (
                    admin["id"],
                    "Content approval requested",
                    f"Post '{post['title']}' is waiting for approval."
                ))

        conn.commit()

        log_activity(
            "submitted_for_approval",
            "post",
            post_id,
            f"Submitted post for approval: {post['title']}",
            post["brand_id"]
        )

        flash(
            "Post submitted for approval.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("publisher")
    )


# =========================================================
# APPROVALS
# =========================================================

@app.route("/approvals")
@login_required
def approvals():

    search = request.args.get(
        "search",
        ""
    ).strip()

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            query = """
                SELECT
                    ca.*,
                    p.title,
                    p.content,
                    p.status AS post_status,
                    p.brand_id,
                    b.name AS brand_name,
                    submitter.name AS submitted_by_name,
                    reviewer.name AS reviewer_name
                FROM content_approvals ca
                JOIN posts p
                    ON p.id = ca.post_id
                JOIN brands b
                    ON b.id = p.brand_id
                LEFT JOIN users submitter
                    ON submitter.id = ca.submitted_by
                LEFT JOIN users reviewer
                    ON reviewer.id = ca.reviewer_id
                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        p.title ILIKE %s
                        OR p.content ILIKE %s
                        OR b.name ILIKE %s
                    )
                """

                like = f"%{search}%"

                params.extend([
                    like,
                    like,
                    like
                ])

            if brand_id:

                query += """
                    AND p.brand_id = %s
                """

                params.append(brand_id)

            if status:

                query += """
                    AND ca.status = %s
                """

                params.append(status)

            query += """
                ORDER BY ca.created_at DESC
            """

            cur.execute(
                query,
                params
            )

            approval_rows = cur.fetchall()

            counts = {}

            for item in [
                "pending",
                "approved",
                "rejected"
            ]:

                cur.execute("""
                    SELECT COUNT(*) AS count
                    FROM content_approvals
                    WHERE status = %s
                """, (item,))

                counts[item] = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM content_approvals
            """)

            counts["total"] = cur.fetchone()["count"]

        return render_template(
            "approvals.html",
            approvals=approval_rows,
            brands=brands_list,
            counts=counts,
            search=search,
            brand_id=brand_id,
            status=status,
        )

    finally:
        conn.close()


@app.route(
    "/approvals/<int:approval_id>/approve",
    methods=["POST"]
)
@login_required
def approve_content(approval_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    ca.*,
                    p.title,
                    p.brand_id,
                    p.created_by
                FROM content_approvals ca
                JOIN posts p
                    ON p.id = ca.post_id
                WHERE ca.id = %s
            """, (approval_id,))

            approval = cur.fetchone()

            if not approval:

                flash(
                    "Approval request not found.",
                    "danger"
                )

                return redirect(
                    url_for("approvals")
                )

            if approval["status"] != "pending":

                flash(
                    "This approval request has already been reviewed.",
                    "warning"
                )

                return redirect(
                    url_for("approvals")
                )

            user = get_current_user()

            cur.execute("""
                UPDATE content_approvals
                SET
                    status = 'approved',
                    reviewer_id = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                user["id"],
                approval_id
            ))

            cur.execute("""
                UPDATE posts
                SET
                    status = 'approved',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                approval["post_id"],
            ))

            if approval["created_by"]:

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        'approval'
                    )
                """, (
                    approval["created_by"],
                    "Content approved",
                    f"Your post '{approval['title']}' has been approved."
                ))

        conn.commit()

        log_activity(
            "approved",
            "content_approval",
            approval_id,
            f"Approved post: {approval['title']}",
            approval["brand_id"]
        )

        flash(
            "Content approved successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("approvals")
    )


@app.route(
    "/approvals/<int:approval_id>/reject",
    methods=["POST"]
)
@login_required
def reject_content(approval_id):

    comments = request.form.get(
        "comments",
        ""
    ).strip()

    if len(comments) > 5000:

        flash(
            "Feedback cannot exceed 5000 characters.",
            "danger"
        )

        return redirect(
            url_for("approvals")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    ca.*,
                    p.title,
                    p.brand_id,
                    p.created_by
                FROM content_approvals ca
                JOIN posts p
                    ON p.id = ca.post_id
                WHERE ca.id = %s
            """, (approval_id,))

            approval = cur.fetchone()

            if not approval:

                flash(
                    "Approval request not found.",
                    "danger"
                )

                return redirect(
                    url_for("approvals")
                )

            if approval["status"] != "pending":

                flash(
                    "This approval request has already been reviewed.",
                    "warning"
                )

                return redirect(
                    url_for("approvals")
                )

            user = get_current_user()

            cur.execute("""
                UPDATE content_approvals
                SET
                    status = 'rejected',
                    reviewer_id = %s,
                    comments = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                user["id"],
                comments or None,
                approval_id
            ))

            cur.execute("""
                UPDATE posts
                SET
                    status = 'rejected',
                    scheduled_at = NULL,
                    published_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                approval["post_id"],
            ))

            if approval["created_by"]:

                message = (
                    f"Your post '{approval['title']}' was rejected."
                )

                if comments:
                    message += f" Feedback: {comments}"

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        'approval'
                    )
                """, (
                    approval["created_by"],
                    "Content rejected",
                    message
                ))

        conn.commit()

        log_activity(
            "rejected",
            "content_approval",
            approval_id,
            f"Rejected post: {approval['title']}",
            approval["brand_id"]
        )

        flash(
            "Content rejected successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("approvals")
    )


# =========================================================
# CALENDAR
# =========================================================

@app.route("/calendar")
@login_required
def calendar():

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            query = """
                SELECT
                    p.*,
                    b.name AS brand_name,
                    u.name AS creator_name,
                    COALESCE(
                        STRING_AGG(
                            DISTINCT sa.platform,
                            ', '
                        ),
                        ''
                    ) AS platforms
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                LEFT JOIN users u
                    ON u.id = p.created_by
                LEFT JOIN post_platforms pp
                    ON pp.post_id = p.id
                LEFT JOIN social_accounts sa
                    ON sa.id = pp.social_account_id
                WHERE 1 = 1
            """

            params = []

            if brand_id:

                query += """
                    AND p.brand_id = %s
                """

                params.append(brand_id)

            if status:

                query += """
                    AND p.status = %s
                """

                params.append(status)

            query += """
                GROUP BY
                    p.id,
                    b.name,
                    u.name
                ORDER BY
                    COALESCE(
                        p.scheduled_at,
                        p.created_at
                    )
            """

            cur.execute(
                query,
                params
            )

            posts = cur.fetchall()

            calendar_stats = {}

            for key, value in [
                ("total", None),
                ("draft", "draft"),
                ("scheduled", "scheduled"),
                ("published", "published"),
            ]:

                if value:

                    cur.execute("""
                        SELECT COUNT(*) AS count
                        FROM posts
                        WHERE status = %s
                    """, (value,))

                else:

                    cur.execute("""
                        SELECT COUNT(*) AS count
                        FROM posts
                    """)

                calendar_stats[key] = cur.fetchone()["count"]

            cur.execute("""
                SELECT
                    p.*,
                    b.name AS brand_name
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                WHERE p.status = 'scheduled'
                AND p.scheduled_at >= CURRENT_TIMESTAMP
                ORDER BY p.scheduled_at
                LIMIT 10
            """)

            upcoming = cur.fetchall()

        return render_template(
            "calendar.html",
            posts=posts,
            brands=brands_list,
            stats=calendar_stats,
            upcoming=upcoming,
            brand_id=brand_id,
            status=status,
            post_statuses=POST_STATUSES,
        )

    finally:
        conn.close()


# =========================================================
# COMMUNITY
# =========================================================

@app.route("/community")
@login_required
def community():

    search = request.args.get(
        "search",
        ""
    ).strip()

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    platform = request.args.get(
        "platform",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            query = """
                SELECT
                    cc.*,
                    b.name AS brand_name,
                    sa.platform,
                    sa.account_name
                FROM community_comments cc
                JOIN brands b
                    ON b.id = cc.brand_id
                LEFT JOIN social_accounts sa
                    ON sa.id = cc.social_account_id
                WHERE 1 = 1
            """

            params = []

            if search:

                query += """
                    AND (
                        cc.content ILIKE %s
                        OR cc.author_name ILIKE %s
                        OR cc.author_username ILIKE %s
                    )
                """

                like = f"%{search}%"

                params.extend([
                    like,
                    like,
                    like
                ])

            if brand_id:

                query += """
                    AND cc.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            if status:

                query += """
                    AND cc.status = %s
                """

                params.append(status)

            query += """
                ORDER BY cc.created_at DESC
                LIMIT 200
            """

            cur.execute(
                query,
                params
            )

            comments = cur.fetchall()

            counts = {}

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
            """)

            counts["total"] = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE status = 'pending'
            """)

            counts["pending"] = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE status = 'unread'
            """)

            counts["unread"] = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE status = 'resolved'
            """)

            counts["resolved"] = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE status = 'replied'
            """)

            counts["replied"] = cur.fetchone()["count"]

        return render_template(
            "community.html",
            comments=comments,
            brands=brands_list,
            counts=counts,
            search=search,
            brand_id=brand_id,
            platform=platform,
            status=status,
            platforms=SOCIAL_PLATFORMS,
        )

    finally:
        conn.close()


@app.route(
    "/community/<int:comment_id>/reply",
    methods=["POST"]
)
@login_required
def reply_community_comment(comment_id):

    reply = request.form.get(
        "reply",
        ""
    ).strip()

    if not reply:

        flash(
            "Reply cannot be empty.",
            "danger"
        )

        return redirect(
            url_for("community")
        )

    if len(reply) > 5000:

        flash(
            "Reply cannot exceed 5000 characters.",
            "danger"
        )

        return redirect(
            url_for("community")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM community_comments
                WHERE id = %s
            """, (comment_id,))

            comment = cur.fetchone()

            if not comment:

                flash(
                    "Comment not found.",
                    "danger"
                )

                return redirect(
                    url_for("community")
                )

            cur.execute("""
                UPDATE community_comments
                SET
                    reply = %s,
                    replied_at = CURRENT_TIMESTAMP,
                    status = 'replied'
                WHERE id = %s
            """, (
                reply,
                comment_id
            ))

        conn.commit()

        log_activity(
            "replied",
            "community_comment",
            comment_id,
            "Replied to community comment.",
            comment["brand_id"]
        )

        flash(
            "Reply saved successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("community")
    )


@app.route(
    "/community/<int:comment_id>/resolve",
    methods=["POST"]
)
@login_required
def resolve_community_comment(comment_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE community_comments
                SET status = 'resolved'
                WHERE id = %s
                RETURNING brand_id
            """, (comment_id,))

            comment = cur.fetchone()

            if not comment:

                flash(
                    "Comment not found.",
                    "danger"
                )

                return redirect(
                    url_for("community")
                )

        conn.commit()

        log_activity(
            "resolved",
            "community_comment",
            comment_id,
            "Resolved community comment.",
            comment["brand_id"]
        )

        flash(
            "Comment marked as resolved.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("community")
    )

# =========================================================
# TEAM & RESPONSIBILITIES
# =========================================================

@app.route("/team")
@login_required
def team():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # FIND BRANDS AVAILABLE TO CURRENT USER
            # -------------------------------------------------

            if current_user.get("role") == "admin":

                cur.execute("""
                    SELECT
                        id,
                        name,
                        description,
                        created_by,
                        is_active,
                        created_at
                    FROM brands
                    WHERE is_active = TRUE
                    ORDER BY name ASC
                """)

            else:

                cur.execute("""
                    SELECT DISTINCT
                        b.id,
                        b.name,
                        b.description,
                        b.created_by,
                        b.is_active,
                        b.created_at
                    FROM brands b
                    LEFT JOIN brand_members bm
                        ON bm.brand_id = b.id
                        AND bm.user_id = %s
                    WHERE b.is_active = TRUE
                    AND (
                        b.created_by = %s
                        OR bm.user_id = %s
                    )
                    ORDER BY b.name ASC
                """, (
                    current_user["id"],
                    current_user["id"],
                    current_user["id"]
                ))

            brands = cur.fetchall()

            # -------------------------------------------------
            # SELECT CURRENT BRAND
            # -------------------------------------------------

            selected_brand_id = request.args.get(
                "brand_id",
                type=int
            )

            if selected_brand_id:

                selected_brand = next(
                    (
                        brand
                        for brand in brands
                        if brand["id"] == selected_brand_id
                    ),
                    None
                )

            else:

                selected_brand = (
                    brands[0]
                    if brands
                    else None
                )

            # -------------------------------------------------
            # AVAILABLE USERS
            # -------------------------------------------------

            available_users = []

            if selected_brand:

                cur.execute("""
                    SELECT
                        u.id,
                        u.name,
                        u.email
                    FROM users u
                    WHERE u.role <> 'admin'
                    AND u.is_active = TRUE
                    AND u.id <> %s
                    AND NOT EXISTS (
                        SELECT 1
                        FROM brand_members bm
                        WHERE bm.brand_id = %s
                        AND bm.user_id = u.id
                    )
                    AND u.id <> %s
                    ORDER BY u.name ASC
                """, (
                    selected_brand["created_by"],
                    selected_brand["id"],
                    selected_brand["created_by"]
                ))

                available_users = cur.fetchall()

            # -------------------------------------------------
            # TEAM MEMBERS
            # -------------------------------------------------

            team_members = []

            if selected_brand:

                cur.execute("""
                    SELECT
                        bm.id AS membership_id,
                        bm.brand_id,
                        bm.user_id,
                        bm.role,
                        bm.created_at,

                        u.name,
                        u.email,
                        u.is_active,
                        u.created_at AS user_created_at,

                        (
                            SELECT COUNT(*)
                            FROM posts p
                            WHERE p.created_by = u.id
                            AND p.brand_id = bm.brand_id
                        ) AS post_count

                    FROM brand_members bm

                    INNER JOIN users u
                        ON u.id = bm.user_id

                    WHERE bm.brand_id = %s

                    ORDER BY
                        CASE bm.role
                            WHEN 'owner' THEN 1
                            WHEN 'manager' THEN 2
                            WHEN 'publisher' THEN 3
                            WHEN 'analyst' THEN 4
                            WHEN 'member' THEN 5
                            ELSE 6
                        END,
                        u.name ASC
                """, (
                    selected_brand["id"],
                ))

                team_members = cur.fetchall()

                # -------------------------------------------------
                # LOAD RESPONSIBILITIES
                # -------------------------------------------------

                for member in team_members:

                    cur.execute("""
                        SELECT responsibility_key
                        FROM brand_member_responsibilities
                        WHERE brand_member_id = %s
                        ORDER BY responsibility_key ASC
                    """, (
                        member["membership_id"],
                    ))

                    responsibility_rows = cur.fetchall()

                    member["responsibilities"] = [
                        row["responsibility_key"]
                        for row in responsibility_rows
                    ]

                    member["is_owner"] = (
                        member["user_id"]
                        == selected_brand["created_by"]
                        or member["role"] == "owner"
                    )

                # -------------------------------------------------
                # INCLUDE BRAND OWNER IF NOT IN brand_members
                # -------------------------------------------------

                cur.execute("""
                    SELECT
                        u.id,
                        u.name,
                        u.email,
                        u.is_active,
                        u.created_at
                    FROM users u
                    INNER JOIN brands b
                        ON b.created_by = u.id
                    WHERE b.id = %s
                """, (
                    selected_brand["id"],
                ))

                brand_owner = cur.fetchone()

                if brand_owner:

                    owner_exists = any(
                        member["user_id"]
                        == brand_owner["id"]
                        for member in team_members
                    )

                    if not owner_exists:

                        team_members.insert(
                            0,
                            {
                                "membership_id": None,
                                "brand_id": selected_brand["id"],
                                "user_id": brand_owner["id"],
                                "role": "owner",
                                "created_at": selected_brand.get(
                                    "created_at"
                                ),
                                "name": brand_owner["name"],
                                "email": brand_owner["email"],
                                "is_active": brand_owner["is_active"],
                                "user_created_at": brand_owner["created_at"],
                                "post_count": 0,
                                "responsibilities": [],
                                "is_owner": True
                            }
                        )

            # -------------------------------------------------
            # TEAM STATISTICS
            # -------------------------------------------------

            total_members = len(team_members)

            manager_count = sum(
                1
                for member in team_members
                if member["role"] == "manager"
            )

            publisher_count = sum(
                1
                for member in team_members
                if member["role"] == "publisher"
            )

            analyst_count = sum(
                1
                for member in team_members
                if member["role"] == "analyst"
            )

            active_members = sum(
                1
                for member in team_members
                if member["is_active"]
            )

        return render_template(
            "team.html",

            current_user=current_user,

            brands=brands,
            selected_brand=selected_brand,

            team_members=team_members,
            available_users=available_users,

            total_members=total_members,
            active_members=active_members,
            manager_count=manager_count,
            publisher_count=publisher_count,
            analyst_count=analyst_count
        )

    except Exception:

        app.logger.exception(
            "Failed to load Team & Responsibilities page."
        )

        flash(
            "Unable to load team management right now.",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    finally:

        conn.close()

# =========================================================
# ADD TEAM MEMBER
# =========================================================

@app.route("/team/add", methods=["POST"])
@login_required
def add_team_member():

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    brand_id = request.form.get("brand_id", type=int)
    user_id = request.form.get("user_id", type=int)
    role = (request.form.get("role") or "").strip().lower()

    allowed_roles = {
        "manager",
        "publisher",
        "analyst",
        "member"
    }

    if not brand_id or not user_id:
        flash("Please select a brand and team member.", "danger")
        return redirect(url_for("team"))

    if role not in allowed_roles:
        flash("Invalid team role selected.", "danger")
        return redirect(
            url_for("team", brand_id=brand_id)
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # BRAND
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name,
                    created_by,
                    is_active
                FROM brands
                WHERE id = %s
            """, (brand_id,))

            brand = cur.fetchone()

            if not brand:
                flash("Brand workspace was not found.", "danger")
                return redirect(url_for("team"))

            if not brand["is_active"]:
                flash(
                    "This brand workspace is currently inactive.",
                    "danger"
                )
                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # CURRENT USER BRAND PERMISSION
            # -------------------------------------------------

            if current_user.get("role") == "admin":

                manager_access = True
                owner_access = True

            elif brand["created_by"] == current_user["id"]:

                manager_access = True
                owner_access = True

            else:

                cur.execute("""
                    SELECT role
                    FROM brand_members
                    WHERE brand_id = %s
                    AND user_id = %s
                    LIMIT 1
                """, (
                    brand_id,
                    current_user["id"]
                ))

                current_membership = cur.fetchone()

                if not current_membership:
                    flash(
                        "You do not have permission to manage this team.",
                        "danger"
                    )
                    return redirect(
                        url_for("team", brand_id=brand_id)
                    )

                current_role = current_membership["role"]

                owner_access = current_role == "owner"
                manager_access = current_role in {
                    "owner",
                    "manager"
                }

            # -------------------------------------------------
            # MANAGER RESTRICTION
            # -------------------------------------------------

            if not owner_access and role == "manager":

                flash(
                    "Only the brand owner or administrator can assign "
                    "the Manager role.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            if not manager_access:

                flash(
                    "You do not have permission to add team members.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # USER
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active
                FROM users
                WHERE id = %s
            """, (user_id,))

            member_user = cur.fetchone()

            if not member_user:

                flash(
                    "Selected user was not found.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # NEVER ADD ADMIN AS BRAND TEAM MEMBER
            # -------------------------------------------------

            if member_user["role"] == "admin":

                flash(
                    "Administrator accounts cannot be added as "
                    "brand team members.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # ACTIVE USER CHECK
            # -------------------------------------------------

            if not member_user["is_active"]:

                flash(
                    "This user account is currently inactive.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # PREVENT DUPLICATE MEMBERSHIP
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    role
                FROM brand_members
                WHERE brand_id = %s
                AND user_id = %s
                LIMIT 1
            """, (
                brand_id,
                user_id
            ))

            existing_membership = cur.fetchone()

            if existing_membership:

                flash(
                    "This user is already a member of this brand.",
                    "warning"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # BRAND OWNER PROTECTION
            # -------------------------------------------------

            if brand["created_by"] == user_id:

                flash(
                    "The brand owner already has ownership access.",
                    "warning"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # INSERT MEMBERSHIP
            # -------------------------------------------------

            cur.execute("""
                INSERT INTO brand_members (
                    brand_id,
                    user_id,
                    role,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    CURRENT_TIMESTAMP
                )
            """, (
                brand_id,
                user_id,
                role
            ))

            # -------------------------------------------------
            # NOTIFICATION
            # -------------------------------------------------

            cur.execute("""
                INSERT INTO notifications (
                    user_id,
                    title,
                    message,
                    notification_type
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'team'
                )
            """, (
                user_id,
                "Added to a brand team",
                f"You have been added to the '{brand['name']}' "
                f"team as {role.capitalize()}."
            ))

        conn.commit()

        # -----------------------------------------------------
        # ACTIVITY LOG
        # -----------------------------------------------------

        log_activity(
            "team_member_added",
            "brand_member",
            user_id,
            (
                f"Added {member_user['name']} to "
                f"{brand['name']} as {role.capitalize()}."
            ),
            brand_id
        )

        flash(
            f"{member_user['name']} was added to the team "
            f"as {role.capitalize()}.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to add team member."
        )

        flash(
            "Unable to add the team member right now.",
            "danger"
        )

    finally:
        conn.close()

    return redirect(
        url_for("team", brand_id=brand_id)
    )
# =========================================================
# GET TEAM MEMBER RESPONSIBILITIES
# =========================================================

@app.route("/team/<int:member_id>/responsibilities")
@login_required
def team_member_responsibilities(member_id):

    current_user = get_current_user()

    if not current_user:
        return jsonify({
            "error": "Authentication required"
        }), 401

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # VERIFY TEAM MEMBER
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    bm.id AS membership_id,
                    bm.brand_id,
                    bm.user_id,
                    bm.role,
                    b.name AS brand_name,
                    b.created_by AS brand_owner_id
                FROM brand_members bm
                INNER JOIN brands b
                    ON b.id = bm.brand_id
                WHERE bm.id = %s
                LIMIT 1
            """, (
                member_id,
            ))

            member = cur.fetchone()

            if not member:

                return jsonify({
                    "error": "Team member not found."
                }), 404


            # -------------------------------------------------
            # CHECK ACCESS
            # -------------------------------------------------

            if current_user.get("role") == "admin":

                has_access = True

            elif member["brand_owner_id"] == current_user["id"]:

                has_access = True

            else:

                cur.execute("""
                    SELECT role
                    FROM brand_members
                    WHERE brand_id = %s
                    AND user_id = %s
                    LIMIT 1
                """, (
                    member["brand_id"],
                    current_user["id"]
                ))

                current_membership = cur.fetchone()

                has_access = (
                    current_membership
                    and current_membership["role"]
                    in {"owner", "manager"}
                )


            if not has_access:

                return jsonify({
                    "error": "You do not have permission to view responsibilities."
                }), 403


            # -------------------------------------------------
            # LOAD RESPONSIBILITIES
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    responsibility_key
                FROM brand_member_responsibilities
                WHERE brand_member_id = %s
                ORDER BY responsibility_key ASC
            """, (
                member_id,
            ))

            rows = cur.fetchall()


            responsibilities = [
                row["responsibility_key"]
                for row in rows
            ]


        return jsonify({
            "member_id": member_id,
            "responsibilities": responsibilities
        })


    except Exception:

        app.logger.exception(
            "Failed to load team member responsibilities."
        )

        return jsonify({
            "error": "Unable to load responsibilities."
        }), 500


    finally:

        conn.close()
# =========================================================
# TEAM MEMBER — UPDATE ROLE & RESPONSIBILITIES
# =========================================================

@app.route("/team/<int:member_id>/update", methods=["POST"])
@login_required
def update_team_member(member_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    new_role = (request.form.get("role") or "").strip().lower()
    brand_id = request.form.get("brand_id", type=int)

    allowed_roles = {
        "manager",
        "publisher",
        "analyst",
        "member"
    }

    allowed_responsibilities = {
        "content_creation",
        "content_scheduling",
        "content_approval",
        "analytics",
        "reporting",
        "community_management",
        "social_accounts",
        "team_management",
        "campaign_management"
    }

    selected_responsibilities = request.form.getlist(
        "responsibilities"
    )

    selected_responsibilities = [
        item.strip().lower()
        for item in selected_responsibilities
        if item.strip().lower() in allowed_responsibilities
    ]

    if not brand_id:
        flash("Brand information is required.", "danger")
        return redirect(url_for("team"))

    if new_role not in allowed_roles:
        flash("Invalid team role selected.", "danger")
        return redirect(url_for("team", brand_id=brand_id))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # BRAND
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name,
                    created_by,
                    is_active
                FROM brands
                WHERE id = %s
            """, (brand_id,))

            brand = cur.fetchone()

            if not brand:
                flash("Brand not found.", "danger")
                return redirect(url_for("team"))

            if not brand["is_active"]:
                flash("This brand is currently inactive.", "danger")
                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # CURRENT USER PERMISSION
            # -------------------------------------------------

            if current_user.get("role") == "admin":

                manager_access = True
                owner_access = True

            elif brand["created_by"] == current_user["id"]:

                manager_access = True
                owner_access = True

            else:

                cur.execute("""
                    SELECT role
                    FROM brand_members
                    WHERE brand_id = %s
                    AND user_id = %s
                    LIMIT 1
                """, (
                    brand_id,
                    current_user["id"]
                ))

                current_membership = cur.fetchone()

                if not current_membership:
                    flash(
                        "You do not have permission to manage this team.",
                        "danger"
                    )
                    return redirect(
                        url_for("team", brand_id=brand_id)
                    )

                current_role = current_membership["role"]

                owner_access = current_role == "owner"

                manager_access = current_role in {
                    "owner",
                    "manager"
                }

            if not manager_access:

                flash(
                    "You do not have permission to update team members.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # MEMBER
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    bm.id,
                    bm.brand_id,
                    bm.user_id,
                    bm.role,
                    u.name,
                    u.email,
                    u.role AS system_role,
                    u.is_active
                FROM brand_members bm
                INNER JOIN users u
                    ON u.id = bm.user_id
                WHERE bm.id = %s
                AND bm.brand_id = %s
                LIMIT 1
            """, (
                member_id,
                brand_id
            ))

            member = cur.fetchone()

            if not member:

                flash(
                    "Team member was not found.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # ADMIN PROTECTION
            # -------------------------------------------------

            if member["system_role"] == "admin":

                flash(
                    "Administrator accounts cannot be managed from a brand team.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # BRAND OWNER PROTECTION
            # -------------------------------------------------

            if member["user_id"] == brand["created_by"]:

                flash(
                    "The brand owner cannot be changed from this screen.",
                    "warning"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # MANAGER RESTRICTION
            # -------------------------------------------------

            if not owner_access and new_role == "manager":

                flash(
                    "Only the brand owner can assign the Manager role.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # UPDATE ROLE
            # -------------------------------------------------

            cur.execute("""
                UPDATE brand_members
                SET role = %s
                WHERE id = %s
                AND brand_id = %s
            """, (
                new_role,
                member_id,
                brand_id
            ))

            # -------------------------------------------------
            # REPLACE RESPONSIBILITIES
            # -------------------------------------------------

            cur.execute("""
                DELETE FROM brand_member_responsibilities
                WHERE brand_member_id = %s
            """, (member_id,))

            for responsibility in selected_responsibilities:

                cur.execute("""
                    INSERT INTO brand_member_responsibilities (
                        brand_member_id,
                        responsibility_key,
                        created_at
                    )
                    VALUES (
                        %s,
                        %s,
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (
                        brand_member_id,
                        responsibility_key
                    )
                    DO NOTHING
                """, (
                    member_id,
                    responsibility
                ))

            # -------------------------------------------------
            # NOTIFICATION
            # -------------------------------------------------

            responsibility_count = len(
                selected_responsibilities
            )

            cur.execute("""
                INSERT INTO notifications (
                    user_id,
                    title,
                    message,
                    notification_type
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'team'
                )
            """, (
                member["user_id"],
                "Team role updated",
                (
                    f"Your role for '{brand['name']}' "
                    f"has been updated to "
                    f"{new_role.capitalize()} with "
                    f"{responsibility_count} responsibility"
                    f"{'' if responsibility_count == 1 else 'ies'}."
                )
            ))

        conn.commit()

        # -----------------------------------------------------
        # ACTIVITY LOG
        # -----------------------------------------------------

        log_activity(
            "team_member_updated",
            "brand_member",
            member_id,
            (
                f"Updated {member['name']} "
                f"to {new_role.capitalize()} "
                f"with {len(selected_responsibilities)} "
                f"responsibilities."
            ),
            brand_id
        )

        flash(
            f"{member['name']}'s role and responsibilities were updated.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to update team member."
        )

        flash(
            "Unable to update the team member right now.",
            "danger"
        )

    finally:

        conn.close()

    return redirect(
        url_for(
            "team",
            brand_id=brand_id
        )
    )


# =========================================================
# TEAM MEMBER — REMOVE
# =========================================================

@app.route("/team/<int:member_id>/remove", methods=["POST"])
@login_required
def remove_team_member(member_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(url_for("login"))

    brand_id = request.form.get("brand_id", type=int)

    if not brand_id:
        flash("Brand information is required.", "danger")
        return redirect(url_for("team"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # BRAND
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name,
                    created_by,
                    is_active
                FROM brands
                WHERE id = %s
            """, (brand_id,))

            brand = cur.fetchone()

            if not brand:
                flash("Brand not found.", "danger")
                return redirect(url_for("team"))

            # -------------------------------------------------
            # CURRENT USER PERMISSION
            # -------------------------------------------------

            if current_user.get("role") == "admin":

                manager_access = True

            elif brand["created_by"] == current_user["id"]:

                manager_access = True

            else:

                cur.execute("""
                    SELECT role
                    FROM brand_members
                    WHERE brand_id = %s
                    AND user_id = %s
                    LIMIT 1
                """, (
                    brand_id,
                    current_user["id"]
                ))

                current_membership = cur.fetchone()

                manager_access = (
                    current_membership
                    and current_membership["role"]
                    in {"owner", "manager"}
                )

            if not manager_access:

                flash(
                    "You do not have permission to remove team members.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # MEMBER
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    bm.id,
                    bm.user_id,
                    bm.role,
                    u.name,
                    u.email,
                    u.role AS system_role
                FROM brand_members bm
                INNER JOIN users u
                    ON u.id = bm.user_id
                WHERE bm.id = %s
                AND bm.brand_id = %s
                LIMIT 1
            """, (
                member_id,
                brand_id
            ))

            member = cur.fetchone()

            if not member:

                flash(
                    "Team member was not found.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # PROTECTION
            # -------------------------------------------------

            if member["system_role"] == "admin":

                flash(
                    "Administrator accounts cannot be removed from a brand team.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            if member["user_id"] == brand["created_by"]:

                flash(
                    "The brand owner cannot be removed from the team.",
                    "danger"
                )

                return redirect(
                    url_for("team", brand_id=brand_id)
                )

            # -------------------------------------------------
            # MANAGER CANNOT REMOVE MANAGER
            # -------------------------------------------------

            if current_user.get("role") != "admin":

                cur.execute("""
                    SELECT role
                    FROM brand_members
                    WHERE brand_id = %s
                    AND user_id = %s
                    LIMIT 1
                """, (
                    brand_id,
                    current_user["id"]
                ))

                current_membership = cur.fetchone()

                if (
                    current_membership
                    and current_membership["role"] == "manager"
                    and member["role"] == "manager"
                ):

                    flash(
                        "Managers cannot remove another Manager.",
                        "danger"
                    )

                    return redirect(
                        url_for("team", brand_id=brand_id)
                    )

            # -------------------------------------------------
            # REMOVE MEMBER
            # -------------------------------------------------

            cur.execute("""
                DELETE FROM brand_members
                WHERE id = %s
                AND brand_id = %s
            """, (
                member_id,
                brand_id
            ))

            # -------------------------------------------------
            # NOTIFICATION
            # -------------------------------------------------

            cur.execute("""
                INSERT INTO notifications (
                    user_id,
                    title,
                    message,
                    notification_type
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    'team'
                )
            """, (
                member["user_id"],
                "Removed from brand team",
                f"You have been removed from the '{brand['name']}' team."
            ))

        conn.commit()

        # -----------------------------------------------------
        # ACTIVITY LOG
        # -----------------------------------------------------

        log_activity(
            "team_member_removed",
            "brand_member",
            member_id,
            (
                f"Removed {member['name']} "
                f"from {brand['name']} team."
            ),
            brand_id
        )

        flash(
            f"{member['name']} was removed from the team.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to remove team member."
        )

        flash(
            "Unable to remove the team member right now.",
            "danger"
        )

    finally:

        conn.close()

    return redirect(
        url_for(
            "team",
            brand_id=brand_id
        )
    )
# =========================================================
# LISTENING
# =========================================================

@app.route("/listening")
@login_required
def listening():

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    platform = request.args.get(
        "platform",
        ""
    ).strip()

    sentiment = request.args.get(
        "sentiment",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            query = """
                SELECT
                    sm.*,
                    b.name AS brand_name,
                    lk.keyword
                FROM social_mentions sm
                JOIN brands b
                    ON b.id = sm.brand_id
                LEFT JOIN listening_keywords lk
                    ON lk.id = sm.keyword_id
                WHERE 1 = 1
            """

            params = []

            if brand_id:

                query += """
                    AND sm.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sm.platform = %s
                """

                params.append(platform)

            if sentiment:

                query += """
                    AND sm.sentiment = %s
                """

                params.append(sentiment)

            if status:

                query += """
                    AND sm.status = %s
                """

                params.append(status)

            if search:

                query += """
                    AND (
                        sm.content ILIKE %s
                        OR sm.author_name ILIKE %s
                        OR sm.author_username ILIKE %s
                        OR lk.keyword ILIKE %s
                    )
                """

                like = f"%{search}%"

                params.extend([
                    like,
                    like,
                    like,
                    like
                ])

            query += """
                ORDER BY sm.mentioned_at DESC
                LIMIT 100
            """

            cur.execute(
                query,
                params
            )

            mentions = cur.fetchall()

            cur.execute("""
                SELECT *
                FROM listening_keywords
                WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)

            keywords = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_mentions
            """)

            total = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM listening_keywords
                WHERE is_active = TRUE
            """)

            active_keywords = cur.fetchone()["count"]

            sentiment_counts = {}

            for item in [
                "positive",
                "negative",
                "neutral"
            ]:

                cur.execute("""
                    SELECT COUNT(*) AS count
                    FROM social_mentions
                    WHERE sentiment = %s
                """, (item,))

                sentiment_counts[item] = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_mentions
                WHERE status = 'new'
            """)

            new_mentions = cur.fetchone()["count"]

            cur.execute("""
                SELECT
                    platform,
                    COUNT(*) AS count
                FROM social_mentions
                GROUP BY platform
                ORDER BY count DESC
            """)

            platform_counts = cur.fetchall()

        return render_template(
            "listening.html",
            mentions=mentions,
            keywords=keywords,
            brands=brands_list,
            total=total,
            active_keywords=active_keywords,
            positive=sentiment_counts["positive"],
            negative=sentiment_counts["negative"],
            neutral=sentiment_counts["neutral"],
            new_mentions=new_mentions,
            platform_counts=platform_counts,
            brand_id=brand_id,
            platform=platform,
            sentiment=sentiment,
            status=status,
            search=search,
            platforms=SOCIAL_PLATFORMS,
        )

    finally:
        conn.close()


@app.route(
    "/listening/keywords/create",
    methods=["POST"]
)
@login_required
def create_listening_keyword():

    brand_id = request.form.get(
        "brand_id",
        ""
    ).strip()

    keyword = request.form.get(
        "keyword",
        ""
    ).strip()

    keyword = keyword.lstrip("#").strip()

    if not brand_id or not keyword:

        flash(
            "Brand and keyword are required.",
            "danger"
        )

        return redirect(
            url_for("listening")
        )

    if len(keyword) > 150:

        flash(
            "Keyword cannot exceed 150 characters.",
            "danger"
        )

        return redirect(
            url_for("listening")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id
                FROM brands
                WHERE id = %s
                AND is_active = TRUE
            """, (brand_id,))

            if not cur.fetchone():

                flash(
                    "Selected brand is invalid or inactive.",
                    "danger"
                )

                return redirect(
                    url_for("listening")
                )

            cur.execute("""
                SELECT id
                FROM listening_keywords
                WHERE brand_id = %s
                AND LOWER(keyword) = LOWER(%s)
            """, (
                brand_id,
                keyword
            ))

            if cur.fetchone():

                flash(
                    "This keyword already exists for the selected brand.",
                    "warning"
                )

                return redirect(
                    url_for("listening")
                )

            cur.execute("""
                INSERT INTO listening_keywords (
                    brand_id,
                    keyword
                )
                VALUES (%s, %s)
                RETURNING id
            """, (
                brand_id,
                keyword
            ))

            result = cur.fetchone()

        conn.commit()

        log_activity(
            "created",
            "listening_keyword",
            result["id"],
            f"Created listening keyword: {keyword}",
            int(brand_id)
        )

        flash(
            "Listening keyword added successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("listening")
    )


@app.route(
    "/listening/keywords/<int:keyword_id>/toggle",
    methods=["POST"]
)
@login_required
def toggle_listening_keyword(keyword_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE listening_keywords
                SET is_active = NOT is_active
                WHERE id = %s
                RETURNING brand_id, is_active
            """, (keyword_id,))

            result = cur.fetchone()

            if not result:

                flash(
                    "Keyword not found.",
                    "danger"
                )

                return redirect(
                    url_for("listening")
                )

        conn.commit()

        state = (
            "activated"
            if result["is_active"]
            else "deactivated"
        )

        log_activity(
            "status_changed",
            "listening_keyword",
            keyword_id,
            f"Listening keyword {state}",
            result["brand_id"]
        )

        flash(
            f"Keyword {state} successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("listening")
    )


@app.route(
    "/listening/keywords/<int:keyword_id>/delete",
    methods=["POST"]
)
@login_required
def delete_listening_keyword(keyword_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT brand_id, keyword
                FROM listening_keywords
                WHERE id = %s
            """, (keyword_id,))

            keyword = cur.fetchone()

            if not keyword:

                flash(
                    "Keyword not found.",
                    "danger"
                )

                return redirect(
                    url_for("listening")
                )

            cur.execute("""
                UPDATE social_mentions
                SET keyword_id = NULL
                WHERE keyword_id = %s
            """, (keyword_id,))

            cur.execute("""
                DELETE FROM listening_keywords
                WHERE id = %s
            """, (keyword_id,))

        conn.commit()

        log_activity(
            "deleted",
            "listening_keyword",
            keyword_id,
            f"Deleted listening keyword: {keyword['keyword']}",
            keyword["brand_id"]
        )

        flash(
            "Listening keyword deleted successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("listening")
    )


# =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
@login_required
def analytics():

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    platform = request.args.get(
        "platform",
        ""
    ).strip()

    today = date.today()

    default_from = today - timedelta(days=30)

    date_from = request.args.get(
        "date_from",
        default_from.isoformat()
    ).strip()

    date_to = request.args.get(
        "date_to",
        today.isoformat()
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            try:
                parsed_from = date.fromisoformat(date_from)
            except ValueError:
                parsed_from = default_from

            try:
                parsed_to = date.fromisoformat(date_to)
            except ValueError:
                parsed_to = today

            query = """
                SELECT
                    COALESCE(SUM(a.impressions), 0) AS impressions,
                    COALESCE(SUM(a.reach), 0) AS reach,
                    COALESCE(SUM(a.likes), 0) AS likes,
                    COALESCE(SUM(a.comments), 0) AS comments,
                    COALESCE(SUM(a.shares), 0) AS shares,
                    COALESCE(SUM(a.clicks), 0) AS clicks,
                    COALESCE(MAX(a.followers), 0) AS followers
                FROM analytics a
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                WHERE a.metric_date BETWEEN %s AND %s
            """

            params = [
                parsed_from,
                parsed_to
            ]

            if brand_id:

                query += """
                    AND a.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            cur.execute(
                query,
                params
            )

            summary = cur.fetchone()

            impressions = summary["impressions"] or 0
            reach = summary["reach"] or 0
            likes = summary["likes"] or 0
            comments = summary["comments"] or 0
            shares = summary["shares"] or 0
            clicks = summary["clicks"] or 0
            followers = summary["followers"] or 0

            engagements = (
                likes
                + comments
                + shares
            )

            engagement_rate = (
                (engagements / reach) * 100
                if reach
                else 0
            )

            click_rate = (
                (clicks / impressions) * 100
                if impressions
                else 0
            )

            # DAILY TREND

            query = """
                SELECT
                    a.metric_date,
                    SUM(a.impressions) AS impressions,
                    SUM(a.reach) AS reach,
                    SUM(a.likes) AS likes,
                    SUM(a.comments) AS comments,
                    SUM(a.shares) AS shares,
                    SUM(a.clicks) AS clicks,
                    MAX(a.followers) AS followers
                FROM analytics a
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                WHERE a.metric_date BETWEEN %s AND %s
            """

            params = [
                parsed_from,
                parsed_to
            ]

            if brand_id:

                query += """
                    AND a.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            query += """
                GROUP BY a.metric_date
                ORDER BY a.metric_date
            """

            cur.execute(
                query,
                params
            )

            daily_trend = cur.fetchall()

            # PLATFORM PERFORMANCE

            query = """
                SELECT
                    COALESCE(sa.platform, 'Unknown') AS platform,
                    SUM(a.impressions) AS impressions,
                    SUM(a.reach) AS reach,
                    SUM(a.likes) AS likes,
                    SUM(a.comments) AS comments,
                    SUM(a.shares) AS shares,
                    SUM(a.clicks) AS clicks,
                    MAX(a.followers) AS followers
                FROM analytics a
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                WHERE a.metric_date BETWEEN %s AND %s
            """

            params = [
                parsed_from,
                parsed_to
            ]

            if brand_id:

                query += """
                    AND a.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            query += """
                GROUP BY sa.platform
                ORDER BY reach DESC
            """

            cur.execute(
                query,
                params
            )

            platform_performance = cur.fetchall()

            # TOP CONTENT

            query = """
                SELECT
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    SUM(a.impressions) AS impressions,
                    SUM(a.reach) AS reach,
                    SUM(a.likes) AS likes,
                    SUM(a.comments) AS comments,
                    SUM(a.shares) AS shares,
                    SUM(a.clicks) AS clicks
                FROM analytics a
                JOIN posts p
                    ON p.id = a.post_id
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                WHERE a.metric_date BETWEEN %s AND %s
            """

            params = [
                parsed_from,
                parsed_to
            ]

            if brand_id:

                query += """
                    AND a.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            query += """
                GROUP BY
                    p.id,
                    p.title,
                    p.content,
                    p.status
                ORDER BY reach DESC
                LIMIT 10
            """

            cur.execute(
                query,
                params
            )

            top_content = cur.fetchall()

            # FOLLOWER TREND

            query = """
                SELECT
                    a.metric_date,
                    MAX(a.followers) AS followers
                FROM analytics a
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                WHERE a.metric_date BETWEEN %s AND %s
            """

            params = [
                parsed_from,
                parsed_to
            ]

            if brand_id:

                query += """
                    AND a.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            query += """
                GROUP BY a.metric_date
                ORDER BY a.metric_date
            """

            cur.execute(
                query,
                params
            )

            follower_trend = cur.fetchall()

            # DETAILED ROWS

            query = """
                SELECT
                    a.*,
                    sa.platform,
                    sa.account_name,
                    p.title AS post_title
                FROM analytics a
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                LEFT JOIN posts p
                    ON p.id = a.post_id
                WHERE a.metric_date BETWEEN %s AND %s
            """

            params = [
                parsed_from,
                parsed_to
            ]

            if brand_id:

                query += """
                    AND a.brand_id = %s
                """

                params.append(brand_id)

            if platform:

                query += """
                    AND sa.platform = %s
                """

                params.append(platform)

            query += """
                ORDER BY a.metric_date DESC
                LIMIT 500
            """

            cur.execute(
                query,
                params
            )

            detailed_rows = cur.fetchall()

        chart_labels = [
            row["metric_date"].isoformat()
            for row in daily_trend
        ]

        chart_reach = [
            row["reach"] or 0
            for row in daily_trend
        ]

        chart_impressions = [
            row["impressions"] or 0
            for row in daily_trend
        ]

        chart_engagement = [
            (
                (row["likes"] or 0)
                + (row["comments"] or 0)
                + (row["shares"] or 0)
            )
            for row in daily_trend
        ]

        return render_template(
            "analytics.html",
            brands=brands_list,
            summary=summary,
            impressions=impressions,
            reach=reach,
            likes=likes,
            comments=comments,
            shares=shares,
            clicks=clicks,
            followers=followers,
            engagements=engagements,
            engagement_rate=engagement_rate,
            click_rate=click_rate,
            daily_trend=daily_trend,
            platform_performance=platform_performance,
            top_content=top_content,
            follower_trend=follower_trend,
            detailed_rows=detailed_rows,
            chart_labels=chart_labels,
            chart_reach=chart_reach,
            chart_impressions=chart_impressions,
            chart_engagement=chart_engagement,
            brand_id=brand_id,
            platform=platform,
            date_from=parsed_from.isoformat(),
            date_to=parsed_to.isoformat(),
            platforms=SOCIAL_PLATFORMS,
        )

    finally:
        conn.close()


# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
@login_required
def reports():

    brand_id = request.args.get(
        "brand_id",
        ""
    ).strip()

    report_type = request.args.get(
        "report_type",
        ""
    ).strip()

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            query = """
                SELECT
                    r.*,
                    b.name AS brand_name,
                    u.name AS creator_name
                FROM reports r
                JOIN brands b
                    ON b.id = r.brand_id
                LEFT JOIN users u
                    ON u.id = r.created_by
                WHERE 1 = 1
            """

            params = []

            if brand_id:

                query += """
                    AND r.brand_id = %s
                """

                params.append(brand_id)

            if report_type:

                query += """
                    AND r.report_type = %s
                """

                params.append(report_type)

            if search:

                query += """
                    AND (
                        r.name ILIKE %s
                        OR b.name ILIKE %s
                    )
                """

                like = f"%{search}%"

                params.extend([
                    like,
                    like
                ])

            query += """
                ORDER BY r.created_at DESC
            """

            cur.execute(
                query,
                params
            )

            report_rows = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM reports
            """)

            total = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM reports
                WHERE created_at::date = CURRENT_DATE
            """)

            today_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT
                    report_type,
                    COUNT(*) AS count
                FROM reports
                GROUP BY report_type
                ORDER BY count DESC
            """)

            type_breakdown = cur.fetchall()

        return render_template(
            "reports.html",
            reports=report_rows,
            brands=brands_list,
            total=total,
            today_count=today_count,
            type_breakdown=type_breakdown,
            brand_id=brand_id,
            report_type=report_type,
            search=search,
        )

    finally:
        conn.close()


@app.route(
    "/reports/create",
    methods=["GET", "POST"]
)
@login_required
def create_report():

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name
            """)

            brands_list = cur.fetchall()

            if request.method == "POST":

                brand_id = request.form.get(
                    "brand_id",
                    ""
                ).strip()

                name = request.form.get(
                    "name",
                    ""
                ).strip()

                period_start = request.form.get(
                    "period_start",
                    ""
                ).strip()

                period_end = request.form.get(
                    "period_end",
                    ""
                ).strip()

                report_type = request.form.get(
                    "report_type",
                    "performance"
                ).strip()

                if (
                    not brand_id
                    or not name
                    or not period_start
                    or not period_end
                ):

                    flash(
                        "All required report fields must be completed.",
                        "danger"
                    )

                    return redirect(
                        url_for("reports")
                    )

                try:

                    start_date = date.fromisoformat(
                        period_start
                    )

                    end_date = date.fromisoformat(
                        period_end
                    )

                except ValueError:

                    flash(
                        "Invalid report dates.",
                        "danger"
                    )

                    return redirect(
                        url_for("reports")
                    )

                if start_date > end_date:

                    flash(
                        "Report start date cannot be after end date.",
                        "danger"
                    )

                    return redirect(
                        url_for("reports")
                    )

                user = get_current_user()

                cur.execute("""
                    INSERT INTO reports (
                        brand_id,
                        created_by,
                        name,
                        period_start,
                        period_end,
                        report_type
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    brand_id,
                    user["id"],
                    name,
                    start_date,
                    end_date,
                    report_type
                ))

                report = cur.fetchone()

        conn.commit()

        log_activity(
            "created",
            "report",
            report["id"],
            f"Created report: {name}",
            int(brand_id)
        )

        flash(
            "Report created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "view_report",
                report_id=report["id"]
            )
        )

    finally:
        conn.close()


@app.route("/reports/<int:report_id>")
@login_required
def view_report(report_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    r.*,
                    b.name AS brand_name,
                    u.name AS creator_name
                FROM reports r
                JOIN brands b
                    ON b.id = r.brand_id
                LEFT JOIN users u
                    ON u.id = r.created_by
                WHERE r.id = %s
            """, (report_id,))

            report = cur.fetchone()

            if not report:
                abort(404)

            cur.execute("""
                SELECT
                    COALESCE(SUM(a.impressions), 0) AS impressions,
                    COALESCE(SUM(a.reach), 0) AS reach,
                    COALESCE(SUM(a.likes), 0) AS likes,
                    COALESCE(SUM(a.comments), 0) AS comments,
                    COALESCE(SUM(a.shares), 0) AS shares,
                    COALESCE(SUM(a.clicks), 0) AS clicks,
                    COALESCE(MAX(a.followers), 0) AS followers
                FROM analytics a
                WHERE a.brand_id = %s
                AND a.metric_date BETWEEN %s AND %s
            """, (
                report["brand_id"],
                report["period_start"],
                report["period_end"]
            ))

            summary = cur.fetchone()

            cur.execute("""
                SELECT
                    COALESCE(sa.platform, 'Unknown') AS platform,
                    SUM(a.impressions) AS impressions,
                    SUM(a.reach) AS reach,
                    SUM(a.likes) AS likes,
                    SUM(a.comments) AS comments,
                    SUM(a.shares) AS shares,
                    SUM(a.clicks) AS clicks
                FROM analytics a
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                WHERE a.brand_id = %s
                AND a.metric_date BETWEEN %s AND %s
                GROUP BY sa.platform
                ORDER BY reach DESC
            """, (
                report["brand_id"],
                report["period_start"],
                report["period_end"]
            ))

            platform_breakdown = cur.fetchall()

        impressions = summary["impressions"] or 0
        reach = summary["reach"] or 0

        engagements = (
            (summary["likes"] or 0)
            + (summary["comments"] or 0)
            + (summary["shares"] or 0)
        )

        engagement_rate = (
            (engagements / reach) * 100
            if reach
            else 0
        )

        return render_template(
            "report_view.html",
            report=report,
            summary=summary,
            platform_breakdown=platform_breakdown,
            engagements=engagements,
            engagement_rate=engagement_rate,
            impressions=impressions,
            reach=reach,
        )

    finally:
        conn.close()


@app.route(
    "/reports/<int:report_id>/delete",
    methods=["POST"]
)
@login_required
def delete_report(report_id):

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM reports
                WHERE id = %s
            """, (report_id,))

            report = cur.fetchone()

            if not report:

                flash(
                    "Report not found.",
                    "danger"
                )

                return redirect(
                    url_for("reports")
                )

            cur.execute("""
                DELETE FROM reports
                WHERE id = %s
            """, (report_id,))

        conn.commit()

        log_activity(
            "deleted",
            "report",
            report_id,
            f"Deleted report: {report['name']}",
            report["brand_id"]
        )

        flash(
            "Report deleted successfully.",
            "success"
        )

    finally:
        conn.close()

    return redirect(
        url_for("reports")
    )


# =========================================================
# NOTIFICATIONS
# =========================================================

@app.route("/notifications")
@login_required
def notifications():

    user = get_current_user()

    notification_type = request.args.get(
        "type",
        ""
    ).strip()

    status = request.args.get(
        "status",
        ""
    ).strip()

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            query = """
                SELECT *
                FROM notifications
                WHERE user_id = %s
            """

            params = [
                user["id"]
            ]

            if notification_type:

                query += """
                    AND notification_type = %s
                """

                params.append(
                    notification_type
                )

            if status == "read":

                query += """
                    AND is_read = TRUE
                """

            elif status == "unread":

                query += """
                    AND is_read = FALSE
                """

            if search:

                query += """
                    AND (
                        title ILIKE %s
                        OR message ILIKE %s
                    )
                """

                like = f"%{search}%"

                params.extend([
                    like,
                    like
                ])

            query += """
                ORDER BY created_at DESC
            """

            cur.execute(
                query,
                params
            )

            notification_rows = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
            """, (user["id"],))

            total = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
                AND is_read = FALSE
            """, (user["id"],))

            unread = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
                AND is_read = TRUE
            """, (user["id"],))

            read = cur.fetchone()["count"]

            cur.execute("""
                SELECT
                    notification_type,
                    COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
                GROUP BY notification_type
                ORDER BY count DESC
            """, (user["id"],))

            type_counts = cur.fetchall()

        return render_template(
            "notifications.html",
            notifications=notification_rows,
            total=total,
            unread=unread,
            read=read,
            type_counts=type_counts,
            notification_type=notification_type,
            status=status,
            search=search,
        )

    finally:
        conn.close()


@app.route(
    "/notifications/<int:notification_id>/read",
    methods=["POST"]
)
@login_required
def mark_notification_read(notification_id):

    user = get_current_user()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE notifications
                SET is_read = TRUE
                WHERE id = %s
                AND user_id = %s
            """, (
                notification_id,
                user["id"]
            ))

        conn.commit()

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("notifications")
    )


@app.route(
    "/notifications/<int:notification_id>/unread",
    methods=["POST"]
)
@login_required
def mark_notification_unread(notification_id):

    user = get_current_user()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE notifications
                SET is_read = FALSE
                WHERE id = %s
                AND user_id = %s
            """, (
                notification_id,
                user["id"]
            ))

        conn.commit()

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("notifications")
    )


@app.route(
    "/notifications/read-all",
    methods=["POST"]
)
@login_required
def mark_all_notifications_read():

    user = get_current_user()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE notifications
                SET is_read = TRUE
                WHERE user_id = %s
            """, (user["id"],))

        conn.commit()

    finally:
        conn.close()

    flash(
        "All notifications marked as read.",
        "success"
    )

    return redirect(
        url_for("notifications")
    )


@app.route(
    "/notifications/<int:notification_id>/delete",
    methods=["POST"]
)
@login_required
def delete_notification(notification_id):

    user = get_current_user()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM notifications
                WHERE id = %s
                AND user_id = %s
            """, (
                notification_id,
                user["id"]
            ))

        conn.commit()

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("notifications")
    )


@app.route(
    "/notifications/delete-read",
    methods=["POST"]
)
@login_required
def delete_read_notifications():

    user = get_current_user()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM notifications
                WHERE user_id = %s
                AND is_read = TRUE
            """, (user["id"],))

        conn.commit()

    finally:
        conn.close()

    flash(
        "Read notifications deleted.",
        "success"
    )

    return redirect(
        url_for("notifications")
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route(
    "/settings",
    methods=["GET", "POST"]
)
@login_required
def settings():

    user = get_current_user()

    if not user:
        flash(
            "Unable to load your account.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not name:

            flash(
                "Name is required.",
                "danger"
            )

            return redirect(
                url_for("settings")
            )

        if not EMAIL_PATTERN.match(email):

            flash(
                "Please enter a valid email address.",
                "danger"
            )

            return redirect(
                url_for("settings")
            )

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                    AND id <> %s
                """, (
                    email,
                    user["id"]
                ))

                if cur.fetchone():

                    flash(
                        "This email address is already in use.",
                        "danger"
                    )

                    return redirect(
                        url_for("settings")
                    )

                cur.execute("""
                    UPDATE users
                    SET
                        name = %s,
                        email = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    name,
                    email,
                    user["id"]
                ))

            conn.commit()

            log_activity(
                "updated",
                "user",
                user["id"],
                "Updated account settings."
            )

            flash(
                "Settings updated successfully.",
                "success"
            )

        except Exception:

            conn.rollback()

            app.logger.exception(
                "Failed to update account settings."
            )

            flash(
                "Unable to update settings right now.",
                "danger"
            )

        finally:
            conn.close()

        return redirect(
            url_for("settings")
        )

    # ---------------------------------------------------------
    # GET CURRENT PROFILE
    # ---------------------------------------------------------

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active,
                    created_at,
                    updated_at
                FROM users
                WHERE id = %s
            """, (user["id"],))

            profile = cur.fetchone()

    finally:
        conn.close()

    if not profile:

        flash(
            "Account profile could not be found.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "settings.html",
        user=profile,
        profile=profile
    )


# =========================================================
# CHANGE PASSWORD
# =========================================================

@app.route(
    "/settings/password",
    methods=["POST"]
)
@login_required
def change_password():

    user = get_current_user()

    if not user:

        flash(
            "Unable to identify your account.",
            "danger"
        )

        return redirect(
            url_for("login")
        )

    current_password = request.form.get(
        "current_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    if not current_password:

        flash(
            "Please enter your current password.",
            "danger"
        )

        return redirect(
            url_for("settings")
        )

    if not new_password:

        flash(
            "Please enter a new password.",
            "danger"
        )

        return redirect(
            url_for("settings")
        )

    if len(new_password) < 8:

        flash(
            "New password must contain at least 8 characters.",
            "danger"
        )

        return redirect(
            url_for("settings")
        )

    if new_password != confirm_password:

        flash(
            "New passwords do not match.",
            "danger"
        )

        return redirect(
            url_for("settings")
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT password_hash
                FROM users
                WHERE id = %s
            """, (user["id"],))

            row = cur.fetchone()

            if not row:

                flash(
                    "Account could not be found.",
                    "danger"
                )

                return redirect(
                    url_for("settings")
                )

            stored_password = row["password_hash"]

            if not stored_password or not check_password_hash(
                stored_password,
                current_password
            ):

                flash(
                    "Current password is incorrect.",
                    "danger"
                )

                return redirect(
                    url_for("settings")
                )

            if check_password_hash(
                stored_password,
                new_password
            ):

                flash(
                    "New password must be different from the current password.",
                    "danger"
                )

                return redirect(
                    url_for("settings")
                )

            cur.execute("""
                UPDATE users
                SET
                    password_hash = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                generate_password_hash(new_password),
                user["id"]
            ))

        conn.commit()

        log_activity(
            "password_changed",
            "user",
            user["id"],
            "Changed account password."
        )

        flash(
            "Password changed successfully.",
            "success"
        )

    except Exception:

        conn.rollback()

        app.logger.exception(
            "Failed to change account password."
        )

        flash(
            "Unable to change password right now.",
            "danger"
        )

    finally:
        conn.close()

    return redirect(
        url_for("settings")
    )
# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    conn = None

    try:

        conn = get_db_connection()

        with conn.cursor() as cur:

            cur.execute("SELECT 1")

            cur.fetchone()

        return jsonify({
            "status": "ok",
            "database": "connected"
        })

    except Exception:

        app.logger.exception(
            "Health check database failure"
        )

        return jsonify({
            "status": "error",
            "database": "unavailable"
        }), 503

    finally:

        if conn:

            conn.close()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

try:

    init_db()

except Exception as exc:

    app.logger.exception(
        "Database initialization failed: %s",
        exc
    )


# =========================================================
# CONTENT CATEGORIES
# =========================================================

@app.route("/content-categories", methods=["GET", "POST"])
@login_required
def content_categories():

    brand_id = request.args.get("brand_id", "").strip()

    active_brand = get_active_brand()

    if not brand_id and active_brand:
        brand_id = str(active_brand["id"])

    if not brand_id:
        flash("Please select a brand workspace first.", "warning")
        return redirect(url_for("brands"))

    try:
        brand_id = int(brand_id)
    except ValueError:
        flash("Invalid brand.", "danger")
        return redirect(url_for("brands"))

    brand = get_brand_by_id(brand_id)

    if not brand:
        flash("Brand not found.", "danger")
        return redirect(url_for("brands"))

    if request.method == "POST":

        if not has_brand_permission(
            brand_id,
            "manage_content"
        ):
            flash(
                "You do not have permission to manage categories.",
                "danger"
            )
            return redirect(
                url_for(
                    "content_categories",
                    brand_id=brand_id
                )
            )

        name = request.form.get("name", "").strip()
        description = request.form.get(
            "description",
            ""
        ).strip()

        color = request.form.get(
            "color",
            "#e31e24"
        ).strip()

        if not name:
            flash(
                "Category name is required.",
                "danger"
            )
            return redirect(
                url_for(
                    "content_categories",
                    brand_id=brand_id
                )
            )

        conn = get_db_connection()

        try:
            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id
                    FROM content_categories
                    WHERE brand_id = %s
                    AND LOWER(name) = LOWER(%s)
                """, (brand_id, name))

                if cur.fetchone():
                    flash(
                        "This category already exists.",
                        "warning"
                    )
                    return redirect(
                        url_for(
                            "content_categories",
                            brand_id=brand_id
                        )
                    )

                cur.execute("""
                    INSERT INTO content_categories (
                        brand_id,
                        name,
                        description,
                        color,
                        created_by
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    brand_id,
                    name,
                    description,
                    color,
                    session.get("user_id")
                ))

                category_id = cur.fetchone()["id"]

            conn.commit()

            log_activity(
                "created",
                "content_category",
                category_id,
                f"Created content category: {name}",
                brand_id
            )

            flash(
                "Content category created successfully.",
                "success"
            )

        except Exception:
            conn.rollback()
            raise

        finally:
            conn.close()

        return redirect(
            url_for(
                "content_categories",
                brand_id=brand_id
            )
        )

    categories = get_brand_categories(brand_id)

    return render_template(
        "content_categories.html",
        brand=brand,
        categories=categories
    )


# =========================================================
# DELETE CONTENT CATEGORY
# =========================================================




        # =========================================================
# POST CATEGORY & TAG MANAGEMENT
# =========================================================

@app.route(
    "/publisher/<int:post_id>/classification",
    methods=["POST"]
)
@login_required
def classify_post(post_id):

    category_id = request.form.get(
        "category_id",
        ""
    ).strip()

    selected_tags = request.form.getlist(
        "tag_ids"
    )

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM posts
                WHERE id = %s
            """, (post_id,))

            post = cur.fetchone()

            if not post:
                flash(
                    "Post not found.",
                    "danger"
                )
                return redirect(
                    url_for("publisher")
                )

            brand_id = post["brand_id"]

            if not has_brand_permission(
                brand_id,
                "manage_content"
            ):
                flash(
                    "You do not have permission to classify this post.",
                    "danger"
                )
                return redirect(
                    url_for(
                        "publisher",
                        brand_id=brand_id
                    )
                )

            # -------------------------------------------------
            # CATEGORY
            # -------------------------------------------------

            if category_id:

                try:
                    category_id_int = int(category_id)
                except ValueError:
                    category_id_int = None

                if category_id_int:

                    cur.execute("""
                        SELECT id
                        FROM content_categories
                        WHERE id = %s
                        AND brand_id = %s
                    """, (
                        category_id_int,
                        brand_id
                    ))

                    valid_category = cur.fetchone()

                    if valid_category:
                        cur.execute("""
                            UPDATE posts
                            SET category_id = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (
                            category_id_int,
                            post_id
                        ))

            else:

                cur.execute("""
                    UPDATE posts
                    SET category_id = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (post_id,))

            # -------------------------------------------------
            # TAGS
            # -------------------------------------------------

            cur.execute("""
                DELETE FROM post_tags
                WHERE post_id = %s
            """, (post_id,))

            for tag_id in selected_tags:

                try:
                    tag_id_int = int(tag_id)
                except ValueError:
                    continue

                cur.execute("""
                    SELECT id
                    FROM content_tags
                    WHERE id = %s
                    AND brand_id = %s
                """, (
                    tag_id_int,
                    brand_id
                ))

                valid_tag = cur.fetchone()

                if valid_tag:

                    cur.execute("""
                        INSERT INTO post_tags (
                            post_id,
                            tag_id
                        )
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (
                        post_id,
                        tag_id_int
                    ))

        conn.commit()

        log_activity(
            "updated",
            "post",
            post_id,
            "Updated post category and tags.",
            brand_id
        )

        flash(
            "Post classification updated successfully.",
            "success"
        )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("publisher")
    )
    # =========================================================
# BULK SCHEDULING
# =========================================================

@app.route(
    "/publisher/bulk-schedule",
    methods=["POST"]
)
@login_required
def bulk_schedule():

    post_ids = request.form.getlist(
        "post_ids"
    )

    scheduled_at_values = request.form.getlist(
        "scheduled_at"
    )

    if not post_ids:
        flash(
            "Please select at least one post.",
            "warning"
        )
        return redirect(
            request.referrer
            or url_for("publisher")
        )

    if len(post_ids) != len(scheduled_at_values):
        flash(
            "Invalid scheduling data.",
            "danger"
        )
        return redirect(
            request.referrer
            or url_for("publisher")
        )

    conn = get_db_connection()

    updated_count = 0

    try:
        with conn.cursor() as cur:

            for post_id, scheduled_at in zip(
                post_ids,
                scheduled_at_values
            ):

                if not scheduled_at.strip():
                    continue

                try:
                    post_id_int = int(post_id)
                except ValueError:
                    continue

                cur.execute("""
                    SELECT
                        id,
                        brand_id,
                        status
                    FROM posts
                    WHERE id = %s
                """, (post_id_int,))

                post = cur.fetchone()

                if not post:
                    continue

                brand_id = post["brand_id"]

                if not has_brand_permission(
                    brand_id,
                    "publish_content"
                ):
                    continue

                cur.execute("""
                    UPDATE posts
                    SET
                        scheduled_at = %s,
                        status = 'Scheduled',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (
                    scheduled_at,
                    post_id_int
                ))

                updated_count += 1

                log_activity(
                    "scheduled",
                    "post",
                    post_id_int,
                    f"Post scheduled for {scheduled_at}.",
                    brand_id
                )

        conn.commit()

        if updated_count:
            flash(
                f"{updated_count} post(s) scheduled successfully.",
                "success"
            )
        else:
            flash(
                "No posts were scheduled.",
                "warning"
            )

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    return redirect(
        request.referrer
        or url_for("publisher")
    )
# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )