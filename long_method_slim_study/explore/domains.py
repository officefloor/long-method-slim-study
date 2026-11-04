"""Code each repository's domain from its name, GitHub description and topics (the snapshot written by
explore.meta), by keyword rules tried in order, the first that matches winning.

The rules are crude on purpose: written down, applied by code, and reviewable, so the coding can be
rerun and argued with. They are not a validated taxonomy. The order runs from the most specific
domain to the most generic, so a "SQL parser library" is a database before it is language tooling,
and either before it is a library. Tutorials and exercise code come first: they are not systems. Anything no rule matches is "unknown".
"""
from __future__ import annotations

import re

RULES: list[tuple[str, list[str]]] = [
    ("learning and examples", [
        "leetcode", "hackerrank", "offer", "interview", "tutorial", "course", "mooc", "example", "examples",
        "quickstart", "quickstarts", "sample", "samples", "demo", "learning java", "java8 learning", "java8 study",
        "design pattern", "designpattern", "algorithms", "solutions", "课", "剑指", "pet clinic", "petclinic"]),
    ("database and query", [
        "database", "sql", "query", "nosql", "olap", "oltp", "time series", "timeseries", "time-series",
        "key-value", "key value", "storage engine", "data grid", "in-memory data", "search engine", "lucene",
        "elasticsearch", "solr", "full-text", "orm", "jdbc", "hive", "presto", "hbase", "data warehouse",
        "big data", "bigdata", "redis", "cassandra", "graph database"]),
    ("language tooling", [
        "compiler", "parser", "interpreter", "decompil", "disassembl", "bytecode", "openjdk", "jdk",
        "java virtual machine", "lexer", "grammar", "programming language", "scripting language", "transpil",
        "static analysis", "code analysis", "linter", "lint", "ide", "refactor", "obfuscat", "code generat",
        "antlr", "language server", "debugger", "profiler", "netbeans", "eclipse plugin",
        "reverse engineer", "jadx", "smali", "dex", "build tool", "gradle", "maven", "expression language",
        "parsing", "formatter", "compressor", "minif", "hotfix", "code generator", "generator gui", "epub", "conformance"]),
    ("numeric, scientific and ML", [
        "machine learning", "deep learning", "neural", "mathemat", "math", "numerical", "numeric", "scientific",
        "statistic", "astronom", "astrodynamic", "orbit", "space flight", "meteorolog", "weather", "climate",
        "gis", "geospatial", "geographic", "remote sensing", "satellite", "bioinformatic", "chemistry",
        "physics", "simulation", "linear algebra", "tensor", "image processing", "computer vision", "signal",
        "noise", "procedural generation", "ml", "ai"]),
    ("games and graphics", [
        "game", "gaming", "roguelike", "graphics", "opengl", "rendering", "render", "3d", "minecraft", "libgdx",
        "chart", "plot", "visualiz", "animation", "processing"]),
    ("android and UI", [
        "android", "ui", "view", "widget", "popup", "material", "recyclerview", "layout", "swing", "javafx",
        "look and feel", "laf", "theme", "calendar", "dialog", "image loader", "imageview", "picker", "toast",
        "banner", "indicator", "refresh", "gesture", "keyboard"]),
    ("distributed systems and middleware", [
        "distributed", "cluster", "messaging", "message queue", "mq", "kafka", "rpc", "grpc", "microservice",
        "service mesh", "kubernetes", "cloud", "stream processing", "streaming", "workflow", "scheduler",
        "application server", "server", "gateway", "proxy", "network", "netty", "http", "websocket",
        "serverless", "orchestrat", "consensus", "raft", "zookeeper", "hadoop", "spark", "flink", "mqtt", "broker",
        "transaction", "schedul", "binlog", "integration", "oauth", "concurrency", "thread pool", "线程池",
        "rabbitmq", "dubbo", "socket", "posix", "pty", "工作流"]),
    ("frameworks and libraries", [
        "framework", "librar", "sdk", "toolkit", "api", "utilities", "util", "client", "plugin", "component",
        "annotation", "spring", "commons", "excel", "download", "payment", "document conver", "similarity",
        "architecture", "rxjava", "retrofit", "fingerprint", "property graph", "collections", "logging", "testing", "mock", "validation", "cache", "dependency injection", "serializ", "json", "xml", "template"]),
    ("applications", [
        "app", "application", "tool", "desktop", "bot", "launcher", "editor", "browser", "player", "manager",
        "management system", "ios", "crawler", "spider", "client app", "客户端", "应用", "阅读", "travel",
        "billing", "banking", "healthcare", "home automation", "openhab", "osmand", "pick and place", "robocode", "mobile", "platform", "system", "website", "blog", "shop"]),
]


def words(meta: dict, full_name: str) -> str:
    """The text the rules read: the repository's name split into words, its description and topics."""
    name = full_name.split("/", 1)[-1]
    name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name).replace("-", " ").replace("_", " ").replace(".", " ")
    parts = [name, meta.get("description") or "", " ".join(t.replace("-", " ") for t in meta.get("topics") or [])]
    return " " + " ".join(parts).lower() + " "


def matches(text: str, keyword: str) -> bool:
    # short keywords (ide, ml, ai, mq, orm, gis, 3d, sql, jdk, jvm, api, app, bot) only as whole words
    if len(keyword) <= 3:
        return re.search(rf"(?<![a-z]){re.escape(keyword)}(?![a-z])", text) is not None
    return keyword in text


def domain(meta: dict, full_name: str) -> tuple[str, str | None]:
    """(domain, the keyword that decided it)."""
    text = words(meta, full_name)
    for name, keywords in RULES:
        for k in keywords:
            if matches(text, k):
                return name, k
    return "unknown", None
