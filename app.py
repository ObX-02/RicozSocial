import os
import re
from functools import wraps
from datetime import datetime

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
# DATABASE
# =========================================================

# Vercel + Neon:
# Prefer DATABASE_URL if available.
# Otherwise use the POSTGRES_URL created by the Neon integration.
# Local development will continue using the local PostgreSQL database.

DATABASE_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("POSTGRES_PRISMA_URL")
    or os.getenv("POSTGRES_URL_NON_POOLING")
    or "postgresql://postgres@localhost:5432/ricoz_social"
)


def get_db_connection():

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


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
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL DEFAULT 'member',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(brand_id, user_id)
                )
            """)

            # =================================================
            # SOCIAL ACCOUNTS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS social_accounts (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    platform VARCHAR(50) NOT NULL,
                    account_name VARCHAR(150) NOT NULL,
                    username VARCHAR(150),
                    account_id VARCHAR(255),
                    profile_url TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP,
                    is_connected BOOLEAN NOT NULL DEFAULT FALSE,
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
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    title VARCHAR(255),
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
                    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
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

            # Safe migration for existing databases
            cur.execute("""
                ALTER TABLE content_approvals
                ADD COLUMN IF NOT EXISTS created_at
                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_approvals_status
                ON content_approvals(status)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_approvals_post
                ON content_approvals(post_id)
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
                    content TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'unread',
                    reply TEXT,
                    replied_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS content_approvals (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    submitted_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    reviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    comments TEXT,
                    reviewed_at TIMESTAMP,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Safe migration for old database
            cur.execute("""
                ALTER TABLE content_approvals
                ADD COLUMN IF NOT EXISTS created_at
                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            """)

            # =================================================
            # COMMUNITY COMMENTS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS community_comments (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    social_account_id INTEGER REFERENCES social_accounts(id) ON DELETE SET NULL,
                    external_comment_id VARCHAR(255),
                    author_name VARCHAR(150),
                    author_username VARCHAR(150),
                    content TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'unread',
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
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    keyword VARCHAR(255) NOT NULL,
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
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    keyword_id INTEGER REFERENCES listening_keywords(id) ON DELETE SET NULL,
                    platform VARCHAR(50),
                    author_name VARCHAR(150),
                    author_username VARCHAR(150),
                    content TEXT,
                    mention_url TEXT,
                    sentiment VARCHAR(50),
                    status VARCHAR(50) NOT NULL DEFAULT 'new',
                    mentioned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # ANALYTICS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    social_account_id INTEGER REFERENCES social_accounts(id) ON DELETE SET NULL,
                    post_id INTEGER REFERENCES posts(id) ON DELETE SET NULL,
                    metric_date DATE NOT NULL,
                    impressions INTEGER NOT NULL DEFAULT 0,
                    reach INTEGER NOT NULL DEFAULT 0,
                    likes INTEGER NOT NULL DEFAULT 0,
                    comments INTEGER NOT NULL DEFAULT 0,
                    shares INTEGER NOT NULL DEFAULT 0,
                    clicks INTEGER NOT NULL DEFAULT 0,
                    followers INTEGER NOT NULL DEFAULT 0
                )
            """)

            # =================================================
            # REPORTS
            # =================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    name VARCHAR(255) NOT NULL,
                    period_start DATE,
                    period_end DATE,
                    report_type VARCHAR(100),
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
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    message TEXT,
                    notification_type VARCHAR(50),
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
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
                    action VARCHAR(100),
                    entity_type VARCHAR(100),
                    entity_id INTEGER,
                    description TEXT,
                    ip_address VARCHAR(100),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # =================================================
            # INDEXES
            # =================================================

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
                "Please log in to continue.",
                "warning"
            )

            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


def admin_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        user = get_current_user()

        if not user:

            flash(
                "Please log in to continue.",
                "warning"
            )

            return redirect(url_for("login"))

        if user["role"] not in ["admin", "owner"]:
            abort(403)

        return view(*args, **kwargs)

    return wrapped_view


# =========================================================
# ACTIVITY LOG
# =========================================================

def log_activity(
    user_id,
    action,
    entity_type=None,
    entity_id=None,
    description=None,
    brand_id=None
):

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
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                user_id,
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
# HELPERS
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
                SELECT
                    sa.*,
                    b.name AS brand_name,
                    b.is_active AS brand_active
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                WHERE sa.id = %s
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
                    SELECT COUNT(*)
                    FROM content_approvals
                    WHERE status = 'pending'
                """)

                pending_approvals = cur.fetchone()["count"]

                cur.execute("""
                    SELECT COUNT(*)
                    FROM notifications
                    WHERE user_id = %s
                    AND is_read = FALSE
                """, (user["id"],))

                unread_notifications = cur.fetchone()["count"]

        finally:
            conn.close()

    return {
        "current_user": user,
        "pending_approvals": pending_approvals,
        "unread_notifications": unread_notifications,
    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    if get_current_user():
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if get_current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            flash("Name is required.", "danger")

        elif len(name) > 150:
            flash("Name is too long.", "danger")

        elif not EMAIL_PATTERN.match(email):
            flash("Please enter a valid email address.", "danger")

        elif len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "danger"
            )

        elif password != confirm_password:
            flash("Passwords do not match.", "danger")

        else:

            conn = get_db_connection()

            try:

                with conn.cursor() as cur:

                    cur.execute("""
                        SELECT id
                        FROM users
                        WHERE email = %s
                    """, (email,))

                    if cur.fetchone():

                        flash(
                            "An account with this email already exists.",
                            "danger"
                        )

                    else:

                        cur.execute("""
                            INSERT INTO users (
                                name,
                                email,
                                password_hash,
                                role
                            )
                            VALUES (
                                %s,
                                %s,
                                %s,
                                'user'
                            )
                            RETURNING id
                        """, (
                            name,
                            email,
                            generate_password_hash(password)
                        ))

                        cur.fetchone()

                        conn.commit()

                        flash(
                            "Account created successfully. Please log in.",
                            "success"
                        )

                        return redirect(url_for("login"))

            finally:
                conn.close()

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if get_current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT *
                    FROM users
                    WHERE email = %s
                """, (email,))

                user = cur.fetchone()

        finally:
            conn.close()

        if (
            user
            and user["is_active"]
            and check_password_hash(
                user["password_hash"],
                password
            )
        ):

            session.clear()
            session["user_id"] = user["id"]

            log_activity(
                user["id"],
                "login",
                "user",
                user["id"],
                "User logged in."
            )

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout", methods=["GET", "POST"])
def logout():

    user_id = session.get("user_id")

    if user_id:
        try:
            log_activity(
                user_id=user_id,
                action="logged_out",
                entity_type="user",
                entity_id=user_id,
                description="User signed out of RicozSocial."
            )
        except Exception:
            pass

    session.clear()

    flash(
        "You have been signed out successfully.",
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

    user = get_current_user()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT COUNT(*)
                FROM brands
                WHERE is_active = TRUE
            """)
            total_brands = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM social_accounts
                WHERE is_connected = TRUE
            """)
            connected_accounts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM posts
                WHERE status = 'scheduled'
            """)
            scheduled_posts = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM content_approvals
                WHERE status = 'pending'
            """)
            pending_approvals = cur.fetchone()["count"]

            cur.execute("""
                SELECT
                    p.*,
                    b.name AS brand_name
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                ORDER BY p.created_at DESC
                LIMIT 8
            """)
            recent_posts = cur.fetchall()

            cur.execute("""
                SELECT
                    p.*,
                    b.name AS brand_name
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                WHERE p.status = 'scheduled'
                ORDER BY p.scheduled_at ASC
                LIMIT 8
            """)
            upcoming_posts = cur.fetchall()

            cur.execute("""
                SELECT
                    ca.*,
                    p.title,
                    p.content,
                    b.name AS brand_name
                FROM content_approvals ca
                JOIN posts p
                    ON p.id = ca.post_id
                JOIN brands b
                    ON b.id = p.brand_id
                WHERE ca.status = 'pending'
                ORDER BY ca.created_at DESC
                LIMIT 8
            """)
            approval_queue = cur.fetchall()

            cur.execute("""
                SELECT
                    sa.*,
                    b.name AS brand_name
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                WHERE sa.is_connected = TRUE
                ORDER BY sa.created_at DESC
                LIMIT 8
            """)
            connected_social_accounts = cur.fetchall()

            cur.execute("""
                SELECT
                    al.*,
                    u.name AS user_name,
                    b.name AS brand_name
                FROM activity_logs al
                LEFT JOIN users u
                    ON u.id = al.user_id
                LEFT JOIN brands b
                    ON b.id = al.brand_id
                ORDER BY al.created_at DESC
                LIMIT 10
            """)
            activity_feed = cur.fetchall()

            cur.execute("""
                SELECT *
                FROM analytics
                ORDER BY metric_date DESC
                LIMIT 20
            """)
            analytics_rows = cur.fetchall()

            cur.execute("""
                SELECT *
                FROM notifications
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 8
            """, (user["id"],))
            notifications = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        "dashboard.html",
        total_brands=total_brands,
        connected_accounts=connected_accounts,
        scheduled_posts=scheduled_posts,
        pending_approvals=pending_approvals,
        recent_posts=recent_posts,
        upcoming_posts=upcoming_posts,
        approval_queue=approval_queue,
        connected_social_accounts=connected_social_accounts,
        activity_feed=activity_feed,
        analytics_rows=analytics_rows,
        notifications=notifications,
    )


# =========================================================
# BRANDS
# =========================================================

@app.route("/brands")
@login_required
def brands():

    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            conditions = []
            params = []

            if search:

                conditions.append("""
                    (
                        b.name ILIKE %s
                        OR COALESCE(b.description, '') ILIKE %s
                    )
                """)

                pattern = f"%{search}%"
                params.extend([pattern, pattern])

            if status == "active":
                conditions.append("b.is_active = TRUE")

            elif status == "inactive":
                conditions.append("b.is_active = FALSE")

            where_clause = ""

            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            cur.execute(f"""
                SELECT
                    b.*,
                    u.name AS creator_name,
                    (
                        SELECT COUNT(*)
                        FROM social_accounts sa
                        WHERE sa.brand_id = b.id
                    ) AS account_count,
                    (
                        SELECT COUNT(*)
                        FROM posts p
                        WHERE p.brand_id = b.id
                    ) AS post_count
                FROM brands b
                LEFT JOIN users u
                    ON u.id = b.created_by
                {where_clause}
                ORDER BY b.created_at DESC
            """, params)

            brand_rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM brands")
            total_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM brands
                WHERE is_active = TRUE
            """)
            active_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM brands
                WHERE is_active = FALSE
            """)
            inactive_count = cur.fetchone()["count"]

    finally:
        conn.close()

    return render_template(
        "brands.html",
        brands=brand_rows,
        total_count=total_count,
        active_count=active_count,
        inactive_count=inactive_count,
        search=search,
        status=status,
        show_brand_modal=False,
    )


@app.route("/brands/create", methods=["POST"])
@login_required
def create_brand():

    user = get_current_user()

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    logo_url = request.form.get("logo_url", "").strip()
    website_url = request.form.get("website_url", "").strip()

    if not name:

        flash("Brand name is required.", "danger")
        return redirect(url_for("brands"))

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id
                FROM brands
                WHERE LOWER(name) = LOWER(%s)
            """, (name,))

            if cur.fetchone():

                flash(
                    "A brand with this name already exists.",
                    "danger"
                )

                return redirect(url_for("brands"))

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
                description or None,
                logo_url or None,
                website_url or None,
                user["id"]
            ))

            brand_id = cur.fetchone()["id"]

            cur.execute("""
                INSERT INTO brand_members (
                    brand_id,
                    user_id,
                    role
                )
                VALUES (%s, %s, 'owner')
                ON CONFLICT (brand_id, user_id)
                DO NOTHING
            """, (
                brand_id,
                user["id"]
            ))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "create",
        "brand",
        brand_id,
        f"Created brand: {name}",
        brand_id
    )

    flash(
        "Brand created successfully.",
        "success"
    )

    return redirect(url_for("brands"))


@app.route("/brands/<int:brand_id>")
@login_required
def brand_detail(brand_id):

    brand = get_brand_or_404(brand_id)

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM social_accounts
                WHERE brand_id = %s
                ORDER BY created_at DESC
            """, (brand_id,))

            accounts = cur.fetchall()

            cur.execute("""
                SELECT *
                FROM posts
                WHERE brand_id = %s
                ORDER BY created_at DESC
                LIMIT 20
            """, (brand_id,))

            posts = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        "brand_detail.html",
        brand=brand,
        accounts=accounts,
        posts=posts
    )


@app.route("/brands/<int:brand_id>/edit", methods=["POST"])
@login_required
def edit_brand(brand_id):

    user = get_current_user()
    brand = get_brand_or_404(brand_id)

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    logo_url = request.form.get("logo_url", "").strip()
    website_url = request.form.get("website_url", "").strip()

    if not name:

        flash(
            "Brand name is required.",
            "danger"
        )

        return redirect(
            url_for(
                "brand_detail",
                brand_id=brand_id
            )
        )

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id
                FROM brands
                WHERE LOWER(name) = LOWER(%s)
                AND id <> %s
            """, (
                name,
                brand_id
            ))

            if cur.fetchone():

                flash(
                    "Another brand already uses this name.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "brand_detail",
                        brand_id=brand_id
                    )
                )

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
                description or None,
                logo_url or None,
                website_url or None,
                brand_id
            ))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "update",
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


@app.route("/brands/<int:brand_id>/toggle", methods=["POST"])
@login_required
def toggle_brand(brand_id):

    user = get_current_user()
    brand = get_brand_or_404(brand_id)

    new_status = not brand["is_active"]

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

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

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "toggle",
        "brand",
        brand_id,
        f"Brand {'activated' if new_status else 'deactivated'}: {brand['name']}",
        brand_id
    )

    flash(
        "Brand status updated.",
        "success"
    )

    return redirect(url_for("brands"))


# =========================================================
# SOCIAL ACCOUNTS
# =========================================================

@app.route("/social-accounts")
@login_required
def social_accounts():

    search = request.args.get("search", "").strip()
    selected_platform = request.args.get("platform", "").strip()
    selected_brand = request.args.get("brand_id", "").strip()
    status = request.args.get("status", "").strip()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                ORDER BY name ASC
            """)

            available_brands = cur.fetchall()

            conditions = []
            params = []

            if search:

                conditions.append("""
                    (
                        sa.account_name ILIKE %s
                        OR COALESCE(sa.username, '') ILIKE %s
                        OR COALESCE(sa.account_id, '') ILIKE %s
                        OR b.name ILIKE %s
                    )
                """)

                pattern = f"%{search}%"

                params.extend([
                    pattern,
                    pattern,
                    pattern,
                    pattern
                ])

            if selected_platform:

                conditions.append(
                    "sa.platform = %s"
                )

                params.append(selected_platform)

            if selected_brand:

                try:

                    brand_id = int(selected_brand)

                    conditions.append(
                        "sa.brand_id = %s"
                    )

                    params.append(brand_id)

                except ValueError:
                    selected_brand = ""

            if status == "connected":
                conditions.append(
                    "sa.is_connected = TRUE"
                )

            elif status == "disconnected":
                conditions.append(
                    "sa.is_connected = FALSE"
                )

            where_clause = ""

            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            cur.execute(f"""
                SELECT
                    sa.*,
                    b.name AS brand_name,
                    b.is_active AS brand_active
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                {where_clause}
                ORDER BY sa.created_at DESC
            """, params)

            account_rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM social_accounts")
            total_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM social_accounts
                WHERE is_connected = TRUE
            """)
            connected_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM social_accounts
                WHERE is_connected = FALSE
            """)
            disconnected_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(DISTINCT platform)
                FROM social_accounts
            """)
            platform_count = cur.fetchone()["count"]

    finally:
        conn.close()

    return render_template(
        "social_accounts.html",
        social_accounts=account_rows,
        available_brands=available_brands,
        platforms=SOCIAL_PLATFORMS,
        search=search,
        selected_platform=selected_platform,
        selected_brand=selected_brand,
        status=status,
        total_count=total_count,
        connected_count=connected_count,
        disconnected_count=disconnected_count,
        platform_count=platform_count,
        show_account_modal=False
    )


@app.route("/social-accounts/create", methods=["POST"])
@login_required
def create_social_account():

    user = get_current_user()

    try:
        brand_id = int(request.form.get("brand_id", ""))
    except ValueError:

        flash(
            "Please select a valid brand.",
            "danger"
        )

        return redirect(url_for("social_accounts"))

    platform = request.form.get("platform", "").strip()
    account_name = request.form.get("account_name", "").strip()
    username = request.form.get("username", "").strip()
    account_id = request.form.get("account_id", "").strip()
    profile_url = request.form.get("profile_url", "").strip()

    if platform not in SOCIAL_PLATFORMS:

        flash(
            "Please select a valid social platform.",
            "danger"
        )

        return redirect(url_for("social_accounts"))

    if not account_name:

        flash(
            "Account name is required.",
            "danger"
        )

        return redirect(url_for("social_accounts"))

    if profile_url and not profile_url.startswith(
        ("http://", "https://")
    ):
        profile_url = "https://" + profile_url

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

                return redirect(url_for("social_accounts"))

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
                    "This social account already exists for this brand.",
                    "danger"
                )

                return redirect(url_for("social_accounts"))

            cur.execute("""
                INSERT INTO social_accounts (
                    brand_id,
                    platform,
                    account_name,
                    username,
                    account_id,
                    profile_url,
                    is_connected
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    FALSE
                )
                RETURNING id
            """, (
                brand_id,
                platform,
                account_name,
                username or None,
                account_id or None,
                profile_url or None
            ))

            account_db_id = cur.fetchone()["id"]

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "create",
        "social_account",
        account_db_id,
        f"Added {platform} account: {account_name}",
        brand_id
    )

    flash(
        "Social account added successfully.",
        "success"
    )

    return redirect(url_for("social_accounts"))


@app.route("/social-accounts/<int:account_id>/edit", methods=["POST"])
@login_required
def edit_social_account(account_id):

    user = get_current_user()
    account = get_social_account_or_404(account_id)

    try:
        brand_id = int(request.form.get("brand_id", ""))
    except ValueError:

        flash(
            "Please select a valid brand.",
            "danger"
        )

        return redirect(url_for("social_accounts"))

    platform = request.form.get("platform", "").strip()
    account_name = request.form.get("account_name", "").strip()
    username = request.form.get("username", "").strip()
    new_account_id = request.form.get("account_id", "").strip()
    profile_url = request.form.get("profile_url", "").strip()

    if platform not in SOCIAL_PLATFORMS:

        flash(
            "Invalid social platform.",
            "danger"
        )

        return redirect(url_for("social_accounts"))

    if not account_name:

        flash(
            "Account name is required.",
            "danger"
        )

        return redirect(url_for("social_accounts"))

    if profile_url and not profile_url.startswith(
        ("http://", "https://")
    ):
        profile_url = "https://" + profile_url

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

                return redirect(url_for("social_accounts"))

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
                    "Another matching social account already exists.",
                    "danger"
                )

                return redirect(url_for("social_accounts"))

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

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "update",
        "social_account",
        account_id,
        f"Updated social account: {account_name}",
        brand_id
    )

    flash(
        "Social account updated successfully.",
        "success"
    )

    return redirect(url_for("social_accounts"))


@app.route("/social-accounts/<int:account_id>/toggle", methods=["POST"])
@login_required
def toggle_social_account(account_id):

    user = get_current_user()
    account = get_social_account_or_404(account_id)

    if (
        not account["is_connected"]
        and not account["brand_active"]
    ):

        flash(
            "This account cannot be connected while its brand is inactive.",
            "danger"
        )

        return redirect(url_for("social_accounts"))

    new_status = not account["is_connected"]

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

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

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "toggle",
        "social_account",
        account_id,
        f"Social account {'connected' if new_status else 'disconnected'}: {account['account_name']}",
        account["brand_id"]
    )

    flash(
        "Social account status updated.",
        "success"
    )

    return redirect(url_for("social_accounts"))


@app.route("/social-accounts/<int:account_id>/delete", methods=["POST"])
@login_required
def delete_social_account(account_id):

    user = get_current_user()
    account = get_social_account_or_404(account_id)

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM social_accounts
                WHERE id = %s
            """, (account_id,))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "delete",
        "social_account",
        account_id,
        f"Deleted social account: {account['account_name']}",
        account["brand_id"]
    )

    flash(
        "Social account deleted successfully.",
        "success"
    )

    return redirect(url_for("social_accounts"))


# =========================================================
# PUBLISHER
# =========================================================

@app.route("/publisher")
@login_required
def publisher():

    search = request.args.get("search", "").strip()
    selected_brand = request.args.get("brand_id", "").strip()
    selected_status = request.args.get("status", "").strip().lower()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, name, is_active
                FROM brands
                ORDER BY name ASC
            """)
            available_brands = cur.fetchall()

            cur.execute("""
                SELECT
                    sa.id,
                    sa.brand_id,
                    sa.platform,
                    sa.account_name,
                    sa.username,
                    sa.account_id,
                    b.name AS brand_name
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                WHERE sa.is_connected = TRUE
                AND b.is_active = TRUE
                ORDER BY b.name ASC, sa.platform ASC
            """)
            connected_accounts = cur.fetchall()

            conditions = []
            params = []

            if search:

                conditions.append("""
                    (
                        COALESCE(p.title, '') ILIKE %s
                        OR p.content ILIKE %s
                        OR b.name ILIKE %s
                    )
                """)

                pattern = f"%{search}%"

                params.extend([
                    pattern,
                    pattern,
                    pattern
                ])

            if selected_brand:

                try:

                    brand_id = int(selected_brand)

                    conditions.append(
                        "p.brand_id = %s"
                    )

                    params.append(brand_id)

                except ValueError:
                    selected_brand = ""

            if selected_status in POST_STATUSES:

                conditions.append(
                    "p.status = %s"
                )

                params.append(selected_status)

            where_clause = ""

            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            cur.execute(f"""
                SELECT
                    p.id,
                    p.brand_id,
                    p.created_by,
                    p.title,
                    p.content,
                    p.media_url,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,
                    p.updated_at,
                    b.name AS brand_name,
                    u.name AS creator_name,

                    (
                        SELECT COUNT(*)
                        FROM post_platforms pp
                        WHERE pp.post_id = p.id
                    ) AS platform_count,

                    (
                        SELECT COUNT(*)
                        FROM post_platforms pp
                        WHERE pp.post_id = p.id
                        AND pp.platform_status = 'published'
                    ) AS published_platform_count

                FROM posts p

                JOIN brands b
                    ON b.id = p.brand_id

                LEFT JOIN users u
                    ON u.id = p.created_by

                {where_clause}

                ORDER BY
                    CASE
                        WHEN p.status = 'pending_approval' THEN 0
                        WHEN p.status = 'approved' THEN 1
                        WHEN p.status = 'scheduled' THEN 2
                        WHEN p.status = 'draft' THEN 3
                        WHEN p.status = 'rejected' THEN 4
                        WHEN p.status = 'failed' THEN 5
                        WHEN p.status = 'published' THEN 6
                        ELSE 7
                    END,
                    COALESCE(
                        p.scheduled_at,
                        p.updated_at,
                        p.created_at
                    ) DESC
            """, params)

            posts = cur.fetchall()

            cur.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (
                        WHERE status = 'draft'
                    ) AS drafts,
                    COUNT(*) FILTER (
                        WHERE status = 'pending_approval'
                    ) AS pending_approval,
                    COUNT(*) FILTER (
                        WHERE status = 'approved'
                    ) AS approved,
                    COUNT(*) FILTER (
                        WHERE status = 'scheduled'
                    ) AS scheduled,
                    COUNT(*) FILTER (
                        WHERE status = 'published'
                    ) AS published,
                    COUNT(*) FILTER (
                        WHERE status = 'rejected'
                    ) AS rejected,
                    COUNT(*) FILTER (
                        WHERE status = 'failed'
                    ) AS failed
                FROM posts
            """)
            stats = cur.fetchone()

    finally:
        conn.close()

    return render_template(
        "publisher.html",
        posts=posts,
        available_brands=available_brands,
        connected_accounts=connected_accounts,
        platforms=SOCIAL_PLATFORMS,
        post_statuses=POST_STATUSES,
        search=search,
        selected_brand=selected_brand,
        selected_status=selected_status,
        stats=stats,
    )


# =========================================================
# CREATE POST
# =========================================================

@app.route("/publisher/create", methods=["POST"])
@login_required
def create_post():

    user = get_current_user()

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    media_url = request.form.get("media_url", "").strip()

    status = request.form.get(
        "status",
        "draft"
    ).strip().lower()

    scheduled_at_raw = request.form.get(
        "scheduled_at",
        ""
    ).strip()

    try:

        brand_id = int(
            request.form.get("brand_id", "")
        )

    except ValueError:

        flash(
            "Please select a valid brand.",
            "danger"
        )

        return redirect(url_for("publisher"))

    account_values = request.form.getlist(
        "social_account_ids"
    )

    try:

        account_ids = list({
            int(value)
            for value in account_values
            if value.strip()
        })

    except ValueError:

        flash(
            "Invalid social account selection.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if not content:

        flash(
            "Post content is required.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if len(title) > 255:

        flash(
            "Post title is too long.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if status not in POST_STATUSES:

        flash(
            "Invalid post status.",
            "danger"
        )

        return redirect(url_for("publisher"))

    scheduled_at = None

    if scheduled_at_raw:

        try:

            scheduled_at = datetime.fromisoformat(
                scheduled_at_raw
            )

        except ValueError:

            flash(
                "Invalid schedule date and time.",
                "danger"
            )

            return redirect(url_for("publisher"))

    if status == "scheduled" and not scheduled_at:

        flash(
            "Please select a schedule date and time.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if status in [
        "draft",
        "pending_approval",
        "approved",
        "rejected"
    ]:
        if status != "approved":
            scheduled_at = None

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    is_active
                FROM brands
                WHERE id = %s
            """, (brand_id,))

            brand = cur.fetchone()

            if not brand:

                flash(
                    "Selected brand does not exist.",
                    "danger"
                )

                return redirect(url_for("publisher"))

            if not brand["is_active"]:

                flash(
                    "Posts cannot be created for an inactive brand.",
                    "danger"
                )

                return redirect(url_for("publisher"))

            valid_accounts = []

            if account_ids:

                cur.execute("""
                    SELECT
                        id,
                        brand_id,
                        platform,
                        account_name
                    FROM social_accounts
                    WHERE id = ANY(%s)
                    AND brand_id = %s
                    AND is_connected = TRUE
                """, (
                    account_ids,
                    brand_id
                ))

                valid_accounts = cur.fetchall()

                if len(valid_accounts) != len(account_ids):

                    flash(
                        "One or more selected social accounts are invalid, disconnected, or belong to another brand.",
                        "danger"
                    )

                    return redirect(url_for("publisher"))

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
                VALUES (
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
                user["id"],
                title or None,
                content,
                media_url or None,
                status,
                scheduled_at
            ))

            post_id = cur.fetchone()["id"]

            for account in valid_accounts:

                cur.execute("""
                    INSERT INTO post_platforms (
                        post_id,
                        social_account_id,
                        platform_status
                    )
                    VALUES (%s, %s, 'pending')
                    ON CONFLICT (
                        post_id,
                        social_account_id
                    )
                    DO NOTHING
                """, (
                    post_id,
                    account["id"]
                ))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "create",
        "post",
        post_id,
        f"Created post: {title or 'Untitled post'}",
        brand_id
    )

    flash(
        "Post created successfully.",
        "success"
    )

    return redirect(url_for("publisher"))


# =========================================================
# EDIT POST
# =========================================================

@app.route(
    "/publisher/<int:post_id>/edit",
    methods=["POST"]
)
@login_required
def edit_post(post_id):

    user = get_current_user()
    post = get_post_or_404(post_id)

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    media_url = request.form.get("media_url", "").strip()

    status = request.form.get(
        "status",
        post["status"]
    ).strip().lower()

    scheduled_at_raw = request.form.get(
        "scheduled_at",
        ""
    ).strip()

    try:

        brand_id = int(
            request.form.get(
                "brand_id",
                post["brand_id"]
            )
        )

    except ValueError:

        flash(
            "Invalid brand.",
            "danger"
        )

        return redirect(url_for("publisher"))

    account_values = request.form.getlist(
        "social_account_ids"
    )

    try:

        account_ids = list({
            int(value)
            for value in account_values
            if value.strip()
        })

    except ValueError:

        flash(
            "Invalid social account selection.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if not content:

        flash(
            "Post content is required.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if len(title) > 255:

        flash(
            "Post title is too long.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if status not in POST_STATUSES:

        flash(
            "Invalid post status.",
            "danger"
        )

        return redirect(url_for("publisher"))

    scheduled_at = None

    if scheduled_at_raw:

        try:

            scheduled_at = datetime.fromisoformat(
                scheduled_at_raw
            )

        except ValueError:

            flash(
                "Invalid schedule date and time.",
                "danger"
            )

            return redirect(url_for("publisher"))

    if status == "scheduled" and not scheduled_at:

        flash(
            "A scheduled post must have a schedule date and time.",
            "danger"
        )

        return redirect(url_for("publisher"))

    if status in [
        "draft",
        "pending_approval",
        "rejected",
        "published"
    ]:
        scheduled_at = None

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT *
                FROM brands
                WHERE id = %s
                AND is_active = TRUE
            """, (brand_id,))

            brand = cur.fetchone()

            if not brand:

                flash(
                    "Selected brand is invalid or inactive.",
                    "danger"
                )

                return redirect(url_for("publisher"))

            if account_ids:

                cur.execute("""
                    SELECT id
                    FROM social_accounts
                    WHERE id = ANY(%s)
                    AND brand_id = %s
                    AND is_connected = TRUE
                """, (
                    account_ids,
                    brand_id
                ))

                valid_ids = {
                    row["id"]
                    for row in cur.fetchall()
                }

                if valid_ids != set(account_ids):

                    flash(
                        "Invalid social account selection.",
                        "danger"
                    )

                    return redirect(url_for("publisher"))

            cur.execute("""
                UPDATE posts
                SET
                    brand_id = %s,
                    title = %s,
                    content = %s,
                    media_url = %s,
                    status = %s,
                    scheduled_at = %s,
                    published_at = CASE
                        WHEN %s = 'published'
                        THEN COALESCE(
                            published_at,
                            CURRENT_TIMESTAMP
                        )
                        ELSE NULL
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                brand_id,
                title or None,
                content,
                media_url or None,
                status,
                scheduled_at,
                status,
                post_id
            ))

            cur.execute("""
                DELETE FROM post_platforms
                WHERE post_id = %s
            """, (post_id,))

            for account_id in account_ids:

                cur.execute("""
                    INSERT INTO post_platforms (
                        post_id,
                        social_account_id,
                        platform_status
                    )
                    VALUES (%s, %s, 'pending')
                    ON CONFLICT (
                        post_id,
                        social_account_id
                    )
                    DO NOTHING
                """, (
                    post_id,
                    account_id
                ))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "update",
        "post",
        post_id,
        f"Updated post: {title or 'Untitled post'}",
        brand_id
    )

    flash(
        "Post updated successfully.",
        "success"
    )

    return redirect(url_for("publisher"))


# =========================================================
# DELETE POST
# =========================================================

@app.route(
    "/publisher/<int:post_id>/delete",
    methods=["POST"]
)
@login_required
def delete_post(post_id):

    user = get_current_user()
    post = get_post_or_404(post_id)

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM posts
                WHERE id = %s
            """, (post_id,))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "delete",
        "post",
        post_id,
        f"Deleted post: {post['title'] or 'Untitled post'}",
        post["brand_id"]
    )

    flash(
        "Post deleted successfully.",
        "success"
    )

    return redirect(url_for("publisher"))


# =========================================================
# SUBMIT POST FOR APPROVAL
# =========================================================

@app.route(
    "/publisher/<int:post_id>/submit-approval",
    methods=["POST"]
)
@login_required
def submit_post_for_approval(post_id):

    user = get_current_user()
    post = get_post_or_404(post_id)

    if post["status"] not in [
        "draft",
        "rejected"
    ]:

        flash(
            "Only draft or rejected posts can be submitted for approval.",
            "danger"
        )

        return redirect(url_for("publisher"))

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

            if cur.fetchone():

                flash(
                    "This post is already waiting for approval.",
                    "warning"
                )

                return redirect(url_for("publisher"))

            cur.execute("""
                UPDATE posts
                SET
                    status = 'pending_approval',
                    scheduled_at = NULL,
                    published_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (post_id,))

            cur.execute("""
                INSERT INTO content_approvals (
                    post_id,
                    submitted_by,
                    status,
                    comments,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    'pending',
                    NULL,
                    CURRENT_TIMESTAMP
                )
                RETURNING id
            """, (
                post_id,
                user["id"]
            ))

            approval_id = cur.fetchone()["id"]

            # Notify active users except submitter
            cur.execute("""
                SELECT id
                FROM users
                WHERE is_active = TRUE
                AND id <> %s
            """, (user["id"],))

            reviewers = cur.fetchall()

            for reviewer in reviewers:

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
                    reviewer["id"],
                    "New Content Approval",
                    f"{user['name']} submitted '{post['title'] or 'Untitled post'}' for approval.",
                    "approval"
                ))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "submitted_for_approval",
        "content_approval",
        approval_id,
        f"Submitted post for approval: {post['title'] or 'Untitled post'}.",
        post["brand_id"]
    )

    flash(
        "Post submitted for approval successfully.",
        "success"
    )

    return redirect(url_for("publisher"))


# =========================================================
# UPDATE POST STATUS
# =========================================================

@app.route(
    "/publisher/<int:post_id>/status",
    methods=["POST"]
)
@login_required
def update_post_status(post_id):

    user = get_current_user()
    post = get_post_or_404(post_id)

    new_status = request.form.get(
        "status",
        ""
    ).strip().lower()

    if new_status not in POST_STATUSES:

        flash(
            "Invalid post status.",
            "danger"
        )

        return redirect(url_for("publisher"))

    scheduled_at = post["scheduled_at"]
    published_at = post["published_at"]

    if new_status == "scheduled":

        if not scheduled_at:

            flash(
                "A scheduled post must have a schedule date and time.",
                "danger"
            )

            return redirect(url_for("publisher"))

        published_at = None

    elif new_status == "published":

        published_at = datetime.now()
        scheduled_at = None

    elif new_status in [
        "draft",
        "pending_approval",
        "rejected"
    ]:

        scheduled_at = None
        published_at = None

    elif new_status == "approved":

        published_at = None

    elif new_status == "failed":

        published_at = None

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

            if new_status == "published":

                cur.execute("""
                    UPDATE post_platforms
                    SET
                        platform_status = 'published',
                        published_at = CURRENT_TIMESTAMP,
                        error_message = NULL
                    WHERE post_id = %s
                """, (post_id,))

        conn.commit()

    finally:
        conn.close()

    log_activity(
        user["id"],
        "status_change",
        "post",
        post_id,
        f"Changed post status to {new_status}.",
        post["brand_id"]
    )

    flash(
        "Post status updated successfully.",
        "success"
    )

    return redirect(url_for("publisher"))


# =========================================================
# PUBLISHER DETAILS
# =========================================================

@app.route(
    "/publisher/<int:post_id>/details"
)
@login_required
def publisher_post_details(post_id):

    post = get_post_or_404(post_id)

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

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
                ORDER BY sa.platform ASC
            """, (post_id,))

            platforms = cur.fetchall()

    finally:
        conn.close()

    return jsonify({
        "post": {
            "id": post["id"],
            "brand_id": post["brand_id"],
            "brand_name": post["brand_name"],
            "title": post["title"],
            "content": post["content"],
            "media_url": post["media_url"],
            "status": post["status"],
            "scheduled_at": (
                post["scheduled_at"].isoformat()
                if post["scheduled_at"]
                else None
            ),
            "published_at": (
                post["published_at"].isoformat()
                if post["published_at"]
                else None
            ),
        },
        "platforms": [
            {
                "id": item["id"],
                "platform": item["platform"],
                "account_name": item["account_name"],
                "username": item["username"],
                "platform_status": item["platform_status"],
                "published_at": (
                    item["published_at"].isoformat()
                    if item["published_at"]
                    else None
                ),
                "error_message": item["error_message"],
            }
            for item in platforms
        ]
    })


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

    query = """
        SELECT
            ca.id,
            ca.post_id,
            ca.submitted_by,
            ca.reviewer_id,
            ca.status,
            ca.comments,
            ca.reviewed_at,
            ca.created_at,

            p.title AS post_title,
            p.content AS post_content,
            p.media_url,
            p.status AS post_status,
            p.scheduled_at,
            p.published_at,

            b.id AS brand_id,
            b.name AS brand_name,

            submitter.name AS submitter_name,
            submitter.email AS submitter_email,

            reviewer.name AS reviewer_name

        FROM content_approvals ca

        LEFT JOIN posts p
            ON p.id = ca.post_id

        LEFT JOIN brands b
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
                OR submitter.name ILIKE %s
            )
        """

        search_value = f"%{search}%"

        params.extend([
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

            params.append(brand_id_value)

        except ValueError:

            brand_id = ""

    if status:

        query += """
            AND ca.status = %s
        """

        params.append(status)

    query += """
        ORDER BY
            CASE
                WHEN ca.status = 'pending' THEN 0
                WHEN ca.status = 'rejected' THEN 1
                WHEN ca.status = 'approved' THEN 2
                ELSE 3
            END,
            ca.created_at DESC
    """

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                params
            )

            approval_items = cur.fetchall()

            cur.execute("""
                SELECT id, name
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
            """)

            available_brands = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*)
                FROM content_approvals
                WHERE status = 'pending'
            """)

            pending_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM content_approvals
                WHERE status = 'approved'
            """)

            approved_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM content_approvals
                WHERE status = 'rejected'
            """)

            rejected_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM content_approvals
            """)

            total_count = cur.fetchone()["count"]

    return render_template(
        "approvals.html",
        approval_items=approval_items,
        available_brands=available_brands,
        search=search,
        selected_brand=brand_id,
        selected_status=status,
        pending_count=pending_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
        total_count=total_count
    )


# =========================================================
# APPROVE CONTENT
# =========================================================

@app.route(
    "/approvals/<int:approval_id>/approve",
    methods=["POST"]
)
@login_required
def approve_content(approval_id):

    current_user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    ca.id,
                    ca.post_id,
                    ca.status,
                    p.brand_id,
                    p.title
                FROM content_approvals ca
                LEFT JOIN posts p
                    ON p.id = ca.post_id
                WHERE ca.id = %s
            """, (approval_id,))

            approval = cur.fetchone()

            if not approval:

                flash(
                    "Approval request could not be found.",
                    "danger"
                )

                return redirect(url_for("approvals"))

            if approval["status"] != "pending":

                flash(
                    "This approval request has already been processed.",
                    "warning"
                )

                return redirect(url_for("approvals"))

            cur.execute("""
                UPDATE content_approvals
                SET
                    status = 'approved',
                    reviewer_id = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                current_user["id"],
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

            cur.execute("""
                SELECT created_by
                FROM posts
                WHERE id = %s
            """, (
                approval["post_id"],
            ))

            post_owner = cur.fetchone()

            if (
                post_owner
                and post_owner["created_by"]
                and post_owner["created_by"] != current_user["id"]
            ):

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type,
                        is_read
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        FALSE
                    )
                """, (
                    post_owner["created_by"],
                    "Content Approved",
                    f"Your post '{approval['title'] or 'Untitled post'}' has been approved.",
                    "approval"
                ))

    log_activity(
        user_id=current_user["id"],
        brand_id=approval["brand_id"],
        action="approved_content",
        entity_type="content_approval",
        entity_id=approval_id,
        description=(
            f"Approved content: "
            f"{approval['title'] or 'Untitled post'}."
        )
    )

    flash(
        "Content approved successfully.",
        "success"
    )

    return redirect(url_for("approvals"))


# =========================================================
# REJECT CONTENT
# =========================================================

@app.route(
    "/approvals/<int:approval_id>/reject",
    methods=["POST"]
)
@login_required
def reject_content(approval_id):

    current_user = get_current_user()

    comments = request.form.get(
        "comments",
        ""
    ).strip()

    if len(comments) > 5000:

        flash(
            "Rejection comments cannot exceed 5000 characters.",
            "danger"
        )

        return redirect(url_for("approvals"))

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    ca.id,
                    ca.post_id,
                    ca.status,
                    p.brand_id,
                    p.title
                FROM content_approvals ca
                LEFT JOIN posts p
                    ON p.id = ca.post_id
                WHERE ca.id = %s
            """, (approval_id,))

            approval = cur.fetchone()

            if not approval:

                flash(
                    "Approval request could not be found.",
                    "danger"
                )

                return redirect(url_for("approvals"))

            if approval["status"] != "pending":

                flash(
                    "This approval request has already been processed.",
                    "warning"
                )

                return redirect(url_for("approvals"))

            cur.execute("""
                UPDATE content_approvals
                SET
                    status = 'rejected',
                    reviewer_id = %s,
                    comments = %s,
                    reviewed_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                current_user["id"],
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

            cur.execute("""
                SELECT created_by
                FROM posts
                WHERE id = %s
            """, (
                approval["post_id"],
            ))

            post_owner = cur.fetchone()

            if (
                post_owner
                and post_owner["created_by"]
                and post_owner["created_by"] != current_user["id"]
            ):

                cur.execute("""
                    INSERT INTO notifications (
                        user_id,
                        title,
                        message,
                        notification_type,
                        is_read
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        FALSE
                    )
                """, (
                    post_owner["created_by"],
                    "Content Rejected",
                    f"Your post '{approval['title'] or 'Untitled post'}' was rejected.",
                    "approval"
                ))

    log_activity(
        user_id=current_user["id"],
        brand_id=approval["brand_id"],
        action="rejected_content",
        entity_type="content_approval",
        entity_id=approval_id,
        description=(
            f"Rejected content: "
            f"{approval['title'] or 'Untitled post'}."
        )
    )

    flash(
        "Content rejected successfully.",
        "success"
    )

    return redirect(url_for("approvals"))


# =========================================================
# CALENDAR
# =========================================================

@app.route("/calendar")
@login_required
def calendar():

    selected_brand = request.args.get(
        "brand_id",
        ""
    ).strip()

    selected_status = request.args.get(
        "status",
        ""
    ).strip().lower()

    conn = get_db_connection()

    try:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, name, is_active
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
            """)

            brands = cur.fetchall()

            query = """
                SELECT
                    p.id,
                    p.brand_id,
                    p.created_by,
                    p.title,
                    p.content,
                    p.media_url,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,
                    p.updated_at,
                    b.name AS brand_name,
                    u.name AS creator_name,

                    COALESCE(
                        STRING_AGG(
                            DISTINCT sa.platform,
                            ', '
                            ORDER BY sa.platform
                        ),
                        ''
                    ) AS platforms,

                    COALESCE(
                        STRING_AGG(
                            DISTINCT sa.account_name,
                            ', '
                            ORDER BY sa.account_name
                        ),
                        ''
                    ) AS account_names

                FROM posts p

                INNER JOIN brands b
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

            if selected_brand:

                try:

                    brand_id = int(selected_brand)

                    query += """
                        AND p.brand_id = %s
                    """

                    params.append(brand_id)

                except ValueError:

                    selected_brand = ""

            if selected_status in [
                "draft",
                "scheduled",
                "published"
            ]:

                query += """
                    AND LOWER(p.status) = %s
                """

                params.append(selected_status)

            query += """
                GROUP BY
                    p.id,
                    p.brand_id,
                    p.created_by,
                    p.title,
                    p.content,
                    p.media_url,
                    p.status,
                    p.scheduled_at,
                    p.published_at,
                    p.created_at,
                    p.updated_at,
                    b.name,
                    u.name

                ORDER BY
                    COALESCE(
                        p.scheduled_at,
                        p.published_at,
                        p.created_at
                    ) ASC,
                    p.id ASC
            """

            cur.execute(
                query,
                params
            )

            posts = cur.fetchall()

            cur.execute("""
                SELECT
                    COUNT(*) AS total_posts,
                    COUNT(*) FILTER (
                        WHERE LOWER(status) = 'draft'
                    ) AS draft_posts,
                    COUNT(*) FILTER (
                        WHERE LOWER(status) = 'scheduled'
                    ) AS scheduled_posts,
                    COUNT(*) FILTER (
                        WHERE LOWER(status) = 'published'
                    ) AS published_posts
                FROM posts
            """)

            stats = cur.fetchone()

            cur.execute("""
                SELECT
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    p.scheduled_at,
                    b.name AS brand_name,

                    COALESCE(
                        STRING_AGG(
                            DISTINCT sa.platform,
                            ', '
                            ORDER BY sa.platform
                        ),
                        ''
                    ) AS platforms

                FROM posts p

                INNER JOIN brands b
                    ON b.id = p.brand_id

                LEFT JOIN post_platforms pp
                    ON pp.post_id = p.id

                LEFT JOIN social_accounts sa
                    ON sa.id = pp.social_account_id

                WHERE LOWER(p.status) = 'scheduled'
                AND p.scheduled_at IS NOT NULL
                AND p.scheduled_at >= CURRENT_TIMESTAMP

                GROUP BY
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    p.scheduled_at,
                    b.name

                ORDER BY p.scheduled_at ASC

                LIMIT 8
            """)

            upcoming_posts = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        "calendar.html",
        posts=posts,
        brands=brands,
        upcoming_posts=upcoming_posts,
        stats=stats,
        selected_brand=selected_brand,
        selected_status=selected_status
    )


# =========================================================
# COMMUNITY
# =========================================================

@app.route("/community")
@login_required
def community():

    search = request.args.get("search", "").strip()
    brand_id = request.args.get("brand_id", "").strip()
    platform = request.args.get("platform", "").strip()
    status = request.args.get("status", "").strip()

    query = """
        SELECT
            cc.id,
            cc.brand_id,
            cc.social_account_id,
            cc.external_comment_id,
            cc.author_name,
            cc.author_username,
            cc.content,
            cc.status,
            cc.reply,
            cc.replied_at,
            cc.created_at,
            b.name AS brand_name,
            sa.platform,
            sa.account_name,
            sa.username AS account_username

        FROM community_comments cc

        LEFT JOIN brands b
            ON b.id = cc.brand_id

        LEFT JOIN social_accounts sa
            ON sa.id = cc.social_account_id

        WHERE 1 = 1
    """

    params = []

    if search:

        query += """
            AND (
                cc.author_name ILIKE %s
                OR cc.author_username ILIKE %s
                OR cc.content ILIKE %s
                OR b.name ILIKE %s
                OR sa.account_name ILIKE %s
                OR sa.username ILIKE %s
            )
        """

        value = f"%{search}%"

        params.extend([
            value,
            value,
            value,
            value,
            value,
            value
        ])

    if brand_id:

        try:

            brand_id_value = int(brand_id)

            query += """
                AND cc.brand_id = %s
            """

            params.append(brand_id_value)

        except ValueError:

            brand_id = ""

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
        ORDER BY
            CASE
                WHEN cc.status = 'pending' THEN 0
                WHEN cc.status = 'unread' THEN 1
                ELSE 2
            END,
            cc.created_at DESC
    """

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute(
                query,
                params
            )

            comments = cur.fetchall()

            cur.execute("""
                SELECT id, name
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
            """)

            available_brands = cur.fetchall()

            cur.execute("""
                SELECT DISTINCT platform
                FROM social_accounts
                WHERE platform IS NOT NULL
                ORDER BY platform ASC
            """)

            available_platforms = [
                row["platform"]
                for row in cur.fetchall()
            ]

            cur.execute("""
                SELECT COUNT(*)
                FROM community_comments
            """)

            total_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM community_comments
                WHERE status IN ('pending', 'unread')
            """)

            pending_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM community_comments
                WHERE status = 'resolved'
            """)

            resolved_count = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM community_comments
                WHERE reply IS NOT NULL
                AND reply <> ''
            """)

            replied_count = cur.fetchone()["count"]

    return render_template(
        "community.html",
        comments=comments,
        available_brands=available_brands,
        available_platforms=available_platforms,
        search=search,
        selected_brand=brand_id,
        selected_platform=platform,
        selected_status=status,
        total_count=total_count,
        pending_count=pending_count,
        resolved_count=resolved_count,
        replied_count=replied_count,
    )


@app.route(
    "/community/<int:comment_id>/reply",
    methods=["POST"]
)
@login_required
def community_reply(comment_id):

    reply = request.form.get(
        "reply",
        ""
    ).strip()

    if not reply:

        flash(
            "Please write a reply before sending.",
            "danger"
        )

        return redirect(url_for("community"))

    if len(reply) > 5000:

        flash(
            "Reply cannot exceed 5000 characters.",
            "danger"
        )

        return redirect(url_for("community"))

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, brand_id, author_name
                FROM community_comments
                WHERE id = %s
            """, (comment_id,))

            comment = cur.fetchone()

            if not comment:

                flash(
                    "The selected conversation could not be found.",
                    "danger"
                )

                return redirect(url_for("community"))

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

    current_user = get_current_user()

    log_activity(
        user_id=current_user["id"],
        brand_id=comment["brand_id"],
        action="replied_to_community_comment",
        entity_type="community_comment",
        entity_id=comment_id,
        description=(
            f"Replied to community comment from "
            f"{comment['author_name'] or 'Unknown User'}."
        )
    )

    flash(
        "Reply sent successfully.",
        "success"
    )

    return redirect(url_for("community"))


@app.route(
    "/community/<int:comment_id>/resolve",
    methods=["POST"]
)
@login_required
def community_resolve(comment_id):

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT id, brand_id, author_name
                FROM community_comments
                WHERE id = %s
            """, (comment_id,))

            comment = cur.fetchone()

            if not comment:

                flash(
                    "The selected conversation could not be found.",
                    "danger"
                )

                return redirect(url_for("community"))

            cur.execute("""
                UPDATE community_comments
                SET status = 'resolved'
                WHERE id = %s
            """, (comment_id,))

    current_user = get_current_user()

    log_activity(
        user_id=current_user["id"],
        brand_id=comment["brand_id"],
        action="resolved_community_comment",
        entity_type="community_comment",
        entity_id=comment_id,
        description=(
            f"Resolved community conversation from "
            f"{comment['author_name'] or 'Unknown User'}."
        )
    )

    flash(
        "Conversation marked as resolved.",
        "success"
    )

    return redirect(url_for("community"))


# =========================================================
# OTHER PAGES
# =========================================================

# =========================================================
# LISTENING KEYWORD MANAGEMENT
# =========================================================

# SOCIAL LISTENING
# =========================================================

@app.route("/listening")
@login_required
def listening():

    user = get_current_user()

    brand_id = request.args.get("brand_id", "").strip()
    platform = request.args.get("platform", "").strip()
    sentiment = request.args.get("sentiment", "").strip()
    status = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()

    params = []

    mention_query = """
        SELECT
            sm.id,
            sm.brand_id,
            sm.keyword_id,
            sm.platform,
            sm.author_name,
            sm.author_username,
            sm.content,
            sm.mention_url,
            sm.sentiment,
            sm.status,
            sm.mentioned_at,
            b.name AS brand_name,
            lk.keyword AS keyword
        FROM social_mentions sm
        LEFT JOIN brands b
            ON b.id = sm.brand_id
        LEFT JOIN listening_keywords lk
            ON lk.id = sm.keyword_id
        WHERE 1 = 1
    """

    if brand_id:
        try:
            brand_id_value = int(brand_id)
            mention_query += " AND sm.brand_id = %s "
            params.append(brand_id_value)
        except ValueError:
            brand_id = ""

    if platform:
        mention_query += " AND sm.platform = %s "
        params.append(platform)

    if sentiment:
        mention_query += " AND sm.sentiment = %s "
        params.append(sentiment)

    if status:
        mention_query += " AND sm.status = %s "
        params.append(status)

    if search:
        search_value = f"%{search}%"
        mention_query += """
            AND (
                sm.content ILIKE %s
                OR sm.author_name ILIKE %s
                OR sm.author_username ILIKE %s
                OR lk.keyword ILIKE %s
                OR b.name ILIKE %s
            )
        """
        params.extend([
            search_value,
            search_value,
            search_value,
            search_value,
            search_value
        ])

    mention_query += """
        ORDER BY
            sm.mentioned_at DESC NULLS LAST,
            sm.id DESC
        LIMIT 100
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(mention_query, params)
            mentions = cur.fetchall()

            cur.execute("""
                SELECT id, name
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
            """)
            available_brands = cur.fetchall()

            keyword_query = """
                SELECT
                    lk.id,
                    lk.brand_id,
                    lk.keyword,
                    lk.is_active,
                    lk.created_at,
                    b.name AS brand_name
                FROM listening_keywords lk
                LEFT JOIN brands b
                    ON b.id = lk.brand_id
                WHERE 1 = 1
            """

            keyword_params = []

            if brand_id:
                try:
                    keyword_query += " AND lk.brand_id = %s "
                    keyword_params.append(int(brand_id))
                except ValueError:
                    pass

            keyword_query += """
                ORDER BY
                    lk.is_active DESC,
                    lk.keyword ASC
            """

            cur.execute(keyword_query, keyword_params)
            keywords = cur.fetchall()

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_mentions
            """)
            total_mentions = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM listening_keywords
                WHERE is_active = TRUE
            """)
            active_keywords = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_mentions
                WHERE LOWER(COALESCE(sentiment, '')) = 'positive'
            """)
            positive_mentions = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_mentions
                WHERE LOWER(COALESCE(sentiment, '')) = 'negative'
            """)
            negative_mentions = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_mentions
                WHERE LOWER(COALESCE(sentiment, '')) = 'neutral'
            """)
            neutral_mentions = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM social_mentions
                WHERE LOWER(COALESCE(status, '')) IN (
                    'new',
                    'unread',
                    'open'
                )
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
        available_brands=available_brands,
        total_mentions=total_mentions,
        active_keywords=active_keywords,
        positive_mentions=positive_mentions,
        negative_mentions=negative_mentions,
        neutral_mentions=neutral_mentions,
        new_mentions=new_mentions,
        platform_counts=platform_counts,
        selected_brand=brand_id,
        selected_platform=platform,
        selected_sentiment=sentiment,
        selected_status=status,
        search=search,
        platforms=[
            "Facebook",
            "Instagram",
            "LinkedIn",
            "X",
            "YouTube",
            "TikTok",
            "Pinterest"
        ]
    )




@app.route("/listening/keywords/create", methods=["POST"])
@login_required
def create_listening_keyword():

    user = get_current_user()

    brand_id = request.form.get("brand_id", "").strip()
    keyword = request.form.get("keyword", "").strip()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not brand_id:

        flash(
            "Please select a brand.",
            "danger"
        )

        return redirect(
            url_for("listening")
        )

    if not keyword:

        flash(
            "Please enter a listening keyword.",
            "danger"
        )

        return redirect(
            url_for(
                "listening",
                brand_id=brand_id
            )
        )

    if len(keyword) > 150:

        flash(
            "Keyword cannot exceed 150 characters.",
            "danger"
        )

        return redirect(
            url_for(
                "listening",
                brand_id=brand_id
            )
        )


    # -----------------------------------------------------
    # CLEAN KEYWORD
    # -----------------------------------------------------

    keyword = keyword.lstrip("#").strip()

    if not keyword:

        flash(
            "Please enter a valid keyword.",
            "danger"
        )

        return redirect(
            url_for(
                "listening",
                brand_id=brand_id
            )
        )


    try:

        brand_id_value = int(brand_id)

    except ValueError:

        flash(
            "Invalid brand selected.",
            "danger"
        )

        return redirect(
            url_for("listening")
        )


    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            # ---------------------------------------------
            # VERIFY BRAND
            # ---------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name
                FROM brands
                WHERE id = %s
                  AND is_active = TRUE
            """, (brand_id_value,))

            brand = cur.fetchone()

            if not brand:

                flash(
                    "Selected brand is invalid or inactive.",
                    "danger"
                )

                return redirect(
                    url_for("listening")
                )


            # ---------------------------------------------
            # DUPLICATE CHECK
            # ---------------------------------------------

            cur.execute("""
                SELECT
                    id
                FROM listening_keywords
                WHERE brand_id = %s
                  AND LOWER(keyword) = LOWER(%s)
                LIMIT 1
            """, (
                brand_id_value,
                keyword
            ))

            existing = cur.fetchone()

            if existing:

                flash(
                    "This keyword already exists for the selected brand.",
                    "warning"
                )

                return redirect(
                    url_for(
                        "listening",
                        brand_id=brand_id_value
                    )
                )


            # ---------------------------------------------
            # CREATE
            # ---------------------------------------------

            cur.execute("""
                INSERT INTO listening_keywords (
                    brand_id,
                    keyword,
                    is_active,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    TRUE,
                    CURRENT_TIMESTAMP
                )
                RETURNING id
            """, (
                brand_id_value,
                keyword
            ))

            new_keyword = cur.fetchone()


        conn.commit()


    # -----------------------------------------------------
    # ACTIVITY LOG
    # -----------------------------------------------------

    log_activity(
        user_id=user["id"],
        brand_id=brand_id_value,
        action="created_listening_keyword",
        entity_type="listening_keyword",
        entity_id=new_keyword["id"],
        description=(
            f"Created listening keyword "
            f"'{keyword}' for brand '{brand['name']}.'"
        )
    )


    flash(
        f"Listening keyword '{keyword}' added successfully.",
        "success"
    )

    return redirect(
        url_for(
            "listening",
            brand_id=brand_id_value
        )
    )


# =========================================================
# TOGGLE KEYWORD
# =========================================================

@app.route(
    "/listening/keywords/<int:keyword_id>/toggle",
    methods=["POST"]
)
@login_required
def toggle_listening_keyword(keyword_id):

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    lk.id,
                    lk.brand_id,
                    lk.keyword,
                    lk.is_active,

                    b.name AS brand_name

                FROM listening_keywords lk

                LEFT JOIN brands b
                    ON b.id = lk.brand_id

                WHERE lk.id = %s
            """, (keyword_id,))

            keyword = cur.fetchone()

            if not keyword:

                flash(
                    "Listening keyword could not be found.",
                    "danger"
                )

                return redirect(
                    url_for("listening")
                )


            new_status = not keyword["is_active"]


            cur.execute("""
                UPDATE listening_keywords
                SET is_active = %s
                WHERE id = %s
            """, (
                new_status,
                keyword_id
            ))


        conn.commit()


    # -----------------------------------------------------
    # ACTIVITY LOG
    # -----------------------------------------------------

    action_text = (
        "activated"
        if new_status
        else
        "paused"
    )


    log_activity(
        user_id=user["id"],
        brand_id=keyword["brand_id"],
        action=f"{action_text}_listening_keyword",
        entity_type="listening_keyword",
        entity_id=keyword_id,
        description=(
            f"{action_text.capitalize()} listening keyword "
            f"'{keyword['keyword']}'."
        )
    )


    flash(
        f"Keyword '{keyword['keyword']}' "
        f"{action_text} successfully.",
        "success"
    )

    return redirect(
        url_for(
            "listening",
            brand_id=keyword["brand_id"]
        )
    )


# =========================================================
# DELETE KEYWORD
# =========================================================

@app.route(
    "/listening/keywords/<int:keyword_id>/delete",
    methods=["POST"]
)
@login_required
def delete_listening_keyword(keyword_id):

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    brand_id,
                    keyword
                FROM listening_keywords
                WHERE id = %s
            """, (keyword_id,))

            keyword = cur.fetchone()

            if not keyword:

                flash(
                    "Listening keyword could not be found.",
                    "danger"
                )

                return redirect(
                    url_for("listening")
                )


            # ---------------------------------------------
            # DELETE
            # ---------------------------------------------

            cur.execute("""
                DELETE FROM listening_keywords
                WHERE id = %s
            """, (keyword_id,))


        conn.commit()


    # -----------------------------------------------------
    # ACTIVITY LOG
    # -----------------------------------------------------

    log_activity(
        user_id=user["id"],
        brand_id=keyword["brand_id"],
        action="deleted_listening_keyword",
        entity_type="listening_keyword",
        entity_id=keyword_id,
        description=(
            f"Deleted listening keyword "
            f"'{keyword['keyword']}'."
        )
    )


    flash(
        f"Keyword '{keyword['keyword']}' deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "listening",
            brand_id=keyword["brand_id"]
        )
    )

# =========================================================
# ANALYTICS / INSIGHTS
# =========================================================

@app.route("/analytics")
@login_required
def analytics():

    user = get_current_user()

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    brand_id = request.args.get("brand_id", "").strip()
    platform = request.args.get("platform", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # -----------------------------------------------------
    # DEFAULT DATE RANGE
    # -----------------------------------------------------

    if not date_from:
        date_from = "2026-09-04"

    if not date_to:
        date_to = datetime.now().strftime("%Y-%m-%d")

    # -----------------------------------------------------
    # VALIDATE BRAND
    # -----------------------------------------------------

    brand_id_value = None

    if brand_id:
        try:
            brand_id_value = int(brand_id)
        except ValueError:
            brand_id = ""
            brand_id_value = None

    # -----------------------------------------------------
    # BASE FILTER
    # -----------------------------------------------------

    where_parts = [
        "a.metric_date >= %s",
        "a.metric_date <= %s"
    ]

    params = [
        date_from,
        date_to
    ]

    if brand_id_value:
        where_parts.append("a.brand_id = %s")
        params.append(brand_id_value)

    if platform:
        where_parts.append("sa.platform = %s")
        params.append(platform)

    where_sql = " AND ".join(where_parts)

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            # =================================================
            # BRANDS
            # =================================================

            cur.execute("""
                SELECT
                    id,
                    name
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
            """)

            available_brands = cur.fetchall()

            # =================================================
            # KPI TOTALS
            # =================================================

            cur.execute(
                f"""
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
                    WHERE {where_sql}
                """,
                params
            )

            totals = cur.fetchone()

            impressions = totals["impressions"] or 0
            reach = totals["reach"] or 0
            likes = totals["likes"] or 0
            comments = totals["comments"] or 0
            shares = totals["shares"] or 0
            clicks = totals["clicks"] or 0
            followers = totals["followers"] or 0

            engagement = (
                likes +
                comments +
                shares
            )

            engagement_rate = 0

            if reach:
                engagement_rate = round(
                    (engagement / reach) * 100,
                    2
                )

            click_rate = 0

            if impressions:
                click_rate = round(
                    (clicks / impressions) * 100,
                    2
                )

            # =================================================
            # DAILY PERFORMANCE TREND
            # =================================================

            cur.execute(
                f"""
                    SELECT
                        a.metric_date,
                        COALESCE(SUM(a.impressions), 0) AS impressions,
                        COALESCE(SUM(a.reach), 0) AS reach,
                        COALESCE(SUM(a.likes), 0) AS likes,
                        COALESCE(SUM(a.comments), 0) AS comments,
                        COALESCE(SUM(a.shares), 0) AS shares,
                        COALESCE(SUM(a.clicks), 0) AS clicks
                    FROM analytics a
                    LEFT JOIN social_accounts sa
                        ON sa.id = a.social_account_id
                    WHERE {where_sql}
                    GROUP BY a.metric_date
                    ORDER BY a.metric_date ASC
                """,
                params
            )

            trend_data = cur.fetchall()

            # =================================================
            # PLATFORM PERFORMANCE
            # =================================================

            cur.execute(
                f"""
                    SELECT
                        COALESCE(sa.platform, 'Unknown') AS platform,
                        COALESCE(SUM(a.impressions), 0) AS impressions,
                        COALESCE(SUM(a.reach), 0) AS reach,
                        COALESCE(SUM(a.likes), 0) AS likes,
                        COALESCE(SUM(a.comments), 0) AS comments,
                        COALESCE(SUM(a.shares), 0) AS shares,
                        COALESCE(SUM(a.clicks), 0) AS clicks
                    FROM analytics a
                    LEFT JOIN social_accounts sa
                        ON sa.id = a.social_account_id
                    WHERE {where_sql}
                    GROUP BY sa.platform
                    ORDER BY impressions DESC
                """,
                params
            )

            platform_data = cur.fetchall()

            # =================================================
            # TOP CONTENT
            # =================================================

            cur.execute(
                f"""
                    SELECT
                        a.post_id,
                        COALESCE(p.title, 'Untitled Post') AS title,
                        COALESCE(p.content, '') AS content,
                        COALESCE(b.name, 'Unknown Brand') AS brand_name,
                        COALESCE(SUM(a.impressions), 0) AS impressions,
                        COALESCE(SUM(a.reach), 0) AS reach,
                        COALESCE(SUM(a.likes), 0) AS likes,
                        COALESCE(SUM(a.comments), 0) AS comments,
                        COALESCE(SUM(a.shares), 0) AS shares,
                        COALESCE(SUM(a.clicks), 0) AS clicks
                    FROM analytics a
                    LEFT JOIN posts p
                        ON p.id = a.post_id
                    LEFT JOIN brands b
                        ON b.id = a.brand_id
                    LEFT JOIN social_accounts sa
                        ON sa.id = a.social_account_id
                    WHERE {where_sql}
                      AND a.post_id IS NOT NULL
                    GROUP BY
                        a.post_id,
                        p.title,
                        p.content,
                        b.name
                    ORDER BY
                        (
                            COALESCE(SUM(a.likes), 0) +
                            COALESCE(SUM(a.comments), 0) +
                            COALESCE(SUM(a.shares), 0)
                        ) DESC,
                        COALESCE(SUM(a.impressions), 0) DESC
                    LIMIT 10
                """,
                params
            )

            top_posts = cur.fetchall()

            # =================================================
            # FOLLOWER TREND
            # =================================================

            cur.execute(
                f"""
                    SELECT
                        a.metric_date,
                        COALESCE(SUM(a.followers), 0) AS followers
                    FROM analytics a
                    LEFT JOIN social_accounts sa
                        ON sa.id = a.social_account_id
                    WHERE {where_sql}
                    GROUP BY a.metric_date
                    ORDER BY a.metric_date ASC
                """,
                params
            )

            follower_data = cur.fetchall()

            # =================================================
            # DETAILED ANALYTICS
            # =================================================

            cur.execute(
                f"""
                    SELECT
                        a.metric_date,
                        COALESCE(b.name, 'Unknown') AS brand_name,
                        COALESCE(sa.platform, 'Unknown') AS platform,
                        COALESCE(a.impressions, 0) AS impressions,
                        COALESCE(a.reach, 0) AS reach,
                        COALESCE(a.likes, 0) AS likes,
                        COALESCE(a.comments, 0) AS comments,
                        COALESCE(a.shares, 0) AS shares,
                        COALESCE(a.clicks, 0) AS clicks,
                        COALESCE(a.followers, 0) AS followers
                    FROM analytics a
                    LEFT JOIN brands b
                        ON b.id = a.brand_id
                    LEFT JOIN social_accounts sa
                        ON sa.id = a.social_account_id
                    WHERE {where_sql}
                    ORDER BY
                        a.metric_date DESC,
                        a.id DESC
                    LIMIT 100
                """,
                params
            )

            analytics_rows = cur.fetchall()

    # -----------------------------------------------------
    # CHART DATA
    # -----------------------------------------------------

    chart_dates = []
    chart_impressions = []
    chart_reach = []
    chart_engagement = []
    chart_clicks = []

    for row in trend_data:

        metric_date = row["metric_date"]

        if hasattr(metric_date, "strftime"):
            label = metric_date.strftime("%b %d")
        else:
            label = str(metric_date)

        chart_dates.append(label)

        chart_impressions.append(
            int(row["impressions"] or 0)
        )

        chart_reach.append(
            int(row["reach"] or 0)
        )

        chart_engagement.append(
            int(
                (row["likes"] or 0) +
                (row["comments"] or 0) +
                (row["shares"] or 0)
            )
        )

        chart_clicks.append(
            int(row["clicks"] or 0)
        )

    # -----------------------------------------------------
    # PLATFORM CHART DATA
    # -----------------------------------------------------

    platform_labels = []
    platform_impressions = []
    platform_reach = []

    for row in platform_data:

        platform_labels.append(
            row["platform"] or "Unknown"
        )

        platform_impressions.append(
            int(row["impressions"] or 0)
        )

        platform_reach.append(
            int(row["reach"] or 0)
        )

    # -----------------------------------------------------
    # FOLLOWER CHART DATA
    # -----------------------------------------------------

    follower_dates = []
    follower_values = []

    for row in follower_data:

        metric_date = row["metric_date"]

        if hasattr(metric_date, "strftime"):
            label = metric_date.strftime("%b %d")
        else:
            label = str(metric_date)

        follower_dates.append(label)

        follower_values.append(
            int(row["followers"] or 0)
        )

    return render_template(
        "analytics.html",

        # Filters
        available_brands=available_brands,
        selected_brand=brand_id,
        selected_platform=platform,
        date_from=date_from,
        date_to=date_to,

        # KPIs
        impressions=impressions,
        reach=reach,
        engagement=engagement,
        clicks=clicks,
        followers=followers,
        engagement_rate=engagement_rate,
        click_rate=click_rate,

        # Tables
        platform_data=platform_data,
        top_posts=top_posts,
        analytics_rows=analytics_rows,

        # Charts
        chart_dates=chart_dates,
        chart_impressions=chart_impressions,
        chart_reach=chart_reach,
        chart_engagement=chart_engagement,
        chart_clicks=chart_clicks,

        platform_labels=platform_labels,
        platform_impressions=platform_impressions,
        platform_reach=platform_reach,

        follower_dates=follower_dates,
        follower_values=follower_values
    )
# =========================================================
# REPORTS
# =========================================================

@app.route("/reports")
@login_required
def reports():

    user = get_current_user()

    brand_id = request.args.get("brand_id", "").strip()
    report_type = request.args.get("report_type", "").strip()
    search = request.args.get("search", "").strip()

    brand_id_value = None

    if brand_id:
        try:
            brand_id_value = int(brand_id)
        except ValueError:
            brand_id = ""
            brand_id_value = None

    where_parts = []
    params = []

    if brand_id_value:
        where_parts.append("r.brand_id = %s")
        params.append(brand_id_value)

    if report_type:
        where_parts.append("r.report_type = %s")
        params.append(report_type)

    if search:
        where_parts.append("""
            (
                r.name ILIKE %s
                OR b.name ILIKE %s
            )
        """)

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value
        ])

    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)
    else:
        where_sql = ""

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # BRANDS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name
                FROM brands
                WHERE is_active = TRUE
                ORDER BY name ASC
            """)

            available_brands = cur.fetchall()

            # -------------------------------------------------
            # REPORTS
            # -------------------------------------------------

            cur.execute(
                f"""
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
                        u.name AS creator_name
                    FROM reports r
                    LEFT JOIN brands b
                        ON b.id = r.brand_id
                    LEFT JOIN users u
                        ON u.id = r.created_by
                    {where_sql}
                    ORDER BY
                        r.created_at DESC,
                        r.id DESC
                """,
                params
            )

            report_rows = cur.fetchall()

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM reports
            """)

            total_reports = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM reports
                WHERE created_at >= CURRENT_DATE
            """)

            reports_today = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM reports
                WHERE report_type = 'Performance'
            """)

            performance_reports = cur.fetchone()["count"]

            cur.execute("""
                SELECT COUNT(*)
                FROM reports
                WHERE report_type = 'Engagement'
            """)

            engagement_reports = cur.fetchone()["count"]

            # -------------------------------------------------
            # REPORT TYPE BREAKDOWN
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    COALESCE(report_type, 'Other') AS report_type,
                    COUNT(*) AS count
                FROM reports
                GROUP BY report_type
                ORDER BY count DESC
            """)

            report_type_counts = cur.fetchall()

    return render_template(
        "reports.html",
        available_brands=available_brands,
        report_rows=report_rows,
        total_reports=total_reports,
        reports_today=reports_today,
        performance_reports=performance_reports,
        engagement_reports=engagement_reports,
        report_type_counts=report_type_counts,
        selected_brand=brand_id,
        selected_report_type=report_type,
        search=search,
        report_types=[
            "Performance",
            "Engagement",
            "Audience",
            "Content",
            "Platform",
            "Custom"
        ]
    )


# =========================================================
# CREATE REPORT
# =========================================================

@app.route("/reports/create", methods=["POST"])
@login_required
def create_report():

    user = get_current_user()

    brand_id = request.form.get("brand_id", "").strip()
    name = request.form.get("name", "").strip()
    period_start = request.form.get("period_start", "").strip()
    period_end = request.form.get("period_end", "").strip()
    report_type = request.form.get("report_type", "").strip()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not brand_id:
        flash("Please select a brand.", "danger")
        return redirect(url_for("reports"))

    if not name:
        flash("Please enter a report name.", "danger")
        return redirect(url_for("reports", brand_id=brand_id))

    if len(name) > 150:
        flash(
            "Report name cannot exceed 150 characters.",
            "danger"
        )
        return redirect(url_for("reports", brand_id=brand_id))

    if not period_start or not period_end:
        flash(
            "Please select the report period.",
            "danger"
        )
        return redirect(url_for("reports", brand_id=brand_id))

    if period_start > period_end:
        flash(
            "Report start date cannot be after the end date.",
            "danger"
        )
        return redirect(url_for("reports", brand_id=brand_id))

    allowed_types = [
        "Performance",
        "Engagement",
        "Audience",
        "Content",
        "Platform",
        "Custom"
    ]

    if report_type not in allowed_types:
        flash(
            "Please select a valid report type.",
            "danger"
        )
        return redirect(url_for("reports", brand_id=brand_id))

    try:
        brand_id_value = int(brand_id)
    except ValueError:
        flash("Invalid brand selected.", "danger")
        return redirect(url_for("reports"))

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # VERIFY BRAND
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    id,
                    name
                FROM brands
                WHERE id = %s
                  AND is_active = TRUE
            """, (brand_id_value,))

            brand = cur.fetchone()

            if not brand:

                flash(
                    "Selected brand is invalid or inactive.",
                    "danger"
                )

                return redirect(url_for("reports"))

            # -------------------------------------------------
            # CREATE REPORT
            # -------------------------------------------------

            cur.execute("""
                INSERT INTO reports (
                    brand_id,
                    created_by,
                    name,
                    period_start,
                    period_end,
                    report_type,
                    file_url,
                    created_at
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    NULL,
                    CURRENT_TIMESTAMP
                )
                RETURNING id
            """, (
                brand_id_value,
                user["id"],
                name,
                period_start,
                period_end,
                report_type
            ))

            new_report = cur.fetchone()

        conn.commit()

    log_activity(
        user_id=user["id"],
        brand_id=brand_id_value,
        action="created_report",
        entity_type="report",
        entity_id=new_report["id"],
        description=(
            f"Created report '{name}' "
            f"for brand '{brand['name']}'."
        )
    )

    flash(
        f"Report '{name}' created successfully.",
        "success"
    )

    return redirect(url_for("reports"))


# =========================================================
# VIEW REPORT
# =========================================================

@app.route("/reports/<int:report_id>")
@login_required
def view_report(report_id):

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # REPORT
            # -------------------------------------------------

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
                    u.name AS creator_name
                FROM reports r
                LEFT JOIN brands b
                    ON b.id = r.brand_id
                LEFT JOIN users u
                    ON u.id = r.created_by
                WHERE r.id = %s
            """, (report_id,))

            report = cur.fetchone()

            if not report:

                flash(
                    "Report could not be found.",
                    "danger"
                )

                return redirect(url_for("reports"))

            # -------------------------------------------------
            # ANALYTICS SUMMARY
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    COALESCE(SUM(impressions), 0) AS impressions,
                    COALESCE(SUM(reach), 0) AS reach,
                    COALESCE(SUM(likes), 0) AS likes,
                    COALESCE(SUM(comments), 0) AS comments,
                    COALESCE(SUM(shares), 0) AS shares,
                    COALESCE(SUM(clicks), 0) AS clicks,
                    COALESCE(MAX(followers), 0) AS followers
                FROM analytics
                WHERE brand_id = %s
                  AND metric_date >= %s
                  AND metric_date <= %s
            """, (
                report["brand_id"],
                report["period_start"],
                report["period_end"]
            ))

            analytics_summary = cur.fetchone()

            # -------------------------------------------------
            # PLATFORM BREAKDOWN
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    COALESCE(sa.platform, 'Unknown') AS platform,
                    COALESCE(SUM(a.impressions), 0) AS impressions,
                    COALESCE(SUM(a.reach), 0) AS reach,
                    COALESCE(SUM(a.likes), 0) AS likes,
                    COALESCE(SUM(a.comments), 0) AS comments,
                    COALESCE(SUM(a.shares), 0) AS shares,
                    COALESCE(SUM(a.clicks), 0) AS clicks
                FROM analytics a
                LEFT JOIN social_accounts sa
                    ON sa.id = a.social_account_id
                WHERE a.brand_id = %s
                  AND a.metric_date >= %s
                  AND a.metric_date <= %s
                GROUP BY sa.platform
                ORDER BY impressions DESC
            """, (
                report["brand_id"],
                report["period_start"],
                report["period_end"]
            ))

            platform_breakdown = cur.fetchall()

    engagement = (
        (analytics_summary["likes"] or 0)
        +
        (analytics_summary["comments"] or 0)
        +
        (analytics_summary["shares"] or 0)
    )

    engagement_rate = 0

    if analytics_summary["reach"]:
        engagement_rate = round(
            (
                engagement /
                analytics_summary["reach"]
            ) * 100,
            2
        )

    return render_template(
        "report_view.html",
        report=report,
        analytics_summary=analytics_summary,
        platform_breakdown=platform_breakdown,
        engagement=engagement,
        engagement_rate=engagement_rate
    )


# =========================================================
# DELETE REPORT
# =========================================================

@app.route(
    "/reports/<int:report_id>/delete",
    methods=["POST"]
)
@login_required
def delete_report(report_id):

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    brand_id,
                    name
                FROM reports
                WHERE id = %s
            """, (report_id,))

            report = cur.fetchone()

            if not report:

                flash(
                    "Report could not be found.",
                    "danger"
                )

                return redirect(url_for("reports"))

            cur.execute("""
                DELETE FROM reports
                WHERE id = %s
            """, (report_id,))

        conn.commit()

    log_activity(
        user_id=user["id"],
        brand_id=report["brand_id"],
        action="deleted_report",
        entity_type="report",
        entity_id=report_id,
        description=(
            f"Deleted report '{report['name']}.'"
        )
    )

    flash(
        f"Report '{report['name']}' deleted successfully.",
        "success"
    )

    return redirect(url_for("reports"))

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

    where_parts = [
        "n.user_id = %s"
    ]

    params = [
        user["id"]
    ]

    # -----------------------------------------------------
    # STATUS FILTER
    # -----------------------------------------------------

    if status == "unread":

        where_parts.append(
            "n.is_read = FALSE"
        )

    elif status == "read":

        where_parts.append(
            "n.is_read = TRUE"
        )

    # -----------------------------------------------------
    # TYPE FILTER
    # -----------------------------------------------------

    if notification_type:

        where_parts.append(
            "n.notification_type = %s"
        )

        params.append(
            notification_type
        )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    if search:

        search_value = f"%{search}%"

        where_parts.append("""
            (
                n.title ILIKE %s
                OR n.message ILIKE %s
                OR n.notification_type ILIKE %s
            )
        """)

        params.extend([
            search_value,
            search_value,
            search_value
        ])

    where_sql = " AND ".join(
        where_parts
    )

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            # -------------------------------------------------
            # NOTIFICATIONS
            # -------------------------------------------------

            cur.execute(
                f"""
                    SELECT
                        n.id,
                        n.user_id,
                        n.title,
                        n.message,
                        n.notification_type,
                        n.is_read,
                        n.created_at
                    FROM notifications n
                    WHERE {where_sql}
                    ORDER BY
                        n.created_at DESC,
                        n.id DESC
                """,
                params
            )

            notification_rows = cur.fetchall()

            # -------------------------------------------------
            # TOTAL
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
            """, (user["id"],))

            total_notifications = (
                cur.fetchone()["count"]
            )

            # -------------------------------------------------
            # UNREAD
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
                  AND is_read = FALSE
            """, (user["id"],))

            unread_notifications = (
                cur.fetchone()["count"]
            )

            # -------------------------------------------------
            # READ
            # -------------------------------------------------

            cur.execute("""
                SELECT COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
                  AND is_read = TRUE
            """, (user["id"],))

            read_notifications = (
                cur.fetchone()["count"]
            )

            # -------------------------------------------------
            # TYPE COUNTS
            # -------------------------------------------------

            cur.execute("""
                SELECT
                    COALESCE(
                        notification_type,
                        'general'
                    ) AS notification_type,
                    COUNT(*) AS count
                FROM notifications
                WHERE user_id = %s
                GROUP BY notification_type
                ORDER BY count DESC
            """, (user["id"],))

            notification_type_counts = (
                cur.fetchall()
            )

    notification_types = [
        "approval",
        "publisher",
        "community",
        "listening",
        "analytics",
        "system",
        "general"
    ]

    return render_template(
        "notifications.html",
        notification_rows=notification_rows,
        total_notifications=total_notifications,
        unread_notifications=unread_notifications,
        read_notifications=read_notifications,
        notification_type_counts=notification_type_counts,
        notification_types=notification_types,
        selected_type=notification_type,
        selected_status=status,
        search=search
    )


# =========================================================
# MARK ONE NOTIFICATION AS READ
# =========================================================

@app.route(
    "/notifications/<int:notification_id>/read",
    methods=["POST"]
)
@login_required
def mark_notification_read(notification_id):

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    title
                FROM notifications
                WHERE id = %s
                  AND user_id = %s
            """, (
                notification_id,
                user["id"]
            ))

            notification = cur.fetchone()

            if not notification:

                flash(
                    "Notification could not be found.",
                    "danger"
                )

                return redirect(
                    url_for("notifications")
                )

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

    return redirect(
        request.referrer
        or url_for("notifications")
    )


# =========================================================
# MARK ONE NOTIFICATION AS UNREAD
# =========================================================

@app.route(
    "/notifications/<int:notification_id>/unread",
    methods=["POST"]
)
@login_required
def mark_notification_unread(notification_id):

    user = get_current_user()

    with get_db_connection() as conn:

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

    return redirect(
        request.referrer
        or url_for("notifications")
    )


# =========================================================
# MARK ALL NOTIFICATIONS AS READ
# =========================================================

@app.route(
    "/notifications/read-all",
    methods=["POST"]
)
@login_required
def mark_all_notifications_read():

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                UPDATE notifications
                SET is_read = TRUE
                WHERE user_id = %s
                  AND is_read = FALSE
            """, (user["id"],))

            updated_count = cur.rowcount

        conn.commit()

    if updated_count:

        flash(
            f"{updated_count} notification(s) marked as read.",
            "success"
        )

    else:

        flash(
            "There are no unread notifications.",
            "info"
        )

    return redirect(
        url_for("notifications")
    )


# =========================================================
# DELETE ONE NOTIFICATION
# =========================================================

@app.route(
    "/notifications/<int:notification_id>/delete",
    methods=["POST"]
)
@login_required
def delete_notification(notification_id):

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    title
                FROM notifications
                WHERE id = %s
                  AND user_id = %s
            """, (
                notification_id,
                user["id"]
            ))

            notification = cur.fetchone()

            if not notification:

                flash(
                    "Notification could not be found.",
                    "danger"
                )

                return redirect(
                    url_for("notifications")
                )

            cur.execute("""
                DELETE FROM notifications
                WHERE id = %s
                  AND user_id = %s
            """, (
                notification_id,
                user["id"]
            ))

        conn.commit()

    flash(
        "Notification deleted successfully.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for("notifications")
    )


# =========================================================
# DELETE ALL READ NOTIFICATIONS
# =========================================================

@app.route(
    "/notifications/delete-read",
    methods=["POST"]
)
@login_required
def delete_read_notifications():

    user = get_current_user()

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM notifications
                WHERE user_id = %s
                  AND is_read = TRUE
            """, (user["id"],))

            deleted_count = cur.rowcount

        conn.commit()

    if deleted_count:

        flash(
            f"{deleted_count} read notification(s) deleted.",
            "success"
        )

    else:

        flash(
            "There are no read notifications to delete.",
            "info"
        )

    return redirect(
        url_for("notifications")
    )
# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings", methods=["GET", "POST"])
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

        if len(name) > 100:

            flash(
                "Name cannot exceed 100 characters.",
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

        with get_db_connection() as conn:

            with conn.cursor() as cur:

                cur.execute("""
                    SELECT id
                    FROM users
                    WHERE email = %s
                      AND id != %s
                """, (
                    email,
                    user["id"]
                ))

                existing_user = cur.fetchone()

                if existing_user:

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

        session["user_id"] = user["id"]

        log_activity(
            user_id=user["id"],
            action="updated_profile",
            entity_type="user",
            entity_id=user["id"],
            description="Updated profile information."
        )

        flash(
            "Profile information updated successfully.",
            "success"
        )

        return redirect(
            url_for("settings")
        )

    with get_db_connection() as conn:

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

    return render_template(
        "settings.html",
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

    with get_db_connection() as conn:

        with conn.cursor() as cur:

            cur.execute("""
                SELECT password_hash
                FROM users
                WHERE id = %s
            """, (user["id"],))

            account = cur.fetchone()

            if not account:

                flash(
                    "Account could not be found.",
                    "danger"
                )

                return redirect(
                    url_for("settings")
                )

            if not check_password_hash(
                account["password_hash"],
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
                account["password_hash"],
                new_password
            ):

                flash(
                    "New password must be different from your current password.",
                    "danger"
                )

                return redirect(
                    url_for("settings")
                )

            new_password_hash = generate_password_hash(
                new_password
            )

            cur.execute("""
                UPDATE users
                SET
                    password_hash = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                new_password_hash,
                user["id"]
            ))

        conn.commit()

    log_activity(
        user_id=user["id"],
        action="changed_password",
        entity_type="user",
        entity_id=user["id"],
        description="Changed account password."
    )

    flash(
        "Password changed successfully.",
        "success"
    )

    return redirect(
        url_for("settings")
    )

# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():

    try:

        conn = get_db_connection()

        try:

            with conn.cursor() as cur:

                cur.execute("SELECT 1")
                cur.fetchone()

        finally:
            conn.close()

        return jsonify({
            "status": "ok",
            "database": "connected"
        })

    except Exception as exc:

        return jsonify({
            "status": "error",
            "database": "unavailable",
            "message": str(exc)
        }), 500


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )