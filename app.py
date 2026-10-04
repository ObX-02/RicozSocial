# =========================================================
# RICOZSOCIAL
# ENTERPRISE SOCIAL MEDIA MANAGEMENT PLATFORM
# =========================================================

import os
import re
from functools import wraps
from datetime import datetime, date, timedelta

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

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

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
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

                cur.execute("""
                    INSERT INTO users (
                        name,
                        email,
                        password_hash
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (
                    name,
                    email,
                    generate_password_hash(password)
                ))

                user = cur.fetchone()

                conn.commit()

                session["user_id"] = user["id"]

                flash(
                    "Account created successfully.",
                    "success"
                )

                return redirect(
                    url_for("dashboard")
                )

        finally:
            conn.close()

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if get_current_user():

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

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT *
                    FROM users
                    WHERE LOWER(email) = LOWER(%s)
                """, (email,))

                user = cur.fetchone()

                if not user or not check_password_hash(
                    user["password_hash"],
                    password
                ):

                    flash(
                        "Invalid email or password.",
                        "danger"
                    )

                    return render_template(
                        "login.html"
                    )

                if not user["is_active"]:

                    flash(
                        "Your account is inactive.",
                        "danger"
                    )

                    return render_template(
                        "login.html"
                    )

                session.clear()
                session["user_id"] = user["id"]

                flash(
                    "Welcome back.",
                    "success"
                )

                next_url = request.args.get("next")

                if next_url and next_url.startswith("/"):
                    return redirect(next_url)

                return redirect(
                    url_for("dashboard")
                )

        finally:
            conn.close()

    return render_template(
        "login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():

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

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

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
                FROM content_approvals
                WHERE status = 'pending'
            """)

            pending_approvals = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM community_comments
                WHERE status IN ('pending', 'unread')
            """)

            community_items = cur.fetchone()["count"]

            cur.execute("""
                SELECT *
                FROM posts
                ORDER BY created_at DESC
                LIMIT 8
            """)

            recent_posts = cur.fetchall()

            cur.execute("""
                SELECT *
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 5
            """, (get_current_user()["id"],))

            notifications = cur.fetchall()

        return render_template(
            "dashboard.html",
            total_brands=total_brands,
            connected_accounts=connected_accounts,
            total_posts=total_posts,
            scheduled_posts=scheduled_posts,
            pending_approvals=pending_approvals,
            community_items=community_items,
            recent_posts=recent_posts,
            notifications=notifications,
        )

    finally:
        conn.close()


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

        finally:
            conn.close()

        return redirect(
            url_for("settings")
        )

    return render_template(
        "settings.html",
        user=user
    )


@app.route(
    "/settings/password",
    methods=["POST"]
)
@login_required
def change_password():

    user = get_current_user()

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

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT password_hash
                FROM users
                WHERE id = %s
            """, (user["id"],))

            row = cur.fetchone()

            if not row or not check_password_hash(
                row["password_hash"],
                current_password
            ):

                flash(
                    "Current password is incorrect.",
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

            if check_password_hash(
                row["password_hash"],
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