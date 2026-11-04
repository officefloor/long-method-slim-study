import java.io.BufferedWriter;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.javaparser.JavaParser;
import com.github.javaparser.ParseResult;
import com.github.javaparser.ParserConfiguration;
import com.github.javaparser.ParserConfiguration.LanguageLevel;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.Node;
import com.github.javaparser.ast.body.CallableDeclaration;
import com.github.javaparser.ast.stmt.ExplicitConstructorInvocationStmt;
import com.github.javaparser.ast.body.ConstructorDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.InitializerDeclaration;
import com.github.javaparser.ast.expr.ArrayInitializerExpr;
import com.github.javaparser.ast.expr.BinaryExpr;
import com.github.javaparser.ast.expr.ConditionalExpr;
import com.github.javaparser.ast.expr.Expression;
import com.github.javaparser.ast.expr.LambdaExpr;
import com.github.javaparser.ast.expr.MethodCallExpr;
import com.github.javaparser.ast.expr.ObjectCreationExpr;
import com.github.javaparser.ast.expr.StringLiteralExpr;
import com.github.javaparser.ast.expr.SwitchExpr;
import com.github.javaparser.ast.expr.TextBlockLiteralExpr;
import com.github.javaparser.ast.stmt.BlockStmt;
import com.github.javaparser.ast.stmt.BreakStmt;
import com.github.javaparser.ast.stmt.ContinueStmt;
import com.github.javaparser.ast.stmt.DoStmt;
import com.github.javaparser.ast.stmt.ForEachStmt;
import com.github.javaparser.ast.stmt.ForStmt;
import com.github.javaparser.ast.stmt.IfStmt;
import com.github.javaparser.ast.stmt.LabeledStmt;
import com.github.javaparser.ast.stmt.ReturnStmt;
import com.github.javaparser.ast.stmt.Statement;
import com.github.javaparser.ast.stmt.SwitchEntry;
import com.github.javaparser.ast.stmt.SwitchStmt;
import com.github.javaparser.ast.stmt.ThrowStmt;
import com.github.javaparser.ast.stmt.WhileStmt;
import com.github.javaparser.ast.stmt.YieldStmt;

import net.officefloor.officefloorslim.core.MethodShape;
import net.officefloor.officefloorslim.core.OfficeFloorSplit;
import net.officefloor.officefloorslim.core.ShapeExtractor;
import net.officefloor.sinewslim.core.Assessment;
import net.officefloor.sinewslim.core.Assessment.Status;
import net.officefloor.sinewslim.core.Assessor;
import net.officefloor.sinewslim.core.Params;
import net.officefloor.sinewslim.core.RunSlimmer;
import net.officefloor.sinewslim.facts.MethodFacts;
import net.officefloor.sinewslim.facts.MethodIndex;
import net.officefloor.sinewslim.facts.Seam;
import net.officefloor.sinewslim.facts.Stmt;
import net.officefloor.sinewslim.javaparser.JavaFacts;
import net.officefloor.sinewslim.javaparser.MethodUnit;
import net.officefloor.sinewslim.javaparser.ParsedFile;

/**
 * Exploratory harness (not part of the registered study): re-reads each category 4 method of one
 * repository, from the clone step 3 scanned, with the pinned OfficeFloorSlim 0.5.2 jar (SinewSlim
 * 0.2.3, JavaParser) on the class path.
 *
 * <pre>
 * java -cp lib/officefloorslim.jar:exploratory/harness/classes Explore REPO TARGETS.json OUT.jsonl
 * </pre>
 *
 * TARGETS.json is a list of {path, line, signature, outer: {start, end} | null, inner: {start, end} |
 * null}, written by long_method_slim_study.explore.harness. One JSON line per method is appended to
 * OUT.jsonl, preceded by a "start" line. A method with a result, or with a timeout the driver
 * recorded, is skipped on a re-run; one that only started (the run was interrupted) is tried again.
 *
 * Per method: the limits raised (SinewSlim's max_inputs, the split's carried values; k = 5 is the
 * scan's and checks the harness), and the syntax of the statement that blocks it.
 */
public final class Explore {

	static final int[] LIMITS = { 5, 6, 7, 8, 10 };
	/**
	 * The result's version. 2 adds every jump (whatever its target), the jumps inside lambdas and
	 * anonymous classes, and the body's shape (top-level statements, a constructor that only delegates).
	 * 3 adds the kind of the only statement of a one-statement body (a single return is not a jump).
	 */
	static final int VERSION = 3;
	static final ObjectMapper JSON = new ObjectMapper();
	static final LanguageLevel[] LEVELS = { LanguageLevel.JAVA_25, LanguageLevel.JAVA_8 }; // as JavaFacts

	public static void main(String[] args) throws Exception {
		Path repo = Path.of(args[0]);
		JsonNode targets = JSON.readTree(new File(args[1]));
		Path out = Path.of(args[2]);
		// id -> the version of its latest result (a timeout the driver recorded counts as any version)
		Map<String, Integer> done = new java.util.HashMap<>();
		if (Files.exists(out)) {
			for (String l : Files.readAllLines(out)) {
				JsonNode n = JSON.readTree(l);
				// a result, or a timeout the driver recorded, is done; a bare start (a run that was
				// interrupted) is tried again
				if (!n.has("start")) {
					int v = n.has("timeout") ? Integer.MAX_VALUE : n.path("v").asInt(1);
					done.merge(n.get("id").asText(), v, Math::max);
				}
			}
		}
		Map<String, List<JsonNode>> byFile = new LinkedHashMap<>();
		for (JsonNode t : targets) {
			byFile.computeIfAbsent(t.get("path").asText(), k -> new ArrayList<>()).add(t);
		}
		try (BufferedWriter w = Files.newBufferedWriter(out, StandardCharsets.UTF_8, StandardOpenOption.CREATE,
				StandardOpenOption.APPEND)) {
			for (var e : byFile.entrySet()) {
				// a target asks for the version it needs (the driver's): an older result is read again
				List<JsonNode> todo = e.getValue().stream()
						.filter(t -> done.getOrDefault(id(t), 0) < t.path("version").asInt(1)).toList();
				if (todo.isEmpty()) {
					continue;
				}
				Path file = repo.resolve(e.getKey());
				ParsedFile parsed;
				CompilationUnit cu;
				try {
					// as the scan reads it (sinewslim Scanner): a malformed byte becomes U+FFFD, not an error
					String source = new String(Files.readAllBytes(file), StandardCharsets.UTF_8);
					parsed = JavaFacts.parse(e.getKey(), source, List.of(ShapeExtractor.INSTANCE));
					cu = parse(source);
				} catch (Throwable x) {
					// the file cannot be read or parsed: each of its methods is a result with the error
					for (JsonNode t : todo) {
						emit(w, Map.of("id", id(t), "error", "file: " + x));
					}
					continue;
				}
				for (JsonNode t : todo) {
					emit(w, Map.of("id", id(t), "start", true));
					Map<String, Object> r = new LinkedHashMap<>();
					r.put("id", id(t));
					r.put("v", VERSION);
					try {
						method(t, parsed, cu, r);
					} catch (Throwable x) {
						r.put("error", x.toString());
					}
					emit(w, r);
				}
			}
		}
	}

	static String id(JsonNode t) {
		return t.get("path").asText() + ":" + t.get("line").asInt() + ":" + t.get("signature").asText();
	}

	static void emit(BufferedWriter w, Map<String, Object> r) throws Exception {
		w.write(JSON.writeValueAsString(r));
		w.newLine();
		w.flush();
	}

	static CompilationUnit parse(String source) {
		for (LanguageLevel level : LEVELS) {
			ParseResult<CompilationUnit> r = new JavaParser(new ParserConfiguration().setLanguageLevel(level))
					.parse(source);
			if (r.isSuccessful() && r.getResult().isPresent()) {
				return r.getResult().get();
			}
		}
		return null;
	}

	static void method(JsonNode t, ParsedFile parsed, CompilationUnit cu, Map<String, Object> r) {
		int line = t.get("line").asInt();
		String sig = t.get("signature").asText();
		MethodUnit m = parsed.methods().stream()
				.filter(u -> (u.declLine() == line || u.nameLine() == line) && u.signature().equals(sig)).findFirst()
				.orElse(null);
		if (m == null) {
			r.put("found", false);
			return;
		}
		r.put("found", true);
		MethodFacts facts = m.facts();
		MethodShape shape = m.extras().get(ShapeExtractor.KEY).orElseThrow();

		// the limits raised
		Map<String, Object> sens = new LinkedHashMap<>();
		Stmt outer = t.hasNonNull("outer") ? find(facts.body(), t.get("outer")) : null;
		for (int k : LIMITS) {
			Map<String, Object> s = new LinkedHashMap<>();
			Assessor a = new Assessor(Params.DEFAULTS.toBuilder().maxInputs(k).build(), true, true, 1);
			s.put("conventional", a.assess(facts).status().name());
			OfficeFloorSplit.Params p = new OfficeFloorSplit.Params(26, 25, k);
			s.put("injection", OfficeFloorSplit.plan(facts, shape, p, OfficeFloorSplit.Version.INJECTION).feasible());
			s.put("combined", OfficeFloorSplit.plan(facts, shape, p, OfficeFloorSplit.Version.COMBINED).feasible());
			if (outer != null) {
				MethodFacts body = RunSlimmer.runFacts(facts, new MethodIndex(facts, true), List.of(outer));
				Status st = a.assess(body).status();
				s.put("body", st.name());
			}
			sens.put(Integer.toString(k), s);
		}
		r.put("limits", sens);
		r.put("conventional_unlimited_inputs",
				new Assessor(Params.DEFAULTS.unlimitedInputs(), true, true, 1).assess(facts).status().name());

		// the syntax: the method, the outer blocking statement, the innermost statement SinewSlim names
		if (cu == null) {
			r.put("syntax", "unparsed");
			return;
		}
		Node decl = declaration(cu, m);
		if (decl == null) {
			r.put("syntax", "no declaration");
			return;
		}
		r.put("method_jumps", jumps(decl, decl));
		r.putAll(allJumps(decl, decl, "method_"));
		BlockStmt body = decl instanceof MethodDeclaration md ? md.getBody().orElse(null)
				: decl instanceof ConstructorDeclaration cd ? cd.getBody() : null;
		if (body != null) {
			r.put("top_statements", body.getStatements().size());
			r.put("constructor_delegation_only", body.getStatements().size() == 1
					&& body.getStatement(0) instanceof ExplicitConstructorInvocationStmt);
			if (body.getStatements().size() == 1) {
				r.put("only_statement", body.getStatement(0).getClass().getSimpleName());
			}
		}
		MethodIndex index = new MethodIndex(facts, false);
		if (t.hasNonNull("outer")) {
			Statement s = statement(decl, t.get("outer"));
			if (s != null) {
				r.put("outer", describe(s, index));
			}
		}
		if (t.hasNonNull("inner")) {
			Statement s = statement(decl, t.get("inner"));
			if (s != null) {
				r.put("inner", describe(s, index));
			}
		}
	}

	/** The facts' statement with these lines (outermost first), or null. */
	static Stmt find(Stmt node, JsonNode at) {
		int a = at.get("start").asInt(), b = at.get("end").asInt();
		if (node.start() == a && node.end() == b && !node.seq()) {
			return node;
		}
		for (Stmt k : node.kids()) {
			Stmt f = find(k, at);
			if (f != null) {
				return f;
			}
		}
		return null;
	}

	static Node declaration(CompilationUnit cu, MethodUnit m) {
		List<Node> found = new ArrayList<>();
		cu.walk(n -> {
			if ((n instanceof CallableDeclaration || n instanceof InitializerDeclaration || n instanceof LambdaExpr)
					&& n.getBegin().isPresent() && n.getEnd().isPresent()) {
				int b = n.getBegin().get().line, e = n.getEnd().get().line;
				if ((b == m.declLine() || b == m.nameLine()) && e == m.endLine()) {
					found.add(n);
				}
			}
		});
		if (found.isEmpty()) {
			cu.walk(CallableDeclaration.class, c -> {
				if (c.getName().getBegin().map(p -> p.line == m.nameLine()).orElse(false)) {
					found.add(c);
				}
			});
		}
		return found.isEmpty() ? null : found.get(0);
	}

	/** The statement spanning exactly these lines inside the declaration, not a bare block when another fits. */
	static Statement statement(Node decl, JsonNode at) {
		int a = at.get("start").asInt(), b = at.get("end").asInt();
		List<Statement> hits = new ArrayList<>();
		decl.walk(Statement.class, s -> {
			if (s.getBegin().isPresent() && s.getEnd().isPresent() && s.getBegin().get().line == a
					&& s.getEnd().get().line == b) {
				hits.add(s);
			}
		});
		return hits.stream().min(Comparator.comparingInt(s -> s instanceof BlockStmt ? 1 : 0)).orElse(null);
	}

	static int lines(Node n) {
		return n.getBegin().isPresent() && n.getEnd().isPresent() ? n.getEnd().get().line - n.getBegin().get().line + 1
				: 0;
	}

	static Map<String, Object> describe(Statement s, MethodIndex index) {
		Map<String, Object> d = new LinkedHashMap<>();
		Statement core = s instanceof LabeledStmt l ? l.getStatement() : s;
		d.put("kind", core.getClass().getSimpleName());
		d.put("lines", lines(s));
		d.put("jumps", jumps(s, core)); // what leaves the runs inside it: its own break and continue count
		d.putAll(allJumps(s, s, "")); // and every jump in it, whatever its target (a nested loop's break too)
		int lo = s.getBegin().get().line, hi = s.getEnd().get().line;
		try {
			Seam seam = index.seam(lo, hi);
			d.put("inputs", seam.inputs().size());
			d.put("outputs", seam.outputs().size());
		} catch (RuntimeException x) {
			d.put("seam", x.toString());
		}
		if (core instanceof SwitchStmt sw) {
			d.put("switch", switchShape(sw.getEntries(), sw));
		} else if (core instanceof IfStmt i) {
			d.put("if", ifShape(i));
		} else if (!(core instanceof ForStmt || core instanceof ForEachStmt || core instanceof WhileStmt
				|| core instanceof DoStmt)) {
			d.put("expression", expressionShape(core));
		}
		return d;
	}

	/** Return, break and continue in the node that leave the scope (or target it), and throws. */
	static Map<String, Integer> jumps(Node n, Node scope) {
		Map<String, Integer> j = new LinkedHashMap<>(Map.of("return", 0, "break", 0, "continue", 0, "throw", 0,
				"labelled", 0, "yield", 0));
		n.walk(x -> {
			if (x instanceof ReturnStmt && !inLambdaOrClass(x, scope)) {
				j.merge("return", 1, Integer::sum);
			} else if (x instanceof ThrowStmt && !inLambdaOrClass(x, scope)) {
				j.merge("throw", 1, Integer::sum);
			} else if (x instanceof BreakStmt b && leaves(b, scope)) {
				j.merge(b.getLabel().isPresent() ? "labelled" : "break", 1, Integer::sum);
			} else if (x instanceof ContinueStmt c && leaves(c, scope)) {
				j.merge(c.getLabel().isPresent() ? "labelled" : "continue", 1, Integer::sum);
			} else if (x instanceof YieldStmt) {
				j.merge("yield", 1, Integer::sum);
			}
		});
		return j;
	}

	/**
	 * Every return, break, continue and yield in the node, whatever its target (a break of a loop nested
	 * inside still crosses a cut between that loop's statements), as {prefix}all_jumps; and the jumps that
	 * belong to a lambda or anonymous class inside it, as {prefix}lambda_jumps.
	 */
	static Map<String, Object> allJumps(Node n, Node scope, String prefix) {
		Map<String, Integer> all = new LinkedHashMap<>(Map.of("return", 0, "break", 0, "continue", 0, "yield", 0));
		int[] lambda = { 0 };
		n.walk(x -> {
			String k = x instanceof ReturnStmt ? "return" : x instanceof BreakStmt ? "break"
					: x instanceof ContinueStmt ? "continue" : x instanceof YieldStmt ? "yield" : null;
			if (k == null) {
				return;
			}
			if (inLambdaOrClass(x, scope)) {
				lambda[0]++;
			} else {
				all.merge(k, 1, Integer::sum);
			}
		});
		return Map.of(prefix + "all_jumps", all, prefix + "lambda_jumps", lambda[0]);
	}

	static boolean inLambdaOrClass(Node x, Node scope) {
		for (Node p = x.getParentNode().orElse(null); p != null && p != scope; p = p.getParentNode().orElse(null)) {
			if (p instanceof LambdaExpr || p instanceof ObjectCreationExpr || p instanceof CallableDeclaration) {
				return true;
			}
		}
		return false;
	}

	/** Whether a break or continue jumps out of the scope: no loop (or, for a break, switch) between. */
	static boolean leaves(Statement j, Node scope) {
		boolean isBreak = j instanceof BreakStmt;
		boolean labelled = isBreak ? ((BreakStmt) j).getLabel().isPresent() : ((ContinueStmt) j).getLabel().isPresent();
		String label = !labelled ? null
				: isBreak ? ((BreakStmt) j).getLabel().get().asString() : ((ContinueStmt) j).getLabel().get().asString();
		for (Node p = j.getParentNode().orElse(null); p != null; p = p.getParentNode().orElse(null)) {
			if (p instanceof LambdaExpr || p instanceof ObjectCreationExpr) {
				return false;
			}
			// a jump leaves the scope when its target is the scope itself (it leaves every run inside it) or
			// outside it
			if (label != null) {
				if (p instanceof LabeledStmt l && l.getLabel().asString().equals(label)) {
					return p == scope || !within(p, scope);
				}
			} else if (p instanceof ForStmt || p instanceof ForEachStmt || p instanceof WhileStmt || p instanceof DoStmt
					|| (isBreak && (p instanceof SwitchStmt || p instanceof SwitchExpr))) {
				return p == scope || !within(p, scope);
			}
			if (p == scope) {
				return true;
			}
		}
		return true;
	}

	static boolean within(Node n, Node scope) {
		for (Node p = n; p != null; p = p.getParentNode().orElse(null)) {
			if (p == scope) {
				return true;
			}
		}
		return false;
	}

	static Map<String, Object> switchShape(List<SwitchEntry> entries, Node sw) {
		Map<String, Object> d = new LinkedHashMap<>();
		int labels = 0, empty = 0, fallthrough = 0, returning = 0, arrow = 0;
		List<Integer> bodyLines = new ArrayList<>();
		for (int i = 0; i < entries.size(); i++) {
			SwitchEntry e = entries.get(i);
			labels += Math.max(1, e.getLabels().size());
			if (e.getType() != SwitchEntry.Type.STATEMENT_GROUP) {
				arrow++;
			}
			if (e.getStatements().isEmpty()) {
				empty++;
				continue;
			}
			int n = 0;
			for (Statement s : e.getStatements()) {
				n += lines(s);
			}
			bodyLines.add(n);
			Statement last = e.getStatements().get(e.getStatements().size() - 1);
			boolean ends = last instanceof BreakStmt || last instanceof ReturnStmt || last instanceof ThrowStmt
					|| last instanceof ContinueStmt || last instanceof YieldStmt;
			if (last instanceof ReturnStmt) {
				returning++;
			}
			if (!ends && e.getType() == SwitchEntry.Type.STATEMENT_GROUP && i < entries.size() - 1) {
				fallthrough++;
			}
		}
		bodyLines.sort(null);
		d.put("entries", entries.size());
		d.put("labels", labels);
		d.put("empty_entries", empty);
		d.put("fallthrough", fallthrough);
		d.put("returning", returning);
		d.put("arrow", arrow);
		d.put("max_case_lines", bodyLines.isEmpty() ? 0 : bodyLines.get(bodyLines.size() - 1));
		d.put("median_case_lines", bodyLines.isEmpty() ? 0 : bodyLines.get(bodyLines.size() / 2));
		d.put("cases_over_target", bodyLines.stream().filter(x -> x > 25).count());
		return d;
	}

	static Map<String, Object> ifShape(IfStmt i) {
		Map<String, Object> d = new LinkedHashMap<>();
		int branches = 1, chain = 0, maxBranch = lines(i.getThenStmt());
		Optional<Statement> e = i.getElseStmt();
		while (e.isPresent()) {
			branches++;
			if (e.get() instanceof IfStmt next) {
				chain++;
				maxBranch = Math.max(maxBranch, lines(next.getThenStmt()));
				e = next.getElseStmt();
			} else {
				maxBranch = Math.max(maxBranch, lines(e.get()));
				e = Optional.empty();
			}
		}
		d.put("branches", branches);
		d.put("else_if", chain);
		d.put("max_branch_lines", maxBranch);
		d.put("in_loop", i.findAncestor(Statement.class, a -> a instanceof ForStmt || a instanceof ForEachStmt
				|| a instanceof WhileStmt || a instanceof DoStmt).isPresent());
		d.put("nested_ifs", i.findAll(IfStmt.class).size() - 1 - chain);
		return d;
	}

	/** The largest construct inside a long statement: what makes one statement long. */
	static Map<String, Object> expressionShape(Statement s) {
		Map<String, Object> d = new LinkedHashMap<>();
		Map<String, Integer> largest = new HashMap<>();
		s.walk(n -> {
			String k = null;
			if (n instanceof LambdaExpr) {
				k = "lambda";
			} else if (n instanceof ObjectCreationExpr o && o.getAnonymousClassBody().isPresent()) {
				k = "anonymous_class";
			} else if (n instanceof ArrayInitializerExpr) {
				k = "array_initializer";
			} else if (n instanceof SwitchExpr) {
				k = "switch_expression";
			} else if (n instanceof TextBlockLiteralExpr) {
				k = "text_block";
			} else if (n instanceof ConditionalExpr) {
				k = "conditional";
			}
			if (k != null) {
				largest.merge(k, lines(n), Math::max);
			}
		});
		int[] chain = { 0 };
		s.walk(MethodCallExpr.class, c -> chain[0] = Math.max(chain[0], chainLength(c)));
		int[] concat = { 0 };
		s.walk(BinaryExpr.class, b -> {
			if (b.getOperator() == BinaryExpr.Operator.PLUS && !(b.getParentNode().orElse(null) instanceof BinaryExpr)) {
				int strings = (int) b.findAll(StringLiteralExpr.class).size();
				concat[0] = Math.max(concat[0], strings);
			}
		});
		int[] args = { 0 };
		s.walk(MethodCallExpr.class, c -> args[0] = Math.max(args[0], c.getArguments().size()));
		s.walk(ObjectCreationExpr.class, c -> args[0] = Math.max(args[0], c.getArguments().size()));
		d.put("largest", largest);
		d.put("max_call_chain", chain[0]);
		d.put("max_string_literals_concatenated", concat[0]);
		d.put("max_arguments", args[0]);
		d.put("lines", lines(s));
		return d;
	}

	static int chainLength(MethodCallExpr c) {
		int n = 1;
		Optional<Expression> scope = c.getScope();
		while (scope.isPresent() && scope.get() instanceof MethodCallExpr m) {
			n++;
			scope = m.getScope();
		}
		return n;
	}
}
