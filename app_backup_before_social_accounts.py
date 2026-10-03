import os
import re
from datetime import datetime, timezone
from functools import wraps

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.security import check_password_hash, generate_password_hash


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key",
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5432/ricoz_social",
)


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
    )


def init_db():
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'user',
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS brands (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    description TEXT,
                    logo_url TEXT,
                    website_url TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by INTEGER REFERENCES users(id)
                        ON DELETE SET NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS brand_members (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id)
                        ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL DEFAULT 'member',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (brand_id, user_id)
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS social_accounts (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    platform VARCHAR(50) NOT NULL,
                    account_name VARCHAR(150),
                    username VARCHAR(150),
                    account_id VARCHAR(255),
                    profile_url TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMPTZ,
                    is_connected BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    created_by INTEGER REFERENCES users(id)
                        ON DELETE SET NULL,
                    title VARCHAR(255),
                    content TEXT,
                    media_url TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'draft',
                    scheduled_at TIMESTAMPTZ,
                    published_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS post_platforms (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id)
                        ON DELETE CASCADE,
                    social_account_id INTEGER NOT NULL
                        REFERENCES social_accounts(id)
                        ON DELETE CASCADE,
                    platform_status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    external_post_id VARCHAR(255),
                    published_at TIMESTAMPTZ,
                    error_message TEXT
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS content_approvals (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id)
                        ON DELETE CASCADE,
                    submitted_by INTEGER REFERENCES users(id)
                        ON DELETE SET NULL,
                    reviewer_id INTEGER REFERENCES users(id)
                        ON DELETE SET NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'pending',
                    comments TEXT,
                    reviewed_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS community_comments (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    social_account_id INTEGER
                        REFERENCES social_accounts(id)
                        ON DELETE SET NULL,
                    external_comment_id VARCHAR(255),
                    author_name VARCHAR(150),
                    author_username VARCHAR(150),
                    content TEXT,
                    status VARCHAR(50) NOT NULL DEFAULT 'open',
                    reply TEXT,
                    replied_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS listening_keywords (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    keyword VARCHAR(255) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS social_mentions (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    keyword_id INTEGER REFERENCES listening_keywords(id)
                        ON DELETE SET NULL,
                    platform VARCHAR(50),
                    author_name VARCHAR(150),
                    author_username VARCHAR(150),
                    content TEXT,
                    mention_url TEXT,
                    sentiment VARCHAR(50),
                    status VARCHAR(50) NOT NULL DEFAULT 'new',
                    mentioned_at TIMESTAMPTZ
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    social_account_id INTEGER
                        REFERENCES social_accounts(id)
                        ON DELETE SET NULL,
                    post_id INTEGER REFERENCES posts(id)
                        ON DELETE SET NULL,
                    metric_date DATE NOT NULL,
                    impressions BIGINT NOT NULL DEFAULT 0,
                    reach BIGINT NOT NULL DEFAULT 0,
                    likes BIGINT NOT NULL DEFAULT 0,
                    comments BIGINT NOT NULL DEFAULT 0,
                    shares BIGINT NOT NULL DEFAULT 0,
                    clicks BIGINT NOT NULL DEFAULT 0,
                    followers BIGINT NOT NULL DEFAULT 0
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS reports (
                    id SERIAL PRIMARY KEY,
                    brand_id INTEGER NOT NULL REFERENCES brands(id)
                        ON DELETE CASCADE,
                    created_by INTEGER REFERENCES users(id)
                        ON DELETE SET NULL,
                    name VARCHAR(255) NOT NULL,
                    period_start DATE,
                    period_end DATE,
                    report_type VARCHAR(100),
                    file_url TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id)
                        ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    message TEXT,
                    notification_type VARCHAR(50),
                    is_read BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id)
                        ON DELETE SET NULL,
                    brand_id INTEGER REFERENCES brands(id)
                        ON DELETE SET NULL,
                    action VARCHAR(100),
                    entity_type VARCHAR(100),
                    entity_id INTEGER,
                    description TEXT,
                    ip_address VARCHAR(100),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_brands_active
                ON brands(is_active);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_brands_created_by
                ON brands(created_by);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_brand_members_brand
                ON brand_members(brand_id);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_social_accounts_brand
                ON social_accounts(brand_id);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_posts_brand
                ON posts(brand_id);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_notifications_user
                ON notifications(user_id);
                """
            )

            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_activity_logs_user
                ON activity_logs(user_id);
                """
            )

        conn.commit()

    finally:
        conn.close()


# =========================================================
# HELPERS
# =========================================================

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def get_current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    role,
                    is_active,
                    created_at
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )

            user = cur.fetchone()

    finally:
        conn.close()

    if not user or not user["is_active"]:
        session.clear()
        return None

    return user


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not get_current_user():
            flash(
                "Please sign in to continue.",
                "warning",
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
                "Please sign in to continue.",
                "warning",
            )
            return redirect(url_for("login"))

        if user["role"] != "admin":
            flash(
                "Administrator access is required for this action.",
                "danger",
            )
            return redirect(url_for("dashboard"))

        return view(*args, **kwargs)

    return wrapped_view


def log_activity(
    user_id,
    action,
    entity_type=None,
    entity_id=None,
    description=None,
    brand_id=None,
):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
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
                """,
                (
                    user_id,
                    brand_id,
                    action,
                    entity_type,
                    entity_id,
                    description,
                    request.remote_addr,
                ),
            )

        conn.commit()

    finally:
        conn.close()


def get_brand_or_404(brand_id):
    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    b.*,
                    u.name AS creator_name
                FROM brands b
                LEFT JOIN users u
                    ON u.id = b.created_by
                WHERE b.id = %s
                """,
                (brand_id,),
            )

            brand = cur.fetchone()

    finally:
        conn.close()

    return brand


# =========================================================
# GLOBAL CONTEXT
# =========================================================

@app.context_processor
def inject_global_data():
    user = get_current_user()

    pending_approvals = 0
    unread_notifications = 0

    if user:
        conn = get_db_connection()

        try:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM content_approvals
                    WHERE status = 'pending'
                    """
                )

                pending_approvals = cur.fetchone()["count"]

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM notifications
                    WHERE user_id = %s
                      AND is_read = FALSE
                    """,
                    (user["id"],),
                )

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
# AUTHENTICATION
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if get_current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password",
            "",
        )

        errors = []

        if len(name) < 2:
            errors.append(
                "Please enter your full name."
            )

        if len(name) > 120:
            errors.append(
                "Name must be 120 characters or fewer."
            )

        if not EMAIL_PATTERN.match(email):
            errors.append(
                "Please enter a valid email address."
            )

        if len(password) < 8:
            errors.append(
                "Password must contain at least 8 characters."
            )

        if len(password) > 128:
            errors.append(
                "Password must be 128 characters or fewer."
            )

        if password != confirm_password:
            errors.append(
                "Passwords do not match."
            )

        if errors:
            for error in errors:
                flash(error, "danger")

            return render_template(
                "register.html",
                name=name,
                email=email,
            )

        conn = get_db_connection()

        try:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE email = %s
                    """,
                    (email,),
                )

                existing_user = cur.fetchone()

                if existing_user:
                    flash(
                        "An account with this email already exists.",
                        "danger",
                    )

                    return render_template(
                        "register.html",
                        name=name,
                        email=email,
                    )

                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM users
                    """
                )

                total_users = cur.fetchone()["total"]

                role = (
                    "admin"
                    if total_users == 0
                    else "user"
                )

                password_hash = generate_password_hash(
                    password
                )

                cur.execute(
                    """
                    INSERT INTO users (
                        name,
                        email,
                        password_hash,
                        role
                    )
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        name,
                        email,
                        password_hash,
                        role,
                    ),
                )

                user_id = cur.fetchone()["id"]

            conn.commit()

        finally:
            conn.close()

        session.clear()
        session["user_id"] = user_id

        flash(
            "Your RicozSocial workspace is ready.",
            "success",
        )

        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if get_current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        email = request.form.get(
            "email",
            "",
        ).strip().lower()

        password = request.form.get(
            "password",
            "",
        )

        conn = get_db_connection()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM users
                    WHERE email = %s
                    """,
                    (email,),
                )

                user = cur.fetchone()

        finally:
            conn.close()

        if not user:
            flash(
                "Invalid email or password.",
                "danger",
            )

            return render_template(
                "login.html",
                email=email,
            )

        if not user["is_active"]:
            flash(
                "This account has been deactivated.",
                "danger",
            )

            return render_template(
                "login.html",
                email=email,
            )

        if not check_password_hash(
            user["password_hash"],
            password,
        ):
            flash(
                "Invalid email or password.",
                "danger",
            )

            return render_template(
                "login.html",
                email=email,
            )

        session.clear()
        session["user_id"] = user["id"]

        flash(
            f"Welcome back, {user['name'].split()[0]}.",
            "success",
        )

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():

    session.clear()

    flash(
        "You have been signed out.",
        "success",
    )

    return redirect(url_for("login"))


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

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = TRUE
                """
            )
            total_brands = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM social_accounts
                WHERE is_connected = TRUE
                """
            )
            connected_accounts = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM posts
                WHERE status = 'scheduled'
                  AND (
                      scheduled_at IS NULL
                      OR scheduled_at >= NOW()
                  )
                """
            )
            scheduled_posts = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM content_approvals
                WHERE status = 'pending'
                """
            )
            pending_approvals = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    p.scheduled_at,
                    p.created_at,
                    b.id AS brand_id,
                    b.name AS brand_name
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                ORDER BY p.created_at DESC
                LIMIT 8
                """
            )
            recent_posts = cur.fetchall()

            cur.execute(
                """
                SELECT
                    p.id,
                    p.title,
                    p.content,
                    p.status,
                    p.scheduled_at,
                    b.name AS brand_name
                FROM posts p
                JOIN brands b
                    ON b.id = p.brand_id
                WHERE p.status = 'scheduled'
                  AND p.scheduled_at IS NOT NULL
                  AND p.scheduled_at >= NOW()
                ORDER BY p.scheduled_at ASC
                LIMIT 6
                """
            )
            upcoming_posts = cur.fetchall()

            cur.execute(
                """
                SELECT
                    ca.id,
                    ca.status,
                    ca.comments,
                    ca.created_at,
                    p.id AS post_id,
                    p.title AS post_title,
                    b.name AS brand_name,
                    u.name AS submitter_name
                FROM content_approvals ca
                JOIN posts p
                    ON p.id = ca.post_id
                JOIN brands b
                    ON b.id = p.brand_id
                LEFT JOIN users u
                    ON u.id = ca.submitted_by
                WHERE ca.status = 'pending'
                ORDER BY ca.created_at DESC
                LIMIT 6
                """
            )
            approval_queue = cur.fetchall()

            cur.execute(
                """
                SELECT
                    sa.id,
                    sa.platform,
                    sa.account_name,
                    sa.username,
                    sa.profile_url,
                    sa.is_connected,
                    b.name AS brand_name
                FROM social_accounts sa
                JOIN brands b
                    ON b.id = sa.brand_id
                WHERE sa.is_connected = TRUE
                ORDER BY b.name ASC, sa.platform ASC
                LIMIT 8
                """
            )
            connected_social_accounts = cur.fetchall()

            cur.execute(
                """
                SELECT
                    al.id,
                    al.action,
                    al.entity_type,
                    al.description,
                    al.created_at,
                    b.name AS brand_name,
                    u.name AS user_name
                FROM activity_logs al
                LEFT JOIN brands b
                    ON b.id = al.brand_id
                LEFT JOIN users u
                    ON u.id = al.user_id
                ORDER BY al.created_at DESC
                LIMIT 8
                """
            )
            activity_feed = cur.fetchall()

            cur.execute(
                """
                SELECT
                    metric_date,
                    COALESCE(SUM(impressions), 0) AS impressions,
                    COALESCE(SUM(reach), 0) AS reach,
                    COALESCE(SUM(likes), 0) AS likes,
                    COALESCE(SUM(comments), 0) AS comments,
                    COALESCE(SUM(shares), 0) AS shares,
                    COALESCE(SUM(clicks), 0) AS clicks
                FROM analytics
                GROUP BY metric_date
                ORDER BY metric_date DESC
                LIMIT 14
                """
            )
            analytics_rows = cur.fetchall()

            cur.execute(
                """
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
                LIMIT 5
                """,
                (user["id"],),
            )
            dashboard_notifications = cur.fetchall()

    finally:
        conn.close()

    analytics_rows = list(reversed(analytics_rows))

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
        dashboard_notifications=dashboard_notifications,
    )


# =========================================================
# BRANDS
# =========================================================

@app.route("/brands")
@login_required
def brands():

    search = request.args.get(
        "search",
        "",
    ).strip()

    status = request.args.get(
        "status",
        "all",
    ).strip().lower()

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:

            conditions = []
            params = []

            if search:
                conditions.append(
                    """
                    (
                        b.name ILIKE %s
                        OR COALESCE(b.description, '') ILIKE %s
                        OR COALESCE(b.website_url, '') ILIKE %s
                    )
                    """
                )

                search_value = f"%{search}%"

                params.extend(
                    [
                        search_value,
                        search_value,
                        search_value,
                    ]
                )

            if status == "active":
                conditions.append(
                    "b.is_active = TRUE"
                )

            elif status == "inactive":
                conditions.append(
                    "b.is_active = FALSE"
                )

            where_sql = ""

            if conditions:
                where_sql = (
                    "WHERE "
                    + " AND ".join(conditions)
                )

            cur.execute(
                f"""
                SELECT
                    b.id,
                    b.name,
                    b.description,
                    b.logo_url,
                    b.website_url,
                    b.is_active,
                    b.created_at,
                    b.updated_at,
                    u.name AS creator_name,

                    (
                        SELECT COUNT(*)
                        FROM brand_members bm
                        WHERE bm.brand_id = b.id
                    ) AS member_count,

                    (
                        SELECT COUNT(*)
                        FROM social_accounts sa
                        WHERE sa.brand_id = b.id
                          AND sa.is_connected = TRUE
                    ) AS connected_account_count,

                    (
                        SELECT COUNT(*)
                        FROM posts p
                        WHERE p.brand_id = b.id
                    ) AS post_count

                FROM brands b

                LEFT JOIN users u
                    ON u.id = b.created_by

                {where_sql}

                ORDER BY
                    b.is_active DESC,
                    b.created_at DESC
                """,
                params,
            )

            brand_list = cur.fetchall()

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = TRUE
                """
            )

            active_count = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT COUNT(*) AS count
                FROM brands
                WHERE is_active = FALSE
                """
            )

            inactive_count = cur.fetchone()["count"]

    finally:
        conn.close()

    return render_template(
        "brands.html",
        brands=brand_list,
        search=search,
        status=status,
        active_count=active_count,
        inactive_count=inactive_count,
        total_count=active_count + inactive_count,
    )


@app.route("/brands/create", methods=["GET", "POST"])
@login_required
def create_brand():

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        ).strip()

        logo_url = request.form.get(
            "logo_url",
            "",
        ).strip()

        website_url = request.form.get(
            "website_url",
            "",
        ).strip()

        if not name:
            flash(
                "Brand name is required.",
                "danger",
            )

            return render_template(
                "brands.html",
                brands=[],
                search="",
                status="all",
                active_count=0,
                inactive_count=0,
                total_count=0,
                show_create_modal=True,
                form_data=request.form,
            )

        if len(name) > 150:
            flash(
                "Brand name must be 150 characters or fewer.",
                "danger",
            )

            return redirect(
                url_for("brands")
            )

        if website_url and not re.match(
            r"^https?://",
            website_url,
            re.IGNORECASE,
        ):
            website_url = "https://" + website_url

        conn = get_db_connection()

        try:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    SELECT id
                    FROM brands
                    WHERE LOWER(name) = LOWER(%s)
                    """,
                    (name,),
                )

                existing = cur.fetchone()

                if existing:
                    flash(
                        "A brand with this name already exists.",
                        "danger",
                    )

                    return redirect(
                        url_for("brands")
                    )

                cur.execute(
                    """
                    INSERT INTO brands (
                        name,
                        description,
                        logo_url,
                        website_url,
                        is_active,
                        created_by
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        TRUE,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        name,
                        description or None,
                        logo_url or None,
                        website_url or None,
                        session["user_id"],
                    ),
                )

                brand_id = cur.fetchone()["id"]

            conn.commit()

        finally:
            conn.close()

        log_activity(
            session["user_id"],
            "brand_created",
            "brand",
            brand_id,
            f"Created brand: {name}",
            brand_id,
        )

        flash(
            f"{name} has been created successfully.",
            "success",
        )

        return redirect(
            url_for(
                "brand_detail",
                brand_id=brand_id,
            )
        )

    return redirect(url_for("brands"))


@app.route(
    "/brands/<int:brand_id>"
)
@login_required
def brand_detail(brand_id):

    brand = get_brand_or_404(brand_id)

    if not brand:
        flash(
            "The requested brand could not be found.",
            "danger",
        )

        return redirect(
            url_for("brands")
        )

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    COUNT(*) AS count
                FROM brand_members
                WHERE brand_id = %s
                """,
                (brand_id,),
            )
            member_count = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT
                    COUNT(*) AS count
                FROM social_accounts
                WHERE brand_id = %s
                  AND is_connected = TRUE
                """,
                (brand_id,),
            )
            connected_account_count = (
                cur.fetchone()["count"]
            )

            cur.execute(
                """
                SELECT
                    COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
                """,
                (brand_id,),
            )
            post_count = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT
                    COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
                  AND status = 'published'
                """,
                (brand_id,),
            )
            published_post_count = (
                cur.fetchone()["count"]
            )

            cur.execute(
                """
                SELECT
                    COUNT(*) AS count
                FROM posts
                WHERE brand_id = %s
                  AND status = 'scheduled'
                """,
                (brand_id,),
            )
            scheduled_post_count = (
                cur.fetchone()["count"]
            )

            cur.execute(
                """
                SELECT
                    id,
                    platform,
                    account_name,
                    username,
                    profile_url,
                    is_connected
                FROM social_accounts
                WHERE brand_id = %s
                ORDER BY platform ASC
                """,
                (brand_id,),
            )
            social_accounts = cur.fetchall()

            cur.execute(
                """
                SELECT
                    id,
                    title,
                    content,
                    status,
                    scheduled_at,
                    published_at,
                    created_at
                FROM posts
                WHERE brand_id = %s
                ORDER BY created_at DESC
                LIMIT 8
                """,
                (brand_id,),
            )
            posts = cur.fetchall()

            cur.execute(
                """
                SELECT
                    al.id,
                    al.action,
                    al.description,
                    al.created_at,
                    u.name AS user_name
                FROM activity_logs al
                LEFT JOIN users u
                    ON u.id = al.user_id
                WHERE al.brand_id = %s
                ORDER BY al.created_at DESC
                LIMIT 8
                """,
                (brand_id,),
            )
            activity = cur.fetchall()

    finally:
        conn.close()

    return render_template(
        "brand_detail.html",
        brand=brand,
        member_count=member_count,
        connected_account_count=connected_account_count,
        post_count=post_count,
        published_post_count=published_post_count,
        scheduled_post_count=scheduled_post_count,
        social_accounts=social_accounts,
        posts=posts,
        activity=activity,
    )


@app.post(
    "/brands/<int:brand_id>/edit"
)
@login_required
def edit_brand(brand_id):

    brand = get_brand_or_404(brand_id)

    if not brand:
        flash(
            "Brand not found.",
            "danger",
        )

        return redirect(
            url_for("brands")
        )

    name = request.form.get(
        "name",
        "",
    ).strip()

    description = request.form.get(
        "description",
        "",
    ).strip()

    logo_url = request.form.get(
        "logo_url",
        "",
    ).strip()

    website_url = request.form.get(
        "website_url",
        "",
    ).strip()

    if not name:
        flash(
            "Brand name is required.",
            "danger",
        )

        return redirect(
            url_for(
                "brand_detail",
                brand_id=brand_id,
            )
        )

    if website_url and not re.match(
        r"^https?://",
        website_url,
        re.IGNORECASE,
    ):
        website_url = "https://" + website_url

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT id
                FROM brands
                WHERE LOWER(name) = LOWER(%s)
                  AND id != %s
                """,
                (
                    name,
                    brand_id,
                ),
            )

            duplicate = cur.fetchone()

            if duplicate:
                flash(
                    "Another brand already uses this name.",
                    "danger",
                )

                return redirect(
                    url_for(
                        "brand_detail",
                        brand_id=brand_id,
                    )
                )

            cur.execute(
                """
                UPDATE brands
                SET
                    name = %s,
                    description = %s,
                    logo_url = %s,
                    website_url = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    name,
                    description or None,
                    logo_url or None,
                    website_url or None,
                    brand_id,
                ),
            )

        conn.commit()

    finally:
        conn.close()

    log_activity(
        session["user_id"],
        "brand_updated",
        "brand",
        brand_id,
        f"Updated brand: {name}",
        brand_id,
    )

    flash(
        "Brand details updated successfully.",
        "success",
    )

    return redirect(
        url_for(
            "brand_detail",
            brand_id=brand_id,
        )
    )


@app.post(
    "/brands/<int:brand_id>/toggle"
)
@login_required
def toggle_brand(brand_id):

    brand = get_brand_or_404(brand_id)

    if not brand:
        flash(
            "Brand not found.",
            "danger",
        )

        return redirect(
            url_for("brands")
        )

    new_status = not brand["is_active"]

    conn = get_db_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE brands
                SET
                    is_active = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (
                    new_status,
                    brand_id,
                ),
            )

        conn.commit()

    finally:
        conn.close()

    action_text = (
        "activated"
        if new_status
        else "deactivated"
    )

    log_activity(
        session["user_id"],
        f"brand_{action_text}",
        "brand",
        brand_id,
        f"{action_text.title()} brand: {brand['name']}",
        brand_id,
    )

    flash(
        f"{brand['name']} has been {action_text}.",
        "success",
    )

    return redirect(
        url_for(
            "brand_detail",
            brand_id=brand_id,
        )
    )


# =========================================================
# PLACEHOLDER MODULE ROUTES
# These keep the navigation working while each module
# is implemented in its own feature step.
# =========================================================

@app.route("/social-accounts")
@login_required
def social_accounts():
    return render_template("social_accounts.html")


@app.route("/publisher")
@login_required
def publisher():
    return render_template("publisher.html")


@app.route("/calendar")
@login_required
def calendar():
    return render_template("calendar.html")


@app.route("/approvals")
@login_required
def approvals():
    return render_template("approvals.html")


@app.route("/community")
@login_required
def community():
    return render_template("community.html")


@app.route("/listening")
@login_required
def listening():
    return render_template("listening.html")


@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")


@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html")


@app.route("/notifications")
@login_required
def notifications():
    return render_template("notifications.html")


@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():
    return {
        "status": "ok",
        "service": "RicozSocial",
    }


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":
    init_db()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )